# RefFiles 功能使用指南

## 概述

新增的 RefFiles 功能允许在代码执行时引用外部文件。系统会自动下载指定的文件并挂载到容器中，供代码使用。

## API 接口

### 请求格式

```json
{
  "code": "要执行的Python代码",
  "timeout": 30,
  "work_dir": "/data",
  "ref_files": [
    {
      "url": "https://example.com/file.txt",
      "filename": "file.txt"
    }
  ]
}
```

### 参数说明

- `code` (必需): 要执行的Python代码
- `timeout` (可选): 执行超时时间，默认30秒
- `work_dir` (可选): 工作目录，默认为"/data"
- `ref_files` (可选): 引用文件列表

#### RefFile 对象

- `url` (必需): 文件的HTTP/HTTPS URL
- `filename` (可选): 文件名，如果不提供则从URL推断

## 使用示例

### 示例1: 基本用法

```python
import requests

data = {
    "code": """
# 读取引用文件
with open('/data/readme.txt', 'r') as f:
    content = f.read()
    print(f"文件内容: {content[:100]}...")
""",
    "work_dir": "/data",
    "ref_files": [
        {
            "url": "https://raw.githubusercontent.com/octocat/Hello-World/master/README",
            "filename": "readme.txt"
        }
    ]
}

response = requests.post('http://localhost:16009/execute', json=data)
print(response.json())
```

### 示例2: 多个文件

```python
data = {
    "code": """
import os
print("可用文件:")
for file in os.listdir('/data'):
    print(f"- {file}")
    
# 处理CSV文件
import pandas as pd
df = pd.read_csv('/data/data.csv')
print(f"数据行数: {len(df)}")
""",
    "work_dir": "/data",
    "ref_files": [
        {
            "url": "https://example.com/data.csv",
            "filename": "data.csv"
        },
        {
            "url": "https://example.com/config.json",
            "filename": "config.json"
        }
    ]
}
```

## 功能特性

1. **自动下载**: 系统自动从指定URL下载文件
2. **路径映射**: 文件被挂载到容器中的指定路径
3. **只读访问**: 引用文件以只读模式挂载，确保安全性
4. **自动清理**: 执行完成后自动清理临时文件
5. **错误处理**: 下载失败时返回详细错误信息
6. **URL验证**: 使用Pydantic进行严格的URL格式验证

## 限制和注意事项

1. **网络访问**: 需要容器能够访问外部网络（当前配置为network_disabled=True，需要调整）
2. **文件大小**: 建议文件大小不超过100MB
3. **超时时间**: 文件下载包含在总的执行超时时间内
4. **安全性**: 只支持HTTP/HTTPS协议，文件以只读模式挂载
5. **路径限制**: 建议使用 `/data/` 目录下的路径

## 错误处理

### 常见错误

1. **URL格式错误** (422):
```json
{
  "detail": [
    {
      "type": "url_parsing",
      "loc": ["body", "ref_files", 0, "url"],
      "msg": "Input should be a valid URL"
    }
  ]
}
```

2. **文件下载失败** (400):
```json
{
  "detail": "Failed to download file from https://example.com/nonexistent.txt"
}
```

3. **Docker不可用** (500):
```json
{
  "detail": "Docker client not available"
}
```

## 测试

项目包含了完整的测试文件：

- `test_ref_files.py`: 基本功能测试
- `test_api_schema.py`: API接口和验证测试

运行测试：
```bash
python3 test_api_schema.py
```

## 技术实现

- 使用 **Pydantic** 进行请求验证
- 使用 **aiohttp** 进行异步文件下载
- 使用 **aiofiles** 进行异步文件操作
- 使用 **Docker volumes** 进行文件挂载
- 自动清理临时文件和工作目录