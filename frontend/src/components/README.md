# 组件说明

## PayeeSelector

通用的收付方选择组件，支持从历史记录中选择收付方或自由输入新的收付方。

### 功能特点

- 支持下拉选择历史收付方
- 支持自由输入新的收付方
- 支持搜索过滤
- 可配置占位符文本
- 完整的双向数据绑定

### 使用方式

```vue
<template>
  <PayeeSelector 
    v-model="payee"
    placeholder="选择或输入收付方"
    @change="handlePayeeChange"
  />
</template>

<script setup>
import PayeeSelector from '@/components/PayeeSelector.vue'

const payee = ref('')

const handlePayeeChange = (value) => {
  console.log('收付方已选择:', value)
}
</script>
```

### Props

- `modelValue`: 当前值 (string, 可选)
- `placeholder`: 占位符文本 (string, 可选, 默认: "选择或输入收付方")

### Events

- `update:modelValue`: 值变化时触发
- `change`: 选择变化时触发

### 使用场景

- 新增交易页面的收付方选择
- 周期记账设置中的收付方选择
- 其他需要收付方输入的表单

## AccountSelector

账户选择组件，用于选择记账账户。

### 使用方式

```vue
<AccountSelector 
  v-model="account" 
  placeholder="选择账户"
/>
```

# 账户选择组件 (AccountSelector)

`AccountSelector` 是一个可复用的账户选择组件，提供智能的账户搜索和选择功能。

## 功能特性

- 🔍 智能搜索：支持账户名称的模糊匹配和分段匹配
- 📊 账户类型显示：自动显示账户类型（资产、负债、支出、收入、权益）
- 🎨 优雅的UI：基于Element Plus的Select组件
- 🎯 类型过滤：可选择性地只显示特定类型的账户
- ⚡ 高性能：本地搜索，无网络延迟

## 基本用法

```vue
<template>
  <AccountSelector
    v-model="selectedAccount"
    placeholder="选择账户"
    @change="handleAccountChange"
  />
</template>

<script setup>
import { ref } from 'vue'

const selectedAccount = ref('')

const handleAccountChange = (account) => {
  console.log('选中的账户:', account)
}
</script>
```

## 属性 (Props)

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `modelValue` | `string` | - | 当前选中的账户（支持v-model） |
| `placeholder` | `string` | `'选择账户'` | 输入框占位符 |
| `disabled` | `boolean` | `false` | 是否禁用 |
| `size` | `'large' \| 'default' \| 'small'` | `'default'` | 组件尺寸 |
| `clearable` | `boolean` | `false` | 是否可清空 |
| `filterTypes` | `string[]` | `[]` | 账户类型过滤（如: `['Assets', 'Expenses']`） |

## 事件 (Events)

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `update:modelValue` | `(value: string)` | 值变化时触发 |
| `change` | `(value: string)` | 选择变化时触发 |

## 高级用法

### 限制账户类型

只显示资产和支出账户：

```vue
<AccountSelector
  v-model="account"
  :filter-types="['Assets', 'Expenses']"
  placeholder="选择资产或支出账户"
/>
```

### 带清空功能

```vue
<AccountSelector
  v-model="account"
  clearable
  placeholder="选择账户（可清空）"
/>
```

### 小尺寸

```vue
<AccountSelector
  v-model="account"
  size="small"
/>
```

## 搜索功能

组件支持多种搜索方式：

1. **完整匹配**：输入完整的账户名称
2. **部分匹配**：输入账户名称的任意部分
3. **分段匹配**：输入账户层级中任意一段的名称

例如，对于账户 `Assets:Bank:ICBC:Checking`：
- 搜索 "ICBC" 可以找到
- 搜索 "Bank" 可以找到  
- 搜索 "Check" 可以找到

## 在分录表单中使用

```vue
<template>
  <div v-for="(posting, index) in postings" :key="index">
    <AccountSelector
      v-model="posting.account"
      placeholder="选择账户"
      @change="onAccountChange(index)"
    />
    <!-- 其他分录字段... -->
  </div>
</template>
```

## 注意事项

- 组件会在mounted时自动加载所有账户数据
- 搜索是本地进行的，性能较好
- 账户类型是根据账户名称前缀自动识别的
- 组件已全局注册，可以直接使用无需导入 