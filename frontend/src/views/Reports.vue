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
      
      <div class="balance-sheet-container" v-if="balanceSheet">
        <el-row :gutter="40">
          <!-- 左侧：资产 -->
          <el-col :span="12">
            <div class="balance-section">
              <h2 class="section-title">资产</h2>
              
              <el-table 
                :data="groupedAssetAccounts" 
                :show-header="false"
                size="default"
                :border="false"
                class="balance-table"
              >
                <el-table-column>
                  <template #default="{ row }">
                    <div :class="['account-row', row.type]">
                      <span 
                        class="account-name" 
                        :style="{ paddingLeft: (12 + row.level * 20) + 'px' }"
                      >
                        {{ row.name }}
                      </span>
                      <span class="account-amount">
                        <span v-if="row.type === 'item'" class="currency-label">CNY</span>
                        {{ row.amount }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-col>
          
          <!-- 右侧：负债和所有者权益 -->
          <el-col :span="12">
            <div class="balance-section">
              <h2 class="section-title">负债</h2>
              
              <el-table 
                :data="groupedLiabilityAccounts" 
                :show-header="false"
                size="default"
                :border="false"
                class="balance-table"
              >
                <el-table-column>
                  <template #default="{ row }">
                    <div :class="['account-row', row.type]">
                      <span 
                        class="account-name" 
                        :style="{ paddingLeft: (12 + row.level * 20) + 'px' }"
                      >
                        {{ row.name }}
                      </span>
                      <span class="account-amount">
                        <span v-if="row.type === 'item'" class="currency-label">CNY</span>
                        {{ row.amount }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="section-divider"></div>
              
              <h2 class="section-title">所有者权益</h2>
              
              <el-table 
                :data="groupedEquityAccounts" 
                :show-header="false"
                size="default"
                :border="false"
                class="balance-table"
              >
                <el-table-column>
                  <template #default="{ row }">
                    <div :class="['account-row', row.type]">
                      <span 
                        class="account-name" 
                        :style="{ paddingLeft: (12 + row.level * 20) + 'px' }"
                      >
                        {{ row.name }}
                      </span>
                      <span class="account-amount">
                        <span v-if="row.type === 'item'" class="currency-label">CNY</span>
                        {{ row.amount }}
                      </span>
                    </div>
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="section-divider"></div>
              
            </div>
          </el-col>
        </el-row>
      </div>
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
          <el-table 
            :data="sortedIncomeAccounts" 
            :show-header="false"
            size="default"
            :border="false"
            class="balance-table"
          >
            <el-table-column>
              <template #default="{ row }">
                <div :class="['account-row', row.type]">
                  <span 
                    class="account-name" 
                    :style="{ paddingLeft: (12 + row.level * 20) + 'px' }"
                  >
                    {{ row.name }}
                  </span>
                  <span class="account-amount">
                    <span v-if="row.type === 'item'" class="currency-label">CNY</span>
                    {{ formatCurrency(row.balance) }}
                  </span>
                </div>
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
          <el-table 
            :data="sortedExpenseAccounts" 
            :show-header="false"
            size="default"
            :border="false"
            class="balance-table"
          >
            <el-table-column>
              <template #default="{ row }">
                <div :class="['account-row', row.type]">
                  <span 
                    class="account-name" 
                    :style="{ paddingLeft: (12 + row.level * 20) + 'px' }"
                  >
                    {{ row.name }}
                  </span>
                  <span class="account-amount">
                    <span v-if="row.type === 'item'" class="currency-label">CNY</span>
                    {{ formatCurrency(row.balance) }}
                  </span>
                </div>
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
    
    <!-- 月度报告 -->
    <el-card v-if="activeTab === 'monthly'" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>月度报告</span>
          <div class="date-selectors">
            <el-select v-model="selectedYear" @change="onDateChange" placeholder="选择年份" style="width: 100px;">
              <el-option 
                v-for="year in getYearOptions()" 
                :key="year" 
                :label="`${year}年`" 
                :value="year" 
              />
            </el-select>
            <el-select v-model="selectedMonth" @change="onDateChange" placeholder="选择月份" style="width: 100px;">
              <el-option 
                v-for="month in getMonthOptions()" 
                :key="month.value" 
                :label="month.label" 
                :value="month.value" 
              />
            </el-select>
          </div>
        </div>
      </template>
      
      <div v-if="monthlySummary && yearToDateSummary">
        <!-- 月度汇总卡片 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :xs="24" :sm="12" :lg="6">
            <el-card class="summary-card monthly-income">
              <div class="summary-content">
                <div class="summary-value">{{ formatCurrency(monthlySummary.income_statement.total_income) }}</div>
                <div class="summary-label">本月收入</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-card class="summary-card monthly-expense">
              <div class="summary-content">
                <div class="summary-value">{{ formatCurrency(Math.abs(monthlySummary.income_statement.total_expenses)) }}</div>
                <div class="summary-label">本月支出</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-card class="summary-card monthly-net">
              <div class="summary-content">
                <div class="summary-value" :class="monthlySummary.income_statement.net_income >= 0 ? 'positive' : 'negative'">
                  {{ formatCurrency(monthlySummary.income_statement.net_income) }}
                </div>
                <div class="summary-label">本月净收益</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="12" :lg="6">
            <el-card class="summary-card monthly-assets">
              <div class="summary-content">
                <div class="summary-value">{{ formatCurrency(monthlySummary.balance_sheet.total_assets) }}</div>
                <div class="summary-label">月末总资产</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 年度至今对比 -->
        <el-row :gutter="20" class="mb-4">
          <el-col :span="24">
            <el-card>
              <template #header>
                <span>{{ selectedYear }}年度至今汇总</span>
              </template>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="8">
                  <div class="ytd-item">
                    <div class="ytd-label">累计收入</div>
                    <div class="ytd-value positive">{{ formatCurrency(yearToDateSummary.income_statement.total_income) }}</div>
                  </div>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <div class="ytd-item">
                    <div class="ytd-label">累计支出</div>
                    <div class="ytd-value negative">{{ formatCurrency(Math.abs(yearToDateSummary.income_statement.total_expenses)) }}</div>
                  </div>
                </el-col>
                <el-col :xs="24" :sm="8">
                  <div class="ytd-item">
                    <div class="ytd-label">累计净收益</div>
                    <div class="ytd-value" :class="yearToDateSummary.income_statement.net_income >= 0 ? 'positive' : 'negative'">
                      {{ formatCurrency(yearToDateSummary.income_statement.net_income) }}
                    </div>
                  </div>
                </el-col>
              </el-row>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 月度详细分析 -->
        <el-row :gutter="20">
          <el-col :xs="24" :lg="12">
            <el-card>
              <template #header>
                <span>{{ selectedMonth }}月收入明细</span>
              </template>
              
              <el-table :data="sortedMonthlyIncomeAccounts" size="small" max-height="300">
                <el-table-column prop="name" label="账户">
                  <template #default="{ row }">
                    {{ row.name.replace('Income:', '') }}
                  </template>
                </el-table-column>
                <el-table-column prop="balance" label="金额" align="right" sortable>
                  <template #default="{ row }">
                    <span class="amount-positive">{{ formatCurrency(-row.balance) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :lg="12">
            <el-card>
              <template #header>
                <span>{{ selectedMonth }}月支出明细</span>
              </template>
              
              <el-table :data="sortedMonthlyExpenseAccounts" size="small" max-height="300">
                <el-table-column prop="name" label="账户">
                  <template #default="{ row }">
                    {{ row.name.replace('Expenses:', '') }}
                  </template>
                </el-table-column>
                <el-table-column prop="balance" label="金额" align="right" sortable>
                  <template #default="{ row }">
                    <span class="amount-negative">{{ formatCurrency(Math.abs(row.balance)) }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
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

const loading = ref(false)
const activeTab = ref('balance-sheet')
const asOfDate = ref(new Date().toISOString().split('T')[0])
const periodRange = ref<[string, string] | null>(null)
const trendsMonths = ref(12)
const isMobile = ref(false)

const balanceSheet = ref<any>(null)
const incomeStatement = ref<any>(null)
const trendsData = ref<any>(null)
const trendsOption = ref<any>(null)

// 月度报告相关数据
const selectedYear = ref(new Date().getFullYear())
const selectedMonth = ref(new Date().getMonth() + 1)
const monthlySummary = ref<any>(null)
const yearToDateSummary = ref<any>(null)

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

// 分组后的资产账户
const groupedAssetAccounts = computed(() => {
  const accounts = assetAccounts.value
  const grouped: any[] = []
  
  // 构建层级树结构
  const buildTree = (accounts: any[]) => {
    const tree: any = {}
    
    accounts.forEach(acc => {
      const parts = acc.name.split(':').slice(1) // 去掉 Assets 前缀
      let current = tree
      
      // 构建路径
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        if (!current[part]) {
          current[part] = {
            name: part,
            fullPath: 'Assets:' + parts.slice(0, i + 1).join(':'),
            children: {},
            balance: 0,
            isLeaf: false
          }
        }
        current[part].balance += Number(acc.balance) || 0
        
        // 如果是最后一级，标记为叶子节点
        if (i === parts.length - 1) {
          current[part].isLeaf = true
          current[part].originalAccount = acc
        }
        
        current = current[part].children
      }
    })
    
    return tree
  }
  
  // 渲染树结构
  const renderTree = (node: any, level = 0) => {
    const result: any[] = []
    
    // 按名称排序
    const sortedKeys = Object.keys(node).sort()
    
    sortedKeys.forEach(key => {
      const item = node[key]
      
      // 如果有子节点，显示为分类
      if (Object.keys(item.children).length > 0) {
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: level === 0 ? 'category' : 'subcategory',
          level: level,
          fullPath: item.fullPath,
          isExpandable: true
        })
        
        // 递归添加子节点
        result.push(...renderTree(item.children, level + 1))
      } else {
        // 叶子节点，显示为具体账户
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: 'item',
          level: level,
          fullPath: item.fullPath,
          isExpandable: false
        })
      }
    })
    
    return result
  }
  
  const tree = buildTree(accounts)
  grouped.push(...renderTree(tree))
  
  // 添加总计行
  if (balanceSheet.value) {
    grouped.push({
      name: '资产总计',
      amount: formatCurrency(balanceSheet.value.total_assets),
      type: 'total',
      level: 0
    })
  }
  
  return grouped
})

