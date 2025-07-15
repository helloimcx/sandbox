#!/usr/bin/env python3
"""
沙盒系统综合集成测试
测试完整的API功能和各种代码执行场景
"""

import unittest
import requests
import time
import json
import sys
import os
from typing import Dict, Any

class TestSandboxAPI(unittest.TestCase):
    """沙盒API综合测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = os.getenv('SANDBOX_URL', 'http://localhost:16009')
        self.timeout = 30
        
        # 等待服务启动
        self._wait_for_service()
    
    def _wait_for_service(self, max_attempts: int = 30):
        """等待服务启动"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    return
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_attempts - 1:
                time.sleep(1)
        
        self.fail(f"服务在 {max_attempts} 秒内未启动")
    
    def _execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """执行代码的辅助方法"""
        response = requests.post(
            f"{self.base_url}/execute",
            json={"code": code, "language": language},
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 200)
        return response.json()
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = requests.get(f"{self.base_url}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_simple_python_execution(self):
        """测试简单Python代码执行"""
        code = "print('Hello, World!')"
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('Hello, World!', result['output'])
        self.assertIsNotNone(result['container_id'])
    
    def test_python_with_variables(self):
        """测试包含变量的Python代码"""
        code = """
x = 10
y = 20
result = x + y
print(f"结果: {result}")
"""
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('结果: 30', result['output'])
    
    def test_python_with_loops(self):
        """测试包含循环的Python代码"""
        code = """
for i in range(5):
    print(f"数字: {i}")
"""
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        
        output_lines = result['output'].strip().split('\n')
        self.assertEqual(len(output_lines), 5)
        for i, line in enumerate(output_lines):
            self.assertIn(f"数字: {i}", line)
    
    def test_python_with_functions(self):
        """测试包含函数的Python代码"""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

for i in range(8):
    print(f"fib({i}) = {fibonacci(i)}")
"""
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('fib(7) = 13', result['output'])
    
    def test_python_with_imports(self):
        """测试包含标准库导入的Python代码"""
        code = """
import math
import json
import datetime

print(f"π = {math.pi:.4f}")
print(f"当前时间: {datetime.datetime.now().strftime('%Y-%m-%d')}")

data = {"name": "test", "value": 42}
print(f"JSON: {json.dumps(data)}")
"""
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('π = 3.1416', result['output'])
        self.assertIn('JSON:', result['output'])
    
    def test_python_error_handling(self):
        """测试Python代码错误处理"""
        code = """
print("开始执行")
raise ValueError("这是一个测试错误")
print("这行不会执行")
"""
        result = self._execute_code(code)
        
        self.assertFalse(result['success'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertIn('开始执行', result['output'])
        self.assertIn('ValueError', result['output'])
        self.assertIn('这是一个测试错误', result['output'])
    
    def test_python_syntax_error(self):
        """测试Python语法错误"""
        code = """
print("正常代码")
if True
    print("语法错误")
"""
        result = self._execute_code(code)
        
        self.assertFalse(result['success'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertIn('SyntaxError', result['output'])
    
    def test_python_infinite_loop_timeout(self):
        """测试无限循环超时处理"""
        code = """
print("开始无限循环")
while True:
    pass
"""
        result = self._execute_code(code)
        
        self.assertFalse(result['success'])
        self.assertIn('开始无限循环', result['output'])
        # 应该因为超时而失败
    
    def test_python_memory_intensive(self):
        """测试内存密集型代码"""
        code = """
print("创建大列表")
try:
    # 尝试创建一个大列表
    big_list = [i for i in range(1000000)]
    print(f"列表长度: {len(big_list)}")
    print("内存测试完成")
except MemoryError:
    print("内存不足")
"""
        result = self._execute_code(code)
        
        # 无论成功还是失败都是可接受的，主要测试不会崩溃
        self.assertIsNotNone(result)
        self.assertIn('container_id', result)
    
    def test_multiple_requests(self):
        """测试多个并发请求"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def execute_test_code(thread_id):
            code = f"print('线程 {thread_id} 执行成功')"
            try:
                result = self._execute_code(code)
                results.put((thread_id, result))
            except Exception as e:
                results.put((thread_id, {'error': str(e)}))
        
        # 创建5个线程同时执行
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_test_code, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        successful_results = 0
        while not results.empty():
            thread_id, result = results.get()
            if 'error' not in result and result.get('success', False):
                successful_results += 1
                self.assertIn(f'线程 {thread_id} 执行成功', result['output'])
        
        # 至少应该有一些成功的结果
        self.assertGreater(successful_results, 0)
    
    def test_invalid_json_request(self):
        """测试无效JSON请求"""
        response = requests.post(
            f"{self.base_url}/execute",
            data="invalid json",
            headers={'Content-Type': 'application/json'},
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
    
    def test_missing_code_field(self):
        """测试缺少code字段的请求"""
        response = requests.post(
            f"{self.base_url}/execute",
            json={"language": "python"},
            timeout=self.timeout
        )
        self.assertEqual(response.status_code, 400)
    
    def test_empty_code(self):
        """测试空代码"""
        result = self._execute_code("")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['output'].strip(), "")
    
    def test_code_with_unicode(self):
        """测试包含Unicode字符的代码"""
        code = """
print("你好，世界！")
print("🐍 Python 测试")
print("数学符号: α β γ δ")
"""
        result = self._execute_code(code)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('你好，世界！', result['output'])
        self.assertIn('🐍 Python 测试', result['output'])
        self.assertIn('α β γ δ', result['output'])

if __name__ == "__main__":
    unittest.main()