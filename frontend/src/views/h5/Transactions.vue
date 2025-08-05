<template>
  <div class="h5-transactions">
    <!-- 筛选栏 -->
    <van-sticky>
      <div class="filter-bar">
        <van-dropdown-menu>
          <van-dropdown-item v-model="filterType" :options="typeOptions" />
          <van-dropdown-item v-model="filterAccount" :options="accountOptions" />
          <van-dropdown-item :title="dateFilterTitle" ref="dateFilterDropdown">
            <div class="date-filter-panel">
              <van-row gutter="8">
                <van-col span="12">
                  <van-cell
                    title="开始日期"
                    :value="formatDateDisplay(startDate)"
                    is-link
                    @click="showStartDateCalendar = true"
                  />
                </van-col>
                <van-col span="12">
                  <van-cell
                    title="结束日期"
                    :value="formatDateDisplay(endDate)"
                    is-link
                    @click="showEndDateCalendar = true"
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
          </van-dropdown-item>
        </van-dropdown-menu>
      </div>
    </van-sticky>



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
          <!-- 日期分组头 - 可点击折叠 -->
          <div class="group-header" :class="{ collapsed: isGroupCollapsed(group.date) }" @click="toggleGroupCollapse(group.date)">
            <div class="group-header-left">
              <van-icon :name="getCollapseIcon()" class="collapse-icon" />
              <span class="group-date">{{ group.date }}</span>
            </div>
            <span class="group-amount" :class="getGroupAmountClass(group.totalAmount)">{{ formatAmount(group.totalAmount) }}</span>
          </div>

          <!-- 交易项 - 支持折叠 -->
          <van-cell-group v-show="!isGroupCollapsed(group.date)">
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
              />
              
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

    <!-- 开始日期日历 -->
    <van-calendar
      v-model:show="showStartDateCalendar"
      title="选择开始日期"
      :default-date="startDate ? new Date(startDate) : new Date()"
      :min-date="new Date(2025, 5, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onStartDateConfirm"
      @close="showStartDateCalendar = false"
    />

    <!-- 结束日期日历 -->
    <van-calendar
      v-model:show="showEndDateCalendar"
      title="选择结束日期"
      :default-date="endDate ? new Date(endDate) : new Date()"
      :min-date="new Date(2025, 5, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onEndDateConfirm"
      @close="showEndDateCalendar = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { getTransactions, deleteTransaction as deleteTransactionApi, getAccounts } from '@/api/transactions'

const router = useRouter()
const route = useRoute()

// 高亮显示的交易ID（从URL参数获取）
const highlightTransactionId = ref(route.query.highlight as string || '')

// 响应式数据
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const fabOffset = ref({ x: -24, y: -100 })

// 折叠状态（记录折叠的日期）
const collapsedGroups = ref<Set<string>>(new Set())

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
const showStartDateCalendar = ref(false)
const showEndDateCalendar = ref(false)

// 选项数据
const typeOptions = [
  { text: '全部类型', value: 'all' },
  { text: '收入', value: 'income' },
  { text: '支出', value: 'expense' },
  { text: '转账', value: 'transfer' }
]

interface AccountOption {
  text: string
  value: string
  disabled?: boolean
}

const accountOptions = ref<AccountOption[]>([
  { text: '全部账户', value: 'all' }
])



interface Transaction {
  id: string  // 改为string类型支持transaction_id
  transaction_id?: string  // 添加transaction_id字段
  filename?: string
  lineno?: number
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



// 计算交易的显示金额（用于合计计算）- 只统计收入和支出，排除转账
const getTransactionDisplayAmount = (transaction: any) => {
  if (transaction.type === 'income') {
    // 收入：计算为正数
    return Math.abs(transaction.amount)
  } else if (transaction.type === 'expense') {
    // 支出：计算为负数
    return -Math.abs(transaction.amount)
  } else {
    // 转账：不纳入统计
    return 0
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
  
  // 对每个日期组内的交易按行号倒序排列
  Object.values(groups).forEach(group => {
    group.transactions.sort((a, b) => {
      const linenoA = a.lineno || 0
      const linenoB = b.lineno || 0
      return linenoB - linenoA // 倒序排列
    })
  })
  
  return Object.values(groups).sort((a, b) => 
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )
})

// 计算属性 - 日期筛选显示标题
const dateFilterTitle = computed(() => {
  if (startDate.value && endDate.value) {
    return `${startDate.value} 至 ${endDate.value}`
  } else if (startDate.value) {
    return `从 ${startDate.value}`
  } else if (endDate.value) {
    return `到 ${endDate.value}`
  }
  return '按日期筛选'
})

// 方法
const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(Math.abs(amount))
}

// 折叠相关方法
const toggleGroupCollapse = (date: string) => {
  if (collapsedGroups.value.has(date)) {
    collapsedGroups.value.delete(date)
  } else {
    collapsedGroups.value.add(date)
  }
}

