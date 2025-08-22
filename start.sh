#!/bin/bash

# Beancount Web 项目启动脚本

echo "🚀 启动 Beancount Web 记账系统..."

# 检查Python环境
echo "📦 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python 3.8或更高版本"
    exit 1
fi

# 检查Node.js环境
echo "📦 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装Node.js 16或更高版本"
    exit 1
fi

# 创建并激活Python虚拟环境
echo "🔧 设置Python虚拟环境..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

# 安装Python依赖
echo "📥 安装后端依赖..."
cd backend
pip install -r requirements.txt

# 启动后端服务
echo "🌟 启动后端API服务..."
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 安装前端依赖并启动
echo "📥 安装前端依赖..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    npm install
fi

# 启动前端开发服务器
echo "🌟 启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Beancount Web 已启动!"
echo "📊 前端地址: http://localhost:5173"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
trap "echo '🛑 正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait 