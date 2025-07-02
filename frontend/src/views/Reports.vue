<template>
  <div class="page-container">
    <h1 class="page-title">报表分析</h1>
    
    <!-- 报表类型选择 -->
    <el-card class="mb-4">
      <el-tabs v-model="activeTab" @tab-change="onTabChange">
        <el-tab-pane label="资产负债表" name="balance-sheet" />
        <el-tab-pane label="损益表" name="income-statement" />
        <el-tab-pane label="趋势分析" name="trends" />
        <el-tab-pane label="月度报告" name="monthly" />
      </el-tabs>
    </el-card>
    
    <!-- 资产负债表 -->
    <el-card v-if="activeTab === 'balance-sheet'" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>资产负债表</span>
          <el-date-picker
            v-model="asOfDate"
            type="date"
            placeholder="截止日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadBalanceSheet"
          />
        </div>
      </template>
      
      <el-row :gutter="20" v-if="balanceSheet">
        <!-- 资产 -->
        <el-col :span="8">
          <h3>资产</h3>
          <el-table :data="assetAccounts" size="small">
            <el-table-column prop="name" label="账户" />
            <el-table-column prop="balance" label="余额" align="right">
              <template #default="{ row }">
                <span class="amount-positive">{{ formatCurrency(row.balance) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="total-row">
            <strong>资产总计: {{ formatCurrency(balanceSheet.total_assets) }}</strong>
          </div>
        </el-col>
        
        <!-- 负债 -->
        <el-col :span="8">
          <h3>负债</h3>
          <el-table :data="liabilityAccounts" size="small">
            <el-table-column prop="name" label="账户" />
            <el-table-column prop="balance" label="余额" align="right">
              <template #default="{ row }">
                <span class="amount-negative">{{ formatCurrency(Math.abs(row.balance)) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="total-row">
            <strong>负债总计: {{ formatCurrency(Math.abs(balanceSheet.total_liabilities)) }}</strong>
          </div>
        </el-col>
        
        <!-- 权益 -->
        <el-col :span="8">
          <h3>所有者权益</h3>
          <el-table :data="equityAccounts" size="small">
            <el-table-column prop="name" label="账户" />
            <el-table-column prop="balance" label="余额" align="right">
              <template #default="{ row }">
                <span>{{ formatCurrency(row.balance) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="total-row">
            <strong>权益总计: {{ formatCurrency(balanceSheet.total_equity) }}</strong>
          </div>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- 损益表 -->
    <el-card v-if="activeTab === 'income-statement'" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>损益表</span>
          <el-date-picker
            v-model="periodRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadIncomeStatement"
          />
        </div>
      </template>
      
      <el-row :gutter="20" v-if="incomeStatement">
        <!-- 收入 -->
        <el-col :span="12">
          <h3>收入</h3>
          <el-table :data="incomeStatement.income_accounts" size="small">
            <el-table-column prop="name" label="账户">
              <template #default="{ row }">
                {{ row.name.replace('Income:', '') }}
              </template>
            </el-table-column>
            <el-table-column prop="balance" label="金额" align="right">
              <template #default="{ row }">
                <span class="amount-positive">{{ formatCurrency(Math.abs(row.balance)) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="total-row">
            <strong>收入总计: {{ formatCurrency(Math.abs(incomeStatement.total_income)) }}</strong>
          </div>
        </el-col>
        
        <!-- 支出 -->
        <el-col :span="12">
          <h3>支出</h3>
          <el-table :data="incomeStatement.expense_accounts" size="small">
            <el-table-column prop="name" label="账户">
              <template #default="{ row }">
                {{ row.name.replace('Expenses:', '') }}
              </template>
            </el-table-column>
            <el-table-column prop="balance" label="金额" align="right">
              <template #default="{ row }">
                <span class="amount-negative">{{ formatCurrency(Math.abs(row.balance)) }}</span>
              </template>
            </el-table-column>
          </el-table>
          <div class="total-row">
            <strong>支出总计: {{ formatCurrency(Math.abs(incomeStatement.total_expenses)) }}</strong>
          </div>
        </el-col>
      </el-row>
      
      <div class="net-income" v-if="incomeStatement">
        <h3>净收益: 
          <span :class="incomeStatement.net_income >= 0 ? 'amount-positive' : 'amount-negative'">
            {{ formatCurrency(incomeStatement.net_income) }}
          </span>
        </h3>
      </div>
    </el-card>
    
    <!-- 趋势分析 -->
    <el-card v-if="activeTab === 'trends'" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>收支趋势分析</span>
          <el-select v-model="trendsMonths" @change="loadTrends">
            <el-option label="最近6个月" :value="6" />
            <el-option label="最近12个月" :value="12" />
            <el-option label="最近24个月" :value="24" />
          </el-select>
        </div>
      </template>
      
      <div class="chart-container">
        <v-chart 
          v-if="trendsOption" 
          :option="trendsOption" 
          style="height: 400px"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

import { 
  getBalanceSheet, 
  getIncomeStatement, 
  getTrends 
} from '@/api/reports'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const loading = ref(false)
const activeTab = ref('balance-sheet')
const asOfDate = ref(new Date().toISOString().split('T')[0])
const periodRange = ref<[string, string] | null>(null)
const trendsMonths = ref(12)

const balanceSheet = ref<any>(null)
const incomeStatement = ref<any>(null)
const trendsData = ref<any>(null)
const trendsOption = ref<any>(null)

// 计算属性
const assetAccounts = computed(() => 
  balanceSheet.value?.accounts.filter((acc: any) => acc.account_type === 'Assets') || []
)

const liabilityAccounts = computed(() => 
  balanceSheet.value?.accounts.filter((acc: any) => acc.account_type === 'Liabilities') || []
)

const equityAccounts = computed(() => 
  balanceSheet.value?.accounts.filter((acc: any) => acc.account_type === 'Equity') || []
)

// 格式化货币
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 加载资产负债表
const loadBalanceSheet = async () => {
  loading.value = true
  try {
    balanceSheet.value = await getBalanceSheet(asOfDate.value)
  } catch (error) {
    console.error('加载资产负债表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载损益表
const loadIncomeStatement = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = periodRange.value || []
    incomeStatement.value = await getIncomeStatement(startDate, endDate)
  } catch (error) {
    console.error('加载损益表失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载趋势数据
const loadTrends = async () => {
  loading.value = true
  try {
    trendsData.value = await getTrends(trendsMonths.value)
    generateTrendsChart()
  } catch (error) {
    console.error('加载趋势数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 生成趋势图表
const generateTrendsChart = () => {
  if (!trendsData.value?.trends) return
  
  const periods = trendsData.value.trends.map((item: any) => item.period)
  const incomes = trendsData.value.trends.map((item: any) => Math.abs(item.total_income))
  const expenses = trendsData.value.trends.map((item: any) => Math.abs(item.total_expenses))
  const netIncomes = trendsData.value.trends.map((item: any) => item.net_income)
  
  trendsOption.value = {
    title: {
      text: '收支趋势分析'
    },
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
      data: ['收入', '支出', '净收益']
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
      },
      {
        name: '净收益',
        type: 'line',
        data: netIncomes,
        itemStyle: { color: '#409eff' }
      }
    ]
  }
}

// 标签页切换
const onTabChange = (tabName: string) => {
  switch (tabName) {
    case 'balance-sheet':
      loadBalanceSheet()
      break
    case 'income-statement':
      loadIncomeStatement()
      break
    case 'trends':
      loadTrends()
      break
  }
}

onMounted(() => {
  loadBalanceSheet()
})
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.total-row {
  margin-top: 12px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
  text-align: right;
}

.net-income {
  margin-top: 24px;
  padding: 16px;
  background-color: #f0f9ff;
  border-radius: 8px;
  text-align: center;
}

.chart-container {
  min-height: 400px;
}
</style> 