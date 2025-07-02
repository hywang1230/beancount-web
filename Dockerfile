# 多阶段构建Dockerfile for Beancount Web - 优化版本

# 阶段1: 前端构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制包管理文件（优化缓存）
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm ci --only=production --silent

# 复制前端源代码
COPY frontend/ ./

# 构建前端（设置内存限制）
ENV NODE_OPTIONS="--max-old-space-size=2048"
RUN npm run build

# 阶段2: Python依赖构建层
FROM python:3.11-alpine AS python-deps

# 安装构建依赖
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    libffi-dev \
    g++ \
    make \
    openblas-dev \
    lapack-dev \
    && pip install --upgrade pip

# 复制依赖文件
COPY backend/requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置pip优化选项
ENV PIP_PREFER_BINARY=1
ENV PIP_NO_BUILD_ISOLATION=0
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_NO_CACHE_DIR=1

# 分批安装依赖以优化构建缓存
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    "pydantic>=2.0.0,<3.0.0" \
    pydantic-settings==2.1.0

RUN pip install --no-cache-dir \
    python-multipart==0.0.6 \
    python-dateutil==2.8.2 \
    sqlalchemy==2.0.23 \
    alembic==1.13.0 \
    python-dotenv==1.0.0 \
    jinja2==3.1.2 \
    aiofiles==23.2.0

# 安装beancount和pandas（最耗时的包）
RUN pip install --no-cache-dir --timeout=600 beancount==3.0.0 || \
    pip install --no-cache-dir --timeout=300 beancount==2.3.6

RUN pip install --no-cache-dir --timeout=300 pandas==2.1.4 || \
    pip install --no-cache-dir --timeout=300 pandas==2.0.3 || \
    echo "警告: pandas安装失败，继续..."

# 清理构建依赖
RUN apk del .build-deps

# 阶段3: 最终运行镜像
FROM python:3.11-alpine AS runtime

# 安装运行时依赖
RUN apk add --no-cache \
    curl \
    openblas \
    lapack \
    libstdc++ \
    && addgroup -g 1001 -S appuser \
    && adduser -S -D -H -u 1001 -h /app -s /sbin/nologin -G appuser appuser

# 从依赖构建层复制虚拟环境
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 设置工作目录
WORKDIR /app

# 复制后端代码
COPY --chown=appuser:appuser backend/ ./

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist ./static

# 创建数据目录
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 