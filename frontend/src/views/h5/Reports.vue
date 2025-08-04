<template>
  <div class="h5-reports">
    <!-- 时间筛选 -->
    <van-sticky>
      <div class="time-filter">
        <van-dropdown-menu>
          <van-dropdown-item v-model="selectedPeriod" :options="periodOptions" />
        </van-dropdown-menu>
      </div>
    </van-sticky>

    <!-- 概览卡片 -->
    <div class="overview-cards">
      <van-row gutter="16">
        <van-col span="12">
          <div class="overview-card income">
            <div class="card-value">{{ formatAmount(overview.income) }}</div>
            <div class="card-label">收入</div>
          </div>
        </van-col>
        <van-col span="12">
          <div class="overview-card expense">
            <div class="card-value">{{ formatAmount(Math.abs(overview.expense)) }}</div>
            <div class="card-label">支出</div>
          </div>
        </van-col>
      </van-row>
      <div class="balance-card">
        <div class="balance-value">{{ formatAmount(overview.balance) }}</div>
        <div class="balance-label">结余</div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <!-- 支出分类 -->
      <van-cell-group title="支出分类" inset>
        <div class="chart-placeholder">
          <van-icon name="bar-chart-o" size="48" />
          <div class="placeholder-text">图表功能开发中</div>
        </div>
      </van-cell-group>

      <!-- 收支趋势 -->
      <van-cell-group title="收支趋势" inset>
        <div class="chart-placeholder">
          <van-icon name="analytics-o" size="48" />
          <div class="placeholder-text">图表功能开发中</div>
        </div>
      </van-cell-group>
    </div>

    <!-- 分类统计 -->
    <van-cell-group title="分类统计" inset>
      <van-cell
        v-for="category in categoryStats"
        :key="category.name"
        :title="category.name"
        :value="formatAmount(category.amount)"
        :value-class="category.amount > 0 ? 'positive' : 'negative'"
      >
        <template #icon>
          <div class="category-icon">
            <van-icon :name="category.icon" />
          </div>
        </template>
        <template #right-icon>
          <div class="category-percent">
            {{ category.percent }}%
          </div>
        </template>
      </van-cell>
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { showToast } from 'vant'
import { getIncomeStatement, getMonthlySummary, getYearToDateSummary } from '@/api/reports'

const selectedPeriod = ref('thisMonth')
const overview = ref({
  income: 0,
  expense: 0,
  balance: 0
})
interface CategoryStat {
  name: string
  amount: number
  percent: number
  icon: string
}

const categoryStats = ref<CategoryStat[]>([])

const periodOptions = [
  { text: '本月', value: 'thisMonth' },
  { text: '上月', value: 'lastMonth' },
  { text: '本年', value: 'thisYear' },
  { text: '自定义', value: 'custom' }
]

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

const loadReportData = async () => {
  try {
    let apiCall
    
    // 根据选择的时期调用不同的API
    switch (selectedPeriod.value) {
      case 'thisMonth':
        const currentDate = new Date()
        apiCall = getMonthlySummary(currentDate.getFullYear(), currentDate.getMonth() + 1)
        break
      case 'lastMonth':
        const lastMonth = new Date()
        lastMonth.setMonth(lastMonth.getMonth() - 1)
        apiCall = getMonthlySummary(lastMonth.getFullYear(), lastMonth.getMonth() + 1)
        break
      case 'thisYear':
        apiCall = getYearToDateSummary(new Date().getFullYear())
        break
      default:
        // 默认使用本月数据
        apiCall = getMonthlySummary()
    }
    
    const response = await apiCall
    const reportData = response.data
    
    // 处理概览数据
    overview.value = {
      income: reportData.total_income || 0,
      expense: reportData.total_expenses || 0,
      balance: reportData.net_income || 0
    }
    
    // 处理分类统计数据
    const stats: CategoryStat[] = []
    
    // 处理支出账户
    if (reportData.expense_accounts) {
      const totalExpense = Math.abs(reportData.total_expenses || 0)
      reportData.expense_accounts.forEach((account: any) => {
        const amount = Math.abs(account.balance || 0)
        if (amount > 0) {
          stats.push({
            name: account.name.split(':').pop() || account.name, // 取账户名的最后部分
            amount: -amount,
            percent: totalExpense > 0 ? Number(((amount / totalExpense) * 100).toFixed(1)) : 0,
            icon: getCategoryIcon(account.name)
          })
        }
      })
    }
    
    // 处理收入账户
    if (reportData.income_accounts) {
      const totalIncome = reportData.total_income || 0
      reportData.income_accounts.forEach((account: any) => {
        const amount = account.balance || 0
        if (amount > 0) {
          stats.push({
            name: account.name.split(':').pop() || account.name,
            amount: amount,
            percent: totalIncome > 0 ? Number(((amount / totalIncome) * 100).toFixed(1)) : 0,
            icon: getCategoryIcon(account.name)
          })
        }
      })
    }
    
    // 按金额绝对值排序
    categoryStats.value = stats.sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
    
  } catch (error) {
    console.error('加载报表数据失败:', error)
    showToast('加载报表数据失败')
  }
}

// 根据账户名称获取合适的图标
const getCategoryIcon = (accountName: string): string => {
  const name = accountName.toLowerCase()
  if (name.includes('餐') || name.includes('food') || name.includes('restaurant')) {
    return 'restaurant-o'
  } else if (name.includes('交通') || name.includes('transport') || name.includes('travel')) {
    return 'location-o'
  } else if (name.includes('购物') || name.includes('shopping')) {
    return 'shopping-cart-o'
  } else if (name.includes('缴费') || name.includes('bill') || name.includes('utility')) {
    return 'bill-o'
  } else if (name.includes('工资') || name.includes('salary') || name.includes('income')) {
    return 'gold-coin-o'
  } else if (name.includes('房租') || name.includes('rent')) {
    return 'home-o'
  } else {
    return 'bill-o'
  }
}

watch(selectedPeriod, () => {
  loadReportData()
})

onMounted(() => {
  loadReportData()
})
</script>

<style scoped>
.h5-reports {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.time-filter {
  background-color: white;
  border-bottom: 1px solid #ebedf0;
}

.overview-cards {
  padding: 16px;
}

.overview-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.overview-card.income {
  border-left: 4px solid #07c160;
}

.overview-card.expense {
  border-left: 4px solid #ee0a24;
}

.card-value {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.overview-card.income .card-value {
  color: #07c160;
}

.overview-card.expense .card-value {
  color: #ee0a24;
}

.card-label {
  font-size: 12px;
  color: #969799;
}

.balance-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 16px;
  border-left: 4px solid #1989fa;
}

.balance-value {
  font-size: 24px;
  font-weight: bold;
  color: #1989fa;
  margin-bottom: 4px;
}

.balance-label {
  font-size: 14px;
  color: #969799;
}

.charts-section {
  padding: 0 16px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #969799;
}

.placeholder-text {
  margin-top: 8px;
  font-size: 14px;
}

.category-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f7f8fa;
  border-radius: 50%;
  margin-right: 12px;
}

.category-percent {
  font-size: 12px;
  color: #969799;
  margin-right: 8px;
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
</style>