FROM jupyter/base-notebook:latest

# 切换到root用户安装Docker客户端
USER root

# 移除Jupyter的健康检查
HEALTHCHECK NONE

# 安装Docker客户端
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

# 在macOS Docker Desktop环境下，使用root用户运行以访问Docker socket
# 注意：这仅适用于开发环境，生产环境需要更安全的配置
USER root

WORKDIR /app

# 创建启动脚本来处理Docker socket权限
RUN echo '#!/bin/bash' > start.sh && \
    echo 'chmod 666 /var/run/docker.sock 2>/dev/null || true' >> start.sh && \
    echo 'exec python main.py' >> start.sh && \
    chmod +x start.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

EXPOSE 16009

CMD ["./start.sh"]