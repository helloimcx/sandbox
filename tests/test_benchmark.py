#!/usr/bin/env python3
"""
沙盒系统性能基准测试
测试系统在各种负载下的性能表现
"""

import unittest
import requests
import time
import threading
import statistics
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

class TestSandboxPerformance(unittest.TestCase):
    """沙盒性能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.base_url = os.getenv('SANDBOX_URL', 'http://localhost:16009')
        self.timeout = 60
        
        # 确保服务可用
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
    
    def _execute_code_with_timing(self, code: str, language: str = "python") -> Dict[str, Any]:
        """执行代码并记录时间"""
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/execute",
                json={"code": code, "language": language},
                timeout=self.timeout
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                result['request_time'] = execution_time
                return result
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'request_time': execution_time
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'error': str(e),
                'request_time': end_time - start_time
            }
    
    def test_single_request_performance(self):
        """测试单个请求的性能"""
        print("\n⚡ 测试单个请求性能...")
        
        code = "print('性能测试')"
        
        # 执行多次测试
        times = []
        for i in range(10):
            result = self._execute_code_with_timing(code)
            self.assertTrue(result['success'], f"第{i+1}次请求失败")
            times.append(result['request_time'])
        
        # 计算统计信息
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        print(f"   平均响应时间: {avg_time:.3f}s")
        print(f"   最快响应时间: {min_time:.3f}s")
        print(f"   最慢响应时间: {max_time:.3f}s")
        print(f"   中位数响应时间: {median_time:.3f}s")
        
        # 性能断言（可根据实际情况调整）
        self.assertLess(avg_time, 10.0, "平均响应时间应小于10秒")
        self.assertLess(max_time, 20.0, "最大响应时间应小于20秒")
    
    def test_concurrent_requests_performance(self):
        """测试并发请求性能"""
        print("\n🚀 测试并发请求性能...")
        
        def execute_single_request(request_id: int) -> Dict[str, Any]:
            code = f"print('并发测试 #{request_id}')"
            result = self._execute_code_with_timing(code)
            result['request_id'] = request_id
            return result
        
        # 测试不同并发级别
        concurrent_levels = [1, 3, 5, 10]
        
        for concurrent_count in concurrent_levels:
            print(f"\n   测试 {concurrent_count} 个并发请求...")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrent_count) as executor:
                futures = [executor.submit(execute_single_request, i) 
                          for i in range(concurrent_count)]
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=self.timeout)
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'success': False,
                            'error': str(e),
                            'request_time': 0
                        })
            
            total_time = time.time() - start_time
            
            # 统计结果
            successful_requests = sum(1 for r in results if r['success'])
            failed_requests = len(results) - successful_requests
            
            if successful_requests > 0:
                avg_request_time = statistics.mean([r['request_time'] for r in results if r['success']])
                throughput = successful_requests / total_time
                
                print(f"     总耗时: {total_time:.3f}s")
                print(f"     成功请求: {successful_requests}/{len(results)}")
                print(f"     失败请求: {failed_requests}")
                print(f"     平均请求时间: {avg_request_time:.3f}s")
                print(f"     吞吐量: {throughput:.2f} 请求/秒")
                
                # 性能断言
                self.assertGreaterEqual(successful_requests, concurrent_count * 0.8, 
                                      f"至少80%的并发请求应该成功")
            else:
                self.fail(f"所有 {concurrent_count} 个并发请求都失败了")
    
    def test_cpu_intensive_performance(self):
        """测试CPU密集型任务性能"""
        print("\n🧮 测试CPU密集型任务性能...")
        
        code = """
import time
start = time.time()

# CPU密集型计算：计算斐波那契数列
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(30)
end = time.time()

print(f"斐波那契(30) = {result}")
print(f"计算耗时: {end - start:.3f}秒")
"""
        
        result = self._execute_code_with_timing(code)
        
        self.assertTrue(result['success'], "CPU密集型任务应该成功执行")
        self.assertIn('斐波那契(30) = 832040', result['output'])
        
        print(f"   请求总耗时: {result['request_time']:.3f}s")
        print(f"   任务执行成功")
        
        # CPU密集型任务可能需要更长时间
        self.assertLess(result['request_time'], 30.0, "CPU密集型任务应在30秒内完成")
    
    def test_memory_usage_performance(self):
        """测试内存使用性能"""
        print("\n💾 测试内存使用性能...")
        
        code = """
import sys

# 创建一个较大的列表
print("开始创建大列表...")
big_list = list(range(100000))
print(f"列表长度: {len(big_list)}")

# 计算列表总和
total = sum(big_list)
print(f"列表总和: {total}")

# 清理内存
del big_list
print("内存测试完成")
"""
        
        result = self._execute_code_with_timing(code)
        
        self.assertTrue(result['success'], "内存使用测试应该成功执行")
        self.assertIn('列表长度: 100000', result['output'])
        self.assertIn('列表总和: 4999950000', result['output'])
        self.assertIn('内存测试完成', result['output'])
        
        print(f"   请求总耗时: {result['request_time']:.3f}s")
        print(f"   内存使用测试成功")
    
    def test_io_intensive_performance(self):
        """测试I/O密集型任务性能"""
        print("\n📁 测试I/O密集型任务性能...")
        
        code = """
