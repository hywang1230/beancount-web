# Makefile for Beancount Web Docker operations

.PHONY: build run stop clean logs shell test help build-multi build-ci frontend backend lint check

# 默认目标
help:
	@echo "🚀 Beancount Web 构建和部署命令"
	@echo ""
	@echo "📦 构建命令:"
	@echo "  build        - 构建优化的Docker镜像"
	@echo "  build-multi  - 构建多平台镜像（amd64+arm64）"
	@echo "  build-ci     - CI快速构建（仅amd64）"
	@echo "  build-cache  - 使用GitHub Actions缓存构建"
	@echo ""
	@echo "🛠️  开发命令:"
	@echo "  frontend     - 构建前端"
	@echo "  backend      - 安装后端依赖"
	@echo "  dev          - 启动开发环境"
	@echo "  lint         - 代码质量检查"
	@echo "  check        - 全面检查（lint + test）"
	@echo ""
	@echo "🐳 Docker命令:"
	@echo "  run          - 启动服务"
	@echo "  stop         - 停止服务"
	@echo "  restart      - 重启服务"
	@echo "  logs         - 查看日志"
	@echo "  shell        - 进入容器shell"
	@echo "  test         - 测试容器健康状态"
	@echo ""
	@echo "🧹 清理命令:"
	@echo "  clean        - 清理Docker镜像和容器"
	@echo "  clean-all    - 深度清理（包括缓存）"
	@echo ""
	@echo "🚀 部署命令:"
	@echo "  deploy       - 生产部署"
	@echo ""

# 构建优化的Docker镜像
build:
	@echo "🔨 构建优化的Docker镜像..."
	docker build -t beancount-web .

# 构建多平台镜像
build-multi:
	@echo "🔨 构建多平台Docker镜像..."
	docker buildx build --platform linux/amd64,linux/arm64 -t beancount-web .

# CI快速构建（仅amd64）
build-ci:
	@echo "⚡ CI快速构建..."
	docker buildx build --platform linux/amd64 --load -t beancount-web:ci .

# 使用GitHub Actions缓存构建
build-cache:
	@echo "📦 使用缓存构建..."
	docker buildx build \
		--cache-from type=gha \
		--cache-to type=gha,mode=max \
		-t beancount-web .

# 前端构建
frontend:
	@echo "🎨 构建前端..."
	cd frontend && npm ci --silent && npm run build

# 后端依赖安装
backend:
	@echo "🐍 安装后端依赖..."
	cd backend && chmod +x install_deps.sh && ./install_deps.sh

# 代码质量检查
lint:
	@echo "🔍 代码质量检查..."
	@if command -v shellcheck >/dev/null 2>&1; then \
		echo "检查Shell脚本..."; \
		find . -name "*.sh" -not -path "./venv/*" -exec shellcheck {} \; || true; \
	fi
	@echo "检查大文件..."
	@find . -type f -size +10M -not -path "./venv/*" -not -path "./.git/*" | head -5 || true
	@echo "检查Docker配置..."
	@if command -v hadolint >/dev/null 2>&1; then \
		hadolint Dockerfile || true; \
	fi

# 全面检查
check: lint
	@echo "🧪 运行测试..."
	@if [ -d "frontend" ]; then \
		echo "检查前端依赖..."; \
		cd frontend && npm audit --audit-level=high || true; \
	fi
	@if [ -f "backend/requirements.txt" ]; then \
		echo "检查Python依赖..."; \
		cd backend && python -m pip check || true; \
	fi

# 启动开发环境
dev: frontend
	@echo "🚀 启动开发环境..."
	docker-compose up -d

# 使用docker-compose启动
run:
	@echo "🚀 启动服务..."
	docker-compose up -d

# 停止服务
stop:
	@echo "⏹️  停止服务..."
	docker-compose down

# 重启服务
restart: stop run

# 查看日志
logs:
	@echo "📄 查看日志..."
	docker-compose logs -f

# 进入容器shell
shell:
	@echo "🐚 进入容器..."
	docker-compose exec beancount-web sh

# 测试健康状态
test:
	@echo "🏥 测试应用健康状态..."
	@sleep 5
	@if curl -f http://localhost:8000/health >/dev/null 2>&1; then \
		echo "✅ 应用运行正常"; \
	else \
		echo "❌ 应用未响应"; \
		exit 1; \
	fi

# 清理镜像和容器
clean:
	@echo "🧹 清理Docker资源..."
	docker-compose down -v
	docker rmi beancount-web 2>/dev/null || true
	docker image prune -f

# 深度清理
clean-all: clean
	@echo "🧹 深度清理..."
	docker system prune -a -f --volumes
	docker buildx prune -f

# 生产部署
deploy:
	@echo "🚀 生产部署..."
	docker-compose -f docker-compose.prod.yml up -d

# 快速开发流程
quick: build-ci run test
	@echo "✅ 快速开发环境已就绪!"

# 生产构建流程
release: check build-multi
	@echo "✅ 生产版本构建完成!"

# 安装开发工具
install-tools:
	@echo "🛠️  安装开发工具..."
	@if ! command -v hadolint >/dev/null 2>&1; then \
		echo "安装hadolint..."; \
		wget -O /tmp/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 && \
		chmod +x /tmp/hadolint && \
		sudo mv /tmp/hadolint /usr/local/bin/ || echo "hadolint安装失败"; \
	fi
	@if ! command -v shellcheck >/dev/null 2>&1; then \
		echo "请安装shellcheck: apt-get install shellcheck 或 brew install shellcheck"; \
	fi 