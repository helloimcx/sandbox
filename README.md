# 沙盒代码执行系统

一个基于Docker容器的安全代码执行沙盒系统，使用FastAPI提供REST API接口。每次代码执行都会创建一个新的隔离容器，执行完成后自动销毁，确保安全性和资源隔离。

## 📁 项目结构

```
sandbox/
├── src/                    # 源代码目录
│   └── main.py            # FastAPI 主应用
├── tests/                  # 测试文件目录
│   ├── test_unit.py       # 单元测试
│   ├── test_sandbox.py    # 简单功能测试
│   ├── test_comprehensive.py  # 综合集成测试
│   └── test_benchmark.py  # 性能基准测试
├── scripts/               # 脚本目录
│   ├── build_and_run.sh  # 构建和运行脚本
│   └── run_tests.py       # 测试运行器
├── docker/                # Docker 相关文件
│   ├── Dockerfile         # 主服务 Dockerfile
│   └── Dockerfile.executor # 执行器 Dockerfile
├── requirements.txt       # Python 依赖
└── README.md             # 项目文档
```

## 🏗️ 架构设计

- **主服务容器**: 运行FastAPI应用，处理API请求
- **执行器容器**: 每次代码执行时动态创建的隔离容器
- **Docker API**: 用于管理执行器容器的生命周期

## 🔒 安全特性

- 每次执行使用全新的容器实例
- 容器资源限制（内存128MB，CPU限制）
- 禁用网络访问
- 使用非root用户执行代码
- 执行完成后自动销毁容器

## 🚀 快速开始

### 方法1: 使用构建脚本（推荐）

```bash
# 一键构建和运行
./scripts/build_and_run.sh
```

### 方法2: 手动构建

```bash
# 1. 构建执行器镜像
docker build -f docker/Dockerfile.executor -t sandbox-executor .

# 2. 构建主服务镜像
docker build -f docker/Dockerfile -t sandbox-api .

# 3. 运行主服务
docker run -d \
    --name sandbox-api \
    -p 16009:16009 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --rm \
    sandbox-api
```

## 📖 API使用

### 执行代码

```bash
curl -X POST "http://localhost:16009/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "code": "print('Hello, Sandbox!')",
       "timeout": 30
     }'
```

### 响应格式

```json
{
  "success": true,
  "output": "Hello, Sandbox!\n",
  "exit_code": 0,
  "container_id": "abc123def456"
}
```

## 🧪 测试

### 快速测试

```bash
# 运行所有测试
./scripts/run_tests.py

# 等待服务启动后运行测试
./scripts/run_tests.py --wait

# 只运行特定类型的测试
./scripts/run_tests.py --unit          # 单元测试
./scripts/run_tests.py --simple        # 简单功能测试
./scripts/run_tests.py --integration   # 集成测试
./scripts/run_tests.py --benchmark     # 性能基准测试
```

### 测试类型说明

#### 1. 单元测试 (`test_unit.py`)
- 测试SandboxExecutor类的核心功能
- 使用Mock对象模拟Docker API
- 不需要实际的Docker环境
- 快速执行，适合开发阶段

#### 2. 简单功能测试 (`test_sandbox.py`)
- 基本的API功能测试
- 测试代码执行、错误处理等
- 需要运行中的沙盒服务

#### 3. 集成测试 (`test_comprehensive.py`)
- 全面的系统集成测试
- 包含安全性、并发性、错误处理等
- 测试真实的容器创建和销毁
- 验证资源限制和隔离效果

#### 4. 性能基准测试 (`test_benchmark.py`)
- 系统性能和负载测试
- 测试并发执行能力
- 容器启动开销分析
- CPU和内存密集型任务性能
- 生成详细的性能报告和图表

### 测试结果

性能测试会生成以下文件：
- `benchmark_results.json` - 详细的性能数据
- `benchmark_results.png` - 性能图表

### 持续集成

```bash
# 在CI环境中运行
./scripts/run_tests.py --no-service-check --unit
```

## 📋 管理命令

```bash
# 查看服务日志
docker logs -f sandbox-api

# 停止服务
docker stop sandbox-api

# 清理所有相关镜像
docker rmi sandbox-api sandbox-executor
```

## 🔧 配置选项

- `timeout`: 代码执行超时时间（秒，默认30）
- 内存限制: 128MB
- CPU限制: 50%
- 网络: 禁用

## 📦 支持的Python包

执行器容器预装了常用的Python包：
- pandas
- numpy
- matplotlib
- requests
- jupyter
- ipython