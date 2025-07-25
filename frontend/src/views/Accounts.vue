<template>
  <div class="page-container">
    <h1 class="page-title">账户管理</h1>
    
    <!-- 账户统计 -->
    <el-row :gutter="20" class="mb-4">
      <el-col v-for="(group, type) in accountGroups" :key="type" :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-value">{{ group.length }}</div>
              <div class="stat-label">{{ getTypeLabel(type) }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 账户列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>账户列表</span>
          <el-input
            v-model="searchText"
            placeholder="搜索账户"
            style="width: 200px"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>
      
      <el-tabs v-model="activeType" @tab-change="onTypeChange">
        <el-tab-pane 
          v-for="(accounts, type) in filteredAccountGroups"
          :key="type"
          :label="getTypeLabel(type)"
          :name="type"
        >
          <el-tree
            :data="getAccountTree(accounts)"
            :props="treeProps"
            default-expand-all
            class="account-tree"
          >
            <template #default="{ data }">
              <div class="tree-node">
                <span class="node-label">{{ data.label }}</span>
                <span v-if="data.isLeaf" class="node-path">{{ data.fullPath }}</span>
              </div>
            </template>
          </el-tree>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getAccountsByType } from '@/api/accounts'

const loading = ref(false)
const searchText = ref('')
const activeType = ref('Assets')
const accountGroups = ref<Record<string, string[]>>({})
const isMobile = ref(false)

const treeProps = {
  children: 'children',
  label: 'label'
}

// 类型标签映射
const typeLabels: Record<string, string> = {
  Assets: '资产账户',
  Liabilities: '负债账户',
  Equity: '权益账户',
  Income: '收入账户',
  Expenses: '支出账户'
}

// 获取类型标签
const getTypeLabel = (type: string) => {
  return typeLabels[type] || type
}

// 过滤后的账户分组
const filteredAccountGroups = computed(() => {
  if (!searchText.value) {
    return accountGroups.value
  }
  
  const filtered: Record<string, string[]> = {}
  
  Object.keys(accountGroups.value).forEach(type => {
    const accounts = accountGroups.value[type].filter(account =>
      account.toLowerCase().includes(searchText.value.toLowerCase())
    )
    if (accounts.length > 0) {
      filtered[type] = accounts
    }
  })
  
  return filtered
})

// 构建账户树
const getAccountTree = (accounts: string[]) => {
  const tree: any = {}
  
  accounts.forEach(account => {
    const parts = account.split(':')
    let current = tree
    
    parts.forEach((part, index) => {
      if (!current[part]) {
        current[part] = {
          label: part,
          fullPath: parts.slice(0, index + 1).join(':'),
          isLeaf: index === parts.length - 1,
          children: {}
        }
      }
      current = current[part].children
    })
  })
  
  // 转换为数组格式
  const convertToArray = (obj: any): any[] => {
    return Object.values(obj).map((node: any) => ({
      ...node,
      children: Object.keys(node.children).length > 0 
        ? convertToArray(node.children) 
        : undefined
    }))
  }
  
  return convertToArray(tree)
}

// 类型切换
const onTypeChange = (type: string) => {
  activeType.value = type
}

// 加载账户数据
const loadAccounts = async () => {
  loading.value = true
  
  try {
    const response = await getAccountsByType()
    // 后端直接返回分组对象，不是包装在data字段中
    const accountData = response.data || response || {}
    accountGroups.value = typeof accountData === 'object' && accountData !== null ? accountData : {}
    
    // 设置默认激活的类型
    const types = Object.keys(accountGroups.value)
    if (types.length > 0) {
      activeType.value = types[0]
    }
    
  } catch (error) {
    console.error('加载账户失败:', error)
    accountGroups.value = {}
  } finally {
    loading.value = false
  }
}

// 检测屏幕尺寸
const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  loadAccounts()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 16px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.account-tree {
  margin-top: 16px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.node-label {
  font-weight: 500;
}

.node-path {
  font-size: 12px;
  color: #909399;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .el-row {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .el-col {
    padding-left: 6px !important;
    padding-right: 6px !important;
    margin-bottom: 12px;
  }
  
  .stat-card .stat-content {
    padding: 12px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .card-header .el-input {
    width: 100% !important;
  }
  
  .el-tabs__item {
    font-size: 12px;
    padding: 0 8px;
  }
  
  .account-tree {
    margin-top: 8px;
  }
  
  .tree-node {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .node-label {
    font-size: 14px;
  }
  
  .node-path {
    font-size: 11px;
    word-break: break-all;
  }
}
</style> 