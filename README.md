# Beancount Web 记账系统

基于 Beancount 的现代化复式记账系统，专为移动端优化。

## 特性

- 💰 **专业记账** - 基于 Beancount 3 引擎，支持复式记账标准
- 📱 **移动优化** - Vue 3 + Vant UI，支持 PWA 安装
- 🔄 **自动同步** - GitHub 云端备份，周期交易自动执行
- 📊 **报表分析** - 实时仪表板，多维度财务报表
- 📁 **多文件管理** - 支持按年份自动分文件，include 引用管理

## 快速开始

### Docker 部署（推荐）
```bash
docker-compose up -d
```
访问：http://localhost:8000

### 本地开发
```bash
# 一键启动脚本
chmod +x start.sh && ./start.sh
```
访问：http://localhost:5173

### 默认登录
- 用户名：`admin`
- 密码：`admin123`

## 技术栈

- **前端**: Vue 3 + TypeScript + Vant UI
- **后端**: Python 3.8+ + FastAPI + Beancount 3  
- **数据库**: SQLite
- **部署**: Docker

## 许可证

MIT License