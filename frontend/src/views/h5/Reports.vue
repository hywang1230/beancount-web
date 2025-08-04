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
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    overview.value = {
      income: 12000.00,
      expense: -8500.00,
      balance: 3500.00
    }
    
    categoryStats.value = [
      {
        name: '餐饮美食',
        amount: -2500.00,
        percent: 29.4,
        icon: 'restaurant-o'
      },
      {
        name: '交通出行',
        amount: -1200.00,
        percent: 14.1,
        icon: 'location-o'
      },
      {
        name: '购物消费',
        amount: -2800.00,
        percent: 32.9,
        icon: 'shopping-cart-o'
      },
      {
        name: '生活缴费',
        amount: -800.00,
        percent: 9.4,
        icon: 'bill-o'
      },
      {
        name: '工资收入',
        amount: 12000.00,
        percent: 100.0,
        icon: 'gold-coin-o'
      }
    ]
  } catch (error) {
    console.error('加载报表数据失败:', error)
    showToast('加载失败')
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