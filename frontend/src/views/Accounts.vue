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
          <div class="header-actions">
            <el-input
              v-model="searchText"
              placeholder="搜索账户"
              style="width: 200px; margin-right: 12px"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon>
              新增账户
            </el-button>
          </div>
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
                <div class="node-info">
                  <span class="node-label">{{ data.label }}</span>
                  <span v-if="data.isLeaf" class="node-path">{{ data.fullPath }}</span>
                </div>
                <div v-if="data.isLeaf" class="node-actions">
                  <el-button 
                    size="small" 
                    type="warning" 
                    text
                    @click="handleCloseAccount(data.fullPath)"
                  >
                    归档
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </el-tab-pane>
        
        <!-- 归档账户标签页 -->
        <el-tab-pane label="已归档账户" name="archived">
          <el-empty v-if="archivedAccounts.length === 0" description="暂无已归档账户" />
          <div v-else class="archived-accounts">
            <div 
              v-for="account in filteredArchivedAccounts"
              :key="account"
              class="archived-account-item"
            >
              <div class="account-info">
                <span class="account-name">{{ account }}</span>
              </div>
              <div class="account-actions">
                <el-button 
                  size="small" 
                  type="primary" 
                  text
                  @click="handleRestoreAccount(account)"
                >
                  恢复
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 新增账户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新增账户"
      width="500px"
      :before-close="handleCloseCreateDialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="账户类型" prop="accountType">
          <el-select v-model="createForm.accountType" placeholder="请选择账户类型" style="width: 100%">
            <el-option
              v-for="type in accountTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="账户名称" prop="accountName">
          <el-input
            v-model="createForm.accountName"
            placeholder="请输入账户名称"
            :prefix-icon="createForm.accountType ? '' : ''"
          >
            <template #prepend>{{ createForm.accountType }}:</template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="开启日期" prop="date">
          <el-date-picker
            v-model="createForm.date"
            type="date"
            placeholder="选择开启日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="约束货币">
          <el-select
            v-model="createForm.currencies"
            multiple
            placeholder="选择约束货币（可选）"
            style="width: 100%"
            clearable
          >
            <el-option label="USD" value="USD" />
            <el-option label="CNY" value="CNY" />
            <el-option label="EUR" value="EUR" />
            <el-option label="JPY" value="JPY" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="记账方法">
          <el-select
            v-model="createForm.bookingMethod"
            placeholder="选择记账方法（可选）"
            style="width: 100%"
            clearable
          >
            <el-option label="STRICT" value="STRICT" />
            <el-option label="FIFO" value="FIFO" />
            <el-option label="LIFO" value="LIFO" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleCloseCreateDialog">取消</el-button>
          <el-button type="primary" @click="handleCreateAccount" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 归档账户对话框 -->
    <el-dialog
      v-model="showCloseDialog"
      title="归档账户"
      width="400px"
    >
      <div class="close-account-content">
        <el-icon class="warning-icon"><WarningFilled /></el-icon>
        <div class="warning-text">
          <p>确定要归档账户 <strong>{{ closeAccountName }}</strong> 吗？</p>
          <p class="warning-note">归档后该账户将在指定日期后不可用。</p>
        </div>
      </div>
      
      <el-form :model="closeForm" label-width="80px" class="mt-4">
        <el-form-item label="归档日期" required>
          <el-date-picker
            v-model="closeForm.date"
            type="date"
            placeholder="选择归档日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCloseDialog = false">取消</el-button>
          <el-button type="danger" @click="confirmCloseAccount" :loading="closeLoading">
            确认归档
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 恢复账户对话框 -->
    <el-dialog
      v-model="showRestoreDialog"
      title="恢复账户"
      width="400px"
    >
      <div class="restore-account-content">
        <el-icon class="success-icon"><SuccessFilled /></el-icon>
        <div class="restore-text">
          <p>确定要恢复账户 <strong>{{ restoreAccountName }}</strong> 吗？</p>
          <p class="restore-note">恢复后该账户将重新可用。</p>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRestoreDialog = false">取消</el-button>
          <el-button type="primary" @click="confirmRestoreAccount" :loading="restoreLoading">
            确认恢复
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Search, Plus, WarningFilled, SuccessFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getAccountsByType, createAccount, closeAccount, getArchivedAccounts, restoreAccount } from '@/api/accounts'
import type { AccountCreateRequest, AccountCloseRequest, AccountRestoreRequest } from '@/api/accounts'

const loading = ref(false)
const searchText = ref('')
const activeType = ref('Assets')
const accountGroups = ref<Record<string, string[]>>({})
const archivedAccounts = ref<string[]>([])
const isMobile = ref(false)

