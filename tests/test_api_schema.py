#!/usr/bin/env python3
"""
测试API接口和Pydantic模型的正确性
"""

import requests
import json

def test_api_schema():
    """测试API接口是否正确接受新的参数格式"""
    
    # API端点
    url = "http://127.0.0.1:16009/execute"
    
    # 测试1: 基本请求（不带ref_files）
    print("=== 测试1: 基本请求 ===")
    test_data = {
        "code": "print('Hello, World!')",
        "timeout": 30
    }
    
    try:
        response = requests.post(
            url, 
            json=test_data,
            proxies={'http': None, 'https': None},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试2: 带ref_files的请求
    print("\n=== 测试2: 带ref_files的请求 ===")
    test_data_with_files = {
        "code": "print('Testing with ref files')",
        "timeout": 30,
        "work_dir": "/data",
        "ref_files": [
            {
                "url": "https://raw.githubusercontent.com/octocat/Hello-World/master/README",
                "filename": "test.txt"
            }
        ]
    }
    
    try:
        response = requests.post(
            url, 
            json=test_data_with_files,
            proxies={'http': None, 'https': None},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 测试3: 无效的ref_files格式
    print("\n=== 测试3: 无效的ref_files格式 ===")
    test_data_invalid = {
        "code": "print('Testing invalid ref files')",
        "timeout": 30,
        "work_dir": "/data",
        "ref_files": [
            {
                "url": "invalid-url"  # 无效的URL
            }
        ]
    }
    
    try:
        response = requests.post(
            url, 
            json=test_data_invalid,
            proxies={'http': None, 'https': None},
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")

def test_health_endpoint():
    """测试健康检查端点"""
    print("\n=== 健康检查 ===")
    
    try:
        response = requests.get(
            "http://127.0.0.1:16009/health",
            proxies={'http': None, 'https': None},
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"健康检查失败: {e}")

if __name__ == "__main__":
    test_health_endpoint()
    test_api_schema()