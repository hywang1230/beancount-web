<template>
  <div class="recurring-transactions">
    <div class="header">
      <h1>周期记账管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建周期记账
        </el-button>
        <el-button @click="executeNow" :loading="executeLoading">
          <el-icon><VideoPlay /></el-icon>
          立即执行
        </el-button>
        <el-button @click="loadSchedulerJobs">
          <el-icon><Timer /></el-icon>
          查看定时任务
        </el-button>
      </div>
    </div>

    <!-- 列表过滤 -->
    <div class="filters">
      <el-switch
        v-model="showActiveOnly"
        @change="loadRecurringTransactions"
        active-text="仅显示启用的"
        inactive-text="显示全部"
      />
    </div>

    <!-- 周期记账列表 -->
    <el-table :data="recurringTransactions" v-loading="loading" class="transaction-table">
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column label="周期类型" width="120">
        <template #default="scope">
          <el-tag :type="getRecurrenceTypeTagType(scope.row.recurrence_type)">
            {{ getRecurrenceTypeText(scope.row.recurrence_type) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="周期详情" min-width="180">
        <template #default="scope">
          <span>{{ getRecurrenceDetail(scope.row) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始日期" width="120" />
      <el-table-column prop="end_date" label="结束日期" width="120">
        <template #default="scope">
          {{ scope.row.end_date || '无期限' }}
        </template>
      </el-table-column>
      <el-table-column prop="last_executed" label="最后执行" width="120">
        <template #default="scope">
          {{ scope.row.last_executed || '未执行' }}
        </template>
      </el-table-column>
      <el-table-column prop="next_execution" label="下次执行" width="120">
        <template #default="scope">
          {{ scope.row.next_execution || '未安排' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="scope">
          <el-switch
            v-model="scope.row.is_active"
            @change="toggleTransaction(scope.row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <div class="action-buttons">
            <el-button
              size="small"
              @click="editTransaction(scope.row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              @click="viewLogs(scope.row)"
            >
              日志
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteTransaction(scope.row)"
            >
              删除
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingTransaction ? '编辑周期记账' : '新建周期记账'"
      width="800px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入周期记账名称" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="可选的描述信息"
            :rows="2"
          />
        </el-form-item>
        
        <el-form-item label="周期类型" prop="recurrence_type">
          <el-select v-model="form.recurrence_type" @change="onRecurrenceTypeChange">
            <el-option label="每日" value="daily" />
            <el-option label="工作日" value="weekdays" />
            <el-option label="每周特定几天" value="weekly" />
            <el-option label="每月特定几日" value="monthly" />
          </el-select>
        </el-form-item>
        
        <!-- 每周特定几天 -->
        <el-form-item v-if="form.recurrence_type === 'weekly'" label="星期">
          <el-checkbox-group v-model="form.weekly_days">
            <el-checkbox :label="0">周一</el-checkbox>
            <el-checkbox :label="1">周二</el-checkbox>
            <el-checkbox :label="2">周三</el-checkbox>
            <el-checkbox :label="3">周四</el-checkbox>
            <el-checkbox :label="4">周五</el-checkbox>
            <el-checkbox :label="5">周六</el-checkbox>
            <el-checkbox :label="6">周日</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <!-- 每月特定几日 -->
        <el-form-item v-if="form.recurrence_type === 'monthly'" label="日期">
          <el-checkbox-group v-model="form.monthly_days" class="monthly-days">
            <el-checkbox v-for="day in 31" :key="day" :label="day">
              {{ day }}日
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择开始日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="结束日期">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="可选的结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item label="收付方">
          <PayeeSelector v-model="form.payee" placeholder="可选的收付方" />
        </el-form-item>
        
        <el-form-item label="摘要">
          <el-input v-model="form.narration" placeholder="请输入交易摘要" />
        </el-form-item>
        
                 <!-- 记账分录 -->
         <el-form-item label="记账分录" required>
           <div class="postings-section">
             <div v-for="(posting, index) in form.postings" :key="index" class="posting-item">
               <AccountSelector
                 v-model="posting.account"
                 placeholder="选择账户"
                 style="width: 200px; margin-right: 10px;"
                 @change="onAccountChange(index)"
               />
               <el-input-number
                 v-model.number="posting.amount"
                 placeholder="金额"
                 :precision="2"
                 :step="0.01"
                 style="width: 150px; margin-right: 10px;"
               />
               <el-select
                 v-model="posting.currency"
                 placeholder="货币"
                 style="width: 80px; margin-right: 10px;"
               >
                 <el-option label="CNY" value="CNY" />
                 <el-option label="USD" value="USD" />
                 <el-option label="EUR" value="EUR" />
                 <el-option label="JPY" value="JPY" />
               </el-select>
               <el-button
                 @click="removePosting(index)"
                 type="danger"
                 size="small"
                 :disabled="form.postings.length <= 2"
               >
                 删除
               </el-button>
             </div>
             <div class="postings-summary">
               <el-button @click="addPosting" type="primary" size="small">
                 添加分录
               </el-button>
                               <div class="balance-info">
                  <span class="balance-label">金额合计：</span>
                  <span :class="['balance-amount', validatePostings() ? 'balanced' : 'unbalanced']">
                    {{ (getPostingsSum() || 0).toFixed(2) }}
                  </span>
                  <el-tag v-if="validatePostings()" type="success" size="small">平衡</el-tag>
                  <el-tag v-else type="danger" size="small">不平衡</el-tag>
                </div>
             </div>
           </div>
         </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveTransaction" :loading="saveLoading">
          {{ editingTransaction ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行日志对话框 -->
    <el-dialog v-model="showLogsDialog" title="执行日志" width="800px">
      <el-table :data="executionLogs" v-loading="logsLoading">
        <el-table-column prop="execution_date" label="执行日期" width="120" />
        <el-table-column label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.success ? 'success' : 'danger'">
              {{ scope.row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" min-width="200">
          <template #default="scope">
            {{ scope.row.error_message || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="记录时间" width="160">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 定时任务状态对话框 -->
    <el-dialog v-model="showJobsDialog" title="定时任务状态" width="600px">
      <el-table :data="schedulerJobs" v-loading="jobsLoading">
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="trigger" label="触发规则" min-width="120" />
        <el-table-column prop="next_run" label="下次运行" width="160">
          <template #default="scope">
            {{ scope.row.next_run ? formatDateTime(scope.row.next_run) : '未安排' }}
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button @click="triggerScheduler" type="primary" :loading="triggerLoading">
          手动触发定时任务
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Timer } from '@element-plus/icons-vue'
import AccountSelector from '@/components/AccountSelector.vue'
import PayeeSelector from '@/components/PayeeSelector.vue'
import {
  recurringApi,
  type RecurringTransaction,
  type RecurringTransactionCreate,
  type ExecutionLog,
  type SchedulerJob
} from '@/api/recurring'

// 响应式数据
const loading = ref(false)
const showActiveOnly = ref(false)
const recurringTransactions = ref<RecurringTransaction[]>([])
const showCreateDialog = ref(false)
const editingTransaction = ref<RecurringTransaction | null>(null)
const saveLoading = ref(false)
const executeLoading = ref(false)

// 表单相关
const formRef = ref()
const form = reactive<RecurringTransactionCreate>({
  name: '',
  description: '',
  recurrence_type: 'daily',
  start_date: '',
  end_date: '',
  weekly_days: [],
  monthly_days: [],
  flag: '*',
  payee: '',
  narration: '',
  tags: [],
  links: [],
  postings: [
    { account: '', amount: 0, currency: 'CNY' },
    { account: '', amount: 0, currency: 'CNY' }
  ],
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  recurrence_type: [{ required: true, message: '请选择周期类型', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  narration: [{ required: true, message: '请输入摘要', trigger: 'blur' }]
}

// 计算分录金额之和
const getPostingsSum = (): number => {
  if (!form.postings || form.postings.length === 0) {
    return 0
  }
  return form.postings.reduce((sum: number, posting: any) => {
    const amount = parseFloat(posting.amount) || 0
    return sum + amount
  }, 0)
}

// 检验分录平衡
const validatePostings = (): boolean => {
  const sum = getPostingsSum()
  return Math.abs(sum) < 0.01 // 允许0.01的误差
}

// 日志相关
const showLogsDialog = ref(false)
const executionLogs = ref<ExecutionLog[]>([])
const logsLoading = ref(false)

// 定时任务相关
const showJobsDialog = ref(false)
const schedulerJobs = ref<SchedulerJob[]>([])
const jobsLoading = ref(false)
const triggerLoading = ref(false)

// 生命周期
onMounted(() => {
  loadRecurringTransactions()
})

// 方法
const loadRecurringTransactions = async () => {
  loading.value = true
  try {
    recurringTransactions.value = await recurringApi.list(showActiveOnly.value)
  } catch (error) {
    ElMessage.error('加载周期记账列表失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  editingTransaction.value = null
  Object.assign(form, {
    name: '',
    description: '',
    recurrence_type: 'daily',
    start_date: '',
    end_date: '',
    weekly_days: [],
    monthly_days: [],
    flag: '*',
    payee: '',
    narration: '',
    tags: [],
    links: [],
    postings: [
      { account: '', amount: 0, currency: 'CNY' },
      { account: '', amount: 0, currency: 'CNY' }
    ],
    is_active: true
  })
}

const editTransaction = (transaction: RecurringTransaction) => {
  editingTransaction.value = transaction
  Object.assign(form, {
    ...transaction,
    weekly_days: transaction.weekly_days || [],
    monthly_days: transaction.monthly_days || [],
    tags: transaction.tags || [],
    links: transaction.links || [],
    postings: transaction.postings.map((p: any) => ({
      account: p.account,
      amount: parseFloat(p.amount) || 0,
      currency: p.currency || 'CNY'
    }))
  })
  showCreateDialog.value = true
}

const saveTransaction = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 检验分录平衡
    if (!validatePostings()) {
      const sum = getPostingsSum() || 0
      ElMessage.error(`分录金额之和必须为0，当前和为：${sum.toFixed(2)}`)
      return
    }
    
    // 检验至少有两个分录
    if (form.postings.length < 2) {
      ElMessage.error('至少需要两个分录')
      return
    }
    
    // 检验分录账户不能为空
    const emptyAccounts = form.postings.filter((p: any) => !p.account.trim())
    if (emptyAccounts.length > 0) {
      ElMessage.error('所有分录都必须选择账户')
      return
    }
    
    saveLoading.value = true
    
    // 准备发送的数据，移除不需要的字段
    const dataToSend = {
      name: form.name,
      description: form.description,
      recurrence_type: form.recurrence_type,
      start_date: form.start_date,
      end_date: form.end_date,
      weekly_days: form.weekly_days,
      monthly_days: form.monthly_days,
      flag: form.flag,
      payee: form.payee,
      narration: form.narration,
      tags: form.tags,
      links: form.links,
      postings: form.postings.map((p: any) => ({
        account: p.account,
        amount: parseFloat(p.amount) || 0,
        currency: p.currency
      })),
      is_active: form.is_active
    }
    
    if (editingTransaction.value) {
      await recurringApi.update(editingTransaction.value.id, dataToSend)
      ElMessage.success('更新成功')
    } else {
      await recurringApi.create(dataToSend)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    loadRecurringTransactions()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saveLoading.value = false
  }
}

const toggleTransaction = async (transaction: RecurringTransaction) => {
  try {
    await recurringApi.toggle(transaction.id)
    ElMessage.success(`已${transaction.is_active ? '启用' : '禁用'}`)
    loadRecurringTransactions()
  } catch (error) {
    ElMessage.error('操作失败')
    transaction.is_active = !transaction.is_active // 回滚状态
  }
}

const deleteTransaction = async (transaction: RecurringTransaction) => {
  try {
    await ElMessageBox.confirm(
      `确定删除周期记账"${transaction.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await recurringApi.delete(transaction.id)
    ElMessage.success('删除成功')
    loadRecurringTransactions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const executeNow = async () => {
  try {
    executeLoading.value = true
    const result = await recurringApi.execute()
    
    if (result.success) {
      ElMessage.success(`执行完成：成功 ${result.executed_count} 个，失败 ${result.failed_count} 个`)
    } else {
      ElMessage.warning(result.message)
    }
    
    loadRecurringTransactions()
  } catch (error) {
    ElMessage.error('执行失败')
  } finally {
    executeLoading.value = false
  }
}

const viewLogs = async (transaction: RecurringTransaction) => {
  logsLoading.value = true
  showLogsDialog.value = true
  
  try {
    executionLogs.value = await recurringApi.getLogs(transaction.id)
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

const loadSchedulerJobs = async () => {
  jobsLoading.value = true
  showJobsDialog.value = true
  
  try {
    schedulerJobs.value = await recurringApi.getSchedulerJobs()
  } catch (error) {
    ElMessage.error('加载定时任务状态失败')
  } finally {
    jobsLoading.value = false
  }
}

const triggerScheduler = async () => {
  try {
    triggerLoading.value = true
    const result = await recurringApi.triggerScheduler()
    ElMessage.success(result.message)
    loadSchedulerJobs() // 刷新状态
    loadRecurringTransactions() // 刷新列表
  } catch (error) {
    ElMessage.error('触发定时任务失败')
  } finally {
    triggerLoading.value = false
  }
}

const onRecurrenceTypeChange = () => {
  form.weekly_days = []
  form.monthly_days = []
}

const addPosting = () => {
  form.postings.push({ account: '', amount: 0, currency: 'CNY' })
}

const removePosting = (index: number) => {
  if (form.postings.length > 2) {
    form.postings.splice(index, 1)
  }
}

const onAccountChange = (index: number) => {
  // 账户变化处理逻辑，可以在这里添加额外的处理
  console.log(`账户 ${index} 发生变化`)
}

// 辅助方法
const getRecurrenceTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    daily: '每日',
    weekdays: '工作日',
    weekly: '每周',
    monthly: '每月'
  }
  return typeMap[type] || type
}

const getRecurrenceTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    daily: 'primary',
    weekdays: 'success',
    weekly: 'warning',
    monthly: 'info'
  }
  return typeMap[type] || 'primary'
}

const getRecurrenceDetail = (transaction: RecurringTransaction) => {
  const { recurrence_type, weekly_days, monthly_days } = transaction
  
  if (recurrence_type === 'weekly' && weekly_days?.length) {
    const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekly_days.map(day => dayNames[day]).join('、')
  }
  
  if (recurrence_type === 'monthly' && monthly_days?.length) {
    return monthly_days.map(day => `${day}日`).join('、')
  }
  
  return ''
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.recurring-transactions {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.actions {
  display: flex;
  gap: 10px;
}

.filters {
  margin-bottom: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.transaction-table {
  margin-bottom: 20px;
}

.postings-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background: #fafafa;
}

.posting-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.posting-item:last-child {
  margin-bottom: 0;
}

.monthly-days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 10px;
}

.monthly-days .el-checkbox {
  margin-right: 0;
}

.postings-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e4e7ed;
}

.balance-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.balance-label {
  font-weight: 500;
  color: #606266;
}

.balance-amount {
  font-weight: bold;
  font-size: 16px;
}

.balance-amount.balanced {
  color: #67c23a;
}

.balance-amount.unbalanced {
  color: #f56c6c;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: flex-start;
}

.action-buttons .el-button {
  margin: 0;
}
</style> 