// 新增账户相关
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = ref({
  accountType: '',
  accountName: '',
  date: '',
  currencies: [] as string[],
  bookingMethod: ''
})

// 归档账户相关
const showCloseDialog = ref(false)
const closeLoading = ref(false)
const closeAccountName = ref('')
const closeForm = ref({
  date: ''
})

// 恢复账户相关
const showRestoreDialog = ref(false)
const restoreLoading = ref(false)
const restoreAccountName = ref('')

const treeProps = {
  children: 'children',
  label: 'label'
}

// 账户类型选项
const accountTypes = [
  { label: '资产账户', value: 'Assets' },
  { label: '负债账户', value: 'Liabilities' },
  { label: '权益账户', value: 'Equity' },
  { label: '收入账户', value: 'Income' },
  { label: '支出账户', value: 'Expenses' }
]

// 表单验证规则
const createRules: FormRules = {
  accountType: [
    { required: true, message: '请选择账户类型', trigger: 'change' }
  ],
  accountName: [
    { required: true, message: '请输入账户名称', trigger: 'blur' },
    { 
      pattern: /^[A-Z0-9][\w\u4e00-\u9fa5-:]*$/,
      message: '账户名称必须以大写字母或数字开头，后续可以包含字母、数字、汉字、下划线和连字符',
      trigger: 'blur'
    }
  ],
  date: [
    { required: true, message: '请选择开启日期', trigger: 'change' }
  ]
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

// 过滤后的归档账户
const filteredArchivedAccounts = computed(() => {
  if (!searchText.value) {
    return archivedAccounts.value
  }
  
  return archivedAccounts.value.filter(account =>
    account.toLowerCase().includes(searchText.value.toLowerCase())
  )
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

// 处理关闭创建对话框
const handleCloseCreateDialog = () => {
  createForm.value = {
    accountType: '',
    accountName: '',
    date: '',
    currencies: [],
    bookingMethod: ''
  }
  createFormRef.value?.clearValidate()
  showCreateDialog.value = false
}

// 处理创建账户
const handleCreateAccount = async () => {
  if (!createFormRef.value) return
  
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return
    
    createLoading.value = true
    
    const fullAccountName = `${createForm.value.accountType}:${createForm.value.accountName}`
    
    const requestData: AccountCreateRequest = {
      name: fullAccountName,
      open_date: createForm.value.date,
      currencies: createForm.value.currencies.length > 0 ? createForm.value.currencies : undefined,
      booking_method: createForm.value.bookingMethod || undefined
    }
    
    const response = await createAccount(requestData)
    
    if (response.success) {
      ElMessage.success('账户创建成功')
      handleCloseCreateDialog()
      await loadAccounts() // 重新加载账户列表
    } else {
      ElMessage.error(response.message || '账户创建失败')
    }
  } catch (error: any) {
    console.error('创建账户失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建账户失败')
  } finally {
    createLoading.value = false
  }
}

// 处理归档账户
const handleCloseAccount = (accountName: string) => {
  closeAccountName.value = accountName
  closeForm.value.date = new Date().toISOString().split('T')[0] // 默认今天
  showCloseDialog.value = true
}

// 确认归档账户
const confirmCloseAccount = async () => {
  if (!closeForm.value.date) {
    ElMessage.warning('请选择归档日期')
    return
  }
  
  try {
    closeLoading.value = true
    
    const requestData: AccountCloseRequest = {
      name: closeAccountName.value,
      close_date: closeForm.value.date
    }
    
    const response = await closeAccount(requestData)
    
    if (response.success) {
      ElMessage.success('账户归档成功')
      showCloseDialog.value = false
      await loadAccounts() // 重新加载账户列表
    } else {
      ElMessage.error(response.message || '账户归档失败')
    }
  } catch (error: any) {
    console.error('归档账户失败:', error)
    ElMessage.error(error.response?.data?.detail || '归档账户失败')
  } finally {
    closeLoading.value = false
  }
}

// 处理恢复账户
const handleRestoreAccount = (accountName: string) => {
  restoreAccountName.value = accountName
  showRestoreDialog.value = true
}

// 确认恢复账户
const confirmRestoreAccount = async () => {
  try {
    restoreLoading.value = true
    
    const requestData: AccountRestoreRequest = {
      name: restoreAccountName.value
    }
    
    const response = await restoreAccount(requestData)
    
    if (response.success) {
      ElMessage.success('账户恢复成功')
      showRestoreDialog.value = false
      await loadAccounts() // 重新加载账户列表
    } else {
      ElMessage.error(response.message || '账户恢复失败')
    }
  } catch (error: any) {
    console.error('恢复账户失败:', error)
    ElMessage.error(error.response?.data?.detail || '恢复账户失败')
  } finally {
    restoreLoading.value = false
  }
}

// 加载账户数据
const loadAccounts = async () => {
  loading.value = true
  
  try {
    // 同时加载活跃账户和归档账户
    const [accountsResponse, archivedResponse] = await Promise.all([
      getAccountsByType(),
      getArchivedAccounts()
    ])
    
    // 处理活跃账户数据
    const accountData = accountsResponse.data || accountsResponse || {}
    accountGroups.value = typeof accountData === 'object' && accountData !== null ? accountData : {}
    
    // 处理归档账户数据
    const archivedData = archivedResponse.data || archivedResponse || []
    archivedAccounts.value = Array.isArray(archivedData) ? archivedData : []
    
    // 设置默认激活的类型
    const types = Object.keys(accountGroups.value)
    if (types.length > 0 && activeType.value !== 'archived') {
      activeType.value = types[0]
    }
    
  } catch (error) {
    console.error('加载账户失败:', error)
    accountGroups.value = {}
    archivedAccounts.value = []
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
.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.mb-4 {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-content {
  padding: 20px 16px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.account-tree {
  margin-top: 16px;
  min-height: 200px;
}

.tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 8px 4px 0;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.tree-node:hover {
  background-color: #f5f7fa;
}

.node-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.node-label {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  line-height: 1.4;
}

.node-path {
  font-size: 12px;
  color: #909399;
  display: block;
  margin-top: 2px;
  line-height: 1.2;
  word-break: break-all;
}

.node-actions {
  flex-shrink: 0;
  margin-left: 12px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.close-account-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
}

.warning-icon {
  color: #e6a23c;
  font-size: 20px;
  margin-top: 2px;
  flex-shrink: 0;
}

.warning-text {
  flex: 1;
}

.warning-text p {
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.warning-note {
  font-size: 12px;
  color: #909399;
  margin-bottom: 0;
}

.restore-account-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
}

.success-icon {
  color: #67c23a;
  font-size: 20px;
  margin-top: 2px;
  flex-shrink: 0;
}

.restore-text {
  flex: 1;
}

.restore-text p {
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.restore-note {
  font-size: 12px;
  color: #909399;
  margin-bottom: 0;
}

.archived-accounts {
  min-height: 200px;
}

.archived-account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #fafafa;
  transition: all 0.2s;
}

.archived-account-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.account-info {
  flex: 1;
  min-width: 0;
}

.account-name {
  font-weight: 500;
  color: #606266;
  font-size: 14px;
  display: block;
  word-break: break-all;
}

.account-actions {
  flex-shrink: 0;
  margin-left: 12px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* Element Plus 组件样式覆盖 */
:deep(.el-card) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-card__header) {
  padding: 18px 20px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-tabs__nav-wrap) {
  margin-bottom: 16px;
}

:deep(.el-tree-node__content) {
  height: auto !important;
  padding: 8px 0;
}

:deep(.el-tree-node__expand-icon) {
  padding: 6px;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .page-container {
    padding: 12px;
  }
  
  .page-title {
    font-size: 20px;
    margin-bottom: 16px;
  }
  
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
    padding: 16px 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .header-actions .el-input {
    width: 100% !important;
    margin-right: 0 !important;
  }
  
  .el-tabs__item {
    font-size: 12px;
    padding: 0 8px;
  }
  
  .account-tree {
    margin-top: 12px;
  }
  
  .tree-node {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 4px;
  }
  
  .node-actions {
    margin-left: 0;
    align-self: flex-end;
    opacity: 1;
  }
  
  .node-label {
    font-size: 14px;
  }
  
  .node-path {
    font-size: 11px;
    word-break: break-all;
  }
  
  .close-account-content {
    flex-direction: column;
    gap: 8px;
  }
  
  .warning-icon {
    align-self: flex-start;
  }
  
  :deep(.el-card__header) {
    padding: 16px;
  }
  
  :deep(.el-card__body) {
    padding: 16px;
  }
  
  :deep(.el-dialog) {
    width: 95% !important;
    margin: 5vh auto !important;
  }
  
  .dialog-footer {
    flex-direction: column;
    gap: 8px;
  }
  
  .dialog-footer .el-button {
    width: 100%;
  }
}

/* 更小屏幕优化 */
@media (max-width: 480px) {
  .el-col {
    flex: 0 0 50% !important;
    max-width: 50% !important;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .node-label {
    font-size: 13px;
  }
  
  .node-path {
    font-size: 10px;
  }
}
</style>