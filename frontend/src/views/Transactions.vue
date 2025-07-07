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
        
        <el-form-item label="收付方">
          <PayeeSelector
            v-model="filterForm.payee"
            placeholder="搜索收付方"
            style="width: 200px"
          />
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
        :data="flattenedTransactions" 
        v-loading="loading"
        row-key="id"
        :row-class-name="getRowClassName"
      >
        
        <el-table-column prop="date" label="日期" width="120" sortable>
          <template #default="{ row }">
            <span v-if="row.isHeader">{{ row.date }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="flag" label="标记" width="80">
          <template #default="{ row }">
            <span v-if="row.isHeader">
              <el-tag 
                v-if="getFlagType(row.flag)"
                :type="getFlagType(row.flag)"
              >
                {{ row.flag }}
              </el-tag>
              <el-tag v-else>{{ row.flag }}</el-tag>
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="payee" label="收付方" width="150">
          <template #default="{ row }">
            <span v-if="row.isHeader">{{ row.payee }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="narration" label="摘要" min-width="100">
          <template #default="{ row }">
            <template v-if="row.isHeader">
              <span v-if="row.flag !== 'P'">{{ row.narration }}</span>
            </template>
          </template>
        </el-table-column>
        
        <el-table-column label="账户" min-width="280">
          <template #default="{ row }">
            <span class="detail-account">
              {{ row.account }}
            </span>
            
          </template>
        </el-table-column>
        
        <el-table-column label="借方" width="120" align="right">
          <template #default="{ row }">
            <span v-if="!row.isHeader && row.amount > 0" class="amount-positive">
              {{ formatCurrency(row.amount) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="贷方" width="120" align="right">
          <template #default="{ row }">
            <span v-if="!row.isHeader && row.amount < 0" class="amount-negative">
              {{ formatCurrency(Math.abs(row.amount)) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column label="币种" width="80">
          <template #default="{ row }">
            <span v-if="!row.isHeader">{{ row.currency }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="标签" width="120">
          <template #default="{ row }">
            <span v-if="row.isHeader">
              <el-tag 
                v-for="tag in row.tags" 
                :key="tag" 
                size="small"
                class="tag-item"
              >
                {{ tag }}
              </el-tag>
            </span>
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
import { ref, onMounted, computed } from 'vue'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import { getTransactions, getAccounts } from '@/api/transactions'
import PayeeSelector from '@/components/PayeeSelector.vue'

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
  payee: '',
  narration: ''
})

// 扁平化交易数据，将每笔交易及其分录展示为多行
const flattenedTransactions = computed(() => {
  const result: any[] = []
  
  transactions.value.forEach((transaction, transactionIndex) => {
    // 添加交易头行
    result.push({
      id: `transaction-${transactionIndex}`,
      isHeader: true,
      transactionIndex,
      date: transaction.date,
      flag: transaction.flag,
      payee: transaction.payee,
      narration: transaction.narration,
      tags: transaction.tags,
      postings: transaction.postings
    })
    
    // 添加每个分录行
    transaction.postings?.forEach((posting: any, postingIndex: number) => {
      result.push({
        id: `posting-${transactionIndex}-${postingIndex}`,
        isHeader: false,
        transactionIndex,
        postingIndex,
        account: posting.account,
        amount: posting.amount,
        currency: posting.currency
      })
    })
  })
  
  return result
})

// 行样式类名
const getRowClassName = ({ row }: { row: any }) => {
  if (row.isHeader) {
    return 'transaction-header-row'
  } else {
    return 'transaction-detail-row'
  }
}

// 格式化货币
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
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
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (!params[key as keyof typeof params]) {
        delete params[key as keyof typeof params]
      }
    })
    
    const result = await getTransactions(params)
    // 响应拦截器已经返回了response.data，所以result就是我们的分页数据
    
    // 检查是否是分页响应格式
    if (result && typeof result === 'object' && 'data' in result && 'total' in result) {
      // 新的分页格式
      transactions.value = result.data || []
      totalCount.value = result.total || 0
      console.log('分页数据:', {
        data: result.data?.length,
        total: result.total,
        page: result.page,
        totalPages: result.total_pages
      })
    } else {
      // 兼容旧格式（直接返回数组）
      transactions.value = Array.isArray(result) ? result : []
      totalCount.value = transactions.value.length
      console.log('非分页数据:', transactions.value.length)
    }
    
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
    payee: '',
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

/* 交易行样式 */
:deep(.transaction-header-row) {
  background-color: #f8f9fa;
  border-top: 2px solid #e9ecef;
  font-weight: 500;
}

:deep(.transaction-header-row:hover) {
  background-color: #e9ecef;
}

:deep(.transaction-detail-row) {
  background-color: #ffffff;
  border-left: 3px solid #dee2e6;
}

:deep(.transaction-detail-row:hover) {
  background-color: #f8f9fa;
}

:deep(.transaction-detail-row td) {
  padding-left: 20px;
}

/* 账户样式 */
.main-account {
  font-weight: 500;
  color: #303133;
}

.detail-account {
  color: #606266;
  margin-left: 16px;
  font-size: 14px;
}
</style> 