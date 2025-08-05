<template>
  <div class="recurring-detail">
    <van-loading v-if="loading" class="loading-wrapper">加载中...</van-loading>
    
    <div v-else-if="recurringData" class="detail-content">
      <!-- 基本信息 -->
      <van-cell-group title="基本信息" inset>
        <van-cell title="名称" :value="recurringData.name" />
        <van-cell 
          title="描述" 
          :value="recurringData.description || '无'"
          :label="recurringData.description ? '' : '未设置描述'"
        />
        <van-cell title="摘要" :value="recurringData.narration" />
        <van-cell title="收付方" :value="recurringData.payee || '无'" />
        <van-cell title="状态">
          <template #value>
            <van-tag :type="recurringData.is_active ? 'success' : 'warning'">
              {{ recurringData.is_active ? '启用' : '已暂停' }}
            </van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 周期设置 -->
      <van-cell-group title="周期设置" inset>
        <van-cell title="周期类型" :value="getRecurrenceTypeText(recurringData.recurrence_type)" />
        <van-cell 
          v-if="recurringData.recurrence_type === 'weekly' && recurringData.weekly_days?.length"
          title="执行日期"
          :value="getWeeklyDaysText(recurringData.weekly_days)"
        />
        <van-cell 
          v-if="recurringData.recurrence_type === 'monthly' && recurringData.monthly_days?.length"
          title="执行日期"
          :value="getMonthlyDaysText(recurringData.monthly_days)"
        />
        <van-cell title="开始日期" :value="recurringData.start_date" />
        <van-cell title="结束日期" :value="recurringData.end_date || '无期限'" />
        <van-cell title="最后执行" :value="recurringData.last_executed || '未执行'" />
        <van-cell title="下次执行" :value="recurringData.next_execution || '未安排'" />
      </van-cell-group>

      <!-- 记账分录 -->
      <van-cell-group title="记账分录" inset>
        <van-cell 
          v-for="(posting, index) in recurringData.postings"
          :key="index"
          :title="formatAccountName(posting.account)"
          :value="formatAmount(posting.amount, posting.currency)"
          :value-class="getAmountClass(posting.amount)"
        >
          <template #icon>
            <van-icon :name="getAccountIcon(posting.account)" />
          </template>
        </van-cell>
        
        <!-- 分录汇总 -->
        <van-cell title="金额合计">
          <template #value>
            <div class="balance-info">
              <span :class="['balance-amount', isBalanced ? 'balanced' : 'unbalanced']">
                {{ totalAmount.toFixed(2) }}
              </span>
              <van-tag :type="isBalanced ? 'success' : 'danger'" size="small">
                {{ isBalanced ? '平衡' : '不平衡' }}
              </van-tag>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <van-button 
          type="primary" 
          size="large" 
          block 
          @click="editRecurring"
        >
          编辑
        </van-button>
        
        <van-button 
          :type="recurringData.is_active ? 'warning' : 'success'"
          size="large" 
          block 
          @click="toggleStatus"
          :loading="toggleLoading"
        >
          {{ recurringData.is_active ? '暂停' : '启用' }}
        </van-button>
        
        <van-button 
          type="default"
          size="large" 
          block 
          @click="viewLogs"
        >
          查看执行日志
        </van-button>
        
        <van-button 
          type="danger" 
          size="large" 
          block 
          @click="deleteRecurring"
          :loading="deleteLoading"
        >
          删除
        </van-button>
      </div>
    </div>

    <!-- 执行日志弹窗 -->
    <van-popup v-model:show="showLogsPopup" position="bottom" :style="{ height: '60%' }">
      <div class="logs-popup">
        <div class="logs-header">
          <h3>执行日志</h3>
          <van-icon name="cross" @click="showLogsPopup = false" />
        </div>
        <van-list
          v-model:loading="logsLoading"
          :finished="logsFinished"
          finished-text="没有更多日志"
        >
          <van-cell
            v-for="log in executionLogs"
            :key="log.id"
            :title="log.execution_date"
            :label="log.error_message || '执行成功'"
            :value="formatDateTime(log.created_at)"
          >
            <template #icon>
              <van-icon 
                :name="log.success ? 'success' : 'warning'" 
                :color="log.success ? '#07c160' : '#ee0a24'"
              />
            </template>
          </van-cell>
        </van-list>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { recurringApi, type RecurringTransaction, type ExecutionLog } from '@/api/recurring'

const route = useRoute()
const router = useRouter()

// 状态
const loading = ref(true)
const toggleLoading = ref(false)
const deleteLoading = ref(false)
const recurringData = ref<RecurringTransaction | null>(null)

