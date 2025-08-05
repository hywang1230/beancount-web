<template>
  <div class="h5-reports">
    <!-- 报表类型选择 -->
    <van-sticky>
      <div class="report-type-selector">
        <van-tabs v-model:active="activeTab" @change="onTabChange" swipeable>
          <van-tab title="资产负债表" name="balance-sheet" />
          <van-tab title="损益表" name="income-statement" />
          <van-tab title="趋势分析" name="trends" />
          <van-tab title="月度报告" name="monthly" />
        </van-tabs>
      </div>
    </van-sticky>

    <!-- 资产负债表 -->
    <div v-if="activeTab === 'balance-sheet'" class="report-content">
      <!-- 日期选择 -->
      <div class="date-selector">
        <van-cell-group inset>
          <van-field
            v-model="asOfDate"
            type="date"
            label="截止日期"
            placeholder="选择截止日期"
            @change="loadBalanceSheet"
          />
        </van-cell-group>
      </div>

      <!-- 资产负债表内容 -->
      <div v-if="balanceSheet" class="balance-sheet">
        <!-- 资产 -->
        <van-cell-group title="资产" inset>
          <van-collapse v-model="assetExpandedItems">
            <van-collapse-item 
              v-for="category in groupedAssetCategories" 
              :key="category.name"
              :name="category.name"
              :title="category.name"
              :value="formatCurrency(category.total)"
            >
              <div class="account-list">
                <template v-for="account in category.accounts" :key="account.fullName">
                  <!-- 如果是子分组，显示为可折叠的子分组 -->
                  <div v-if="account.isSubGroup" class="sub-group">
                    <van-collapse v-model="subGroupExpandedItems">
                      <van-collapse-item 
                        :name="account.fullName"
                        :title="account.name"
                        :value="formatCurrency(account.balance)"
                        
                      >
                        <div class="sub-account-list">
                          <div 
                            v-for="subAccount in account.subAccounts" 
                            :key="subAccount.fullName"
                            class="sub-account-item"
                          >
                            <span class="account-name">{{ subAccount.name }}</span>
                            <span class="account-amount">{{ formatCurrency(subAccount.balance) }}</span>
                          </div>
                        </div>
                      </van-collapse-item>
                    </van-collapse>
                  </div>
                  <!-- 普通账户直接显示 -->
                  <div v-else class="account-item">
                    <span class="account-name">{{ account.name }}</span>
                    <span class="account-amount">{{ formatCurrency(account.balance) }}</span>
                  </div>
                </template>
              </div>
            </van-collapse-item>
          </van-collapse>
          <div class="total-row">
            <span class="total-label">资产总计</span>
            <span class="total-amount">{{ formatCurrency(balanceSheet.total_assets) }}</span>
          </div>
        </van-cell-group>

        <!-- 负债 -->
        <van-cell-group title="负债" inset>
          <van-collapse v-model="liabilityExpandedItems">
            <van-collapse-item 
              v-for="category in groupedLiabilityCategories" 
              :key="category.name"
              :name="category.name"
              :title="category.name"
              :value="formatCurrency(category.total)"
            >
              <div class="account-list">
                <template v-for="account in category.accounts" :key="account.fullName">
                  <!-- 如果是子分组，显示为可折叠的子分组 -->
                  <div v-if="account.isSubGroup" class="sub-group">
                    <van-collapse v-model="subGroupExpandedItems">
                      <van-collapse-item 
                        :name="account.fullName"
                        :title="account.name"
                        :value="formatCurrency(Math.abs(account.balance))"
                      >
                        <div class="sub-account-list">
                          <div 
                            v-for="subAccount in account.subAccounts" 
                            :key="subAccount.fullName"
                            class="sub-account-item"
                          >
                            <span class="account-name">{{ subAccount.name }}</span>
                            <span class="account-amount">{{ formatCurrency(Math.abs(subAccount.balance)) }}</span>
                          </div>
                        </div>
                      </van-collapse-item>
                    </van-collapse>
                  </div>
                  <!-- 普通账户直接显示 -->
                  <div v-else class="account-item">
                    <span class="account-name">{{ formatAccountName(account.name) }}</span>
                    <span class="account-amount">{{ formatCurrency(Math.abs(account.balance)) }}</span>
                  </div>
                </template>
              </div>
            </van-collapse-item>
          </van-collapse>
          <div class="total-row">
            <span class="total-label">负债总计</span>
            <span class="total-amount">{{ formatCurrency(Math.abs(balanceSheet.total_liabilities)) }}</span>
          </div>
        </van-cell-group>

        <!-- 所有者权益 -->
        <van-cell-group title="所有者权益" inset>
          <van-collapse v-model="equityExpandedItems">
            <van-collapse-item 
              v-for="category in groupedEquityCategories" 
              :key="category.name"
              :name="category.name"
              :title="category.name"
              :value="formatCurrency(category.total)"
            >
              <div class="account-list">
                <template v-for="account in category.accounts" :key="account.fullName">
                  <!-- 如果是子分组，显示为可折叠的子分组 -->
                  <div v-if="account.isSubGroup" class="sub-group">
                    <van-collapse v-model="subGroupExpandedItems">
                      <van-collapse-item 
                        :name="account.fullName"
                        :title="account.name"
                        :value="formatCurrency(account.balance)"
                        
                      >
                        <div class="sub-account-list">
                          <div 
                            v-for="subAccount in account.subAccounts" 
                            :key="subAccount.fullName"
                            class="sub-account-item"
                          >
                            <span class="account-name">{{ subAccount.name }}</span>
                            <span class="account-amount">{{ formatCurrency(subAccount.balance) }}</span>
                          </div>
                        </div>
                      </van-collapse-item>
                    </van-collapse>
                  </div>
                  <!-- 普通账户直接显示 -->
                  <div v-else class="account-item">
                    <span class="account-name">{{ account.name }}</span>
                    <span class="account-amount">{{ formatCurrency(account.balance) }}</span>
                  </div>
                </template>
              </div>
            </van-collapse-item>
          </van-collapse>
          <div class="total-row">
            <span class="total-label">所有者权益总计</span>
            <span class="total-amount">{{ formatCurrency(balanceSheet.total_equity) }}</span>
          </div>
        </van-cell-group>
      </div>
    </div>

    <!-- 损益表 -->
    <div v-if="activeTab === 'income-statement'" class="report-content">
      <!-- 日期范围选择 -->
      <div class="date-range-selector">
        <van-cell-group inset>
          <van-field
            v-model="startDate"
            type="date"
            label="开始日期"
            placeholder="选择开始日期"
            @change="onStartDateChange"
          />
          <van-field
            v-model="endDate"
            type="date"
            label="结束日期"
            placeholder="选择结束日期"
            @change="onEndDateChange"
          />
        </van-cell-group>
      </div>

      <!-- 损益表内容 -->
      <div v-if="incomeStatement" class="income-statement">
        <!-- 收入 -->
        <van-cell-group title="收入" inset>
          <van-collapse v-model="incomeExpandedItems">
            <van-collapse-item 
              v-for="category in groupedIncomeCategories" 
              :key="category.name"
              :name="category.name"
              :title="category.name"
              :value="formatCurrency(category.total)"
            >
              <div class="account-list">
                <div 
                  v-for="account in category.accounts" 
                  :key="account.name"
                  class="account-item"
                >
                  <span class="account-name">{{ formatAccountName(account.name) }}</span>
                  <span class="account-amount positive">{{ formatCurrency(Math.abs(account.balance)) }}</span>
                </div>
              </div>
            </van-collapse-item>
          </van-collapse>
          <div class="total-row">
            <span class="total-label">收入总计</span>
            <span class="total-amount positive">{{ formatCurrency(Math.abs(incomeStatement.total_income)) }}</span>
          </div>
        </van-cell-group>

        <!-- 支出 -->
        <van-cell-group title="支出" inset>
          <van-collapse v-model="expenseExpandedItems">
            <van-collapse-item 
              v-for="category in groupedExpenseCategories" 
              :key="category.name"
              :name="category.name"
              :title="category.name"
              :value="formatCurrency(category.total)"
            >
              <div class="account-list">
                <div 
                  v-for="account in category.accounts" 
                  :key="account.name"
                  class="account-item"
                >
                  <span class="account-name">{{ formatAccountName(account.name) }}</span>
                  <span class="account-amount negative">{{ formatCurrency(Math.abs(account.balance)) }}</span>
                </div>
              </div>
            </van-collapse-item>
          </van-collapse>
          <div class="total-row">
            <span class="total-label">支出总计</span>
            <span class="total-amount negative">{{ formatCurrency(Math.abs(incomeStatement.total_expenses)) }}</span>
          </div>
        </van-cell-group>

        <!-- 净收益 -->
        <van-cell-group title="汇总" inset>
          <div class="net-income-card">
            <div class="net-income-value" :class="incomeStatement.net_income >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(incomeStatement.net_income) }}
            </div>
            <div class="net-income-label">净收益</div>
          </div>
        </van-cell-group>
      </div>
    </div>

    <!-- 趋势分析 -->
    <div v-if="activeTab === 'trends'" class="report-content">
      <!-- 时间范围选择 -->
      <div class="trends-selector">
        <van-cell-group inset>
          <van-cell 
            title="统计周期" 
            :value="trendsOptions.find((opt: any) => opt.value === trendsMonths)?.text" 
            is-link 
            @click="showTrendsPicker = true"
          />
        </van-cell-group>
      </div>

      <!-- 趋势图表 -->
      <div v-if="trendsOption" class="trends-chart">
        <van-cell-group title="收支趋势" inset>
          <div class="chart-container">
            <v-chart :option="trendsOption" style="height: 300px;" />
          </div>
        </van-cell-group>
      </div>
    </div>

    <!-- 月度报告 -->
    <div v-if="activeTab === 'monthly'" class="report-content">
      <!-- 年月选择 -->
      <div class="monthly-selector">
        <van-cell-group inset>
          <van-cell 
            title="年份" 
            :value="`${selectedYear}年`" 
            is-link 
            @click="showYearPicker = true"
          />
          <van-cell 
            title="月份" 
            :value="`${selectedMonth}月`" 
            is-link 
            @click="showMonthPicker = true"
          />
        </van-cell-group>
      </div>

      <!-- 月度汇总 -->
      <div v-if="monthlySummary" class="monthly-summary">
        <!-- 概览卡片 -->
        <div class="summary-cards">
          <van-row gutter="8">
            <van-col span="12">
              <div class="summary-card income">
                <div class="card-value">{{ formatCurrency(monthlySummary.income_statement.total_income) }}</div>
                <div class="card-label">本月收入</div>
              </div>
            </van-col>
            <van-col span="12">
              <div class="summary-card expense">
                <div class="card-value">{{ formatCurrency(Math.abs(monthlySummary.income_statement.total_expenses)) }}</div>
                <div class="card-label">本月支出</div>
              </div>
            </van-col>
          </van-row>
          <div class="net-card">
            <div class="net-value" :class="monthlySummary.income_statement.net_income >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(monthlySummary.income_statement.net_income) }}
            </div>
            <div class="net-label">本月净收益</div>
          </div>
          <div class="assets-card">
            <div class="assets-value">{{ formatCurrency(monthlySummary.balance_sheet.total_assets) }}</div>
            <div class="assets-label">月末总资产</div>
          </div>
        </div>

        <!-- 年度至今汇总 -->
        <div v-if="yearToDateSummary" class="ytd-summary">
          <van-cell-group :title="`${selectedYear}年度至今汇总`" inset>
            <van-cell 
              title="累计收入" 
              :value="formatCurrency(yearToDateSummary.income_statement.total_income)"
              value-class="positive"
            />
            <van-cell 
              title="累计支出" 
              :value="formatCurrency(Math.abs(yearToDateSummary.income_statement.total_expenses))"
              value-class="negative"
            />
            <van-cell 
              title="累计净收益" 
              :value="formatCurrency(yearToDateSummary.income_statement.net_income)"
              :value-class="yearToDateSummary.income_statement.net_income >= 0 ? 'positive' : 'negative'"
            />
          </van-cell-group>
        </div>

        <!-- 月度明细 -->
        <van-cell-group :title="`${selectedMonth}月收入明细`" inset>
          <van-cell 
            v-for="account in sortedMonthlyIncomeAccounts" 
            :key="account.name"
            :title="formatAccountName(account.name.replace('Income:', ''))"
            :value="formatCurrency(Math.abs(account.balance))"
            value-class="positive"
          />
        </van-cell-group>

        <van-cell-group :title="`${selectedMonth}月支出明细`" inset>
          <van-cell 
            v-for="account in sortedMonthlyExpenseAccounts" 
            :key="account.name"
            :title="formatAccountName(account.name.replace('Expenses:', ''))"
            :value="formatCurrency(Math.abs(account.balance))"
            value-class="negative"
          />
        </van-cell-group>
      </div>
    </div>





    <van-popup v-model:show="showTrendsPicker" position="bottom">
      <van-picker
        :columns="trendsOptions"
        @confirm="onTrendsConfirm"
        @cancel="showTrendsPicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showYearPicker" position="bottom">
      <van-picker
        :columns="yearOptions"
        @confirm="onYearConfirm"
        @cancel="showYearPicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showMonthPicker" position="bottom">
      <van-picker
        :columns="monthOptions"
        @confirm="onMonthConfirm"
        @cancel="showMonthPicker = false"
      />
    </van-popup>

    <!-- 加载状态 -->
    <van-loading v-if="loading" type="spinner" vertical>加载中...</van-loading>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { showToast } from 'vant'
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
  getTrends,
  getMonthlySummary,
  getYearToDateSummary
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

