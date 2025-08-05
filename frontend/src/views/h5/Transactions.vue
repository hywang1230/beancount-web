<template>
  <div class="h5-transactions">
    <!-- 筛选栏 -->
    <van-sticky>
      <div class="filter-bar">
        <van-dropdown-menu>
          <van-dropdown-item v-model="filterType" :options="typeOptions" />
          <van-dropdown-item v-model="filterAccount" :options="accountOptions" />
          <van-dropdown-item v-model="sortBy" :options="sortOptions" />
        </van-dropdown-menu>
      </div>
    </van-sticky>

    <!-- 日期筛选栏 -->
    <div class="date-filter-bar">
      <van-row gutter="8">
        <van-col span="12">
          <van-field
            v-model="startDate"
            type="date"
            label="开始日期"
            placeholder="选择开始日期"
          />
        </van-col>
        <van-col span="12">
          <van-field
            v-model="endDate"
            type="date"
            label="结束日期"
            placeholder="选择结束日期"
          />
        </van-col>
      </van-row>
      <van-row gutter="8" style="margin-top: 8px;">
        <van-col span="6">
          <van-button size="small" @click="setQuickDateRange('last7days')">7天</van-button>
        </van-col>
        <van-col span="6">
          <van-button size="small" @click="setQuickDateRange('last30days')">30天</van-button>
        </van-col>
        <van-col span="6">
          <van-button size="small" @click="setQuickDateRange('thisMonth')">本月</van-button>
        </van-col>
        <van-col span="6">
          <van-button size="small" @click="clearDateRange()">清空</van-button>
        </van-col>
      </van-row>
    </div>



    <!-- 交易列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <div
          v-for="group in groupedTransactions"
          :key="group.date"
          class="transaction-group"
        >
          <!-- 日期分组头 -->
          <div class="group-header">
            <span class="group-date">{{ group.date }}</span>
            <span class="group-amount">{{ formatAmount(group.totalAmount) }}</span>
          </div>

          <!-- 交易项 -->
          <van-cell-group>
            <van-swipe-cell
              v-for="transaction in group.transactions"
              :key="transaction.id"
            >
              <van-cell
                :title="formatAccountName(transaction.account)"
                :label="transaction.payee || transaction.date"
                :value="formatTransactionAmount(transaction)"
                :value-class="getTransactionAmountClass(transaction)"
                :class="{ 'highlighted-transaction': transaction.transaction_id === highlightTransactionId }"
                is-link
                @click="viewTransaction(transaction)"
              >
                <template #icon>
                  <div class="transaction-icon">
                    <van-icon :name="getTransactionIcon(transaction.type)" />
                  </div>
                </template>
              </van-cell>
              
              <!-- 滑动操作 -->
              <template #right>
                <van-button
                  square
                  type="primary"
                  text="编辑"
                  @click="editTransaction(transaction)"
                />
                <van-button
                  square
                  type="danger"
                  text="删除"
                  @click="deleteTransaction(transaction)"
                />
              </template>
            </van-swipe-cell>
          </van-cell-group>
        </div>
      </van-list>
    </van-pull-refresh>

    <!-- 悬浮按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="$router.push('/h5/add-transaction')"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { getTransactions, deleteTransaction as deleteTransactionApi } from '@/api/transactions'
import { getAllAccounts } from '@/api/accounts'

const router = useRouter()
const route = useRoute()

// 高亮显示的交易ID（从URL参数获取）
const highlightTransactionId = ref(route.query.highlight as string || '')

// 响应式数据
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const fabOffset = ref({ x: -24, y: -100 })

// 分页状态
const currentPage = ref(1)
const totalPages = ref(1)

// 筛选条件
const filterType = ref('all')
const filterAccount = ref('all')
const sortBy = ref('date_desc')

// 日期筛选相关
const startDate = ref('')
const endDate = ref('')

// 选项数据
const typeOptions = [
  { text: '全部类型', value: 'all' },
  { text: '收入', value: 'income' },
  { text: '支出', value: 'expense' },
  { text: '转账', value: 'transfer' }
]

const accountOptions = ref([
  { text: '全部账户', value: 'all' }
])

const sortOptions = [
  { text: '按日期降序', value: 'date_desc' },
  { text: '按日期升序', value: 'date_asc' },
  { text: '按金额降序', value: 'amount_desc' },
  { text: '按金额升序', value: 'amount_asc' }
]

interface Transaction {
  id: string  // 改为string类型支持transaction_id
  transaction_id?: string  // 添加transaction_id字段
  payee: string
  account: string
  date: string
  amount: number
  type: string
}

// 数据
const transactions = ref<Transaction[]>([])

