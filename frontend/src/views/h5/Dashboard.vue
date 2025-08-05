<template>
  <div class="h5-dashboard">
    <!-- 账户概览卡片 -->
    <van-card class="balance-card">
      <template #title>
        <div class="balance-header">
          <span>总资产</span>
          <van-icon name="eye-o" @click="toggleBalanceVisibility" />
        </div>
      </template>
      <template #desc>
        <div class="balance-amount">
          {{ showBalance ? formatAmount(totalBalance) : '****' }}
        </div>
      </template>
    </van-card>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <van-grid :column-num="4" :border="false">
        <van-grid-item
          v-for="action in quickActions"
          :key="action.name"
          :icon="action.icon"
          :text="action.text"
          @click="action.onClick"
        />
      </van-grid>
    </div>

    <!-- 最近交易 -->
    <van-cell-group title="最近交易">
      <van-cell
        v-for="transaction in recentTransactions"
        :key="transaction.id"
        :title="formatAccountName(transaction.account)"
        :label="transaction.date"
        :value="formatAmount(transaction.amount)"
        :value-class="transaction.amount > 0 ? 'positive' : 'negative'"
        is-link
        @click="viewTransaction(transaction)"
      />
      
      <van-cell
        title="查看更多"
        is-link
        @click="$router.push('/h5/transactions')"
      />
    </van-cell-group>

    <!-- 月度统计 -->
    <van-cell-group title="本月统计">
      <van-cell title="收入" :value="formatAmount(monthlyStats.income)" value-class="positive" />
      <van-cell title="支出" :value="formatAmount(monthlyStats.expense)" value-class="negative" />
      <van-cell title="结余" :value="formatAmount(monthlyStats.balance)" />
    </van-cell-group>

    <!-- 账户列表 -->
    <van-cell-group title="账户概览">
      <van-cell
        v-for="account in mainAccounts"
        :key="account.name"
        :title="formatAccountName(account.name)"
        :value="formatAmount(account.balance)"
        is-link
        @click="viewAccount(account)"
      />
      
      <van-cell
        title="查看全部账户"
        is-link
        @click="$router.push('/h5/accounts')"
      />
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getBalanceSheet, getMonthlySummary } from '@/api/reports'
import { getRecentTransactions } from '@/api/transactions'
import { showToast } from 'vant'

const router = useRouter()

const showBalance = ref(true)
const totalBalance = ref(0)
interface Transaction {
  id: string  // 改为string类型，支持transaction_id
  transaction_id?: string  // 添加transaction_id字段
  payee: string
  account: string
  date: string
  amount: number
  type: string
}

interface Account {
  id: number
  name: string
  balance: number
}

const recentTransactions = ref<Transaction[]>([])
const monthlyStats = ref({
  income: 0,
  expense: 0,
  balance: 0
})
const mainAccounts = ref<Account[]>([])

const quickActions = [
  {
    name: 'expense',
    icon: 'minus',
    text: '支出',
    onClick: () => router.push('/h5/add-transaction?type=expense')
  },
  {
    name: 'income',
    icon: 'plus',
    text: '收入',
    onClick: () => router.push('/h5/add-transaction?type=income')
  },
  {
    name: 'transfer',
    icon: 'exchange',
    text: '转账',
    onClick: () => router.push('/h5/add-transaction?type=transfer')
  },
  {
    name: 'reports',
    icon: 'bar-chart-o',
    text: '报表',
    onClick: () => router.push('/h5/reports')
  }
]

const toggleBalanceVisibility = () => {
  showBalance.value = !showBalance.value
}

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
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



const viewTransaction = (transaction: any) => {
  // 跳转到交易详情页面
  router.push(`/h5/transactions/${transaction.transaction_id}`)
}


const viewAccount = (account: any) => {
  // 跳转到账户详情
  router.push(`/h5/accounts/${account.id}`)
}

