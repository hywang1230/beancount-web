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
              <span v-if="selectedCategory" class="selected-category">
                已选择: {{ selectedCategory }}
              </span>
            </div>
          </template>
          <div class="chart-container">
            <v-chart 
              v-if="expensesPieOption" 
              :option="expensesPieOption" 
              style="height: 300px"
              @click="onPieChartClick"
            />
            <div v-else class="loading-container">
              <el-icon class="is-loading"><Loading /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 分类支出明细 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>
            {{ selectedCategory ? `${selectedCategory} 支出明细` : '支出明细' }}
          </span>
          <div class="header-actions">
            <el-button 
              v-if="selectedCategory" 
              @click="clearSelection"
              size="small"
            >
              清除选择
            </el-button>
            <el-button type="primary" @click="$router.push('/transactions')">
              查看全部
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="!selectedCategory" class="no-selection">
        <el-empty description="点击上方支出分类饼图查看对应的交易明细" />
      </div>
      
      <el-table 
        v-else
        :data="categoryTransactions" 
        v-loading="transactionLoading"
        max-height="400"
      >
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="payee" label="收付方" width="140">
          <template #default="{ row }">
            <span v-if="row.payee" class="payee-text">{{ row.payee }}</span>
            <span v-else class="no-payee">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="narration" label="摘要" min-width="180" />
        <el-table-column label="账户" min-width="160">
          <template #default="{ row }">
            <div v-for="posting in row.postings" :key="posting.account">
              <span 
                :class="{ 'highlight-account': posting.account.includes(selectedAccountName) }"
              >
                {{ posting.account }}
              </span>
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
import { getTransactions, type TransactionFilter } from '@/api/transactions'

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
const transactionLoading = ref(false)
const balanceSheet = ref<any>(null)
const incomeStatement = ref<any>(null)
const trendsData = ref<any>(null)
const selectedCategory = ref<string>('')
const selectedAccountName = ref<string>('')
const categoryTransactions = ref<any[]>([])

const trendsOption = ref<any>(null)
const expensesPieOption = ref<any>(null)

// 当前月份的日期范围
const getCurrentMonthRange = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const startDate = `${year}-${month.toString().padStart(2, '0')}-01`
  const endDate = `${year}-${month.toString().padStart(2, '0')}-${new Date(year, month, 0).getDate().toString().padStart(2, '0')}`
  return { startDate, endDate }
}

// 格式化货币
const formatCurrency = (amount: string | number) => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(numAmount)
}

// 获取金额样式类
const getAmountClass = (amount: string | number) => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  if (numAmount > 0) return 'amount-positive'
  if (numAmount < 0) return 'amount-negative'
  return 'amount-zero'
}

// 饼图点击事件
const onPieChartClick = async (params: any) => {
  if (params.data) {
    selectedCategory.value = params.data.name
    selectedAccountName.value = params.data.fullAccountName || params.data.name
    await loadCategoryTransactions()
  }
}

// 清除选择
const clearSelection = () => {
  selectedCategory.value = ''
  selectedAccountName.value = ''
  categoryTransactions.value = []
}

// 加载分类交易明细
const loadCategoryTransactions = async () => {
  if (!selectedAccountName.value) return
  
  transactionLoading.value = true
  
  try {
    const { startDate, endDate } = getCurrentMonthRange()
    
    // 获取该月的所有交易
    const response = await getTransactions({
      start_date: startDate,
      end_date: endDate,
      page_size: 200
    })
    
    // 筛选包含选中账户的交易
    const filteredTransactions = response.data.filter(transaction => 
      transaction.postings?.some((posting: any) => 
        posting.account && posting.account.includes(selectedAccountName.value)
      )
    )
    
    categoryTransactions.value = filteredTransactions.slice(0, 50) // 限制显示50条
    
  } catch (error) {
    console.error('加载分类交易失败:', error)
    categoryTransactions.value = []
  } finally {
    transactionLoading.value = false
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  
  try {
    const { startDate, endDate } = getCurrentMonthRange()
    
    // 并行加载数据
    const [balanceRes, incomeRes, trendsRes] = await Promise.all([
      getBalanceSheet(),
      getIncomeStatement(startDate, endDate), // 获取本月收入支出
      getTrends(6)
    ])
    
    balanceSheet.value = balanceRes
    incomeStatement.value = incomeRes
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
        fullAccountName: account.name,
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

.selected-category {
  font-size: 12px;
  color: #409eff;
  background: #ecf5ff;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.no-selection {
  padding: 40px 0;
}

.highlight-account {
  background: #f0f9ff;
  color: #409eff;
  padding: 2px 4px;
  border-radius: 4px;
  font-weight: 500;
}

.amount-positive {
  color: #67c23a;
  font-weight: 500;
}

.amount-negative {
  color: #f56c6c;
  font-weight: 500;
}

.amount-zero {
  color: #909399;
}

.payee-text {
  color: #606266;
  font-weight: 500;
}

.no-payee {
  color: #c0c4cc;
  font-style: italic;
}
</style> 