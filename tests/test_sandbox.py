#!/usr/bin/env python3
"""
沙盒系统简单测试
快速验证基本功能是否正常工作
"""

import unittest
import requests
import time
import os
import sys

class TestSandboxBasic(unittest.TestCase):
    """沙盒基本功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = os.getenv('SANDBOX_URL', 'http://127.0.0.1:16009')
        self.timeout = 10
        # 禁用代理以避免502错误
        self.proxies = {'http': None, 'https': None}
    
    def test_service_health(self):
        """测试服务健康状态"""
        print("\n🔍 检查服务健康状态...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5, proxies=self.proxies)
            print(response)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'healthy')
            
            print("✅ 服务健康检查通过")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 无法连接到服务: {e}")
    
    def test_basic_python_execution(self):
        """测试基本Python代码执行"""
        print("\n🐍 测试基本Python代码执行...")
        
        code = "print('Hello from sandbox!')"
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": code},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            self.assertIn('success', result)
            self.assertIn('output', result)
            self.assertIn('exit_code', result)
            self.assertIn('container_id', result)
            
            if result['success']:
                self.assertEqual(result['exit_code'], 0)
                self.assertIn('Hello from sandbox!', result['output'])
                print("✅ Python代码执行成功")
                print(f"   输出: {result['output'].strip()}")
            else:
                print(f"❌ Python代码执行失败: {result.get('output', '未知错误')}")
                self.fail("Python代码执行失败")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")
    
    def test_python_with_calculation(self):
        """测试包含计算的Python代码"""
        print("\n🧮 测试Python计算功能...")
        
        code = """
a = 10
b = 20
result = a + b
print(f"计算结果: {a} + {b} = {result}")
"""
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": code},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            
            if result['success']:
                self.assertEqual(result['exit_code'], 0)
                self.assertIn('计算结果: 10 + 20 = 30', result['output'])
                print("✅ Python计算功能正常")
                print(f"   输出: {result['output'].strip()}")
            else:
                print(f"❌ Python计算失败: {result.get('output', '未知错误')}")
                self.fail("Python计算功能失败")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")
    
    def test_python_error_handling(self):
        """测试Python错误处理"""
        print("\n⚠️  测试Python错误处理...")
        
        code = """
print("执行开始")
raise ValueError("这是一个测试错误")
print("这行不会执行")
"""
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": code},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            
            # 错误代码应该返回失败状态
            self.assertFalse(result['success'])
            self.assertNotEqual(result['exit_code'], 0)
            
            # 应该包含错误信息
            self.assertIn('执行开始', result['output'])
            self.assertIn('ValueError', result['output'])
            self.assertIn('这是一个测试错误', result['output'])
            
            print("✅ Python错误处理正常")
            print(f"   错误输出包含预期信息")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")
    
    def test_invalid_request(self):
        """测试无效请求处理"""
        print("\n🚫 测试无效请求处理...")
        
        # 测试缺少code字段的请求
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"language": "python"},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            self.assertEqual(response.status_code, 422)
            print("✅ 无效请求正确返回422状态码")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")
    
    def test_empty_code(self):
        """测试空代码处理"""
        print("\n📝 测试空代码处理...")
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": ""},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            # 空代码应该返回400错误（API设计如此）
            self.assertEqual(response.status_code, 400)
            
            print("✅ 空代码处理正常")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")
    
    def test_unicode_support(self):
        """测试Unicode字符支持"""
        print("\n🌍 测试Unicode字符支持...")
        
        code = """
print("中文测试: 你好世界")
print("Emoji测试: 🐍🚀✨")
print("特殊字符: αβγδε")
"""
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": code},
                timeout=self.timeout,
                proxies=self.proxies
            )
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            
            if result['success']:
                self.assertEqual(result['exit_code'], 0)
                self.assertIn('你好世界', result['output'])
                self.assertIn('🐍🚀✨', result['output'])
                self.assertIn('αβγδε', result['output'])
                
                print("✅ Unicode字符支持正常")
                print(f"   输出包含所有Unicode字符")
            else:
                print(f"❌ Unicode测试失败: {result.get('output', '未知错误')}")
                self.fail("Unicode字符支持失败")
                
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ 请求失败: {e}")

def run_simple_tests():
    """运行简单测试的主函数"""
    print("🧪 开始运行沙盒简单测试")
    print("=" * 50)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSandboxBasic)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # 打印结果摘要
    print("\n" + "=" * 50)
    print("📊 测试结果摘要")
    print("=" * 50)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successful = total_tests - failures - errors
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {successful}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 所有简单测试都通过了！")
        return True
    else:
        print("\n⚠️  有测试失败，请检查上面的错误信息")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)