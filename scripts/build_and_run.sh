#!/bin/bash

# 构建和运行沙盒系统脚本
docker stop sandbox-api

set -e

echo "🚀 开始构建沙盒容器执行系统..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

echo "✅ Docker已运行"

# 构建执行器镜像
echo "📦 构建沙盒执行器镜像..."
docker build -f docker/Dockerfile.executor -t sandbox-executor .
echo "✅ 执行器镜像构建完成"

# 构建主服务镜像
echo "📦 构建主服务镜像..."
docker build -f docker/Dockerfile -t sandbox-api .
echo "✅ 主服务镜像构建完成"

# 运行主服务
echo "🚀 启动沙盒API服务..."
docker run -d \
    --name sandbox-api \
    -p 16009:16009 \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --rm \
    sandbox-api


echo "✅ 沙盒API服务已启动在 http://localhost:16009"
echo "📋 服务日志: docker logs -f sandbox-api"
echo "🛑 停止服务: docker stop sandbox-api"
echo ""
echo "🧪 运行测试:"
echo "   python test_sandbox.py"
echo ""
echo "📖 API文档: http://localhost:16009/docs"