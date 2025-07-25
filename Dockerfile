# 多阶段构建Dockerfile
# 阶段1: 构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端package文件
COPY frontend/package*.json ./

# 安装前端依赖（包括开发依赖，构建时需要）
RUN npm ci

# 复制前端源码
COPY frontend/ .

# 构建前端应用
RUN npm run build

# 阶段2: 运行时环境
FROM python:3.11-slim

WORKDIR /app

# 设置时区为东八区
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 复制后端requirements文件
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端源码
COPY backend/ .

# 从前端构建阶段复制构建结果到静态文件目录
COPY --from=frontend-builder /app/frontend/dist/ ./static/

# 创建数据目录并设置权限
RUN mkdir -p /app/data && chmod 755 /app/data

# 设置环境变量
ENV DATA_DIR=/app/data
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 