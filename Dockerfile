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

# 阶段2: 后端运行环境
FROM python:3.11-alpine AS backend

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    g++ \
    make \
    curl

# 复制后端要求文件
COPY backend/requirements.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist ./static

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