// 基础数据
const loading = ref(false)
const activeTab = ref('balance-sheet')

// 资产负债表相关
const asOfDate = ref(new Date().toLocaleDateString('en-CA')) // 格式: YYYY-MM-DD
const balanceSheet = ref<any>(null)
const assetExpandedItems = ref<string[]>([])
const liabilityExpandedItems = ref<string[]>([])
const equityExpandedItems = ref<string[]>([])
const subGroupExpandedItems = ref<string[]>([]) // 子分组展开状态

// 损益表相关
const today = new Date()
const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1) // 本月第一天
const startDate = ref(thisMonthStart.toLocaleDateString('en-CA')) // 格式: YYYY-MM-DD
const endDate = ref(today.toLocaleDateString('en-CA')) // 今天
const incomeStatement = ref<any>(null)
const incomeExpandedItems = ref<string[]>([])
const expenseExpandedItems = ref<string[]>([])

// 趋势分析相关
const trendsMonths = ref(12)
const trendsData = ref<any>(null)
const trendsOption = ref<any>(null)

// 月度报告相关
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)
const monthlySummary = ref<any>(null)
const yearToDateSummary = ref<any>(null)

// 日期选择器相关
const showTrendsPicker = ref(false)
const showYearPicker = ref(false)
const showMonthPicker = ref(false)

