<div align="center">

# 💰 Beancount Web 记账系统

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)

一个基于 **Beancount 3** 的现代化复式记账系统，专为移动端优化，提供直观的触屏界面进行记账、流水查看和报表分析。

🎯 **单用户系统** - 专为个人记账设计，支持用户认证，安全可靠

📱 **移动端优化** - 基于Vant UI的原生移动体验，支持PWA安装

🚀 **快速部署** - 支持Docker一键部署，5分钟即可启动

</div>

---

## 项目结构

```
beancount-web/
├── frontend/           # Vue3 移动端应用
│   ├── src/
│   │   ├── views/
│   │   │   └── h5/     # 移动端页面
│   │   ├── layout/
│   │   │   └── h5/     # 移动端布局
│   │   ├── components/ # 共享组件
│   │   ├── api/        # API接口
│   │   └── utils/      # 工具函数
├── backend/           # Python FastAPI 后端
│   ├── app/
│   │   ├── routers/    # API路由
│   │   ├── services/   # 业务服务
│   │   ├── models/     # 数据模型
│   │   ├── utils/      # 工具函数
│   │   └── core/       # 核心配置
├── data/             # Beancount 账本文件存储
└── logs/             # 应用日志
```

## ✨ 功能特性

<table>
<tr>
<td width="50%">

### 💰 核心记账功能
- 🏦 **完整复式记账** - 基于Beancount标准的双分录记账系统
- 📋 **智能账户管理** - 支持资产、负债、收入、支出、权益五大类账户
- ⚡ **快速记账** - 一键添加收入、支出、转账等常用交易
- 🏷️ **标签分类** - 支持多级分类和自定义标签，精细化管理
- 💱 **多币种支持** - 完整的外币和汇率管理

### 📊 报表分析
- 📈 **实时财务仪表板** - 关键财务指标一目了然
- 📉 **趋势分析图表** - 收支趋势、资产变化可视化展示
- 🏦 **资产负债表** - 实时更新的财务状况报告
- 💸 **收支损益表** - 按期间的详细收支分析
- 📊 **自定义报表** - 支持按时间、账户、分类等多维度分析

### 🔄 智能周期记账
- ⏰ **自动化记账** - 设置后自动执行周期性交易
- 📅 **灵活周期设置** - 支持日、周、月、年等多种周期
- 🎯 **智能提醒** - 到期前自动提醒，避免遗漏
- 🔧 **批量管理** - 批量创建、编辑、暂停周期交易

</td>
<td width="50%">

### 📱 移动端体验
- 📱 **原生移动体验** - 基于Vant UI组件，专为触屏设计
- ✋ **触摸手势优化** - 支持滑动、长按等移动端交互
- 📱 **PWA支持** - 可安装为原生应用，支持离线使用
- 🔄 **响应式设计** - 完美适配各种移动设备屏幕

### 📁 文件管理系统
- 📄 **多格式支持** - `.beancount`、`.bean` 文件完全兼容
- ☁️ **在线编辑器** - 内置语法高亮的编辑器
- ✅ **实时语法检查** - 自动验证Beancount语法
- 💾 **自动备份** - 文件变更自动备份，数据安全保障
- 📤 **导入导出** - 支持CSV等格式的批量导入导出

### 🔍 高级功能
- 🔎 **全文搜索** - 支持交易描述、账户名称等全文搜索
- 🏷️ **高级筛选** - 按日期、金额、账户等多条件筛选
- 📋 **交易模板** - 常用交易保存为模板，快速复用
- 🎨 **个性化设置** - 主题切换、界面布局自定义
- 🔐 **数据安全** - 本地部署，用户认证保护，数据完全掌控
- 📱 **PWA支持** - 支持安装为桌面/移动应用，离线使用

</td>
</tr>
</table>

## 技术栈

