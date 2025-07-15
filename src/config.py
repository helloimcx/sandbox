#!/usr/bin/env python3
"""
配置管理模块
管理应用程序的配置参数和环境变量
"""

import os
from typing import Optional

class Config:
    """应用程序配置类"""
    
    # Docker配置
    DOCKER_SOCKET_PATH: str = os.getenv("DOCKER_SOCKET_PATH", "/var/run/docker.sock")
    DOCKER_CLIENT_TIMEOUT: int = int(os.getenv("DOCKER_CLIENT_TIMEOUT", "60"))
    DOCKER_CLIENT_MAX_RETRIES: int = int(os.getenv("DOCKER_CLIENT_MAX_RETRIES", "3"))
    DOCKER_CLIENT_RETRY_DELAY: int = int(os.getenv("DOCKER_CLIENT_RETRY_DELAY", "2"))
    
    # 执行器配置
    EXECUTOR_IMAGE_NAME: str = os.getenv("EXECUTOR_IMAGE_NAME", "sandbox-executor")
    EXECUTOR_DOCKERFILE_PATH: str = os.getenv("EXECUTOR_DOCKERFILE_PATH", "docker/Dockerfile.executor")
    
    # 容器资源限制
    CONTAINER_MEMORY_LIMIT: str = os.getenv("CONTAINER_MEMORY_LIMIT", "128m")
    CONTAINER_CPU_QUOTA: int = int(os.getenv("CONTAINER_CPU_QUOTA", "50000"))
    CONTAINER_TIMEOUT: int = int(os.getenv("CONTAINER_TIMEOUT", "30"))
    CONTAINER_USER: str = os.getenv("CONTAINER_USER", "sandbox")
    
    # 安全配置
    NETWORK_DISABLED: bool = os.getenv("NETWORK_DISABLED", "true").lower() == "true"
    SECURITY_OPTS: list = ["no-new-privileges"]
    
    # API配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "16009"))
    API_TITLE: str = os.getenv("API_TITLE", "Python Sandbox Executor")
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # 开发模式
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def get_docker_client_config(cls) -> dict:
        """获取Docker客户端配置"""
        return {
            "timeout": cls.DOCKER_CLIENT_TIMEOUT,
            "max_retries": cls.DOCKER_CLIENT_MAX_RETRIES,
            "retry_delay": cls.DOCKER_CLIENT_RETRY_DELAY
        }
    
    @classmethod
    def get_container_config(cls) -> dict:
        """获取容器配置"""
        return {
            "mem_limit": cls.CONTAINER_MEMORY_LIMIT,
            "cpu_quota": cls.CONTAINER_CPU_QUOTA,
            "timeout": cls.CONTAINER_TIMEOUT,
            "user": cls.CONTAINER_USER,
            "network_disabled": cls.NETWORK_DISABLED,
            "security_opt": cls.SECURITY_OPTS
        }
    
    @classmethod
    def get_api_config(cls) -> dict:
        """获取API配置"""
        return {
            "host": cls.API_HOST,
            "port": cls.API_PORT,
            "title": cls.API_TITLE,
            "version": cls.API_VERSION
        }

# 全局配置实例
config = Config()