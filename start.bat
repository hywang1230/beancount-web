@echo off
chcp 65001
echo 🚀 启动 Beancount Web 记账系统...

REM 检查Python环境
echo 📦 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查Node.js环境
echo 📦 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js 未安装，请先安装Node.js 16或更高版本
    pause
    exit /b 1
)

REM 创建并激活Python虚拟环境
echo 🔧 设置Python虚拟环境...
if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate.bat

REM 安装Python依赖
echo 📥 安装后端依赖...
cd backend
pip install -r requirements.txt

REM 启动后端服务
echo 🌟 启动后端API服务...
start /b python main.py

REM 等待后端启动
timeout /t 5 /nobreak >nul

REM 安装前端依赖并启动
echo 📥 安装前端依赖...
cd ..\frontend

if not exist node_modules (
    npm install
)

REM 启动前端开发服务器
echo 🌟 启动前端开发服务器...
start /b npm run dev

echo.
echo ✅ Beancount Web 已启动!
echo 📊 前端地址: http://localhost:5173
echo 🔧 后端API: http://localhost:8000
echo 📚 API文档: http://localhost:8000/docs
echo.
echo 按任意键退出...
pause >nul 