// 选择器选项
const trendsOptions = [
  { text: '最近6个月', value: 6 },
  { text: '最近12个月', value: 12 },
  { text: '最近24个月', value: 24 }
]

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 5; i--) {
    years.push({ text: `${i}年`, value: i })
  }
  return years
})

const monthOptions = [
  { text: '1月', value: 1 },
  { text: '2月', value: 2 },
  { text: '3月', value: 3 },
  { text: '4月', value: 4 },
  { text: '5月', value: 5 },
  { text: '6月', value: 6 },
  { text: '7月', value: 7 },
  { text: '8月', value: 8 },
  { text: '9月', value: 9 },
  { text: '10月', value: 10 },
  { text: '11月', value: 11 },
  { text: '12月', value: 12 }
]

// 格式化货币
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

// 格式化账户名称 - 去掉字母前缀和连字符，但保持层级
const formatAccountName = (accountName: string) => {
  if (!accountName) return '未知账户'
  
  // 处理单个名称段：去掉字母前缀和连字符
  const dashIndex = accountName.indexOf('-')
  if (dashIndex > 0) {
    return accountName.substring(dashIndex + 1)
  }
  return accountName
}

// 格式化分类名称
const formatCategoryName = (categoryName: string) => {
  return formatAccountName(categoryName)
}