// 分组后的负债账户
const groupedLiabilityAccounts = computed(() => {
  const accounts = liabilityAccounts.value
  const grouped: any[] = []
  
  // 构建层级树结构
  const buildTree = (accounts: any[]) => {
    const tree: any = {}
    
    accounts.forEach(acc => {
      const parts = acc.name.split(':').slice(1) // 去掉 Liabilities 前缀
      let current = tree
      
      // 构建路径
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        if (!current[part]) {
          current[part] = {
            name: part,
            fullPath: 'Liabilities:' + parts.slice(0, i + 1).join(':'),
            children: {},
            balance: 0,
            isLeaf: false
          }
        }
        current[part].balance += Number(Math.abs(acc.balance)) || 0
        
        // 如果是最后一级，标记为叶子节点
        if (i === parts.length - 1) {
          current[part].isLeaf = true
          current[part].originalAccount = acc
        }
        
        current = current[part].children
      }
    })
    
    return tree
  }
  
  // 渲染树结构
  const renderTree = (node: any, level = 0) => {
    const result: any[] = []
    
    // 按名称排序
    const sortedKeys = Object.keys(node).sort()
    
    sortedKeys.forEach(key => {
      const item = node[key]
      
      // 如果有子节点，显示为分类
      if (Object.keys(item.children).length > 0) {
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: level === 0 ? 'category' : 'subcategory',
          level: level,
          fullPath: item.fullPath,
          isExpandable: true
        })
        
        // 递归添加子节点
        result.push(...renderTree(item.children, level + 1))
      } else {
        // 叶子节点，显示为具体账户
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: 'item',
          level: level,
          fullPath: item.fullPath,
          isExpandable: false
        })
      }
    })
    
    return result
  }
  
  const tree = buildTree(accounts)
  grouped.push(...renderTree(tree))
  
  // 添加总计行
  if (balanceSheet.value) {
    grouped.push({
      name: '负债总计',
      amount: formatCurrency(Math.abs(balanceSheet.value.total_liabilities)),
      type: 'total',
      level: 0
    })
  }
  
  return grouped
})

