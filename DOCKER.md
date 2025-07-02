# Docker 部署说明

本项目支持通过Docker进行容器化部署，包含完整的前端和后端服务。

## 前置要求

1. 安装 Docker 和 Docker Compose
2. 如果要推送到DockerHub，需要配置GitHub Secrets

## GitHub Secrets 配置

为了使GitHub Actions能够推送镜像到DockerHub，需要在GitHub仓库中配置以下Secrets：

1. 进入GitHub仓库 -> Settings -> Secrets and variables -> Actions
2. 添加以下Secrets：
   - `DOCKERHUB_USERNAME`: 你的DockerHub用户名
   - `DOCKERHUB_TOKEN`: 你的DockerHub访问令牌（在DockerHub -> Account Settings -> Security -> Access Tokens中创建）

## 本地构建和运行

### 使用Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用Docker命令

```bash
# 构建镜像
docker build -t beancount-web .

# 运行容器
docker run -d \
  --name beancount-web \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  beancount-web
```

## 访问应用

- 应用地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 数据持久化

应用的数据文件存储在 `./data` 目录中，通过Docker卷挂载到容器的 `/app/data` 目录。

## 环境变量配置

可以通过环境变量配置应用：

- `PYTHONPATH`: Python路径 (默认: /app)
- `DATA_DIR`: 数据目录路径 (默认: /app/data)
- `ALLOWED_ORIGINS`: 允许的CORS源地址，多个地址用逗号分隔

## 生产部署建议

1. 使用Nginx作为反向代理
2. 配置SSL证书
3. 设置适当的环境变量
4. 定期备份数据目录
5. 监控容器健康状态

## CI/CD 流程

当代码推送到 `main` 或 `develop` 分支时，GitHub Actions会自动：

1. 构建Docker镜像
2. 推送到DockerHub
3. 支持多平台构建 (linux/amd64, linux/arm64)

镜像标签规则：
- `latest`: main分支的最新代码
- `main`: main分支
- `develop`: develop分支  
- `v1.0.0`: 版本标签

## 故障排除

### 构建失败
- 检查依赖是否正确安装
- 查看构建日志中的错误信息

### 容器启动失败
- 检查端口是否被占用
- 验证数据目录权限
- 查看容器日志: `docker logs beancount-web`

### 推送到DockerHub失败
- 确认GitHub Secrets配置正确
- 检查DockerHub访问令牌权限 