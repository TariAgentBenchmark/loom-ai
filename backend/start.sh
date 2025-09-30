#!/bin/bash

# LoomAI Backend 启动脚本

echo "🚀 启动 LoomAI Backend..."

# 检查是否安装了uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，请先安装 uv"
    echo "安装命令: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 创建虚拟环境（如果不存在）
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    uv venv
fi

# 激活虚拟环境并安装依赖
echo "📥 安装依赖..."
uv sync

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，复制示例文件..."
    cp env.example .env
    echo "📝 请编辑 .env 文件配置必要的环境变量"
fi

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p uploads/originals
mkdir -p uploads/results
mkdir -p uploads/temp

# 初始化数据库
echo "🗄️  初始化数据库..."
uv run python -c "from app.core.database import init_db; init_db()"

# 启动服务器
echo "🌟 启动服务器..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""

uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
