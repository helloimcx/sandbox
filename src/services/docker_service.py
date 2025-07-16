"""Docker服务类"""

import docker
import logging
import time
from typing import Optional
from config import config

logger = logging.getLogger(__name__)


class DockerService:
    """Docker服务管理类"""
    
    def __init__(self):
        self.client: Optional[docker.DockerClient] = None
        self.image_name = config.EXECUTOR_IMAGE_NAME
        self.dockerfile_path = config.EXECUTOR_DOCKERFILE_PATH
        self.container_config = config.get_container_config()
        
        self._initialize_client()
        if self.client:
            self._ensure_image_exists()
    
    def _initialize_client(self) -> None:
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
                self.client = client
                logger.info("Docker客户端初始化成功")
                return
            except docker.errors.DockerException as e:
                logger.error(f"Docker连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Docker客户端初始化失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error("Docker客户端初始化最终失败")
    
    def _ensure_image_exists(self) -> None:
        """确保执行器镜像存在"""
        if not self.client:
            raise RuntimeError("Docker客户端未初始化")
            
        try:
            self.client.images.get(self.image_name)
            logger.info(f"执行器镜像 {self.image_name} 已存在")
        except docker.errors.ImageNotFound:
            logger.info(f"构建执行器镜像 {self.image_name}...")
            try:
                # Build the image from Dockerfile.executor
                self.client.images.build(
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
    
    def is_available(self) -> bool:
        """检查Docker服务是否可用"""
        return self.client is not None
    
    def get_client(self) -> docker.DockerClient:
        """获取Docker客户端"""
        if not self.client:
            raise RuntimeError("Docker客户端不可用")
        return self.client