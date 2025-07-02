#!/bin/bash

# Beancount Web Docker 快速部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
Beancount Web Docker 部署脚本

用法: $0 [选项]

选项:
    -h, --help          显示此帮助信息
    -m, --mode MODE     部署模式: dev (开发) 或 prod (生产)，默认: dev
    -p, --port PORT     端口号，默认: 8000
    -d, --data DIR      数据目录，默认: ./data
    --pull              拉取最新镜像（仅生产模式）
    --build             强制重新构建镜像（仅开发模式）
    --logs              启动后显示日志
    --stop              停止服务
    --restart           重启服务

示例:
    $0                          # 使用默认配置启动开发环境
    $0 -m prod --pull          # 启动生产环境并拉取最新镜像
    $0 -p 9000 -d /data/bc     # 自定义端口和数据目录
    $0 --stop                   # 停止服务
    $0 --logs                   # 查看服务日志

EOF
}

# 默认配置
MODE="dev"
PORT="8000"
DATA_DIR="./data"
PULL_IMAGE=false
BUILD_IMAGE=false
SHOW_LOGS=false
STOP_SERVICE=false
RESTART_SERVICE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--data)
            DATA_DIR="$2"
            shift 2
            ;;
        --pull)
            PULL_IMAGE=true
            shift
            ;;
        --build)
            BUILD_IMAGE=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --stop)
            STOP_SERVICE=true
            shift
            ;;
        --restart)
            RESTART_SERVICE=true
            shift
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 验证模式
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
    print_error "无效的部署模式: $MODE (支持: dev, prod)"
    exit 1
fi

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    print_error "Docker 未安装或不在PATH中"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose 未安装或不在PATH中"
    exit 1
fi

# 停止服务
if [[ "$STOP_SERVICE" == true ]]; then
    print_info "停止 Beancount Web 服务..."
    if [[ "$MODE" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml down
    else
        docker-compose down
    fi
    print_success "服务已停止"
    exit 0
fi

# 重启服务
if [[ "$RESTART_SERVICE" == true ]]; then
    print_info "重启 Beancount Web 服务..."
    if [[ "$MODE" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml restart
    else
        docker-compose restart
    fi
    print_success "服务已重启"
    exit 0
fi

# 仅显示日志
if [[ "$SHOW_LOGS" == true && "$STOP_SERVICE" == false && "$RESTART_SERVICE" == false ]]; then
    print_info "显示服务日志..."
    if [[ "$MODE" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
    exit 0
fi

print_info "开始部署 Beancount Web..."
print_info "部署模式: $MODE"
print_info "端口: $PORT"
print_info "数据目录: $DATA_DIR"

# 创建数据目录
if [[ ! -d "$DATA_DIR" ]]; then
    print_info "创建数据目录: $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

# 设置环境变量
export PORT="$PORT"
export DATA_DIR="$(realpath "$DATA_DIR")"

# 生产模式
if [[ "$MODE" == "prod" ]]; then
    if [[ -z "$DOCKERHUB_USERNAME" ]]; then
        print_error "生产模式需要设置 DOCKERHUB_USERNAME 环境变量"
        print_info "请运行: export DOCKERHUB_USERNAME=your-username"
        exit 1
    fi
    
    if [[ "$PULL_IMAGE" == true ]]; then
        print_info "拉取最新镜像..."
        docker pull "$DOCKERHUB_USERNAME/beancount-web:latest"
    fi
    
    print_info "启动生产环境..."
    docker-compose -f docker-compose.prod.yml up -d
    
# 开发模式
else
    if [[ "$BUILD_IMAGE" == true ]]; then
        print_info "重新构建镜像..."
        docker-compose build --no-cache
    fi
    
    print_info "启动开发环境..."
    docker-compose up -d
fi

# 等待服务启动
print_info "等待服务启动..."
sleep 10

# 检查服务状态
if curl -f "http://localhost:$PORT/health" &>/dev/null; then
    print_success "✅ Beancount Web 部署成功!"
    print_success "🌐 访问地址: http://localhost:$PORT"
    print_info "💾 数据目录: $DATA_DIR"
else
    print_warning "⚠️  服务可能还在启动中，请稍等片刻"
    print_info "🔍 查看日志: $0 --logs"
fi

# 显示日志
if [[ "$SHOW_LOGS" == true ]]; then
    print_info "显示服务日志..."
    if [[ "$MODE" == "prod" ]]; then
        docker-compose -f docker-compose.prod.yml logs -f
    else
        docker-compose logs -f
    fi
fi

print_info "🔧 管理命令:"
print_info "  查看日志: $0 --logs"
print_info "  停止服务: $0 --stop"
print_info "  重启服务: $0 --restart" 