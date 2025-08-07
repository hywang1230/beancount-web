# Beancount Web 记账系统

一个基于 Beancount 3 的现代化复式记账系统，提供直观的 Web 界面进行记账、流水查看和报表分析。

**单用户系统** - 专为个人记账设计，无需用户认证，开箱即用。

## 项目结构

```
beancount-web/
├── frontend/           # Vue3 前端应用
│   ├── src/
│   │   ├── views/
│   │   │   ├── pc/     # PC端页面
│   │   │   └── h5/     # 移动端页面
│   │   ├── layout/     # 布局组件
│   │   ├── components/ # 共享组件
│   │   └── api/        # API接口
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── routers/    # API路由
│   │   ├── services/   # 业务服务
│   │   ├── models/     # 数据模型
│   │   └── core/       # 核心配置
├── data/             # Beancount 账本文件存储
└── logs/             # 应用日志
```

## 功能特性

### 💰 核心记账功能
- **复式记账** - 支持完整的Beancount复式记账系统
- **多账户管理** - 资产、负债、收入、支出账户全方位管理
- **快速记账** - 直观的记账界面，支持转账、收入、支出等多种类型

### 📊 报表分析
- **收支统计** - 按时间、分类的详细收支分析
- **资产负债表** - 实时资产负债情况一目了然
- **趋势分析** - 图表展示财务趋势变化

### 📁 文件管理
- 支持 `.beancount` 和 `.bean` 文件格式
- 文件上传、下载、在线编辑
- 语法验证和错误检查
- 自动备份机制

### 🔄 周期记账
- **自动化记账** - 支持按日、周、月的周期性交易
- **智能执行** - 自动检测并执行到期的周期交易
- **灵活配置** - 支持复杂的周期规则设置

### 📱 移动端支持
- **跨端体验** - PC端和移动端分离式设计，体验更优
- **智能适配** - 自动检测设备类型，使用对应UI组件
- **触摸优化** - 移动端触摸交互优化，支持手势操作

### 🔍 其他功能
- **强大搜索** - 支持多维度的交易搜索和过滤
- **数据导出** - 支持CSV等格式的数据导出
- **单用户模式** - 专为个人使用设计，无需认证，开箱即用

## 技术栈

### 前端
- **框架**: Vue 3.x + TypeScript
- **构建工具**: Vite 5.x
- **PC端UI**: Element Plus + @element-plus/icons
- **移动端UI**: Vant 4.x + @vant/icons
- **路由**: Vue Router 4.x
- **状态管理**: Pinia
- **图表**: ECharts + Vue-ECharts
- **HTTP客户端**: Axios
- **日期处理**: Day.js

### 后端
- **框架**: Python 3.8+ + FastAPI
- **记账引擎**: Beancount 3.x
- **异步支持**: Uvicorn + asyncio
- **数据处理**: Pandas
- **任务调度**: APScheduler
- **文件处理**: aiofiles
- **数据验证**: Pydantic 2.x
- **配置管理**: pydantic-settings

## 快速开始

### 方式一：使用启动脚本（推荐）

```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

等待服务启动后，访问: http://localhost:5173

### 方式二：手动启动

**后端服务**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**前端服务**
```bash
cd frontend
npm install
npm run dev
```

### 方式三：Docker部署

```bash
# 开发环境
docker-compose up -d

# 生产环境
docker-compose -f docker-compose.prod.yml up -d
```

访问: http://localhost:8000

## 跨端支持

### PC端
- 优雅的桌面端界面，使用Element Plus
- 侧边栏导航 + 面包屑
- 支持大屏幕显示和复杂操作

### 移动端
- 专为移动设备优化，使用Vant UI
- 底部Tab导航 + 顶部操作栏
- 支持手势操作和触摸交互
- 自适应屏幕尺寸

### 智能路由
- 自动检测设备类型（User Agent + 屏幕尺寸）
- 无缝切换对应端的界面
- 支持手动指定访问端（/dashboard 或 /h5/dashboard）

## 部署指南

### 开发环境
请参考上方的快速开始部分。

### 生产环境

1. **Docker部署**（推荐）
   详细信息请查看 [DOCKER.md](./DOCKER.md)

2. **手动部署**
   ```bash
   # 构建前端
   cd frontend
   npm run build
   
   # 启动后端生产服务
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### 数据持久化
- 账本数据存储在 `data/` 目录
- 支持多种格式的Beancount文件
- 建议定期备份数据目录

## 许可证

MIT License
