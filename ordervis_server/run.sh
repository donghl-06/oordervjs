#!/bin/bash

# FastAPI 启动脚本

echo "🚀 启动 OrderVis Server - FastAPI 版本"

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 需要Python 3.8或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "❌ 找不到 requirements.txt 文件"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt

# 检查是否安装成功
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI安装失败，请检查依赖安装"
    exit 1
fi

echo "✅ 依赖安装完成"

# 启动服务器
echo "🌐 启动FastAPI服务器..."
echo "📍 访问地址: http://localhost:18080"
echo "📖 API文档: http://localhost:18080/docs"
echo "🔌 WebSocket: ws://localhost:18080/ws"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

# 启动服务器
python3 main.py 