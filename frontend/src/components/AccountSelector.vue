<template>
  <el-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    filterable
    remote
    :placeholder="placeholder"
    :remote-method="searchAccounts"
    :loading="accountLoading"
    @change="handleChange"
    @focus="onAccountFocus"
    style="width: 100%"
    popper-class="account-select-dropdown"
    :no-data-text="accountSuggestions.length === 0 ? '未找到匹配账户' : ''"
    reserve-keyword
    :disabled="disabled"
    :size="size"
    :clearable="clearable"
  >
    <el-option
      v-for="account in accountSuggestions"
      :key="account"
      :label="account"
      :value="account"
    >
      <span style="float: left">{{ account }}</span>
      <span style="float: right; color: #8492a6; font-size: 13px">
        {{ getAccountType(account) }}
      </span>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getAllAccounts } from '@/api/accounts'

interface Props {
  modelValue: string
  placeholder?: string
  disabled?: boolean
  size?: 'large' | 'default' | 'small'
  clearable?: boolean
  filterTypes?: string[] // 可选：限制显示的账户类型
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '选择账户',
  disabled: false,
  size: 'default',
  clearable: false,
  filterTypes: () => []
})

const emit = defineEmits<Emits>()

// 响应式数据
const accountLoading = ref(false)
const accountSuggestions = ref<string[]>([])
const allAccounts = ref<string[]>([])

// 初始化时加载所有账户
onMounted(async () => {
  await loadAllAccounts()
})

// 监听filterTypes变化，重新过滤账户
watch(() => props.filterTypes, () => {
  if (allAccounts.value.length > 0) {
    updateAccountSuggestions('')
  }
}, { immediate: true })

// 加载所有账户
const loadAllAccounts = async () => {
  try {
    accountLoading.value = true
    const response = await getAllAccounts()
    
    // getAllAccounts 直接返回字符串数组，不是包装在data中
    const accounts = response.data || response || []
    
    allAccounts.value = Array.isArray(accounts) ? accounts : []
    updateAccountSuggestions('') // 更新建议列表
    
    console.log('加载账户成功，总数:', allAccounts.value.length)
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
    // 设置默认值避免后续错误
    allAccounts.value = []
    accountSuggestions.value = []
  } finally {
    accountLoading.value = false
  }
}

// 更新账户建议列表
const updateAccountSuggestions = (query: string) => {
  let filtered = allAccounts.value

  // 如果指定了账户类型过滤
  if (props.filterTypes && props.filterTypes.length > 0) {
    filtered = filtered.filter(account => {
      return props.filterTypes.some(type => account.startsWith(type + ':'))
    })
  }

  if (!query || query.length === 0) {
    // 如果查询为空，显示所有（已过滤的）账户
    accountSuggestions.value = filtered
    return
  }
  
  // 本地搜索，支持更智能的匹配
  const queryLower = query.toLowerCase()
  const searchFiltered = filtered.filter(account => {
    const accountLower = account.toLowerCase()
    
    // 支持多种匹配方式：
    // 1. 完整包含匹配
    if (accountLower.includes(queryLower)) return true
    
    // 2. 按:分割后的部分匹配
    const parts = account.split(':')
    for (const part of parts) {
      if (part.toLowerCase().includes(queryLower)) return true
    }
    
    return false
  })
  
  // 按匹配度排序：优先显示精确匹配和前缀匹配
  searchFiltered.sort((a, b) => {
    const aLower = a.toLowerCase()
    const bLower = b.toLowerCase()
    
    // 精确匹配优先
    if (aLower === queryLower && bLower !== queryLower) return -1
    if (bLower === queryLower && aLower !== queryLower) return 1
    
    // 前缀匹配优先
    if (aLower.startsWith(queryLower) && !bLower.startsWith(queryLower)) return -1
    if (bLower.startsWith(queryLower) && !aLower.startsWith(queryLower)) return 1
    
    // 最后按字母顺序
    return a.localeCompare(b)
  })
  
  accountSuggestions.value = searchFiltered
}

// 搜索账户
const searchAccounts = async (query: string) => {
  updateAccountSuggestions(query)
}

// 账户选择器获得焦点时显示所有账户
const onAccountFocus = () => {
  if (accountSuggestions.value.length === 0 && allAccounts.value.length > 0) {
    updateAccountSuggestions('')
  }
}

// 获取账户类型
const getAccountType = (account: string): string => {
  if (account.startsWith('Assets:')) return '资产'
  if (account.startsWith('Liabilities:')) return '负债'
  if (account.startsWith('Expenses:')) return '支出'
  if (account.startsWith('Income:')) return '收入'
  if (account.startsWith('Equity:')) return '权益'
  return '其他'
}

// 处理账户变化
const handleChange = (value: string) => {
  emit('change', value)
}

// 暴露方法供父组件调用
defineExpose({
  loadAccounts: loadAllAccounts,
  searchAccounts,
  allAccounts,
  accountSuggestions
})
</script>

<style scoped>
.account-select-dropdown {
  /* 可以在这里添加特定的样式 */
}
</style> 