// 分组后的权益账户
const groupedEquityAccounts = computed(() => {
  const accounts = equityAccounts.value
  const grouped: any[] = []
  
  // 构建层级树结构
  const buildTree = (accounts: any[]) => {
    const tree: any = {}
    
    accounts.forEach(acc => {
      const parts = acc.name.split(':')
      let current = tree
      
      // 构建路径
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        if (!current[part]) {
          current[part] = {
            name: part,
            fullPath: parts.slice(0, i + 1).join(':'),
            children: {},
            balance: 0,
            isLeaf: false
          }
        }
        current[part].balance += Number(acc.balance) || 0
        
        // 如果是最后一级，标记为叶子节点
        if (i === parts.length - 1) {
          current[part].isLeaf = true
          current[part].originalAccount = acc
        }
        
        current = current[part].children
      }
    })
    
    return tree
  }
  
  // 渲染树结构
  const renderTree = (node: any, level = 0) => {
    const result: any[] = []
    
    // 按名称排序
    const sortedKeys = Object.keys(node).sort()
    
    sortedKeys.forEach(key => {
      const item = node[key]
      
      // 如果有子节点，显示为分类
      if (Object.keys(item.children).length > 0) {
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: level === 0 ? 'category' : 'subcategory',
          level: level,
          fullPath: item.fullPath,
          isExpandable: true
        })
        
        // 递归添加子节点
        result.push(...renderTree(item.children, level + 1))
      } else {
        // 叶子节点，显示为具体账户
        result.push({
          name: item.name,
          amount: formatCurrency(item.balance),
          type: 'item',
          level: level,
          fullPath: item.fullPath,
          isExpandable: false
        })
      }
    })
    
    return result
  }
  
  const tree = buildTree(accounts)
  grouped.push(...renderTree(tree))
  
  // 添加总计行
  if (balanceSheet.value) {
    grouped.push({
      name: '所有者权益总计',
      amount: formatCurrency(balanceSheet.value.total_equity),
      type: 'total',
      level: 0
    })
  }
  
  return grouped
})