const isGroupCollapsed = (date: string) => {
  return collapsedGroups.value.has(date)
}

const getCollapseIcon = () => {
  return 'arrow-down'
}

// 获取日金额样式类
const getGroupAmountClass = (amount: number) => {
  return amount >= 0 ? 'positive' : 'negative'
}

// 格式化交易显示金额（转换为用户友好的显示方式）
const formatTransactionAmount = (transaction: any) => {
  let displayAmount = transaction.amount
  
  if (transaction.type === 'income') {
    // 收入：显示为正数
    displayAmount = Math.abs(transaction.amount)
  } else if (transaction.type === 'expense') {
    // 支出：显示为正数
    displayAmount = Math.abs(transaction.amount)
  }
  
  return formatAmount(displayAmount)
}

// 获取交易显示金额的正负性（用于颜色显示）
const getTransactionAmountClass = (transaction: any) => {
  if (transaction.type === 'income') {
    // 收入：显示绿色
    return 'positive'
  } else if (transaction.type === 'expense') {
    // 支出：显示红色
    return 'negative'
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

// 通用的交易数据转换函数
const convertTransactionData = (trans: any, fallbackId: string) => {
  // 根据账户类型分组分录
  const incomePostings = trans.postings?.filter((p: any) => p.account.startsWith('Income:')) || []
  const expensePostings = trans.postings?.filter((p: any) => p.account.startsWith('Expenses:')) || []
  
  let mainAccountName = ''
  let mainAmount = 0
  let transactionType = 'transfer'
  
  if (expensePostings.length > 0) {
    // 支出类：汇总所有支出分录的账户名和金额
    const accountNames = expensePostings.map((p: any) => formatAccountName(p.account)).join(',')
    const totalAmount = expensePostings.reduce((sum: number, p: any) => {
      const amount = typeof p.amount === 'string' ? parseFloat(p.amount) : (p.amount || 0)
      return sum + Math.abs(amount) // 取绝对值确保显示正数
    }, 0)
    
    mainAccountName = accountNames
    mainAmount = totalAmount
    transactionType = 'expense'
  } else if (incomePostings.length > 0) {
    // 收入类：汇总所有收入分录的账户名和金额
    const accountNames = incomePostings.map((p: any) => formatAccountName(p.account)).join(',')
    const totalAmount = incomePostings.reduce((sum: number, p: any) => {
      const amount = typeof p.amount === 'string' ? parseFloat(p.amount) : (p.amount || 0)
      return sum + Math.abs(amount) // 取绝对值确保显示正数
    }, 0)
    
    mainAccountName = accountNames
    mainAmount = totalAmount
    transactionType = 'income'
  } else {
    // 转账：使用第一个分录
    const firstPosting = trans.postings?.[0]
    if (firstPosting) {
      mainAccountName = firstPosting.account
      const amount = typeof firstPosting.amount === 'string' ? parseFloat(firstPosting.amount) : (firstPosting.amount || 0)
      mainAmount = amount
      transactionType = 'transfer'
    }
  }
  
  return {
    id: trans.transaction_id || fallbackId, // 使用唯一ID
    transaction_id: trans.transaction_id, // 文件名+行号组成的唯一标识
    filename: trans.filename,
    lineno: trans.lineno,
    payee: trans.payee || trans.narration || '',
    account: mainAccountName,
    date: trans.date,
    amount: mainAmount,
    type: transactionType
  }
}

// 已移除交易图标函数，不再需要

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
  
  // 检查是否已经完成加载
  if (finished.value) {
    console.log('⛔ onLoad early return: finished')
    return
  }
  
  
  // 检查是否还有更多页面
  if (currentPage.value >= totalPages.value && totalPages.value > 0) {
    console.log('⛔ onLoad: no more pages to load, currentPage:', currentPage.value, 'totalPages:', totalPages.value)
    finished.value = true
    return
  }
  
  // 立即设置 loading 状态，让 van-list 知道开始加载
  loading.value = true
  console.log('📄 onLoad: set loading=true, loading page', currentPage.value + 1)
  
  try {
    // 加载下一页数据
    const nextPage = currentPage.value + 1
    await loadTransactions(false, nextPage)
  } catch (error) {
    console.error('onLoad failed:', error)
    loading.value = false
  }
}

const loadTransactions = async (isRefresh = false, pageToLoad?: number) => {
  console.log('📥 loadTransactions called:', {
    isRefresh,
    pageToLoad,
    currentLoading: loading.value,
    currentPage: currentPage.value,
    finished: finished.value
  })
  
  // 如果不是刷新，且还没有设置 loading 状态，则设置它
  if (!isRefresh && !loading.value) {
    loading.value = true
  }
  
  // 如果是刷新，总是设置 loading 状态
  if (isRefresh) {
    loading.value = true
  }
  
  try {
    
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
    const convertedTransactions = (response.data || []).map((trans: any, index: number) => 
      convertTransactionData(trans, `transaction-${currentPage.value}-${index + 1}`)
    )
    
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

// 格式化账户名称（用于显示）
const formatAccountNameForDisplay = (accountName: string) => {
  if (!accountName) return '未知账户'
  
  // 去掉第一级账户名称（Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(':')
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(':')
    
    // 进一步处理：去掉第一个"-"以及前面的字母部分
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

// 获取账户类型
const getAccountType = (accountName: string) => {
  if (accountName.startsWith('Assets:')) return 'assets'
  if (accountName.startsWith('Liabilities:')) return 'liabilities'
  if (accountName.startsWith('Income:')) return 'income'
  if (accountName.startsWith('Expenses:')) return 'expenses'
  if (accountName.startsWith('Equity:')) return 'equity'
  return 'other'
}

// 获取账户类型的显示名称
const getAccountTypeLabel = (type: string) => {
  const typeLabels: Record<string, string> = {
    'assets': '💰 资产',
    'liabilities': '📝 负债',
    'income': '💵 收入',
    'expenses': '💸 支出',
    'equity': '⚖️ 权益',
    'other': '📁 其他'
  }
  return typeLabels[type] || '📁 其他'
}

// 加载账户选项
const loadAccountOptions = async () => {
  try {
    const response = await getAccounts()
    const accounts = response.data || response || []
    
    // 按类型分组账户
    const accountsByType: Record<string, any[]> = {
      'assets': [],
      'liabilities': [],
      'income': [],
      'expenses': [],
      'equity': [],
      'other': []
    }
    
    accounts.forEach((account: any) => {
      const accountName = typeof account === 'string' ? account : (account.name || account.full_path)
      const accountType = getAccountType(accountName)
      accountsByType[accountType].push({
        text: formatAccountNameForDisplay(accountName),
        value: accountName
      })
    })
    
    // 构建分层选项
    const options: AccountOption[] = [{ text: '全部账户', value: 'all' }]
    
    // 按类型添加账户，并在每个类型前添加分隔符
    const typeOrder = ['assets', 'liabilities', 'income', 'expenses', 'equity', 'other']
    
    typeOrder.forEach(type => {
      if (accountsByType[type].length > 0) {
        // 添加类型标题（不可选择）
        options.push({
          text: getAccountTypeLabel(type),
          value: `__type_${type}__`,
          disabled: true // 标记为不可选择
        })
        
        // 添加该类型下的账户，并增加缩进
        accountsByType[type].forEach(account => {
          options.push({
            text: `　　${account.text}`, // 使用全角空格增加缩进
            value: account.value
          })
        })
      }
    })
    
    accountOptions.value = options
    console.log('账户选项加载成功:', accounts.length, '个账户，按', typeOrder.filter(type => accountsByType[type].length > 0).length, '种类型分组')
  } catch (error) {
    console.error('加载账户选项失败:', error)
  }
}

// 日期筛选相关方法
const formatDate = (date: Date) => {
  return date.toLocaleDateString('en-CA')
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

// 日期处理
const formatDateDisplay = (dateStr: string) => {
  if (!dateStr) return '选择日期'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const onStartDateConfirm = (date: Date) => {
  startDate.value = formatDate(date)
  showStartDateCalendar.value = false
}

const onEndDateConfirm = (date: Date) => {
  endDate.value = formatDate(date)
  showEndDateCalendar.value = false
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

.date-filter-panel {
  padding: 16px;
  background-color: white;
}

/* 账户分组样式 */
:deep(.van-dropdown-item__option) {
  padding: 10px 16px;
}

/* 账户类型标题样式 */
:deep(.van-dropdown-item__option[disabled]) {
  background-color: #f7f8fa !important;
  color: #646566 !important;
  font-weight: 500;
  font-size: 13px;
  padding: 8px 16px;
  cursor: default;
}

/* 账户选项缩进样式 */
:deep(.van-dropdown-item__option:not([disabled])) {
  border-left: 2px solid transparent;
}

:deep(.van-dropdown-item__option:hover:not([disabled])) {
  border-left-color: #1989fa;
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
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.group-header:hover {
  background-color: #ebedf0;
}

.group-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-icon {
  font-size: 12px;
  color: #969799;
  transition: transform 0.2s;
}

.group-header .collapse-icon {
  transform: rotate(0deg);
}

.group-header.collapsed .collapse-icon {
  transform: rotate(-90deg);
}

.group-date {
  color: #646566;
}

.group-amount {
  font-weight: 500;
}

.group-amount.positive {
  color: #07c160;
}

.group-amount.negative {
  color: #ee0a24;
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