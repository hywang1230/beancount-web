# Makefile for Beancount Web Docker operations

.PHONY: build run stop clean logs shell test help

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  build       - 构建Docker镜像（Alpine版本）"
	@echo "  build-debian- 使用Debian版本构建（ARM64推荐）"
	@echo "  build-fast  - 快速构建版本（最小依赖）"
	@echo "  run         - 使用docker-compose启动服务"
	@echo "  stop        - 停止服务"
	@echo "  restart     - 重启服务"
	@echo "  logs        - 查看日志"
	@echo "  shell       - 进入容器shell"
	@echo "  clean       - 清理Docker镜像和容器"
	@echo "  test        - 测试容器健康状态"

# 构建镜像
build:
	docker build -t beancount-web .

# 使用Debian版本构建（ARM64平台推荐）
build-debian:
	docker build -f Dockerfile.debian -t beancount-web .

# 快速构建版本（最小依赖，用于测试）
build-fast:
	docker build -f Dockerfile.fast -t beancount-web .

# 使用docker-compose启动
run:
	docker-compose up -d

# 停止服务
stop:
	docker-compose down

# 重启服务
restart: stop run

# 查看日志
logs:
	docker-compose logs -f

# 进入容器shell
shell:
	docker-compose exec beancount-web sh

# 清理镜像和容器
clean:
	docker-compose down -v
	docker rmi beancount-web 2>/dev/null || true
	docker system prune -f

# 测试健康状态
test:
	@echo "测试应用健康状态..."
	@curl -f http://localhost:8000/health || echo "应用未响应"

# 构建并运行
dev: build run

# 生产部署（使用已发布的镜像）
deploy:
	docker-compose -f docker-compose.prod.yml up -d 