// 计算属性 - 过滤后的交易（用于前端显示，服务端已过滤大部分）
const filteredTransactions = computed(() => {
  let filtered = transactions.value

  // 所有类型筛选现在都在后端完成，前端不需要额外过滤

  return filtered
})



// 计算交易的显示金额（用于合计计算）
const getTransactionDisplayAmount = (transaction: any) => {
  if (transaction.type === 'income') {
    // 收入账户：负数是盈利，转换为正数；正数是亏损，转换为负数
    return -transaction.amount
  } else if (transaction.type === 'expense') {
    // 支出账户：保持原值
    return transaction.amount
  } else {
    // 转账：保持原值
    return transaction.amount
  }
}

// 计算属性 - 分组交易
const groupedTransactions = computed(() => {
  const groups: Record<string, { date: string; transactions: Transaction[]; totalAmount: number }> = {}
  
  filteredTransactions.value.forEach(transaction => {
    const date = transaction.date
    if (!groups[date]) {
      groups[date] = {
        date,
        transactions: [],
        totalAmount: 0
      }
    }
    groups[date].transactions.push(transaction)
    // 使用显示金额计算每日合计
    groups[date].totalAmount += getTransactionDisplayAmount(transaction)
  })
  
  return Object.values(groups).sort((a, b) => 
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
})

// 方法
const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 格式化交易显示金额（转换为用户友好的显示方式）
const formatTransactionAmount = (transaction: any) => {
  let displayAmount = transaction.amount
  
  if (transaction.type === 'income') {
    // 收入账户：负数是盈利，转换为正数显示；正数是亏损，转换为负数显示
    displayAmount = -transaction.amount
  } else if (transaction.type === 'expense') {
    // 支出账户：正数是支出，保持正数；负数是退款，保持负数
    displayAmount = transaction.amount
  }
  
  return formatAmount(displayAmount)
}

// 获取交易显示金额的正负性（用于颜色显示）
const getTransactionAmountClass = (transaction: any) => {
  if (transaction.type === 'income') {
    // 收入：负数是盈利(显示绿色)，正数是亏损(显示红色)
    return transaction.amount < 0 ? 'positive' : 'negative'
  } else if (transaction.type === 'expense') {
    // 支出：正数是支出(显示红色)，负数是退款(显示绿色)
    return transaction.amount > 0 ? 'negative' : 'positive'
  } else {
    // 转账：根据金额正负显示
    return transaction.amount > 0 ? 'positive' : 'negative'
  }
}

const formatAccountName = (accountName: string) => {
  if (!accountName) return '未知账户'
  // 去掉第一级账户名称（通常是Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(':')
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(':')
    
    // 进一步处理：去掉第一个"-"以及前面的字母部分
    // 例如：JT-交通:过路费 -> 交通:过路费，然后替换":"为"-"变成：交通-过路费
    const dashIndex = formattedName.indexOf('-')
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1)
    }
    
    // 将":"替换为"-"以提高可读性
    formattedName = formattedName.replace(/:/g, '-')
    
    return formattedName
  }
  return accountName
}

const getTransactionIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'income': 'arrow-up',
    'expense': 'arrow-down',
    'transfer': 'exchange'
  }
  return iconMap[type] || 'bill-o'
}

const viewTransaction = (transaction: any) => {
  const transactionId = transaction.transaction_id || transaction.id
  router.push(`/h5/transactions/${transactionId}`)
}

const editTransaction = (transaction: any) => {
  const transactionId = transaction.transaction_id || transaction.id
  router.push(`/h5/add-transaction?id=${transactionId}`)
}

const deleteTransaction = async (transaction: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这条交易记录吗？删除后无法恢复。'
    })
    
    // 调用API删除交易
    const transactionId = transaction.transaction_id || transaction.id
    await deleteTransactionApi(transactionId)
    
    // 从列表中移除
    const index = transactions.value.findIndex(t => 
      (t.transaction_id && t.transaction_id === transactionId) || 
      t.id === transaction.id
    )
    if (index > -1) {
      transactions.value.splice(index, 1)
    }
    
    showToast('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交易失败:', error)
      showToast('删除交易失败')
    }
  }
}

const onRefresh = async () => {
  console.log('🔄 onRefresh called: resetting state and loading page 1')
  
  // 重置到初始状态
  currentPage.value = 1  // 重置为第一页
  finished.value = false
  loading.value = false  // 确保loading状态正确
  totalPages.value = 1
  transactions.value = []  // 清空现有数据
  
  console.log('🚀 onRefresh: state reset, loading page 1')
  // 直接加载第一页
  try {
    await loadTransactions(true)
  } catch (error) {
    console.error('刷新失败:', error)
  } finally {
    refreshing.value = false
  }
}

