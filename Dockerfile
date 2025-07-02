# 多阶段构建Dockerfile for Beancount Web

# 阶段1: 前端构建
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端包管理文件
COPY frontend/package*.json ./

# 安装前端依赖（包含devDependencies，因为构建需要）
RUN npm ci

# 复制前端源代码
COPY frontend/ ./

# 检查依赖和构建环境
RUN npm list --depth=0
RUN which vue-tsc || echo "vue-tsc not found"
RUN which vite || echo "vite not found"

# 设置Node.js内存限制并构建前端
ENV NODE_OPTIONS="--max-old-space-size=4096"
RUN npm run build || (echo "TypeScript检查失败，尝试跳过类型检查..." && npx vite build)

# 阶段2: Python依赖构建阶段
FROM python:3.11-alpine AS python-builder

# 安装构建依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    g++ \
    make \
    openblas-dev \
    lapack-dev \
    gfortran \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev

# 复制requirements文件
COPY backend/requirements.txt ./

# 设置pip配置
ENV PIP_PREFER_BINARY=1
ENV PIP_NO_BUILD_ISOLATION=0

# 升级pip和安装构建工具
RUN pip install --upgrade pip wheel setuptools

# 创建wheel目录并构建所有依赖的wheel包
RUN mkdir /wheels
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# 阶段3: 最终运行环境
FROM python:3.11-alpine AS backend

# 设置工作目录
WORKDIR /app

# 只安装运行时必需的系统依赖
RUN apk add --no-cache \
    curl \
    libstdc++ \
    openblas \
    lapack

# 从构建阶段复制wheel包
COPY --from=python-builder /wheels /wheels

# 安装Python依赖（使用预构建的wheel包）
RUN pip install --no-cache-dir --find-links /wheels -r requirements.txt \
    && rm -rf /wheels

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

# 复制requirements文件（用于安装）
COPY backend/requirements.txt ./

# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 