#!/usr/bin/env python3
"""
测试图片生成和提取功能
"""

import requests
import json
import base64
from pathlib import Path

def test_image_generation():
    """测试代码执行后图片文件的生成和提取"""
    
    # 测试代码：生成一个简单的matplotlib图片
    test_code = """
import matplotlib.pyplot as plt
import numpy as np

# 生成测试数据
x = np.linspace(0, 10, 100)
y = np.sin(x)

# 创建图表
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.xlabel('X轴')
plt.ylabel('Y轴')
plt.title('正弦函数图像')
plt.legend()
plt.grid(True)

# 保存图片到工作目录
plt.savefig('/data/test_plot.png', dpi=150, bbox_inches='tight')
plt.close()

print("图片已生成: test_plot.png")

# 再生成一个简单的图片
import matplotlib.pyplot as plt

plt.figure(figsize=(6, 4))
plt.bar(['A', 'B', 'C', 'D'], [1, 3, 2, 4])
plt.title('柱状图示例')
plt.savefig('/data/bar_chart.png')
plt.close()

print("图片已生成: bar_chart.png")
"""
    
    # 发送请求
    url = "http://localhost:16009/execute"
    payload = {
        "code": test_code,
        "timeout": 30
    }
    
    print("发送图片生成测试请求...")
    response = requests.post(url, json=payload, proxies={'http': None, 'https': None})
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"执行成功: {result['success']}")
        print(f"输出: {result['output']}")
        print(f"退出码: {result['exit_code']}")
        
        # 检查生成的图片
        if 'generated_images' in result:
            images = result['generated_images']
            print(f"\n生成了 {len(images)} 个图片文件:")
            
            for i, image in enumerate(images):
                filename = image['filename']
                size = image['size']
                content = image['content']
                
                print(f"  {i+1}. {filename} ({size} bytes)")
                
                # 可选：保存图片到本地进行验证
                try:
                    image_data = base64.b64decode(content)
                    output_path = Path(f"./test_output_{filename}")
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    print(f"     已保存到: {output_path}")
                except Exception as e:
                    print(f"     保存失败: {e}")
        else:
            print("\n未找到生成的图片文件")
    else:
        print(f"请求失败: {response.text}")

if __name__ == "__main__":
    test_image_generation()