const onLoad = async () => {
  console.log('🔄 onLoad called:', {
    finished: finished.value,
    loading: loading.value,
    currentPage: currentPage.value,
    totalPages: totalPages.value,
    transactionsCount: transactions.value.length
  })
  
  // 检查是否已经完成加载，避免重复请求
  if (finished.value || loading.value) {
    console.log('⛔ onLoad early return: finished or loading')
    return
  }
  
  // 检查是否还有更多页面
  if (currentPage.value >= totalPages.value && totalPages.value > 0) {
    console.log('⛔ onLoad: no more pages to load, currentPage:', currentPage.value, 'totalPages:', totalPages.value)
    finished.value = true
    return
  }
  
  // 加载下一页数据
  const nextPage = currentPage.value + 1
  console.log('📄 onLoad: loading page', nextPage)
  await loadTransactions(false, nextPage)
}

const loadTransactions = async (isRefresh = false, pageToLoad?: number) => {
  console.log('📥 loadTransactions called:', {
    isRefresh,
    pageToLoad,
    currentLoading: loading.value,
    currentPage: currentPage.value,
    finished: finished.value
  })
  
  // 防止重复加载
  if (loading.value) {
    console.log('⛔ loadTransactions: already loading, skipping')
    return
  }
  
  try {
    loading.value = true
    
    // 确定要加载的页码
    const targetPage = pageToLoad || currentPage.value
    
    // 如果是刷新，重置状态
    if (isRefresh) {
      finished.value = false
    }
    
    // 构建筛选参数
    const params: any = {
      page: targetPage,
      page_size: 20
    }
    
    console.log('🚀 About to call API with params:', params)
    console.log('🔍 Current filter state:', {
      filterType: filterType.value,
      filterAccount: filterAccount.value,
      sortBy: sortBy.value,
      startDate: startDate.value,
      endDate: endDate.value,
      isRefresh,
      targetPage
    })
    
    // 类型筛选
    if (filterType.value !== 'all') {
      params.transaction_type = filterType.value
    }
    
    // 账户筛选
    if (filterAccount.value !== 'all') {
      params.account = filterAccount.value
    }
    
    // 日期范围筛选
    if (startDate.value) {
      params.start_date = startDate.value
    }
    if (endDate.value) {
      params.end_date = endDate.value
    }
    
    // 如果没有设置日期范围，默认获取最近3个月的数据
    if (!startDate.value && !endDate.value) {
      const today = new Date()
      const threeMonthsAgo = new Date()
      threeMonthsAgo.setMonth(today.getMonth() - 3)
      params.start_date = formatDate(threeMonthsAgo)
      params.end_date = formatDate(today)
    }

    console.log('🌐 Making API call to getTransactions with final params:', params)
    const response = await getTransactions(params)
    console.log('🎯 API call completed successfully')
    console.log('📡 API response received:', {
      requested_page: targetPage,
      current_page: currentPage.value,
      total_pages: response.total_pages,
      total: response.total,
      data_length: response.data?.length,
      response_keys: Object.keys(response),
      params
    })
    
    // 更新分页信息
    totalPages.value = response.total_pages
    
    // 只有API调用成功后才更新当前页码
    if (pageToLoad) {
      currentPage.value = pageToLoad
    }
    
    // 转换API数据格式
    const convertedTransactions = (response.data || []).map((trans: any, index: number) => {
      // 智能选择主要账户和金额：优先使用Income/Expenses账户
      let mainPosting = trans.postings?.[0]
      let mainAmount = mainPosting?.amount || 0
      
      // 查找收入或支出账户作为主要显示账户
      const incomePosting = trans.postings?.find((p: any) => p.account.startsWith('Income:'))
      const expensePosting = trans.postings?.find((p: any) => p.account.startsWith('Expenses:'))
      
      if (incomePosting) {
        mainPosting = incomePosting
        mainAmount = incomePosting.amount || 0
      } else if (expensePosting) {
        mainPosting = expensePosting
        mainAmount = expensePosting.amount || 0
      }
      
      const parsedAmount = typeof mainAmount === 'string' ? parseFloat(mainAmount) : mainAmount
      
      return {
        id: trans.transaction_id || `transaction-${currentPage.value}-${index + 1}`, // 使用唯一ID
        transaction_id: trans.transaction_id, // 文件名+行号组成的唯一标识
        filename: trans.filename,
        lineno: trans.lineno,
        payee: trans.payee || trans.narration || '',
        account: mainPosting?.account || '',
        date: trans.date,
        amount: parsedAmount,
        type: mainPosting?.account.startsWith('Income:') ? 'income' : 
              (mainPosting?.account.startsWith('Expenses:') ? 'expense' : 'transfer')
      }
    })
    
    if (isRefresh) {
      transactions.value = convertedTransactions
    } else {
      transactions.value.push(...convertedTransactions)
    }
    
    // 统计数据现在通过计算属性自动更新
    
    // 判断是否还有更多数据
    const hasMoreData = currentPage.value < response.total_pages
    
    // 设置finished状态
    if (response.total_pages === 0 || (currentPage.value === 1 && convertedTransactions.length === 0)) {
      // 没有数据或第一页没有数据
      finished.value = true
      console.log('📄 No data available, marking as finished')
    } else {
      finished.value = !hasMoreData
    }
    
    console.log('📊 Pagination check:', {
      currentPage: currentPage.value,
      totalPages: response.total_pages,
      convertedTransactions: convertedTransactions.length,
      hasMoreData,
      finished: finished.value,
      totalTransactions: transactions.value.length,
      isRefresh
    })
    
    // 移除临时测试代码
    
  } catch (error) {
    console.error('加载交易数据失败:', error)
    showToast('加载交易数据失败')
    // 发生错误时，如果是加载新页面失败，则设置finished为true停止继续加载
    if (!isRefresh && pageToLoad && pageToLoad > currentPage.value) {
      finished.value = true
    }
  } finally {
    loading.value = false
  }
}

