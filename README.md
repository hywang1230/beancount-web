# Beancount Web 记账系统

一个基于 Beancount 3 的现代化复式记账系统，提供直观的 Web 界面进行记账、流水查看和报表分析。

**单用户系统** - 专为个人记账设计，无需用户认证，开箱即用。

## 项目结构

```
beancount-web/
├── frontend/           # Vue3 前端应用
├── backend/           # Python FastAPI 后端
├── data/             # Beancount 账本文件存储
└── docs/             # 项目文档
```

## 功能特性

- 📊 **报表统计** - 收支分析、资产负债表、损益表等
- 💰 **流水管理** - 交易记录查看、筛选、导出
- ✏️ **记账功能** - 可视化记账界面，支持复式记账
- 📁 **文件管理** - Beancount 文件管理和同步
  - 支持 `.beancount` 和 `.bean` 两种文件格式
  - 文件上传、编辑、验证功能
  - 自动备份机制
- 🔍 **搜索过滤** - 强大的交易搜索和过滤功能
- 👤 **单用户模式** - 专为个人使用优化，简洁高效

## 技术栈

### 前端
- Vue 3.x
- Element Plus UI
- TypeScript
- Vite

### 后端
- Python 3.8+
- FastAPI
- Beancount 3.x
- SQLAlchemy (可选，用于缓存)

## 快速开始

### 1.启动
``` shell
./start.sh
```
### 2.访问
http://localhost:5173

## 许可证

MIT License