// 按金额倒序排序的收入账户
const sortedIncomeAccounts = computed(() => {
  if (!incomeStatement.value?.income_accounts) return []
  
  const accounts = incomeStatement.value.income_accounts
  const grouped: any[] = []
  
  // 构建层级树结构
  const buildTree = (accounts: any[]) => {
    const tree: any = {}
    
    accounts.forEach(acc => {
      const parts = acc.name.split(':').slice(1) // 去掉 Income 前缀
      let current = tree
      
      // 构建路径
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        if (!current[part]) {
          current[part] = {
            name: part,
            fullPath: 'Income:' + parts.slice(0, i + 1).join(':'),
            children: {},
            balance: 0,
            isLeaf: false
          }
        }
        current[part].balance += Number(Math.abs(acc.balance)) || 0
        
        // 如果是最后一级，标记为叶子节点
        if (i === parts.length - 1) {
          current[part].isLeaf = true
          current[part].originalAccount = acc
        }
        
        current = current[part].children
      }
    })
    
    return tree
  }
  
  // 渲染树结构
  const renderTree = (node: any, level = 0) => {
    const result: any[] = []
    
    // 按余额排序（从大到小）
    const sortedKeys = Object.keys(node).sort((a, b) => node[b].balance - node[a].balance)
    
    sortedKeys.forEach(key => {
      const item = node[key]
      
      // 如果有子节点，显示为分类
      if (Object.keys(item.children).length > 0) {
        result.push({
          name: item.name,
          balance: item.balance,
          type: level === 0 ? 'category' : 'subcategory',
          level: level,
          fullPath: item.fullPath,
          isExpandable: true
        })
        
        // 递归添加子节点
        result.push(...renderTree(item.children, level + 1))
      } else {
        // 叶子节点，显示为具体账户
        result.push({
          name: item.name,
          balance: item.balance,
          type: 'item',
          level: level,
          fullPath: item.fullPath,
          isExpandable: false
        })
      }
    })
    
    return result
  }
  
  const tree = buildTree(accounts)
  grouped.push(...renderTree(tree))
  
  return grouped
})

