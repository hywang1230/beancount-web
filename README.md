# Beancount Web 记账系统

一个基于 Beancount 3 的现代化复式记账系统，提供直观的 Web 界面进行记账、流水查看和报表分析。

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
- 🔍 **搜索过滤** - 强大的交易搜索和过滤功能

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

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
cd backend
python main.py
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 5. 访问应用

打开浏览器访问 `http://localhost:5173`

## 开发说明

- 账本文件统一存放在 `data/` 目录下
- 后端API运行在 `http://localhost:8000`
- 前端开发服务器运行在 `http://localhost:5173`

## 许可证

MIT License

## Recent Updates

### 账户列表修复和优化
- 修复了 `get_all_accounts()` 方法，现在正确返回所有类型的账户
- 使用 Beancount 的 `getters.get_accounts()` 方法获取完整账户列表
- 包含：Assets（资产）、Liabilities（负债）、Expenses（支出）、Income（收入）、Equity（所有者权益）
- 移除了前端20个账户的显示限制，现在显示所有70+个账户
- 优化了账户搜索算法，支持智能匹配和按相关度排序
- 改进了下拉列表UI，显示账户类型标签，提升用户体验
- 提高了后端搜索建议的返回数量限制（10→50个）

### 分录金额输入功能增强

AddTransaction.vue 中的分录现在支持以下新功能：

#### 1. 公式计算支持
- 金额字段支持数学公式输入，如：`1+2+3`、`100*0.15`、`(200+300)*0.1`
- 实时显示计算结果
- 按 Enter 键可以将公式结果替换为计算值
- 公式输入时字段会显示蓝色边框以示区别

#### 2. 灵活的金额填写规则
- 金额字段变为非必填
- 最多只能有一个分录不填金额（空金额将自动平衡）
- 至少需要两个包含账户的分录
- 当所有分录都有金额时，系统会验证借贷平衡

#### 3. 视觉指示
- 空金额分录：浅蓝色背景
- 公式输入：蓝色边框和占位符
- 负数金额：红色显示
- 无效输入：红色边框和背景
- 公式计算结果显示在输入框右侧

#### 4. 用户体验优化
- 添加了功能提示说明
- 智能验证和错误提示
- 平滑的视觉过渡效果

## Setup

1. Install dependencies for backend and frontend
2. Run the development servers
3. Access the web interface

## Usage

The application provides a modern web interface for Beancount file management and transaction entry with enhanced formula calculation capabilities. 