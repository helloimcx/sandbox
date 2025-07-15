#!/usr/bin/env python3
"""
测试运行器 - 整合所有测试类型
支持运行单元测试、集成测试、性能测试等
"""

import argparse
import sys
import os
import subprocess
import time
import requests
from typing import List, Dict

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

class TestRunner:
    """测试运行器类"""
    
    def __init__(self, base_url: str = "http://localhost:16009"):
        self.base_url = base_url
        self.test_results = {}
    
    def check_service_health(self) -> bool:
        """检查沙盒服务是否健康"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("status") == "healthy"
            return False
        except Exception:
            return False
    
    def wait_for_service(self, max_wait: int = 60) -> bool:
        """等待服务启动"""
        print(f"⏳ 等待沙盒服务启动 (最多等待{max_wait}秒)...")
        
        for i in range(max_wait):
            if self.check_service_health():
                print("✅ 沙盒服务已就绪")
                return True
            
            if i % 10 == 0 and i > 0:
                print(f"   仍在等待... ({i}/{max_wait}秒)")
            
            time.sleep(1)
        
        print("❌ 等待服务启动超时")
        return False
    
    def run_unit_tests(self) -> bool:
        """运行单元测试"""
        print("\n🔬 运行单元测试...")
        print("=" * 50)
        
        try:
            result = subprocess.run(
                [sys.executable, "test_unit.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            
            success = result.returncode == 0
            self.test_results["unit_tests"] = {
                "success": success,
                "return_code": result.returncode
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 单元测试超时")
            self.test_results["unit_tests"] = {"success": False, "error": "timeout"}
            return False
        except Exception as e:
            print(f"❌ 运行单元测试时出错: {e}")
            self.test_results["unit_tests"] = {"success": False, "error": str(e)}
            return False
    
    def run_integration_tests(self) -> bool:
        """运行集成测试"""
        print("\n🧪 运行集成测试...")
        print("=" * 50)
        
        if not self.check_service_health():
            print("❌ 沙盒服务不可用，跳过集成测试")
            self.test_results["integration_tests"] = {"success": False, "error": "service_unavailable"}
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, "test_comprehensive.py"],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            print(result.stdout)
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            
            success = result.returncode == 0
            self.test_results["integration_tests"] = {
                "success": success,
                "return_code": result.returncode
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 集成测试超时")
            self.test_results["integration_tests"] = {"success": False, "error": "timeout"}
            return False
        except Exception as e:
            print(f"❌ 运行集成测试时出错: {e}")
            self.test_results["integration_tests"] = {"success": False, "error": str(e)}
            return False
    
    def run_simple_tests(self) -> bool:
        """运行简单测试"""
        print("\n🚀 运行简单测试...")
        print("=" * 50)
        
        if not self.check_service_health():
            print("❌ 沙盒服务不可用，跳过简单测试")
            self.test_results["simple_tests"] = {"success": False, "error": "service_unavailable"}
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, "test_sandbox.py"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            print(result.stdout)
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            
            success = result.returncode == 0
            self.test_results["simple_tests"] = {
                "success": success,
                "return_code": result.returncode
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 简单测试超时")
            self.test_results["simple_tests"] = {"success": False, "error": "timeout"}
            return False
        except Exception as e:
            print(f"❌ 运行简单测试时出错: {e}")
            self.test_results["simple_tests"] = {"success": False, "error": str(e)}
            return False
    
    def run_benchmark_tests(self) -> bool:
        """运行性能基准测试"""
        print("\n🏁 运行性能基准测试...")
        print("=" * 50)
        
        if not self.check_service_health():
            print("❌ 沙盒服务不可用，跳过性能测试")
            self.test_results["benchmark_tests"] = {"success": False, "error": "service_unavailable"}
            return False
        
        try:
            result = subprocess.run(
                [sys.executable, "test_benchmark.py"],
                capture_output=True,
                text=True,
                timeout=1200  # 20分钟超时
            )
            
            print(result.stdout)
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
            
            success = result.returncode == 0
            self.test_results["benchmark_tests"] = {
                "success": success,
                "return_code": result.returncode
            }
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ 性能测试超时")
            self.test_results["benchmark_tests"] = {"success": False, "error": "timeout"}
            return False
        except Exception as e:
            print(f"❌ 运行性能测试时出错: {e}")
            self.test_results["benchmark_tests"] = {"success": False, "error": str(e)}
            return False
    
    def print_summary(self):
        """打印测试结果摘要"""
        print("\n" + "=" * 60)
        print("📊 测试结果摘要")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result["success"] else "❌ 失败"
            print(f"{test_name:20} : {status}")
            
            if not result["success"] and "error" in result:
                print(f"{'':22} 错误: {result['error']}")
        
        print("-" * 60)
        print(f"总测试套件: {total_tests}")
        print(f"成功: {successful_tests}")
        print(f"失败: {total_tests - successful_tests}")
        print(f"成功率: {successful_tests / total_tests * 100:.1f}%")
        
        if successful_tests == total_tests:
            print("\n🎉 所有测试都通过了！")
        else:
            print("\n⚠️  有测试失败，请检查上面的错误信息")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="沙盒系统测试运行器")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试")
    parser.add_argument("--integration", action="store_true", help="只运行集成测试")
    parser.add_argument("--simple", action="store_true", help="只运行简单测试")
    parser.add_argument("--benchmark", action="store_true", help="只运行性能测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试（默认）")
    parser.add_argument("--url", default="http://localhost:16009", help="沙盒服务URL")
    parser.add_argument("--wait", action="store_true", help="等待服务启动")
    parser.add_argument("--no-service-check", action="store_true", help="跳过服务健康检查")
    
    args = parser.parse_args()
    
    # 如果没有指定特定测试，默认运行所有测试
    if not any([args.unit, args.integration, args.simple, args.benchmark]):
        args.all = True
    
    runner = TestRunner(args.url)
    
    print("🧪 沙盒系统测试运行器")
    print(f"服务URL: {args.url}")
    print()
    
    # 检查服务状态（除非明确跳过）
    if not args.no_service_check:
        if args.wait:
            if not runner.wait_for_service():
                print("❌ 无法连接到沙盒服务")
                sys.exit(1)
        else:
            if not runner.check_service_health():
                print("⚠️  警告: 沙盒服务似乎不可用")
                print("   某些测试可能会失败")
                print("   使用 --wait 参数等待服务启动")
                print("   使用 --no-service-check 跳过此检查")
                print()
    
    # 运行测试
    all_passed = True
    
    if args.unit or args.all:
        if not runner.run_unit_tests():
            all_passed = False
    
    if args.simple or args.all:
        if not runner.run_simple_tests():
            all_passed = False
    
    if args.integration or args.all:
        if not runner.run_integration_tests():
            all_passed = False
    
    if args.benchmark or args.all:
        if not runner.run_benchmark_tests():
            all_passed = False
    
    # 打印摘要
    runner.print_summary()
    
    # 退出码
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()