// 按金额倒序排序的支出账户
const sortedExpenseAccounts = computed(() => {
  if (!incomeStatement.value?.expense_accounts) return []
  
  const accounts = incomeStatement.value.expense_accounts
  const grouped: any[] = []
  
  // 构建层级树结构
  const buildTree = (accounts: any[]) => {
    const tree: any = {}
    
    accounts.forEach(acc => {
      const parts = acc.name.split(':').slice(1) // 去掉 Expenses 前缀
      let current = tree
      
      // 构建路径
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i]
        if (!current[part]) {
          current[part] = {
            name: part,
            fullPath: 'Expenses:' + parts.slice(0, i + 1).join(':'),
            children: {},
            balance: 0,
            isLeaf: false
          }
        }
        current[part].balance += Number(Math.abs(acc.balance)) || 0
        
        // 如果是最后一级，标记为叶子节点
        if (i === parts.length - 1) {
          current[part].isLeaf = true
          current[part].originalAccount = acc
        }
        
        current = current[part].children
      }
    })
    
    return tree
  }
  
  // 渲染树结构
  const renderTree = (node: any, level = 0) => {
    const result: any[] = []
    
    // 按余额排序（从大到小）
    const sortedKeys = Object.keys(node).sort((a, b) => node[b].balance - node[a].balance)
    
    sortedKeys.forEach(key => {
      const item = node[key]
      
      // 如果有子节点，显示为分类
      if (Object.keys(item.children).length > 0) {
        result.push({
          name: item.name,
          balance: item.balance,
          type: level === 0 ? 'category' : 'subcategory',
          level: level,
          fullPath: item.fullPath,
          isExpandable: true
        })
        
        // 递归添加子节点
        result.push(...renderTree(item.children, level + 1))
      } else {
        // 叶子节点，显示为具体账户
        result.push({
          name: item.name,
          balance: item.balance,
          type: 'item',
          level: level,
          fullPath: item.fullPath,
          isExpandable: false
        })
      }
    })
    
    return result
  }
  
  const tree = buildTree(accounts)
  grouped.push(...renderTree(tree))
  
  return grouped
})

// 按金额倒序排序的月度收入账户
const sortedMonthlyIncomeAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.income_accounts) return []
  return [...monthlySummary.value.income_statement.income_accounts].sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
})

// 按金额倒序排序的月度支出账户
const sortedMonthlyExpenseAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.expense_accounts) return []
  return [...monthlySummary.value.income_statement.expense_accounts].sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
})

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
  const incomes = trendsData.value.trends.map((item: any) => item.total_income)
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
  } finally {
    loading.value = false
  }
}

// 年份或月份变化处理
const onDateChange = () => {
  loadMonthlyReport()
}

// 获取年份选项
const getYearOptions = () => {
  const currentYear = new Date().getFullYear()
  const years = []
  for (let i = currentYear; i >= currentYear - 5; i--) {
    years.push(i)
  }
  return years
}

// 获取月份选项
const getMonthOptions = () => {
  return [
    { value: 1, label: '1月' },
    { value: 2, label: '2月' },
    { value: 3, label: '3月' },
    { value: 4, label: '4月' },
    { value: 5, label: '5月' },
    { value: 6, label: '6月' },
    { value: 7, label: '7月' },
    { value: 8, label: '8月' },
    { value: 9, label: '9月' },
    { value: 10, label: '10月' },
    { value: 11, label: '11月' },
    { value: 12, label: '12月' }
  ]
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
    case 'monthly':
      loadMonthlyReport()
      break
  }
}