// 分组账户数据
const groupedAssetCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return []
  
  const assetAccounts = balanceSheet.value.accounts.filter((acc: any) => acc.account_type === 'Assets')
  return groupAccountsByCategory(assetAccounts, 'Assets')
})

const groupedLiabilityCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return []
  
  const liabilityAccounts = balanceSheet.value.accounts.filter((acc: any) => acc.account_type === 'Liabilities')
  return groupAccountsByCategory(liabilityAccounts, 'Liabilities')
})

const groupedEquityCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return []
  
  const equityAccounts = balanceSheet.value.accounts.filter((acc: any) => acc.account_type === 'Equity')
  return groupAccountsByCategory(equityAccounts, 'Equity')
})

const groupedIncomeCategories = computed(() => {
  if (!incomeStatement.value?.income_accounts) return []
  return groupAccountsByCategory(incomeStatement.value.income_accounts, 'Income')
})

const groupedExpenseCategories = computed(() => {
  if (!incomeStatement.value?.expense_accounts) return []
  return groupAccountsByCategory(incomeStatement.value.expense_accounts, 'Expenses')
})

// 月度收入支出账户排序
const sortedMonthlyIncomeAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.income_accounts) return []
  return [...monthlySummary.value.income_statement.income_accounts].sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
})

const sortedMonthlyExpenseAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.expense_accounts) return []
  return [...monthlySummary.value.income_statement.expense_accounts].sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
})