### 前端
- **框架**: Vue 3.3.8 + TypeScript 5.2.2
- **构建工具**: Vite 5.0.0
- **移动端UI**: Vant 4.8.0 + @vant/icons 1.2.2
- **路由**: Vue Router 4.2.5
- **状态管理**: Pinia 2.1.7
- **图表**: ECharts 5.4.3 + Vue-ECharts 6.6.1
- **HTTP客户端**: Axios 1.6.2
- **日期处理**: Day.js 1.11.10
- **PWA支持**: Vite-plugin-pwa 1.0.2
- **构建优化**: 自动导入、组件自动注册、代码分割

### 后端
- **框架**: Python 3.8+ + FastAPI 0.104.1
- **记账引擎**: Beancount 3.0.0
- **异步服务器**: Uvicorn 0.24.0
- **数据处理**: Pandas 2.1.4
- **任务调度**: APScheduler 3.10.4
- **文件处理**: aiofiles 23.2.0 + portalocker 2.8.2
- **数据验证**: Pydantic 2.x + pydantic-settings 2.1.0
- **认证系统**: python-jose 3.3.0 + passlib 1.7.4
- **JSON处理**: orjson 3.9.10（高性能JSON序列化）
- **数据库**: SQLAlchemy 2.0.23 + Alembic 1.13.0

## 🚀 快速开始

> 💡 **提示**: 第一次启动需要安装依赖，大约需要3-5分钟。建议使用方式一的启动脚本，会自动处理所有依赖。

### 🎯 方式一：一键启动（推荐新手）

```bash
# Linux/macOS 用户
chmod +x start.sh
./start.sh

# Windows 用户
start.bat
```

🎉 启动成功后，浏览器会自动打开: **http://localhost:5173**
> 💡 系统会自动跳转到移动端界面 `/h5/dashboard`，在桌面浏览器中也能完美体验

---

### 🔧 方式二：手动启动（开发者）

<details>
<summary>👆 点击展开详细步骤</summary>

**1. 启动后端服务**
```bash
cd backend
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

**2. 启动前端服务**
```bash
cd frontend
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

✅ 访问地址: **http://localhost:5173**

</details>

---

### 🐳 方式三：Docker部署（生产环境推荐）

```bash
# 使用官方镜像直接启动
docker-compose up -d
```

**docker-compose.yml 示例:**
```yaml
version: '3.8'
services:
  beancount-web:
    image: pionnerwang/beancount-web:latest
    ports:
      - "8000:8000"
    volumes:
      - beancount-data:/app/data
    environment:
      - USERNAME=admin
      - PASSWORD=admin123
    restart: unless-stopped

volumes:
  beancount-data:
```

🌐 访问地址: **http://localhost:8000**

**默认登录信息:**
- 用户名: `admin`
- 密码: `admin123`

> 💡 可通过环境变量 `USERNAME` 和 `PASSWORD` 自定义登录信息

---

### 📱 首次使用指南

1. **🔐 登录系统**: 使用默认用户名 `admin` 和密码 `admin123` 登录
2. **💰 开始记账**: 点击"添加交易"，输入你的第一笔记录
3. **📊 查看报表**: 在仪表板查看你的财务概览
4. **🔄 设置周期交易**: 为房租、工资等定期项目设置自动记账

> 🆕 **新用户?** 系统会自动创建示例账本文件，包含基础账户结构和示例交易，你可以直接开始体验！

## 移动端特性

### 界面设计
- 基于Vant UI组件库，原生移动体验
- 底部Tab导航 + 顶部操作栏
- 深色/浅色主题自动切换
- 简洁直观的操作界面

### 交互体验
- 触摸手势优化（滑动、长按、拖拽）
- 快速操作面板，常用功能一触即达
- 智能表单输入，防止缩放和焦点问题
- 流畅的页面切换动画

### PWA支持
- 可安装为手机原生应用
- 支持离线缓存和数据同步
- 推送通知和后台更新
- 原生应用级别的启动速度

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
   npm install
   npm run build
   
   # 复制构建产物到后端static目录
   cp -r dist/* ../backend/static/
   
   # 启动后端生产服务
   cd ../backend
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

### 数据持久化
- 账本数据存储在 `data/` 目录
- 支持多种格式的Beancount文件
- 建议定期备份数据目录

---




## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个星星! ⭐**


</div>