// 检测屏幕尺寸
const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  // 根据当前选中的标签页加载对应数据
  switch (activeTab.value) {
    case 'balance-sheet':
      loadBalanceSheet()
      break
    case 'income-statement':
      loadIncomeStatement()
      break
    case 'trends':
      loadTrends()
      break
    case 'monthly':
      loadMonthlyReport()
      break
    default:
      loadBalanceSheet()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
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

.date-selectors {
  display: flex;
  gap: 12px;
}

.summary-card {
  margin-bottom: 16px;
}

.summary-content {
  text-align: center;
  padding: 16px 0;
}

.summary-value {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.summary-value.positive {
  color: #67c23a;
}

.summary-value.negative {
  color: #f56c6c;
}

.summary-label {
  font-size: 14px;
  color: #909399;
}

.monthly-income .summary-value {
  color: #67c23a;
}

.monthly-expense .summary-value {
  color: #f56c6c;
}

.monthly-assets .summary-value {
  color: #409eff;
}

.ytd-item {
  text-align: center;
  padding: 16px 0;
}

.ytd-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.ytd-value {
  font-size: 18px;
  font-weight: 600;
}

.ytd-value.positive {
  color: #67c23a;
}

.ytd-value.negative {
  color: #f56c6c;
}

.currency-notice {
  margin-bottom: 16px;
  padding: 8px 12px;
  background-color: #f0f9ff;
  border: 1px solid #b3d9ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.currency-notice .info-icon {
  font-size: 16px;
}

/* 资产负债表样式 */
.balance-sheet-container {
  margin-top: 16px;
}

.balance-section {
  height: 100%;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #e4e7ed;
}

.balance-table {
  border: none !important;
}

.balance-table .el-table__body-wrapper {
  border: none !important;
}

.balance-table .el-table__row {
  border: none !important;
}

.balance-table .el-table__cell {
  border: none !important;
  padding: 6px 0;
}

.account-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  width: 100%;
}

.account-row.subcategory {
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
  padding: 6px 0;
  margin: 2px 0;
}

.account-row.subcategory .account-name {
  color: #606266;
  font-weight: 500;
  font-size: 13px;
  padding-left: 8px;
}

.account-row.subcategory .account-amount {
  font-weight: 500;
  color: #606266;
}

.account-row.category {
  background-color: #f8f9fa;
  border-bottom: 1px solid #e4e7ed;
  padding: 8px 0;
  margin: 4px 0;
}

.account-row.category .account-name {
  color: #409eff;
  font-weight: 600;
  font-size: 14px;
  padding-left: 8px;
}

.account-row.category .account-amount {
  font-weight: 600;
  color: #409eff;
}

.account-row.item {
  border-bottom: 1px dotted #e4e7ed;
}

.account-row.item .account-name {
  color: #606266;
  font-size: 14px;
  padding-left: 12px;
}

.account-row.total {
  border-top: 1px solid #303133;
  border-bottom: 3px double #303133;
  padding: 8px 0;
  margin-top: 8px;
}

.account-row.total .account-name {
  color: #303133;
  font-weight: 600;
  font-size: 15px;
}

.account-amount {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  color: #303133;
  min-width: 120px;
}

.account-row.total .account-amount {
  font-weight: 600;
  font-size: 15px;
}

.currency-label {
  font-size: 11px;
  color: #909399;
  margin-right: 4px;
  font-family: inherit;
}

.section-divider {
  margin: 24px 0;
  border-bottom: 1px solid #e4e7ed;
}

.total-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 2px solid #303133;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  background-color: #f8f9fa;
  padding: 12px 16px;
  border-radius: 4px;
}

.total-label {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
}

.total-amount {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.total-amount .currency-label {
  font-size: 12px;
  margin-right: 4px;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .el-row {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .el-col {
    padding-left: 6px !important;
    padding-right: 6px !important;
  }
  
  .el-tabs__item {
    font-size: 12px;
    padding: 0 8px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .date-selectors {
    flex-direction: column;
    gap: 8px;
  }
  
  .date-selectors .el-select {
    width: 100% !important;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table .cell {
    padding: 4px 8px;
  }
  
  .total-row {
    font-size: 14px;
    text-align: center;
  }
  
  .net-income h3 {
    font-size: 16px;
  }
  
  .chart-container {
    min-height: 300px;
  }
  
  .summary-card .summary-content {
    padding: 12px 0;
  }
  
  .summary-value {
    font-size: 16px;
  }
  
  .summary-label {
    font-size: 12px;
  }
  
  .ytd-item {
    text-align: center;
    margin-bottom: 16px;
  }
  
  .ytd-value {
    font-size: 16px;
  }
  
  .ytd-label {
    font-size: 12px;
  }
  
  /* 资产负债表移动端优化 */
  .balance-sheet-container .el-row {
    flex-direction: column;
  }
  
  .balance-sheet-container .el-col {
    width: 100% !important;
    margin-bottom: 24px;
  }
  
  .section-title {
    font-size: 16px;
    margin-bottom: 12px;
  }
  
  .account-row {
    padding: 6px 0;
  }
  
  .account-row.item .account-name {
    font-size: 13px;
    padding-left: 8px;
  }
  
  .account-amount {
    font-size: 13px;
    min-width: 100px;
  }
  
  .currency-label {
    font-size: 10px;
  }
  
  .total-row {
    padding: 8px 12px;
  }
  
  .total-label {
    font-size: 14px;
  }
  
  .total-amount {
    font-size: 14px;
  }
  
  .section-divider {
    margin: 16px 0;
  }
}
</style> 