#!/usr/bin/env python3
"""
测试RefFiles功能的示例脚本
"""

import requests
import json

def test_ref_files():
    """测试带有引用文件的代码执行"""
    
    # API端点
    url = "http://127.0.0.1:16009/execute"
    
    # 测试数据 - 包含引用文件
    test_data = {
        "code": """
# 读取引用文件并处理
import os

# 检查引用文件是否存在
if os.path.exists('/data/test.txt'):
    with open('/data/test.txt', 'r') as f:
        content = f.read()
        print(f"成功读取引用文件，内容: {content.strip()}")
else:
    print("引用文件不存在")
    
# 列出可用的文件
if os.path.exists('/data'):
    files = os.listdir('/data')
    print(f"可用文件: {files}")
""",
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
        # 发送请求
        response = requests.post(
            url, 
            json=test_data,
            proxies={'http': None, 'https': None},
            timeout=60
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
    except Exception as e:
        print(f"请求失败: {e}")

def test_without_ref_files():
    """测试不带引用文件的代码执行"""
    
    url = "http://127.0.0.1:16009/execute"
    
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

if __name__ == "__main__":
    print("=== 测试不带引用文件的执行 ===")
    test_without_ref_files()
    
    print("\n=== 测试带引用文件的执行 ===")
    test_ref_files()