const loadDashboardData = async () => {
  try {
    // 并行加载各种数据
    const [balanceSheetRes, monthlySummaryRes, recentTransactionsRes] = await Promise.allSettled([
      getBalanceSheet(),
      getMonthlySummary(),
      getRecentTransactions(7) // 获取最近7天的交易
    ])

    // 处理资产负债表数据
    if (balanceSheetRes.status === 'fulfilled') {
      const balanceData = balanceSheetRes.value as any
      totalBalance.value = balanceData?.net_worth || 0
      
      // 取前几个主要账户
      const assetAccounts = balanceData?.accounts?.filter((acc: any) => 
        acc.account_type === 'Assets' && parseFloat(acc.balance) > 0
      ).slice(0, 3) || []
      
      mainAccounts.value = assetAccounts.map((acc: any, index: number) => ({
        id: index + 1,
        name: acc.name,
        balance: parseFloat(acc.balance)
      }))
    } else {
      console.error('获取资产负债表失败:', balanceSheetRes.reason)
    }

    // 处理月度统计数据
    if (monthlySummaryRes.status === 'fulfilled') {
      const monthlyData = monthlySummaryRes.value as any
      monthlyStats.value = {
        income: monthlyData?.income_statement?.total_income || 0,
        expense: monthlyData?.income_statement?.total_expenses || 0,
        balance: monthlyData?.income_statement?.net_income || 0
      }
    } else {
      console.error('获取月度统计失败:', monthlySummaryRes.reason)
    }

    // 处理最近交易数据
    if (recentTransactionsRes.status === 'fulfilled') {
      const transactionsData = recentTransactionsRes.value as unknown as any[]
      const expenseTransactions: Transaction[] = []
      let count = 0
      
      for (const trans of transactionsData || []) {
        if (count >= 3) break
        
        // 查找支出账户（Expenses开头且金额为正的账户）
        const expensePosting = trans.postings?.find((posting: any) => {
          const amount = typeof posting.amount === 'string' ? parseFloat(posting.amount) : posting.amount
          const account = posting.account || ''
          // 只选择支出账户（Expenses开头）且金额为正的posting
          return account.startsWith('Expenses:') && amount > 0
        })
        
        if (expensePosting) {
          const amount = expensePosting.amount || 0
          const parsedAmount = typeof amount === 'string' ? parseFloat(amount) : amount
          
          expenseTransactions.push({
            id: trans.transaction_id || `transaction-${count + 1}`,  // 使用transaction_id作为id
            transaction_id: trans.transaction_id,  // 保存原始的transaction_id
            payee: trans.payee || trans.narration || '未知',
            account: expensePosting.account,
            date: trans.date,
            amount: parsedAmount,
            type: 'expense'
          })
          count++
        }
      }
      
      recentTransactions.value = expenseTransactions
    } else {
      console.error('获取最近交易失败:', recentTransactionsRes.reason)
    }

  } catch (error: any) {
    console.error('加载仪表盘数据失败:', error)
    
    // 详细错误信息
    if (error.response) {
      // 服务器响应了错误状态码
      console.error('API错误响应:', error.response.status, error.response.data)
      showToast(`API错误: ${error.response.status}`)
    } else if (error.request) {
      // 请求发出了但没有收到响应
      console.error('网络错误:', error.request)
      showToast('网络连接失败，请检查后端服务')
    } else {
      // 其他错误
      console.error('未知错误:', error.message)
      showToast('加载数据失败')
    }
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.h5-dashboard {
  padding: 16px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.balance-card {
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.balance-card :deep(.van-card__header) {
  padding: 16px;
}

.balance-card :deep(.van-card__content) {
  padding: 0 16px 16px;
}

.balance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  opacity: 0.8;
}

.balance-amount {
  font-size: 32px;
  font-weight: bold;
  margin-top: 8px;
}

.quick-actions {
  margin-bottom: 16px;
  background-color: white;
  border-radius: 12px;
  padding: 16px;
}

.quick-actions :deep(.van-grid-item__content) {
  padding: 16px 8px;
}

.quick-actions :deep(.van-grid-item__icon) {
  font-size: 24px;
  color: #1989fa;
}

.quick-actions :deep(.van-grid-item__text) {
  margin-top: 8px;
  font-size: 12px;
  color: #646566;
}

:deep(.van-cell-group) {
  margin-bottom: 16px;
  border-radius: 12px;
  overflow: hidden;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  font-weight: 500;
  color: #323233;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-cell__left-icon) {
  margin-right: 12px;
  color: #969799;
}
</style>