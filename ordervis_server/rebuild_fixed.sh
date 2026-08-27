#!/bin/bash

# 修复后的重建 Docker 容器脚本
# 使用方法: ./rebuild_fixed.sh

echo "🔄 开始重建 Docker 容器..."

# 修复 locale 问题
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

echo "📦 停止容器并删除镜像..."

# 使用 docker compose（新语法）替代 docker-compose（旧语法）
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    echo "使用 Docker Compose V2..."
    docker compose down --rmi local
    echo "🔨 重新构建并启动容器..."
    docker compose up -d --build
else
    echo "使用 Docker Compose V1..."
    # 设置环境变量避免兼容性问题
    export DOCKER_CLIENT_TIMEOUT=120
    export COMPOSE_HTTP_TIMEOUT=120
    docker-compose down --rmi local
    echo "🔨 重新构建并启动容器..."
    docker-compose up -d --build
fi

# 检查状态
echo "✅ 重建完成！"
echo "📊 容器状态:"

# 根据可用的 docker compose 版本显示状态
if command -v docker &> /dev/null && docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

echo ""
echo "🌐 访问地址: http://localhost:18080"
echo "📚 API文档: http://localhost:18080/docs"