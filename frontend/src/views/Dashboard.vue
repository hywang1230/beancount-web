<template>
  <div class="page-container">
    <h1 class="page-title">仪表盘</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon assets">
              <el-icon><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatCurrency(balanceSheet?.total_assets || 0) }}</div>
              <div class="stat-label">总资产</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon liabilities">
              <el-icon><CreditCard /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatCurrency(balanceSheet?.total_liabilities || 0) }}</div>
              <div class="stat-label">总负债</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon net-worth">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatCurrency(balanceSheet?.net_worth || 0) }}</div>
              <div class="stat-label">净资产</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon income">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatCurrency(incomeStatement?.total_income || 0) }}</div>
              <div class="stat-label">本月收入</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :lg="8" :xl="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon expenses">
              <el-icon><ShoppingCart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatCurrency(incomeStatement?.total_expenses || 0) }}</div>
              <div class="stat-label">本月支出</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表区域 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>收支趋势</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              v-if="trendsOption" 
              :option="trendsOption" 
              style="height: 300px"
            />
            <div v-else class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>支出分类</span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              v-if="expensesPieOption" 
              :option="expensesPieOption" 
              style="height: 300px"
            />
            <div v-else class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近交易 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>最近交易</span>
          <el-button type="primary" @click="$router.push('/transactions')">
            查看全部
          </el-button>
        </div>
      </template>
      
      <el-table :data="recentTransactions" v-loading="loading">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="narration" label="摘要" min-width="200" />
        <el-table-column label="账户" min-width="180">
          <template #default="{ row }">
            <div v-for="posting in row.postings" :key="posting.account">
              {{ posting.account }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <div v-for="posting in row.postings" :key="posting.account">
              <span 
                v-if="posting.amount"
                :class="getAmountClass(posting.amount)"
              >
                {{ formatCurrency(posting.amount) }}
              </span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import {
  Wallet,
  CreditCard,
  TrendCharts,
  ShoppingCart,
  Loading,
  DataAnalysis
} from '@element-plus/icons-vue'

import { getBalanceSheet, getIncomeStatement, getTrends } from '@/api/reports'
import { getRecentTransactions } from '@/api/transactions'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const loading = ref(false)
const balanceSheet = ref<any>(null)
const incomeStatement = ref<any>(null)
const recentTransactions = ref<any[]>([])
const trendsData = ref<any>(null)

const trendsOption = ref<any>(null)
const expensesPieOption = ref<any>(null)

// 格式化货币
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 获取金额样式类
const getAmountClass = (amount: number) => {
  if (amount > 0) return 'amount-positive'
  if (amount < 0) return 'amount-negative'
  return 'amount-zero'
}

// 加载数据
const loadData = async () => {
  loading.value = true
  
  try {
    // 获取本月的开始和结束日期
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1
    const startDate = `${year}-${month.toString().padStart(2, '0')}-01`
    const endDate = `${year}-${month.toString().padStart(2, '0')}-${new Date(year, month, 0).getDate().toString().padStart(2, '0')}`
    
    // 并行加载数据
    const [balanceRes, incomeRes, recentRes, trendsRes] = await Promise.all([
      getBalanceSheet(),
      getIncomeStatement(startDate, endDate), // 获取本月收入支出
      getRecentTransactions(10),
      getTrends(6)
    ])
    
    balanceSheet.value = balanceRes
    incomeStatement.value = incomeRes
    recentTransactions.value = recentRes
    trendsData.value = trendsRes
    
    // 生成图表配置
    generateChartOptions()
    
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 生成图表配置
const generateChartOptions = () => {
  // 收支趋势图
  if (trendsData.value?.trends) {
    const periods = trendsData.value.trends.map((item: any) => item.period)
    const incomes = trendsData.value.trends.map((item: any) => item.total_income)
    const expenses = trendsData.value.trends.map((item: any) => Math.abs(item.total_expenses))
    
    trendsOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `${params[0].axisValue}<br/>`
          params.forEach((param: any) => {
            result += `${param.seriesName}: ${formatCurrency(param.value)}<br/>`
          })
          return result
        }
      },
      legend: {
        data: ['收入', '支出']
      },
      xAxis: {
        type: 'category',
        data: periods
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => formatCurrency(value)
        }
      },
      series: [
        {
          name: '收入',
          type: 'line',
          data: incomes,
          itemStyle: { color: '#67c23a' }
        },
        {
          name: '支出',
          type: 'line',
          data: expenses,
          itemStyle: { color: '#f56c6c' }
        }
      ]
    }
  }
  
  // 支出分类饼图
  if (incomeStatement.value?.expense_accounts) {
    const expenseData = incomeStatement.value.expense_accounts
      .filter((account: any) => Math.abs(account.balance) > 0)
      .map((account: any) => ({
        name: account.name.split(':').pop(),
        value: Math.abs(account.balance)
      }))
    
    expensesPieOption.value = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [
        {
          name: '支出分类',
          type: 'pie',
          radius: '70%',
          data: expenseData,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.assets {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.liabilities {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.income {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.expenses {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-icon.net-worth {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.chart-container {
  min-height: 300px;
}
</style> 