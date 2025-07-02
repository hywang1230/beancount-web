# Docker部署指南

本文档介绍如何使用Docker部署Beancount Web记账系统。

## 快速开始

### 使用Docker Compose

```bash
# 克隆项目
git clone <your-repo>
cd beancount-web

# 使用docker-compose启动
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

访问 http://localhost:8000 即可使用系统。

### 使用预构建镜像

```bash
# 拉取最新镜像
docker pull <your-dockerhub-username>/beancount-web:latest

# 运行容器
docker run -d \
  --name beancount-web \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  <your-dockerhub-username>/beancount-web:latest
```

## 生产环境部署

### 环境变量配置

创建 `.env` 文件：

```bash
# DockerHub用户名
DOCKERHUB_USERNAME=your-username

# 允许的跨域源
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 使用生产配置

```bash
# 使用生产环境配置
docker-compose -f docker-compose.prod.yml up -d
```

## GitHub Actions自动化部署

### 设置DockerHub Secrets

在GitHub仓库的Settings -> Secrets and variables -> Actions中添加以下secrets：

1. `DOCKERHUB_USERNAME`: 你的DockerHub用户名
2. `DOCKERHUB_TOKEN`: 你的DockerHub访问令牌

#### 创建DockerHub访问令牌

1. 登录 [DockerHub](https://hub.docker.com)
2. 点击右上角头像 -> Account Settings
3. 选择 Security -> New Access Token
4. 输入令牌名称（如：github-actions）
5. 选择权限：Read, Write, Delete
6. 点击Generate生成令牌
7. 复制令牌并添加到GitHub Secrets

### 自动构建触发条件

镜像会在以下情况自动构建和推送：

- 推送到 `main` 或 `develop` 分支
- 创建版本标签（如 `v1.0.0`）

### 镜像标签规则

- `latest`: main分支的最新构建
- `develop`: develop分支的最新构建
- `v1.0.0`: 对应版本标签
- `1.0`: 主要版本号
- `1`: 大版本号

## 数据持久化

### 数据目录

容器中的数据存储在 `/app/data` 目录，建议挂载到宿主机：

```bash
-v /path/to/your/data:/app/data
```

### 备份数据

```bash
# 备份数据目录
docker exec beancount-web tar czf /tmp/backup.tar.gz /app/data

# 从容器复制备份文件
docker cp beancount-web:/tmp/backup.tar.gz ./backup-$(date +%Y%m%d).tar.gz
```

## 健康检查

容器包含健康检查，可以监控服务状态：

```bash
# 查看健康状态
docker inspect beancount-web | grep -A5 Health

# 手动检查健康状态
curl http://localhost:8000/health
```

## 故障排除

### 查看日志

```bash
# Docker Compose
docker-compose logs -f beancount-web

# Docker直接运行
docker logs -f beancount-web
```

### 进入容器调试

```bash
docker exec -it beancount-web /bin/bash
```

### 常见问题

1. **端口冲突**: 确保8000端口未被其他服务占用
2. **权限问题**: 确保数据目录有正确的读写权限
3. **内存不足**: 生产环境建议至少512MB内存

## 性能优化

### 资源限制

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
```

### 使用多阶段构建

Dockerfile已使用多阶段构建优化镜像大小：
- 构建阶段：Node.js环境构建前端
- 运行阶段：Python精简环境运行应用

## 安全建议

1. **不要在镜像中包含敏感信息**
2. **定期更新基础镜像**
3. **使用非root用户运行容器**
4. **限制容器权限**
5. **定期扫描镜像安全漏洞**

GitHub Actions会自动进行安全扫描，只报告高危和严重漏洞。 