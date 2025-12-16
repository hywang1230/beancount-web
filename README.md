# 🧮 Beancount Web 记账系统

<div align="center">

基于 [Beancount](https://beancount.github.io/) 的现代化复式记账系统，专为移动端优化，集成 AI 智能财务分析。

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://hub.docker.com/r/pionnerwang/beancount-web)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D?style=flat-square&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

</div>

---

## ✨ 功能特性

### 📱 核心记账

- **复式记账引擎** - 基于 Beancount 3，确保账务准确性与专业性
- **移动端优先** - Vue 3 + Vant 4 UI，针对移动设备深度优化
- **PWA 支持** - 可安装为桌面/移动应用，支持离线访问
- **多账本管理** - 支持按年份自动分文件，账本 include 引用管理

### 🤖 AI 财务助手

- **智能分析** - 集成阿里云百炼 (通义千问) 大模型
- **流式对话** - 实时流式输出，对话体验流畅自然
- **财务洞察** - 自动分析消费习惯，提供个性化理财建议
- **多轮对话** - 支持上下文连续对话，深入探讨财务问题

### 📊 报表与分析

- **实时仪表盘** - 直观展示收支趋势与资产分布
- **多维度报表** - 月度/季度/年度报表，支持自定义日期范围
- **BQL 高级查询** - 完整支持 Beancount Query Language，8 个预置查询模板
- **图表可视化** - 基于 ECharts 的交互式图表

### 💰 预算管理

- **灵活周期** - 支持月度、季度、年度预算设置
- **实时追踪** - 预算执行进度实时更新
- **超支预警** - 接近或超出预算时自动提醒

### � 周期交易

- **自动记账** - 设置周期规则，自动生成定期交易
- **灵活配置** - 支持每日/每周/每月/每年等多种频率
- **执行管理** - 一键执行待处理的周期交易

### ☁️ 数据同步

- **GitHub 备份** - 自动同步账本到 GitHub 仓库
- **多设备同步** - 在多台设备间保持数据一致
- **版本控制** - 利用 Git 记录每次变更历史

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 使用 docker-compose
docker-compose up -d

# 或者直接运行 Docker 镜像
docker run -d \
  --name beancount-web \
  -p 8000:8000 \
  -v beancount-data:/app/data \
  -e USERNAME=admin \
  -e PASSWORD=admin123 \
  -e ENABLE_AUTH=true \
  -e DASHSCOPE_API_KEY=your-api-key \
  pionnerwang/beancount-web:latest
```

访问地址：http://localhost:8000

### 方式二：本地开发

```bash
# 克隆项目
git clone https://github.com/your-repo/beancount-web.git
cd beancount-web

# 一键启动（后端 + 前端）
chmod +x start.sh && ./start.sh
```

- 前端开发地址：http://localhost:5173
- 后端 API 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 默认登录凭证

- **用户名**：`admin`
- **密码**：`admin123`

---

## 🛠️ 技术栈

### 前端

| 技术       | 版本 | 说明                   |
| ---------- | ---- | ---------------------- |
| Vue.js     | 3.x  | 渐进式 JavaScript 框架 |
| TypeScript | 5.x  | 类型安全的 JavaScript  |
| Vant       | 4.x  | 轻量级移动端 UI 组件库 |
| Vite       | 5.x  | 现代化前端构建工具     |
| Pinia      | 2.x  | Vue 状态管理           |
| Vue Router | 4.x  | 官方路由管理器         |
| ECharts    | 5.x  | 数据可视化图表库       |
| PWA        | -    | 渐进式 Web 应用支持    |

### 后端

| 技术        | 版本 | 说明                |
| ----------- | ---- | ------------------- |
| Python      | 3.8+ | 主开发语言          |
| FastAPI     | -    | 高性能异步 Web 框架 |
| Beancount   | 3.x  | 复式记账引擎        |
| SQLAlchemy  | -    | ORM 数据库框架      |
| SQLite      | -    | 轻量级数据库        |
| APScheduler | -    | 任务调度器          |
| Alembic     | -    | 数据库迁移工具      |

### AI 能力

| 技术       | 说明                        |
| ---------- | --------------------------- |
| 阿里云百炼 | 通义千问大模型 API          |
| qwen3-max  | 默认使用模型                |
| SSE        | Server-Sent Events 流式响应 |

### 基础设施

| 技术           | 说明             |
| -------------- | ---------------- |
| Docker         | 容器化部署       |
| GitHub Actions | CI/CD 自动化     |
| Nginx          | 反向代理（可选） |

---

## 📁 项目结构

```
beancount-web/
├── backend/                    # 后端 Python 服务
│   ├── app/
│   │   ├── ai/                 # AI 分析模块
│   │   │   ├── service.py      # AI 服务核心逻辑
│   │   │   ├── tools/          # AI 工具集
│   │   │   │   ├── budget_tool.py    # 预算分析工具
│   │   │   │   ├── ledger_tool.py    # 账本查询工具
│   │   │   │   └── report_tool.py    # 报表生成工具
│   │   │   └── config/         # AI 配置
│   │   ├── core/               # 核心配置
│   │   ├── models/             # 数据模型
│   │   ├── routers/            # API 路由
│   │   │   ├── transactions.py # 交易接口
│   │   │   ├── reports.py      # 报表接口
│   │   │   ├── accounts.py     # 账户接口
│   │   │   ├── budgets.py      # 预算接口
│   │   │   ├── recurring.py    # 周期记账接口
│   │   │   ├── query.py        # BQL 查询接口
│   │   │   ├── ai.py           # AI 分析接口
│   │   │   └── ...
│   │   ├── services/           # 业务服务层
│   │   └── utils/              # 工具函数
│   ├── requirements.txt        # Python 依赖
│   └── main.py                 # 应用入口
├── frontend/                   # 前端 Vue 应用
│   ├── src/
│   │   ├── api/                # API 接口封装
│   │   ├── components/         # 通用组件
│   │   │   ├── AIAssistant.vue # AI 助手对话框
│   │   │   └── ...
│   │   ├── views/              # 页面视图
│   │   │   └── h5/             # 移动端页面
│   │   │       ├── Dashboard.vue       # 仪表盘
│   │   │       ├── Transactions.vue    # 交易列表
│   │   │       ├── Accounts.vue        # 账户管理
│   │   │       ├── Reports.vue         # 报表分析
│   │   │       ├── Budgets.vue         # 预算管理
│   │   │       ├── Query.vue           # BQL 查询
│   │   │       └── ...
│   │   ├── router/             # 路由配置
│   │   ├── stores/             # Pinia 状态管理
│   │   └── utils/              # 工具函数
│   └── package.json            # Node.js 依赖
├── data/                       # 账本数据目录
├── docker-compose.yml          # Docker 编排配置
├── Dockerfile                  # Docker 镜像构建
├── start.sh                    # 本地开发启动脚本
└── README.md
```

---

## ⚙️ 配置说明

### 环境变量

创建 `backend/.env` 文件（可参考 `.env.example`）：

```bash
# AI 分析功能（阿里云百炼 通义千问）
DASHSCOPE_API_KEY=your-api-key-here

# 认证配置
ENABLE_AUTH=true
USERNAME=admin
PASSWORD=admin123

# 可选：数据目录
# DATA_DIR=/app/data
```

### Docker Compose 配置

```yaml
version: "3.8"

services:
  beancount-web:
    image: pionnerwang/beancount-web:latest
    ports:
      - "8000:8000"
    volumes:
      - beancount-data:/app/data # 持久化账本数据
      - ./my-ledger:/app/data # 或挂载本地目录
    environment:
      - USERNAME=admin
      - PASSWORD=admin123
      - ENABLE_AUTH=true
      - DASHSCOPE_API_KEY=your-api-key
    restart: unless-stopped

volumes:
  beancount-data:
```

---

## 📖 API 文档

启动服务后访问自动生成的交互式 API 文档：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

### 主要 API 端点

| 模块     | 端点                  | 说明           |
| -------- | --------------------- | -------------- |
| 认证     | `/api/auth/*`         | 用户登录/登出  |
| 交易     | `/api/transactions/*` | 交易增删改查   |
| 报表     | `/api/reports/*`      | 财务报表查询   |
| 账户     | `/api/accounts/*`     | 账户管理       |
| 预算     | `/api/budgets/*`      | 预算管理       |
| 周期记账 | `/api/recurring/*`    | 周期交易管理   |
| BQL 查询 | `/api/query/*`        | Beancount 查询 |
| AI 分析  | `/api/ai/*`           | AI 财务分析    |
| 文件管理 | `/api/files/*`        | 账本文件管理   |
| 同步     | `/api/sync/*`         | GitHub 同步    |

---

## 🖥️ 界面预览

### 主要功能页面

- **仪表盘** - 财务概览，收支趋势图表
- **交易列表** - 全部交易记录，支持搜索筛选
- **记账页面** - 快速添加交易，智能分类
- **账户管理** - 资产/负债/收入/支出账户树
- **报表分析** - 多维度财务报表
- **预算管理** - 预算设置与执行追踪
- **BQL 查询** - 高级数据查询
- **AI 助手** - 智能财务对话

---

## 🔧 开发指南

### 前端开发

```bash
cd frontend
npm install
npm run dev       # 开发模式
npm run build     # 生产构建
npm run lint      # 代码检查
```

### 后端开发

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py    # 启动开发服务器
```

### 代码规范

- **前端**：ESLint + Vue 官方风格指南
- **后端**：Black + isort + flake8

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 发起 Pull Request

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

## 🙏 致谢

- [Beancount](https://beancount.github.io/) - 强大的纯文本复式记账引擎
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架
- [Vant](https://vant-ui.github.io/) - 轻量级移动端 Vue 组件库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代 Python Web 框架
- [阿里云百炼](https://bailian.console.aliyun.com/) - 通义千问大模型能力支持