// 按分类分组账户，支持层级结构
const groupAccountsByCategory = (accounts: any[], _prefix: string) => {
  const categories: { [key: string]: any } = {}
  
  // 调试：打印账户数据
  console.log('账户数据:', accounts.map(acc => ({ name: acc.name, balance: acc.balance })))
  
  accounts.forEach(account => {
    const parts = account.name.split(':')
    console.log(`处理账户: ${account.name}, parts:`, parts)
    
    let categoryName = '其他'
    
    if (parts.length > 1) {
      categoryName = parts[1] // 取第二级作为分类名
    }
    
    if (!categories[categoryName]) {
      categories[categoryName] = {
        accounts: [],
        subGroups: {}
      }
    }
    
    // 从第三级开始构建子层级
    const remainingParts = parts.slice(2)
    console.log(`  remainingParts:`, remainingParts)
    
    if (remainingParts.length === 0) {
      // 如果没有更多层级，直接添加到accounts中
      categories[categoryName].accounts.push({
        name: formatAccountName(account.name.split(':').pop() || ''),
        balance: account.balance,
        fullName: account.name
      })
    } else if (remainingParts.length === 1) {
      // 只有一级子账户，直接添加
      categories[categoryName].accounts.push({
        name: formatAccountName(remainingParts[0]),
        balance: account.balance,
        fullName: account.name
      })
    } else {
      // 有多级子账户，按第一级分组
      const subGroupName = remainingParts[0]
      console.log(`  创建子分组: ${subGroupName}`)
      
      if (!categories[categoryName].subGroups[subGroupName]) {
        categories[categoryName].subGroups[subGroupName] = []
      }
      
      // 剩余的层级作为子账户名称
      const finalAccountName = remainingParts.slice(1).map((part: string) => formatAccountName(part)).join('-')
      console.log(`  子账户名称: ${finalAccountName}`)
      
      categories[categoryName].subGroups[subGroupName].push({
        name: finalAccountName,
        balance: account.balance,
        fullName: account.name
      })
    }
  })
  
  // 构建最终的分类结构
  return Object.keys(categories).map(categoryName => {
    const category = categories[categoryName]
    const allAccounts = [...category.accounts]
    
    // 添加子分组
    Object.keys(category.subGroups).forEach(subGroupName => {
      const subGroupAccounts = category.subGroups[subGroupName]
      const subGroupTotal = subGroupAccounts.reduce((sum: number, acc: any) => sum + Math.abs(acc.balance), 0)
      
      // 为子分组创建一个汇总账户
      allAccounts.push({
        name: formatAccountName(subGroupName),
        balance: subGroupTotal,
        fullName: `${categoryName}-${subGroupName}`,
        isSubGroup: true,
        subAccounts: subGroupAccounts
      })
    })
    
    const result = {
      name: formatCategoryName(categoryName),
      accounts: allAccounts,
      total: allAccounts.reduce((sum, acc) => sum + Math.abs(acc.balance), 0)
    }
    
    // 调试：打印分组结果
    console.log(`分类 ${categoryName}:`, allAccounts.map(acc => ({
      name: acc.name,
      isSubGroup: acc.isSubGroup,
      subAccounts: acc.subAccounts?.length || 0
    })))
    
    return result
  })
}

// 加载资产负债表
const loadBalanceSheet = async () => {
  loading.value = true
  try {
    balanceSheet.value = await getBalanceSheet(asOfDate.value)
  } catch (error) {
    console.error('加载资产负债表失败:', error)
    showToast('加载资产负债表失败')
  } finally {
    loading.value = false
  }
}

// 加载损益表
const loadIncomeStatement = async () => {
  loading.value = true
  try {
    if (startDate.value && endDate.value) {
      incomeStatement.value = await getIncomeStatement(startDate.value, endDate.value)
    }
  } catch (error) {
    console.error('加载损益表失败:', error)
    showToast('加载损益表失败')
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
    showToast('加载趋势数据失败')
  } finally {
    loading.value = false
  }
}

