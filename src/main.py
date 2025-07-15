from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, HttpUrl
import docker
import asyncio
import json
import uuid
import os
import logging
import time
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION,
    description="一个基于Docker的安全Python代码执行环境"
)

# Pydantic模型定义
class RefFile(BaseModel):
    """引用文件模型"""
    url: HttpUrl
    filename: Optional[str] = None  # 可选的文件名，如果不提供则从URL推断

class ExecuteRequest(BaseModel):
    """代码执行请求模型"""
    code: str
    timeout: Optional[int] = 30
    work_dir: Optional[str] = "/data"  # 工作目录，默认为/data
    ref_files: Optional[List[RefFile]] = None

def initialize_docker_client():
    """初始化Docker客户端，带重试机制"""
    docker_config = config.get_docker_client_config()
    max_retries = docker_config['max_retries']
    retry_delay = docker_config['retry_delay']
    timeout = docker_config['timeout']
    
    for attempt in range(max_retries):
        try:
            client = docker.from_env(timeout=timeout)
            # 测试连接
            client.ping()
            logger.info("Docker客户端初始化成功")
            return client
        except docker.errors.DockerException as e:
            logger.error(f"Docker连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Docker客户端初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error("Docker客户端初始化最终失败")
    return None

# Initialize Docker client with retry
docker_client = initialize_docker_client()

class SandboxExecutor:
    def __init__(self):
        self.image_name = config.EXECUTOR_IMAGE_NAME
        self.dockerfile_path = config.EXECUTOR_DOCKERFILE_PATH
        self.container_config = config.get_container_config()
        
        if docker_client:
            self._ensure_image_exists()
        else:
            logger.error("无法初始化SandboxExecutor：Docker客户端不可用")
    
    def _ensure_image_exists(self):
        """确保执行器镜像存在"""
        try:
            docker_client.images.get(self.image_name)
            logger.info(f"执行器镜像 {self.image_name} 已存在")
        except docker.errors.ImageNotFound:
            logger.info(f"构建执行器镜像 {self.image_name}...")
            try:
                # Build the image from Dockerfile.executor
                docker_client.images.build(
                    path=".",
                    dockerfile=self.dockerfile_path,
                    tag=self.image_name,
                    rm=True
                )
                logger.info(f"镜像 {self.image_name} 构建成功")
            except Exception as e:
                logger.error(f"镜像构建失败: {e}")
                raise
        except Exception as e:
            logger.error(f"检查镜像时发生错误: {e}")
            raise
    
    async def download_ref_files(self, ref_files: List[RefFile], work_dir: Path) -> List[str]:
        """下载引用文件到工作目录"""
        downloaded_files = []
        
        if not ref_files:
            return downloaded_files
            
        logger.info(f"开始下载 {len(ref_files)} 个引用文件")
        
        async with aiohttp.ClientSession() as session:
            for ref_file in ref_files:
                try:
                    # 确定文件名
                    if ref_file.filename:
                        filename = ref_file.filename
                    else:
                        # 从URL推断文件名
                        filename = Path(str(ref_file.url)).name or f"file_{uuid.uuid4().hex[:8]}"
                    
                    # 创建目标路径
                    target_path = work_dir / filename
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 下载文件
                    async with session.get(str(ref_file.url)) as response:
                        if response.status == 200:
                            async with aiofiles.open(target_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    await f.write(chunk)
                            
                            downloaded_files.append(str(target_path))
                            logger.info(f"文件下载成功: {ref_file.url} -> {target_path}")
                        else:
                            logger.error(f"文件下载失败: {ref_file.url}, 状态码: {response.status}")
                            raise HTTPException(status_code=400, detail=f"Failed to download file from {ref_file.url}")
                            
                except Exception as e:
                    logger.error(f"下载文件时发生错误: {ref_file.url}, 错误: {e}")
                    raise HTTPException(status_code=400, detail=f"Error downloading file: {str(e)}")
        
        return downloaded_files
    
    async def execute_code(self, code: str, timeout: int = None, work_dir_str: str = "/data", ref_files: Optional[List[RefFile]] = None) -> Dict[str, Any]:
        """在新的容器中执行代码"""
        if timeout is None:
            timeout = self.container_config['timeout']
            
        container_name = f"sandbox-{uuid.uuid4().hex[:8]}"
        container = None
        
        logger.info(f"开始执行代码，容器名: {container_name}，超时: {timeout}秒")
        
        # 处理引用文件下载
        temp_work_dir = None
        downloaded_files = []
        
        if ref_files:
            # 创建临时工作目录
            import tempfile
            temp_work_dir = Path(tempfile.mkdtemp(prefix="sandbox_"))
            logger.info(f"创建临时工作目录: {temp_work_dir}")
            
            try:
                # 下载文件
                downloaded_files = await self.download_ref_files(ref_files, temp_work_dir)
                logger.info(f"已下载 {len(downloaded_files)} 个文件到临时目录")
                
            except Exception as e:
                # 清理工作目录
                if temp_work_dir and temp_work_dir.exists():
                    import shutil
                    shutil.rmtree(temp_work_dir)
                raise
        
        try:
            # 创建并启动容器
            container_args = {
                'image': self.image_name,
                'command': ["python", "-c", code],
                'name': container_name,
                'detach': True,
                'remove': False,  # 先不自动删除，方便获取日志
                'mem_limit': self.container_config['mem_limit'],
                'cpu_quota': self.container_config['cpu_quota'],
                'network_disabled': self.container_config['network_disabled'],
                'security_opt': self.container_config['security_opt'],
                'user': self.container_config['user'],
            }
            
            container = docker_client.containers.run(**container_args)
            
            # 如果有引用文件，将文件拷贝到容器内
            if downloaded_files:
                logger.info(f"开始将 {len(downloaded_files)} 个文件拷贝到容器内")
                
                # 多次尝试确保容器内的目标目录存在
                import time
                for _ in range(3):
                    exec_result = container.exec_run(f"mkdir -p {work_dir_str}")
                    if exec_result.exit_code == 0:
                        break
                    logger.warning(f"创建目录失败: {exec_result.output.decode()}，重试...")
                    time.sleep(1)
                else:
                    logger.error(f"多次尝试后仍无法创建目录: {work_dir_str}")
                    raise RuntimeError(f"无法在容器内创建目录: {work_dir_str}")
                
                # 拷贝每个文件到容器内
                for local_file_path in downloaded_files:
                    local_path = Path(local_file_path)
                    target_path = f"{work_dir_str}/{local_path.name}"
                    
                    try:
                        # 读取本地文件内容
                        with open(local_path, 'rb') as f:
                            file_content = f.read()
                        
                        # 将文件内容写入容器
                        import tarfile
                        import io
                        
                        # 创建tar文件
                        tar_stream = io.BytesIO()
                        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                            tarinfo = tarfile.TarInfo(name=local_path.name)
                            tarinfo.size = len(file_content)
                            tar.addfile(tarinfo, io.BytesIO(file_content))
                        
                        tar_stream.seek(0)
                        
                        # 将tar文件提取到容器中
                        container.put_archive(work_dir_str, tar_stream.getvalue())
                        logger.info(f"文件已拷贝: {local_path.name} -> {target_path}")
                        
                    except Exception as e:
                        logger.error(f"拷贝文件失败 {local_file_path}: {e}")
                        raise
            
            logger.info(f"容器 {container_name} 已创建，等待执行完成")
            
            # 等待容器执行完成
            result = container.wait(timeout=timeout)
            
            # 获取输出
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            # 获取退出状态
            exit_code = result['StatusCode']
            
            logger.info(f"容器 {container_name} 执行完成，退出码: {exit_code}")
            
            return {
                "success": exit_code == 0,
                "output": logs,
                "exit_code": exit_code,
                "container_id": container.id[:12]
            }
            
        except docker.errors.ContainerError as e:
            logger.error(f"容器执行错误: {e}")
            return {
                "success": False,
                "output": f"Container error: {str(e)}",
                "exit_code": e.exit_status,
                "container_id": None
            }
        except Exception as e:
            logger.error(f"代码执行异常: {e}")
            return {
                "success": False,
                "output": f"Execution error: {str(e)}",
                "exit_code": -1,
                "container_id": None
            }
        finally:
            # 清理容器
            if container:
                try:
                    container.remove(force=True)
                    logger.info(f"容器 {container_name} 已清理")
                except Exception as e:
                    logger.warning(f"清理容器 {container_name} 失败: {e}")
            
            # 清理工作目录
            if temp_work_dir and temp_work_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(temp_work_dir)
                    logger.info(f"工作目录 {temp_work_dir} 已清理")
                except Exception as e:
                    logger.warning(f"清理工作目录 {temp_work_dir} 失败: {e}")

# 创建执行器实例
sandbox_executor = SandboxExecutor() if docker_client else None

@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_status = {
        "status": "unknown",
        "docker_connected": False,
        "executor_image_ready": False,
        "sandbox_executor_ready": False,
        "timestamp": time.time()
    }
    
    try:
        if not docker_client:
            health_status.update({
                "status": "unhealthy",
                "error": "Docker客户端未初始化"
            })
            return health_status
        
        # 检查Docker连接
        docker_client.ping()
        health_status["docker_connected"] = True
        logger.info("Docker连接检查通过")
        
        # 检查执行器镜像是否存在
        try:
            docker_client.images.get(config.EXECUTOR_IMAGE_NAME)
            health_status["executor_image_ready"] = True
            logger.info("执行器镜像检查通过")
        except docker.errors.ImageNotFound:
            health_status["executor_image_ready"] = False
            logger.warning("执行器镜像不存在")
        
        # 检查沙盒执行器是否就绪
        if sandbox_executor:
            health_status["sandbox_executor_ready"] = True
        
        # 综合判断健康状态
        if (health_status["docker_connected"] and 
            health_status["executor_image_ready"] and 
            health_status["sandbox_executor_ready"]):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        health_status.update({
            "status": "unhealthy",
            "error": str(e)
        })
        return health_status

@app.post("/execute")
async def execute_code(request: ExecuteRequest):
    """执行代码端点"""
    if not docker_client or not sandbox_executor:
        raise HTTPException(status_code=500, detail="Docker client not available")
    
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")
    
    # 在新的容器中执行代码
    result = await sandbox_executor.execute_code(
        code=request.code, 
        timeout=request.timeout,
        work_dir_str=request.work_dir,
        ref_files=request.ref_files
    )
    
    return result

if __name__ == "__main__":
    import uvicorn
    api_config = config.get_api_config()
    uvicorn.run(
        app, 
        host=api_config['host'], 
        port=api_config['port'],
        log_level=config.LOG_LEVEL.lower()
    )