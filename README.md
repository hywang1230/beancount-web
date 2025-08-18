<div align="center">

# 💰 Beancount Web 记账系统

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)

一个基于 **Beancount 3** 的现代化复式记账系统，专为移动端优化，提供直观的触屏界面进行记账、流水查看和报表分析。

🎯 **专业记账引擎** - 基于Beancount标准的复式记账，数据格式开放可移植

📱 **移动端优化** - 基于Vant UI的原生移动体验，支持PWA安装

🔄 **智能自动化** - 周期记账自动执行，GitHub云端同步无忧备份

</div>

## ✨ 核心能力

### 💰 专业复式记账
- 基于 **Beancount 3** 引擎，遵循国际复式记账标准
- 支持资产、负债、收入、支出、权益五大账户类型
- 完整的多币种和汇率管理
- 数据格式开放，支持导入导出，避免厂商锁定

### 📱 移动端原生体验
- **Vue 3 + Vant UI** 构建，专为触屏优化
- **PWA支持** - 可安装为手机原生应用
- 触摸手势优化，流畅的操作体验
- 响应式设计，完美适配各种移动设备

### 🔄 智能自动化
- **周期记账** - 工资、房租等定期交易自动执行
- **GitHub同步** - 数据自动备份到GitHub，支持多设备同步
- **实时文件监控** - 本地文件变化自动触发云端同步
- **冲突解决** - 智能处理多设备编辑冲突

### 📊 可视化报表
- **实时仪表板** - 关键财务指标一目了然
- **趋势分析** - 收支趋势、资产变化图表展示
- **财务报表** - 资产负债表、损益表等专业报表
- **多维分析** - 按时间、账户、分类等维度统计

### 🔐 安全可靠
- **本地部署** - 数据完全掌控，隐私安全
- **用户认证** - 登录保护，支持自定义密码
- **加密存储** - GitHub token等敏感信息加密保存
- **数据备份** - 自动备份，防止数据丢失

## 🚀 快速开始

### 方式一：一键启动（推荐）

```bash
# Linux/macOS 用户
chmod +x start.sh && ./start.sh

# Windows 用户
start.bat
```

启动成功后自动打开：**http://localhost:5173**

### 方式二：Docker部署

```bash
docker-compose up -d
```

访问地址：**http://localhost:8000**

**默认登录信息：**
- 用户名：`admin`
- 密码：`admin123`

## 🔧 技术栈

- **前端**: Vue 3 + TypeScript + Vant UI + ECharts
- **后端**: Python 3.8+ + FastAPI + Beancount 3
- **部署**: Docker + Docker Compose

## 📱 移动端特性

- 基于Vant UI的原生移动体验
- PWA支持，可安装为手机应用
- 触摸优化，支持滑动、长按等手势
- 离线缓存，网络不稳定时也能使用

## 🔄 GitHub同步配置

1. **创建GitHub仓库** - 用于存储账本数据
2. **生成访问令牌** - 在GitHub设置中创建Personal Access Token
3. **配置同步** - 在系统设置中填入仓库信息和令牌
4. **自动同步** - 本地文件变化将自动同步到GitHub

## 📁 数据格式

所有账本数据存储为标准的Beancount格式文件（`.beancount` 或 `.bean`），完全兼容Beancount生态系统的其他工具。

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个星星! ⭐**

</div>