// 日志相关
const showLogsPopup = ref(false)
const logsLoading = ref(false)
const logsFinished = ref(false)
const executionLogs = ref<ExecutionLog[]>([])

// 计算属性
const totalAmount = computed(() => {
  if (!recurringData.value?.postings) return 0
  return recurringData.value.postings.reduce((sum, posting) => {
    return sum + (parseFloat(posting.amount?.toString() || '0') || 0)
  }, 0)
})

const isBalanced = computed(() => {
  return Math.abs(totalAmount.value) < 0.01
})

// 方法
const formatAccountName = (accountName: string) => {
  if (!accountName) return '未知账户'
  const parts = accountName.split(':')
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(':')
    const dashIndex = formattedName.indexOf('-')
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1)
    }
    return formattedName.replace(/:/g, '-')
  }
  return accountName
}

const getAccountIcon = (accountName: string) => {
  if (!accountName) return 'manager-o'
  const parts = accountName.split(':')
  const iconMap: Record<string, string> = {
    'Assets': 'gold-coin-o',
    'Liabilities': 'credit-pay',
    'Income': 'arrow-up',
    'Expenses': 'arrow-down',
    'Equity': 'balance-o'
  }
  return iconMap[parts[0]] || 'manager-o'
}

const formatAmount = (amount: any, currency = 'CNY') => {
  const numAmount = parseFloat(amount?.toString() || '0') || 0
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency
  }).format(numAmount)
}

const getAmountClass = (amount: any) => {
  const numAmount = parseFloat(amount?.toString() || '0') || 0
  return numAmount > 0 ? 'positive' : 'negative'
}

const getRecurrenceTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    'daily': '每日',
    'weekdays': '工作日',
    'weekly': '每周',
    'monthly': '每月'
  }
  return typeMap[type] || type
}

const getWeeklyDaysText = (days: number[]) => {
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days.map(day => dayNames[day]).join('、')
}

const getMonthlyDaysText = (days: number[]) => {
  return days.map(day => `${day}日`).join('、')
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 操作方法
const editRecurring = () => {
  router.push(`/h5/recurring/edit/${route.params.id}`)
}

const toggleStatus = async () => {
  if (!recurringData.value) return
  
  try {
    const newStatus = !recurringData.value.is_active
    const actionText = newStatus ? '启用' : '暂停'
    
    await showConfirmDialog({
      title: `确认${actionText}`,
      message: `确定要${actionText}这个周期记账吗？`
    })
    
    toggleLoading.value = true
    await recurringApi.toggle(recurringData.value.id)
    
    // 更新本地状态
    recurringData.value.is_active = newStatus
    showToast(`${actionText}成功`)
  } catch (error) {
    if (error !== 'cancel') {
      showToast('操作失败')
      console.error('切换状态失败:', error)
    }
  } finally {
    toggleLoading.value = false
  }
}

const deleteRecurring = async () => {
  if (!recurringData.value) return
  
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这个周期记账吗？删除后无法恢复。'
    })
    
    deleteLoading.value = true
    await recurringApi.delete(recurringData.value.id)
    
    showToast('删除成功')
    router.back()
  } catch (error) {
    if (error !== 'cancel') {
      showToast('删除失败')
      console.error('删除失败:', error)
    }
  } finally {
    deleteLoading.value = false
  }
}

const viewLogs = async () => {
  if (!recurringData.value) return
  
  try {
    showLogsPopup.value = true
    logsLoading.value = true
    
    const logs = await recurringApi.getLogs(recurringData.value.id)
    executionLogs.value = logs
    logsFinished.value = true
  } catch (error) {
    console.error('加载日志失败:', error)
    showToast('加载日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 加载数据
const loadRecurringData = async () => {
  try {
    loading.value = true
    const id = route.params.id as string
    recurringData.value = await recurringApi.get(id)
  } catch (error) {
    console.error('加载周期记账详情失败:', error)
    showToast('加载数据失败')
    router.back()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRecurringData()
})
</script>

<style scoped>
.recurring-detail {
  padding: 16px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.detail-content {
  padding-bottom: 20px;
}

.balance-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.balance-amount {
  font-weight: 500;
  font-size: 14px;
}

.balance-amount.balanced {
  color: #07c160;
}

.balance-amount.unbalanced {
  color: #ee0a24;
}

.action-buttons {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 日志弹窗样式 */
.logs-popup {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebedf0;
}

.logs-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-cell__left-icon) {
  margin-right: 12px;
  color: #1989fa;
}
</style>