#!/bin/bash
set -e

echo "开始安装Python依赖..."

# 检测架构
ARCH=$(uname -m)
echo "检测到架构: $ARCH"

# 先安装纯Python包（快速）
echo "安装核心依赖..."
pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    python-dateutil==2.8.2 \
    "pydantic>=2.0.0,<3.0.0" \
    pydantic-settings==2.1.0 \
    sqlalchemy==2.0.23 \
    alembic==1.13.0 \
    python-dotenv==1.0.0 \
    jinja2==3.1.2 \
    aiofiles==23.2.0

# 安装pandas（可选）
echo "安装pandas..."
if [ "$ARCH" = "aarch64" ]; then
    echo "ARM64架构，尝试安装预编译的pandas..."
    pip install --no-cache-dir --timeout 300 pandas==2.1.4 || \
    pip install --no-cache-dir --timeout 300 pandas==2.0.3 || \
    echo "警告: pandas安装失败，跳过..."
else
    pip install --no-cache-dir pandas==2.1.4
fi

# 安装beancount
echo "安装beancount..."
if [ "$ARCH" = "aarch64" ]; then
    echo "ARM64架构，尝试安装beancount..."
    pip install --no-cache-dir --timeout 600 beancount==3.0.0 || \
    pip install --no-cache-dir --timeout 300 beancount==2.3.6 || \
    echo "警告: beancount安装失败，跳过..."
else
    pip install --no-cache-dir beancount==3.0.0
fi

echo "依赖安装完成！" 