// 加载账户选项
const loadAccountOptions = async () => {
  try {
    const response = await getAllAccounts()
    const accounts = response.data || []
    
    // 添加账户选项
    const options = [{ text: '全部账户', value: 'all' }]
    accounts.forEach((account: any) => {
      options.push({
        text: account.name || account.full_path,
        value: account.name || account.full_path
      })
    })
    
    accountOptions.value = options
  } catch (error) {
    console.error('加载账户选项失败:', error)
  }
}

// 日期筛选相关方法
const formatDate = (date: Date) => {
  return date.toISOString().split('T')[0]
}

const setQuickDateRange = (range: string) => {
  const today = new Date()
  const endDateValue = new Date(today)
  let startDateValue = new Date(today)
  
  switch (range) {
    case 'last7days':
      startDateValue.setDate(today.getDate() - 7)
      break
    case 'last30days':
      startDateValue.setDate(today.getDate() - 30)
      break
    case 'thisMonth':
      startDateValue = new Date(today.getFullYear(), today.getMonth(), 1)
      break
  }
  
  startDate.value = formatDate(startDateValue)
  endDate.value = formatDate(endDateValue)
}

const clearDateRange = () => {
  startDate.value = ''
  endDate.value = ''
}

// 组件是否已初始化完成
const isInitialized = ref(false)
// 是否正在处理筛选变化
const isHandlingFilterChange = ref(false)

// 监听筛选条件变化
watch([filterType, filterAccount, sortBy, startDate, endDate], async () => {
  // 只有在组件初始化完成后才响应筛选条件变化
  if (isInitialized.value && !isHandlingFilterChange.value) {
    isHandlingFilterChange.value = true
    console.log('🔄 Filter changed, refreshing data:', {
      filterType: filterType.value,
      filterAccount: filterAccount.value,
      sortBy: sortBy.value,
      startDate: startDate.value,
      endDate: endDate.value
    })
    try {
      await onRefresh()
    } finally {
      isHandlingFilterChange.value = false
    }
  }
}, { deep: true })

onMounted(async () => {
  console.log('🚀 Component mounting, initializing state')
  
  // 确保初始状态正确
  finished.value = false
  loading.value = false
  currentPage.value = 1  // 直接从1开始
  totalPages.value = 1
  transactions.value = []
  
  console.log('📊 Initial state set:', {
    finished: finished.value,
    loading: loading.value,
    currentPage: currentPage.value,
    totalPages: totalPages.value,
    transactionsLength: transactions.value.length
  })
  
  console.log('🚀 Loading account options and initial data')
  
  loadAccountOptions()
  
  // 初始加载第一页
  await loadTransactions(true)  // 直接调用loadTransactions作为初始加载
  
  // 标记组件已初始化完成，现在可以响应筛选条件变化
  isInitialized.value = true
  console.log('✅ Component initialization completed:', {
    finished: finished.value,
    loading: loading.value,
    currentPage: currentPage.value,
    totalPages: totalPages.value,
    transactionsLength: transactions.value.length
  })
})
</script>

<style scoped>
.h5-transactions {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.filter-bar {
  background-color: white;
  border-bottom: 1px solid #ebedf0;
}

.date-filter-bar {
  padding: 12px 16px;
  background-color: white;
  border-bottom: 1px solid #ebedf0;
}

.transaction-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: #f7f8fa;
  font-size: 14px;
}

.group-date {
  color: #646566;
}

.group-amount {
  color: #323233;
  font-weight: 500;
}

.transaction-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f7f8fa;
  border-radius: 50%;
  margin-right: 12px;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

/* 高亮显示的交易 */
.highlighted-transaction {
  background-color: #fff7e6 !important;
  border-left: 4px solid #ff9500 !important;
}
</style>