import tempfile
import os

# 创建临时文件并写入数据
with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
    temp_file = f.name
    for i in range(1000):
        f.write(f"这是第 {i} 行数据\n")

print(f"写入了1000行数据到临时文件")

# 读取文件内容
with open(temp_file, 'r') as f:
    lines = f.readlines()
    print(f"读取了 {len(lines)} 行数据")

# 清理临时文件
os.unlink(temp_file)
print("I/O测试完成")
"""
        
        result = self._execute_code_with_timing(code)
        
        self.assertTrue(result['success'], "I/O密集型任务应该成功执行")
        self.assertIn('写入了1000行数据到临时文件', result['output'])
        self.assertIn('读取了 1000 行数据', result['output'])
        self.assertIn('I/O测试完成', result['output'])
        
        print(f"   请求总耗时: {result['request_time']:.3f}s")
        print(f"   I/O操作测试成功")
    
    def test_error_handling_performance(self):
        """测试错误处理性能"""
        print("\n⚠️  测试错误处理性能...")
        
        error_codes = [
            "raise ValueError('测试错误1')",
            "1 / 0",  # ZeroDivisionError
            "undefined_variable",  # NameError
            "import non_existent_module",  # ImportError
        ]
        
        total_time = 0
        successful_error_handling = 0
        
        for i, code in enumerate(error_codes):
            result = self._execute_code_with_timing(code)
            total_time += result['request_time']
            
            # 错误代码应该被正确处理（返回失败状态但不崩溃）
            if not result['success'] and 'output' in result:
                successful_error_handling += 1
                print(f"   错误 {i+1}: 正确处理 ({result['request_time']:.3f}s)")
            else:
                print(f"   错误 {i+1}: 处理异常")
        
        avg_error_time = total_time / len(error_codes)
        
        print(f"   平均错误处理时间: {avg_error_time:.3f}s")
        print(f"   成功处理的错误: {successful_error_handling}/{len(error_codes)}")
        
        # 错误处理应该快速且可靠
        self.assertLess(avg_error_time, 5.0, "错误处理应该在5秒内完成")
        self.assertGreaterEqual(successful_error_handling, len(error_codes) * 0.8, 
                               "至少80%的错误应该被正确处理")
    
    def test_stress_test(self):
        """压力测试"""
        print("\n🔥 运行压力测试...")
        
        # 连续执行大量请求
        request_count = 20
        max_concurrent = 5
        
        def execute_stress_request(request_id: int) -> Dict[str, Any]:
            code = f"""
import time
start = time.time()

# 模拟一些工作负载
result = sum(i * i for i in range(1000))
time.sleep(0.1)  # 模拟一些延迟

end = time.time()
print(f"压力测试 #{request_id}: 结果={result}, 耗时={end-start:.3f}s")
"""
            return self._execute_code_with_timing(code)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [executor.submit(execute_stress_request, i) 
                      for i in range(request_count)]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'success': False,
                        'error': str(e),
                        'request_time': 0
                    })
        
        total_time = time.time() - start_time
        
        # 统计结果
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = len(results) - successful_requests
        
        if successful_requests > 0:
            avg_request_time = statistics.mean([r['request_time'] for r in results if r['success']])
            throughput = successful_requests / total_time
            
            print(f"   总请求数: {request_count}")
            print(f"   总耗时: {total_time:.3f}s")
            print(f"   成功请求: {successful_requests}")
            print(f"   失败请求: {failed_requests}")
            print(f"   平均请求时间: {avg_request_time:.3f}s")
            print(f"   吞吐量: {throughput:.2f} 请求/秒")
            print(f"   成功率: {successful_requests/request_count*100:.1f}%")
            
            # 压力测试断言
            self.assertGreaterEqual(successful_requests, request_count * 0.7, 
                                  "至少70%的压力测试请求应该成功")
            self.assertLess(avg_request_time, 15.0, "压力测试下平均响应时间应小于15秒")
        else:
            self.fail("所有压力测试请求都失败了")

def run_benchmark_tests():
    """运行性能基准测试的主函数"""
    print("🏁 开始运行沙盒性能基准测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSandboxPerformance)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # 打印结果摘要
    print("\n" + "=" * 60)
    print("📊 性能测试结果摘要")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successful = total_tests - failures - errors
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {successful}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 所有性能测试都通过了！")
        print("   系统性能表现良好")
        return True
    else:
        print("\n⚠️  有性能测试失败，请检查系统性能")
        if failures > 0:
            print("\n失败的测试:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if errors > 0:
            print("\n错误的测试:")
            for test, traceback in result.errors:
                print(f"  - {test}: 执行错误")
        
        return False

if __name__ == "__main__":
    success = run_benchmark_tests()
    sys.exit(0 if success else 1)