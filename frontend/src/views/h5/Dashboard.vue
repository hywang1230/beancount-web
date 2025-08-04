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
        :title="transaction.payee"
        :label="transaction.date"
        :value="formatAmount(transaction.amount)"
        :value-class="transaction.amount > 0 ? 'positive' : 'negative'"
        is-link
        @click="viewTransaction(transaction)"
      >
        <template #icon>
          <van-icon :name="getTransactionIcon(transaction.type)" />
        </template>
      </van-cell>
      
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
        :title="account.name"
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

const router = useRouter()

const showBalance = ref(true)
const totalBalance = ref(0)
interface Transaction {
  id: number
  payee: string
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
    name: 'add',
    icon: 'plus',
    text: '记账',
    onClick: () => router.push('/h5/add-transaction')
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
  },
  {
    name: 'more',
    icon: 'apps-o',
    text: '更多',
    onClick: () => {}
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

const getTransactionIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'income': 'arrow-up',
    'expense': 'arrow-down',
    'transfer': 'exchange'
  }
  return iconMap[type] || 'bill-o'
}

const viewTransaction = (transaction: any) => {
  // 跳转到交易详情
  router.push(`/h5/transactions/${transaction.id}`)
}

const viewAccount = (account: any) => {
  // 跳转到账户详情
  router.push(`/h5/accounts/${account.id}`)
}

const loadDashboardData = async () => {
  try {
    // 这里应该调用API获取真实数据
    // 现在使用模拟数据
    totalBalance.value = 25680.50
    
    recentTransactions.value = [
      {
        id: 1,
        payee: '星巴克',
        date: '2024-01-15',
        amount: -45.00,
        type: 'expense'
      },
      {
        id: 2,
        payee: '工资收入',
        date: '2024-01-15',
        amount: 8000.00,
        type: 'income'
      },
      {
        id: 3,
        payee: '超市购物',
        date: '2024-01-14',
        amount: -128.50,
        type: 'expense'
      }
    ]
    
    monthlyStats.value = {
      income: 12000.00,
      expense: -3500.00,
      balance: 8500.00
    }
    
    mainAccounts.value = [
      { id: 1, name: '招商银行储蓄卡', balance: 15680.50 },
      { id: 2, name: '支付宝', balance: 8500.00 },
      { id: 3, name: '微信钱包', balance: 1500.00 }
    ]
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
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