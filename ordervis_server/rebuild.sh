#!/bin/bash

# 重建 Docker 容器脚本
# 使用方法: ./rebuild.sh

echo "🔄 开始重建 Docker 容器..."

# 停止并删除容器和镜像
echo "📦 停止容器并删除镜像..."
docker-compose down --rmi local

# 重新构建并启动
echo "🔨 重新构建并启动容器..."
docker-compose up -d --build

# 检查状态
echo "✅ 重建完成！"
echo "📊 容器状态:"
docker-compose ps

echo ""
echo "🌐 访问地址: http://localhost:18080"
echo "📚 API文档: http://localhost:18080/docs"
