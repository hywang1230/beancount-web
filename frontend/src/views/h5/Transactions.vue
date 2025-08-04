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

    <!-- 统计信息 -->
    <div class="stats-section">
      <van-row gutter="16">
        <van-col span="8">
          <div class="stat-item income">
            <div class="stat-value">{{ formatAmount(stats.income) }}</div>
            <div class="stat-label">收入</div>
          </div>
        </van-col>
        <van-col span="8">
          <div class="stat-item expense">
            <div class="stat-value">{{ formatAmount(stats.expense) }}</div>
            <div class="stat-label">支出</div>
          </div>
        </van-col>
        <van-col span="8">
          <div class="stat-item balance">
            <div class="stat-value">{{ formatAmount(stats.balance) }}</div>
            <div class="stat-label">结余</div>
          </div>
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
                :title="transaction.payee"
                :label="transaction.account"
                :value="formatAmount(transaction.amount)"
                :value-class="transaction.amount > 0 ? 'positive' : 'negative'"
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'

const router = useRouter()

// 响应式数据
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const fabOffset = ref({ x: -24, y: -100 })

// 筛选条件
const filterType = ref('all')
const filterAccount = ref('all')
const sortBy = ref('date_desc')

// 选项数据
const typeOptions = [
  { text: '全部类型', value: 'all' },
  { text: '收入', value: 'income' },
  { text: '支出', value: 'expense' },
  { text: '转账', value: 'transfer' }
]

const accountOptions = [
  { text: '全部账户', value: 'all' },
  { text: '招商银行', value: 'cmb' },
  { text: '支付宝', value: 'alipay' },
  { text: '微信', value: 'wechat' }
]

const sortOptions = [
  { text: '按日期降序', value: 'date_desc' },
  { text: '按日期升序', value: 'date_asc' },
  { text: '按金额降序', value: 'amount_desc' },
  { text: '按金额升序', value: 'amount_asc' }
]

interface Transaction {
  id: number
  payee: string
  account: string
  date: string
  amount: number
  type: string
}

// 数据
const transactions = ref<Transaction[]>([])
const stats = ref({
  income: 0,
  expense: 0,
  balance: 0
})

// 计算属性 - 分组交易
const groupedTransactions = computed(() => {
  const groups: Record<string, { date: string; transactions: Transaction[]; totalAmount: number }> = {}
  
  transactions.value.forEach(transaction => {
    const date = transaction.date
    if (!groups[date]) {
      groups[date] = {
        date,
        transactions: [],
        totalAmount: 0
      }
    }
    groups[date].transactions.push(transaction)
    groups[date].totalAmount += transaction.amount
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

const getTransactionIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'income': 'arrow-up',
    'expense': 'arrow-down',
    'transfer': 'exchange'
  }
  return iconMap[type] || 'bill-o'
}

const viewTransaction = (transaction: any) => {
  router.push(`/h5/transactions/${transaction.id}`)
}

const editTransaction = (transaction: any) => {
  router.push(`/h5/add-transaction?id=${transaction.id}`)
}

const deleteTransaction = async (transaction: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这条交易记录吗？'
    })
    
    // 这里应该调用API删除交易
    // await deleteTransactionApi(transaction.id)
    
    // 从列表中移除
    const index = transactions.value.findIndex(t => t.id === transaction.id)
    if (index > -1) {
      transactions.value.splice(index, 1)
    }
    
    showToast('删除成功')
  } catch {
    // 用户取消删除
  }
}

const onRefresh = async () => {
  // 重新加载数据
  await loadTransactions(true)
  refreshing.value = false
}

const onLoad = async () => {
  // 加载更多数据
  await loadTransactions(false)
}

const loadTransactions = async (isRefresh = false) => {
  try {
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const mockData = [
      {
        id: 1,
        payee: '星巴克',
        account: '招商银行',
        date: '2024-01-15',
        amount: -45.00,
        type: 'expense'
      },
      {
        id: 2,
        payee: '工资收入',
        account: '招商银行',
        date: '2024-01-15',
        amount: 8000.00,
        type: 'income'
      },
      {
        id: 3,
        payee: '超市购物',
        account: '支付宝',
        date: '2024-01-14',
        amount: -128.50,
        type: 'expense'
      },
      {
        id: 4,
        payee: '地铁费用',
        account: '微信',
        date: '2024-01-14',
        amount: -6.00,
        type: 'expense'
      },
      {
        id: 5,
        payee: '午餐',
        account: '支付宝',
        date: '2024-01-13',
        amount: -25.00,
        type: 'expense'
      }
    ]
    
    if (isRefresh) {
      transactions.value = mockData
    } else {
      transactions.value.push(...mockData)
    }
    
    // 计算统计数据
    stats.value = {
      income: transactions.value.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0),
      expense: transactions.value.filter(t => t.amount < 0).reduce((sum, t) => sum + t.amount, 0),
      balance: transactions.value.reduce((sum, t) => sum + t.amount, 0)
    }
    
    finished.value = transactions.value.length >= 50 // 假设最多50条
  } catch (error) {
    console.error('加载交易数据失败:', error)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTransactions(true)
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

.stats-section {
  background-color: white;
  padding: 16px;
  margin-bottom: 8px;
}

.stat-item {
  text-align: center;
  padding: 8px;
  border-radius: 8px;
}

.stat-item.income {
  background-color: #f0f9ff;
}

.stat-item.expense {
  background-color: #fef2f2;
}

.stat-item.balance {
  background-color: #f9fafb;
}

.stat-value {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-item.income .stat-value {
  color: #07c160;
}

.stat-item.expense .stat-value {
  color: #ee0a24;
}

.stat-item.balance .stat-value {
  color: #323233;
}

.stat-label {
  font-size: 12px;
  color: #969799;
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
</style>