<div align="center">

# 💰 Beancount Web 记账系统

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-009688.svg)](https://fastapi.tiangolo.com/)

一个基于 **Beancount 3** 的现代化复式记账系统，提供直观的 Web 界面进行记账、流水查看和报表分析。

🎯 **单用户系统** - 专为个人记账设计，支持用户认证，安全可靠

📱 **跨端体验** - PC端和移动端分离式设计，自动适配不同设备

🚀 **快速部署** - 支持Docker一键部署，5分钟即可启动

</div>

---

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

### 📱 跨端体验
- 💻 **PC端优雅界面** - Element Plus设计，专业财务软件体验
- 📱 **移动端专用设计** - Vant UI组件，原生移动体验
- 🔄 **智能设备识别** - 自动适配PC/移动端，无缝切换
- ✋ **触摸手势优化** - 移动端滑动、长按等交互优化

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
- **PC端UI**: Element Plus 2.4.4 + @element-plus/icons 2.1.0
- **移动端UI**: Vant 4.8.0 + @vant/icons 1.2.2
- **路由**: Vue Router 4.2.5
- **状态管理**: Pinia 2.1.7
- **图表**: ECharts 5.4.3 + Vue-ECharts 6.6.1
- **HTTP客户端**: Axios 1.6.2
- **日期处理**: Day.js 1.11.10
- **PWA支持**: Vite-plugin-pwa 1.0.2

### 后端
- **框架**: Python 3.11+ + FastAPI 0.104.1
- **记账引擎**: Beancount 3.0.0
- **异步支持**: Uvicorn 0.24.0 + asyncio
- **数据处理**: Pandas 2.1.4
- **任务调度**: APScheduler 3.10.4
- **文件处理**: aiofiles 23.2.0
- **数据验证**: Pydantic 2.x
- **配置管理**: pydantic-settings 2.1.0
- **认证系统**: python-jose 3.3.0 + passlib 1.7.4

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

### 🐳 方式三：Docker部署（生产环境）

```bash
# 克隆项目
git clone <your-repo-url>
cd beancount-web

# 使用docker-compose启动
docker-compose up -d
```

🌐 访问地址: **http://localhost:8000**

**默认登录信息:**
- 用户名: `admin`
- 密码: `admin123`

> 💡 可通过环境变量 `USERNAME` 和 `PASSWORD` 自定义登录信息

---

### 📱 首次使用指南

1. **🔐 登录系统**: 使用默认用户名 `admin` 和密码 `admin123` 登录
2. **📁 管理账本文件**: 进入"文件管理"页面，上传你的 `.beancount` 文件或使用系统自动创建的示例文件
3. **💰 开始记账**: 点击"添加交易"，输入你的第一笔记录
4. **📊 查看报表**: 在仪表板查看你的财务概览
5. **🔄 设置周期交易**: 为房租、工资等定期项目设置自动记账

> 🆕 **新用户?** 系统会自动创建示例账本文件，包含基础账户结构和示例交易，你可以直接开始体验！

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

---

## ❓ 常见问题

<details>
<summary><strong>Q: 启动时报错 "端口被占用"</strong></summary>

**A:** 检查是否有其他服务占用了端口
```bash
# 检查端口占用情况
lsof -i :5173  # 前端端口
lsof -i :8000  # 后端端口

# 杀死占用进程
kill -9 <PID>
```
</details>

<details>
<summary><strong>Q: 前端页面显示空白</strong></summary>

**A:** 通常是后端服务未启动或认证失败
1. 确认后端服务正常运行 (http://localhost:8000/docs)
2. 检查是否已正确登录系统
3. 检查浏览器控制台是否有错误信息
4. 尝试清除浏览器缓存后重新访问
</details>

<details>
<summary><strong>Q: Beancount文件语法错误</strong></summary>

**A:** 使用内置的语法检查功能
1. 在"文件管理"页面上传文件
2. 系统会自动进行语法验证
3. 根据错误提示修改文件内容
4. 也可以使用官方 `bean-check` 命令验证
</details>

<details>
<summary><strong>Q: 如何导入已有的财务数据</strong></summary>

**A:** 支持多种导入方式
1. **标准Beancount文件**: 直接上传 `.beancount` 文件
2. **CSV格式**: 使用导入功能，支持自定义字段映射
3. **其他记账软件**: 先导出为CSV，再导入本系统
</details>

<details>
<summary><strong>Q: 移动端和PC端数据不同步</strong></summary>

**A:** 移动端和PC端使用同一个后端数据源
1. 确认访问的是同一个服务器地址
2. 尝试刷新页面或清除缓存
3. 检查网络连接是否正常
</details>

<details>
<summary><strong>Q: 如何备份我的账本数据</strong></summary>

**A:** 多种备份方式保证数据安全
1. **文件备份**: 定期下载 `data/` 目录下的所有文件
2. **自动备份**: 系统会在每次修改时自动创建备份
3. **导出备份**: 使用导出功能生成CSV等格式的备份
4. **Docker数据卷**: 如使用Docker部署，确保挂载数据卷到宿主机
</details>

<details>
<summary><strong>Q: 如何修改登录密码</strong></summary>

**A:** 可通过环境变量修改默认登录信息
1. **Docker环境**: 在docker-compose.yml中设置 `USERNAME` 和 `PASSWORD` 环境变量
2. **本地部署**: 在 `.env` 文件中设置相应变量
3. **重启服务**: 修改后需要重启服务使配置生效
</details>

---

## 🛠️ 故障排除

### 安装问题
- **Python版本**: 确保使用Python 3.8+
- **Node.js版本**: 确保使用Node.js 16+
- **网络问题**: 如遇到下载慢，可考虑使用国内镜像源

### 运行问题
- **内存不足**: 关闭其他占用内存的应用
- **磁盘空间**: 确保有足够的磁盘空间存储账本文件
- **权限问题**: 确保对项目目录有读写权限

### 数据问题
- **编码问题**: 确保Beancount文件使用UTF-8编码
- **路径问题**: 避免使用包含特殊字符的文件路径
- **文件大小**: 过大的账本文件可能导致加载缓慢

> 💡 **获得帮助**: 如果遇到其他问题，欢迎提交 [Issue](https://github.com/your-repo/issues) 或查看项目文档。

---

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 💻 代码贡献
1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 🐛 问题反馈
- 使用 [Issue模板](https://github.com/your-repo/issues/new) 提交Bug报告
- 详细描述问题现象和复现步骤
- 提供系统环境信息

### 📖 文档改进
- 改进现有文档
- 添加使用示例
- 翻译文档到其他语言

### 💡 功能建议
- 在Issues中提出新功能建议
- 参与功能讨论
- 帮助设计用户界面

---


## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个星星! ⭐**

Made with ❤️ by Beancount Web Team

</div>
