"""沙盒服务类"""

import os
import uuid
import tempfile
import logging
import tarfile
import io
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional

import docker
from fastapi import HTTPException

from models.request_models import RefFile
from models.response_models import ExecuteResponse, ImageFile
from services.docker_service import DockerService
from services.file_service import FileService
from config import config

logger = logging.getLogger(__name__)


class SandboxService:
    """沙盒执行服务类"""
    
    def __init__(self):
        self.docker_service = DockerService()
        self.file_service = FileService()
        
        if not self.docker_service.is_available():
            logger.error("无法初始化SandboxService：Docker服务不可用")
    
    async def execute_code(
        self, 
        code: str, 
        timeout: int = None, 
        work_dir_str: str = "/data", 
        ref_files: Optional[List[RefFile]] = None
    ) -> ExecuteResponse:
        """执行代码并返回结果"""
        if not self.docker_service.is_available():
            raise HTTPException(status_code=503, detail="Docker服务不可用")
        
        if timeout is None:
            timeout = config.DEFAULT_TIMEOUT
        
        docker_client = self.docker_service.get_client()
        container_name = f"sandbox-{uuid.uuid4().hex[:8]}"
        host_work_dir = None
        
        try:
            # 创建宿主机工作目录
            host_work_dir = tempfile.mkdtemp(prefix=f"sandbox_{container_name}_")
            logger.info(f"创建宿主机工作目录: {host_work_dir}")
            
            # 下载引用文件到宿主机工作目录
            if ref_files:
                logger.info(f"开始下载 {len(ref_files)} 个引用文件到宿主机挂载目录")
                await self.file_service.download_ref_files(ref_files, Path(host_work_dir))
                logger.info(f"已下载 {len(ref_files)} 个文件到宿主机挂载目录")
            
            # 创建并启动容器
            container_args = {
                'image': self.docker_service.image_name,
                'command': ["python", "-c", code],
                'name': container_name,
                'detach': True,
                'remove': False,  # 先不自动删除，方便获取日志
                'mem_limit': self.docker_service.container_config['mem_limit'],
                'cpu_quota': self.docker_service.container_config['cpu_quota'],
                'network_disabled': self.docker_service.container_config['network_disabled'],
                'security_opt': self.docker_service.container_config['security_opt'],
                'user': self.docker_service.container_config['user'],
                'volumes': {host_work_dir: {'bind': work_dir_str, 'mode': 'rw'}},  # 挂载工作目录
            }
            
            container = docker_client.containers.run(**container_args)
            logger.info(f"容器 {container_name} 已创建，等待执行完成")
            
            # 如果有引用文件，将它们复制到容器内
            if ref_files and host_work_dir:
                await self._copy_files_to_container(container, host_work_dir)
            
            # 等待容器执行完成
            result = container.wait(timeout=timeout)
            exit_code = result['StatusCode']
            
            logger.info(f"容器 {container_name} 执行完成，退出码: {exit_code}")
            
            # 提取生成的图片文件
            generated_images = await self._extract_images_from_container(container)
            
            # 获取输出日志
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            return ExecuteResponse(
                success=exit_code == 0,
                output=logs,
                exit_code=exit_code,
                container_id=container.id[:12],
                generated_images=generated_images
            )
            
        except docker.errors.ContainerError as e:
            logger.error(f"容器执行错误: {e}")
            return ExecuteResponse(
                success=False,
                output=str(e),
                exit_code=e.exit_status,
                container_id=container_name,
                generated_images=[],
                error_message=f"Container execution failed: {str(e)}"
            )
            
        except Exception as e:
            logger.error(f"代码执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
            
        finally:
            # 清理资源
            await self._cleanup_resources(docker_client, container_name, host_work_dir)
    
    async def _copy_files_to_container(self, container, host_work_dir: str) -> None:
        """将文件复制到容器内"""
        try:
            # 创建tar文件包含所有下载的文件
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                for file_path in os.listdir(host_work_dir):
                    full_path = os.path.join(host_work_dir, file_path)
                    if os.path.isfile(full_path):
                        tar.add(full_path, arcname=file_path)
            
            tar_buffer.seek(0)
            
            # 将文件复制到容器的/data目录
            container.put_archive('/data', tar_buffer.getvalue())
            
            # 设置正确的权限
            container.exec_run("chown -R sandbox:sandbox /data", user="root")
            container.exec_run("chmod -R 644 /data/*", user="root")
            
            logger.info(f"已将 {len(os.listdir(host_work_dir))} 个引用文件复制到容器内")
            
        except Exception as e:
            logger.error(f"文件复制到容器失败: {e}")
    
    async def _extract_images_from_container(self, container) -> List[ImageFile]:
        """从容器内提取图片文件"""
        generated_images = []
        
        try:
            # 支持的图片格式
            image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']
            
            # 从容器内获取/data目录的内容
            try:
                # 获取容器内/data目录的tar包
                bits, stat = container.get_archive('/data')
                
                # 解析tar包
                tar_stream = io.BytesIO()
                for chunk in bits:
                    tar_stream.write(chunk)
                tar_stream.seek(0)
                
                with tarfile.open(fileobj=tar_stream, mode='r') as tar:
                    for member in tar.getmembers():
                        if member.isfile():
                            # 检查是否是图片文件
                            filename = os.path.basename(member.name)
                            if any(filename.lower().endswith(ext) for ext in image_extensions):
                                try:
                                    # 提取文件内容
                                    file_obj = tar.extractfile(member)
                                    if file_obj:
                                        file_content = file_obj.read()
                                        
                                        # 转换为base64
                                        base64_content = base64.b64encode(file_content).decode('utf-8')
                                        
                                        generated_images.append(ImageFile(
                                            filename=filename,
                                            content=base64_content,
                                            size=len(file_content)
                                        ))
                                        
                                        logger.info(f"已提取图片文件: {filename} ({len(file_content)} bytes)")
                                except Exception as e:
                                    logger.warning(f"提取图片文件失败 {filename}: {e}")
                
                logger.info(f"发现 {len(generated_images)} 个图片文件")
                
            except Exception as e:
                logger.warning(f"从容器提取文件失败: {e}")
                
        except Exception as e:
            logger.warning(f"图片提取过程失败: {e}")
        
        return generated_images
    
    async def _cleanup_resources(
        self, 
        docker_client: docker.DockerClient, 
        container_name: str, 
        host_work_dir: Optional[str]
    ) -> None:
        """清理资源"""
        # 清理容器
        try:
            container = docker_client.containers.get(container_name)
            container.remove(force=True)
            logger.info(f"容器 {container_name} 已清理")
        except docker.errors.NotFound:
            pass  # 容器已经不存在
        except Exception as e:
            logger.warning(f"清理容器失败: {e}")
        
        # 清理宿主机工作目录
        if host_work_dir:
            self.file_service.cleanup_directory(Path(host_work_dir))