// 生成趋势图表
const generateTrendsChart = () => {
  if (!trendsData.value?.trends) return
  
  const periods = trendsData.value.trends.map((item: any) => item.period)
  const incomes = trendsData.value.trends.map((item: any) => item.total_income)
  const expenses = trendsData.value.trends.map((item: any) => Math.abs(item.total_expenses))
  const netIncomes = trendsData.value.trends.map((item: any) => item.net_income)
  
  trendsOption.value = {
    title: {
      text: '收支趋势分析',
      textStyle: {
        fontSize: 14
      }
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
      data: ['收入', '支出', '净收益'],
      bottom: 0,
      textStyle: {
        fontSize: 12
      }
    },
    grid: {
      top: 40,
      bottom: 60,
      left: 10,
      right: 10,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: periods,
      axisLabel: {
        fontSize: 10,
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 10,
        formatter: (value: number) => {
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + '万'
          }
          return value.toString()
        }
      }
    },
    series: [
      {
        name: '收入',
        type: 'line',
        data: incomes,
        itemStyle: { color: '#07c160' },
        lineStyle: { width: 2 }
      },
      {
        name: '支出',
        type: 'line',
        data: expenses,
        itemStyle: { color: '#ee0a24' },
        lineStyle: { width: 2 }
      },
      {
        name: '净收益',
        type: 'line',
        data: netIncomes,
        itemStyle: { color: '#1989fa' },
        lineStyle: { width: 2 }
      }
    ]
  }
}

// 加载月度报告
const loadMonthlyReport = async () => {
  loading.value = true
  try {
    const [monthlyRes, ytdRes] = await Promise.all([
      getMonthlySummary(selectedYear.value, selectedMonth.value),
      getYearToDateSummary(selectedYear.value)
    ])
    monthlySummary.value = monthlyRes
    yearToDateSummary.value = ytdRes
  } catch (error) {
    console.error('加载月度报告失败:', error)
    showToast('加载月度报告失败')
  } finally {
    loading.value = false
  }
}

// 标签页切换处理
const onTabChange = (tabName: string) => {
  switch (tabName) {
    case 'balance-sheet':
      loadBalanceSheet()
      break
    case 'income-statement':
      if (startDate.value && endDate.value) {
        loadIncomeStatement()
      }
      break
    case 'trends':
      loadTrends()
      break
    case 'monthly':
      loadMonthlyReport()
      break
  }
}



// 损益表日期变化处理
const onStartDateChange = (value: string) => {
  startDate.value = value
  if (startDate.value && endDate.value) {
    loadIncomeStatement()
  }
}

const onEndDateChange = (value: string) => {
  endDate.value = value
  if (startDate.value && endDate.value) {
    loadIncomeStatement()
  }
}

const onTrendsConfirm = ({ selectedOptions }: any) => {
  trendsMonths.value = selectedOptions[0].value
  showTrendsPicker.value = false
  loadTrends()
}

const onYearConfirm = ({ selectedOptions }: any) => {
  selectedYear.value = selectedOptions[0].value
  showYearPicker.value = false
  loadMonthlyReport()
}

const onMonthConfirm = ({ selectedOptions }: any) => {
  selectedMonth.value = selectedOptions[0].value
  showMonthPicker.value = false
  loadMonthlyReport()
}

onMounted(() => {
  // 默认加载资产负债表
  loadBalanceSheet()
})
</script>

<style scoped>
.h5-reports {
  background-color: #f7f8fa;
  min-height: 100vh;
  padding-bottom: 20px;
}

/* 报表类型选择器 */
.report-type-selector {
  background-color: white;
  border-bottom: 1px solid #ebedf0;
}

/* 报表内容区域 */
.report-content {
  padding-bottom: 60px;
}

/* 日期选择器 */
.date-selector,
.date-range-selector,
.trends-selector,
.monthly-selector {
  margin-bottom: 16px;
}

/* 资产负债表样式 */
.balance-sheet {
  padding: 0;
}

