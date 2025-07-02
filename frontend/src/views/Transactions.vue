<template>
  <div class="page-container">
    <h1 class="page-title">交易流水</h1>
    
    <!-- 筛选条件 -->
    <el-card class="mb-4">
      <el-form :model="filterForm" inline>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="onDateRangeChange"
          />
        </el-form-item>
        
        <el-form-item label="账户">
          <el-select
            v-model="filterForm.account"
            placeholder="选择账户"
            clearable
            filterable
            style="width: 200px"
          >
            <el-option
              v-for="account in accounts"
              :key="account"
              :label="account"
              :value="account"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="摘要">
          <el-input
            v-model="filterForm.narration"
            placeholder="搜索摘要"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="searchTransactions">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilter">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 交易列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>交易记录</span>
          <el-button type="primary" @click="$router.push('/add-transaction')">
            <el-icon><Plus /></el-icon>
            新增交易
          </el-button>
        </div>
      </template>
      
      <el-table 
        :data="transactions" 
        v-loading="loading"
        row-key="date"
        default-expand-all
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="transaction-detail">
              <h4>分录详情</h4>
              <el-table :data="row.postings" size="small">
                <el-table-column prop="account" label="账户" min-width="200" />
                <el-table-column label="借方" width="120" align="right">
                  <template #default="{ row: posting }">
                    <span v-if="posting.amount > 0" class="amount-positive">
                      {{ formatCurrency(posting.amount) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column label="贷方" width="120" align="right">
                  <template #default="{ row: posting }">
                    <span v-if="posting.amount < 0" class="amount-negative">
                      {{ formatCurrency(Math.abs(posting.amount)) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="currency" label="币种" width="80" />
              </el-table>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="date" label="日期" width="120" sortable />
        
        <el-table-column prop="flag" label="标记" width="80">
          <template #default="{ row }">
            <el-tag 
              v-if="getFlagType(row.flag)"
              :type="getFlagType(row.flag)"
            >
              {{ row.flag }}
            </el-tag>
            <el-tag v-else>{{ row.flag }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="payee" label="收付方" width="150" />
        <el-table-column prop="narration" label="摘要" min-width="200" />
        
        <el-table-column label="主要账户" min-width="180">
          <template #default="{ row }">
            {{ getMainAccount(row.postings) }}
          </template>
        </el-table-column>
        
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="getAmountClass(getMainAmount(row.postings))">
              {{ formatCurrency(Math.abs(getMainAmount(row.postings))) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="标签" width="120">
          <template #default="{ row }">
            <el-tag 
              v-for="tag in row.tags" 
              :key="tag" 
              size="small"
              class="tag-item"
            >
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getTransactions, getAccounts } from '@/api/transactions'

const loading = ref(false)
const transactions = ref<any[]>([])
const accounts = ref<string[]>([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)

const dateRange = ref<[string, string] | null>(null)
const filterForm = ref({
  start_date: '',
  end_date: '',
  account: '',
  narration: ''
})

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

// 获取标记类型
const getFlagType = (flag: string) => {
  switch (flag) {
    case '*': return 'success'
    case '!': return 'warning'
    case 'txn': return 'info'
    default: return undefined
  }
}

// 获取主要账户
const getMainAccount = (postings: any[]) => {
  return postings[0]?.account || ''
}

// 获取主要金额
const getMainAmount = (postings: any[]) => {
  return postings[0]?.amount || 0
}

// 日期范围变化
const onDateRangeChange = (dates: [string, string] | null) => {
  if (dates) {
    filterForm.value.start_date = dates[0]
    filterForm.value.end_date = dates[1]
  } else {
    filterForm.value.start_date = ''
    filterForm.value.end_date = ''
  }
}

// 搜索交易
const searchTransactions = async () => {
  loading.value = true
  
  try {
    const params = {
      ...filterForm.value,
      limit: pageSize.value * currentPage.value
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (!params[key as keyof typeof params]) {
        delete params[key as keyof typeof params]
      }
    })
    
    const result = await getTransactions(params)
    // 后端直接返回数组，不是包装在data字段中
    const transactionData = result.data || result || []
    transactions.value = Array.isArray(transactionData) ? transactionData : []
    totalCount.value = transactions.value.length
    
  } catch (error) {
    console.error('搜索交易失败:', error)
    transactions.value = []
    totalCount.value = 0
  } finally {
    loading.value = false
  }
}

// 重置筛选
const resetFilter = () => {
  dateRange.value = null
  filterForm.value = {
    start_date: '',
    end_date: '',
    account: '',
    narration: ''
  }
  currentPage.value = 1
  searchTransactions()
}

// 分页处理
const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  searchTransactions()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  searchTransactions()
}

// 加载账户列表
const loadAccounts = async () => {
  try {
    const accountsResult = await getAccounts()
    // 后端直接返回数组，不是包装在data字段中
    const accountData = accountsResult.data || accountsResult || []
    accounts.value = Array.isArray(accountData) ? accountData : []
  } catch (error) {
    console.error('加载账户列表失败:', error)
    accounts.value = []
  }
}

onMounted(() => {
  loadAccounts()
  searchTransactions()
})
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.transaction-detail {
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.transaction-detail h4 {
  margin-bottom: 12px;
  color: #303133;
}

.tag-item {
  margin-right: 4px;
}

.pagination-container {
  margin-top: 20px;
  text-align: center;
}
</style> 