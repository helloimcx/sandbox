#!/usr/bin/env python3
"""
沙盒执行器单元测试
测试SandboxExecutor类的核心功能
"""

import unittest
import asyncio
import docker
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from main import SandboxExecutor

class TestSandboxExecutor(unittest.TestCase):
    """SandboxExecutor单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        # Mock Docker客户端
        self.mock_docker_client = Mock()
        self.mock_image = Mock()
        self.mock_container = Mock()
        
        # 设置mock返回值
        self.mock_docker_client.images.get.return_value = self.mock_image
        self.mock_docker_client.containers.run.return_value = self.mock_container
        
        # Mock容器行为
        self.mock_container.wait.return_value = {'StatusCode': 0}
        self.mock_container.logs.return_value = b"Hello, World!\n"
        self.mock_container.id = "abc123def456789"
        self.mock_container.remove = Mock()
    
    @patch('main.docker_client')
    def test_executor_initialization(self, mock_client):
        """测试执行器初始化"""
        mock_client.images.get.return_value = self.mock_image
        
        executor = SandboxExecutor()
        
        self.assertEqual(executor.image_name, "sandbox-executor")
        mock_client.images.get.assert_called_once_with("sandbox-executor")
    
    @patch('main.docker_client')
    def test_image_build_when_not_exists(self, mock_client):
        """测试镜像不存在时自动构建"""
        # 模拟镜像不存在
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        mock_client.images.build.return_value = (self.mock_image, [])
        
        executor = SandboxExecutor()
        
        # 验证构建被调用
        mock_client.images.build.assert_called_once_with(
            path=".",
            dockerfile="docker/Dockerfile.executor",
            tag="sandbox-executor",
            rm=True
        )
    
    @patch('main.docker_client')
    async def test_successful_code_execution(self, mock_client):
        """测试成功的代码执行"""
        mock_client.images.get.return_value = self.mock_image
        mock_client.containers.run.return_value = self.mock_container
        
        executor = SandboxExecutor()
        result = await executor.execute_code("print('Hello, World!')")
        
        # 验证容器创建参数
        mock_client.containers.run.assert_called_once()
        call_args = mock_client.containers.run.call_args
        
        self.assertEqual(call_args[0][0], "sandbox-executor")  # 镜像名
        self.assertEqual(call_args[1]['command'], ["python", "-c", "print('Hello, World!')"])
        self.assertEqual(call_args[1]['mem_limit'], "128m")
        self.assertEqual(call_args[1]['cpu_quota'], 50000)
        self.assertTrue(call_args[1]['network_disabled'])
        self.assertEqual(call_args[1]['user'], "sandbox")
        
        # 验证返回结果
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['output'], "Hello, World!\n")
        self.assertEqual(result['container_id'], "abc123def456")
        
        # 验证容器被清理
        self.mock_container.remove.assert_called_once_with(force=True)

# 为异步测试方法添加同步包装器
for method_name in dir(TestSandboxExecutor):
    if method_name.startswith('test_') and asyncio.iscoroutinefunction(getattr(TestSandboxExecutor, method_name)):
        original_method = getattr(TestSandboxExecutor, method_name)
        
        def create_sync_wrapper(async_method):
            def sync_wrapper(self):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(async_method(self))
                finally:
                    loop.close()
            return sync_wrapper
        
        setattr(TestSandboxExecutor, method_name, create_sync_wrapper(original_method))

if __name__ == "__main__":
    unittest.main()