.account-list {
  padding: 0;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.account-item:last-child {
  border-bottom: none;
}

.account-name {
  flex: 1;
  color: #323233;
}

.account-amount {
  color: #646566;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

/* 子分组样式 */
.sub-group {
  margin-bottom: 8px;
}

.sub-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background-color: #f7f8fa;
  border-bottom: 1px solid #ebedf0;
  font-weight: 500;
}

.sub-group-name {
  flex: 1;
  color: #323233;
  font-size: 14px;
}

.sub-group-amount {
  color: #646566;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  font-weight: 600;
}

.sub-account-list {
  background-color: #ffffff;
}

.sub-account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px 8px 32px; /* 左侧增加缩进表示层级 */
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.sub-account-item:last-child {
  border-bottom: none;
}

/* 子分组折叠样式 */
.sub-group-collapse {
  margin: 0;
}

.sub-group-collapse :deep(.van-collapse-item__title) {
  background-color: #f7f8fa;
  font-size: 14px;
  font-weight: 500;
  padding: 10px 16px;
}

.sub-group-collapse :deep(.van-collapse-item__content) {
  padding: 0;
  background-color: #ffffff;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: #f8f9fa;
  border-top: 1px solid #ebedf0;
  font-weight: 600;
  color: #323233;
}

.total-label {
  font-size: 14px;
}

.total-amount {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
}

/* 损益表样式 */
.income-statement {
  padding: 0;
}

.net-income-card {
  padding: 20px;
  text-align: center;
  background-color: white;
  margin: 16px;
  border-radius: 8px;
  border-left: 4px solid #1989fa;
}

.net-income-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.net-income-label {
  font-size: 14px;
  color: #969799;
}

/* 趋势分析样式 */
.trends-chart {
  margin-top: 16px;
}

.chart-container {
  padding: 16px;
  background-color: white;
}

/* 月度报告样式 */
.monthly-summary {
  padding: 0;
}

.summary-cards {
  padding: 16px;
}

.summary-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-bottom: 8px;
}

.summary-card.income {
  border-left: 4px solid #07c160;
}

.summary-card.expense {
  border-left: 4px solid #ee0a24;
}

.card-value {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.summary-card.income .card-value {
  color: #07c160;
}

.summary-card.expense .card-value {
  color: #ee0a24;
}

.card-label {
  font-size: 12px;
  color: #969799;
}

.net-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 8px;
  border-left: 4px solid #1989fa;
}

.net-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.net-label {
  font-size: 12px;
  color: #969799;
}

.assets-card {
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 8px;
  border-left: 4px solid #909399;
}

.assets-value {
  font-size: 18px;
  font-weight: bold;
  color: #909399;
  margin-bottom: 4px;
}

.assets-label {
  font-size: 12px;
  color: #969799;
}

.ytd-summary {
  margin-top: 16px;
}

/* 通用样式 */
:deep(.van-cell-group--inset) {
  margin: 16px;
}

:deep(.van-cell-group__title) {
  padding-left: 16px;
  font-weight: 600;
  color: #323233;
}

:deep(.van-collapse-item__content) {
  padding: 0;
}

:deep(.van-collapse-item__title) {
  font-weight: 500;
}

:deep(.van-tabs__line) {
  background-color: #1989fa;
}

:deep(.van-tab--active) {
  color: #1989fa;
}

:deep(.positive) {
  color: #07c160 !important;
  font-weight: 500;
}

:deep(.negative) {
  color: #ee0a24 !important;
  font-weight: 500;
}

/* 加载状态 */
:deep(.van-loading) {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 999;
}

/* 移动端优化 */
@media (max-width: 375px) {
  .account-item {
    padding: 6px 12px;
    font-size: 13px;
  }
  
  .account-amount {
    font-size: 12px;
  }
  
  .total-row {
    padding: 10px 12px;
    font-size: 13px;
  }
  
  .total-amount {
    font-size: 13px;
  }
  
  .summary-card {
    padding: 12px;
  }
  
  .card-value {
    font-size: 14px;
  }
  
  .net-value {
    font-size: 18px;
  }
  
  .assets-value {
    font-size: 16px;
  }
  
  .net-income-value {
    font-size: 20px;
  }
}

/* 横屏适配 */
@media (orientation: landscape) {
  .chart-container {
    height: 250px;
  }
  
  :deep(.v-chart) {
    height: 250px !important;
  }
}

/* 大屏手机适配 */
@media (min-width: 414px) {
  .account-item {
    padding: 10px 16px;
  }
  
  .summary-cards {
    padding: 20px;
  }
  
  .summary-card {
    padding: 20px;
  }
}
</style>