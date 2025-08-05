<template>
  <div class="h5-add-transaction">
    <!-- 头部导航 -->
    <div class="header-nav">
      <div class="nav-left">
        <van-button 
          type="default" 
          size="small" 
          plain 
          @click="handleCancel"
        >
          取消
        </van-button>
      </div>
      <div class="nav-title">
        {{ getPageTitle() }}
      </div>
      <div class="nav-right">
        <van-button 
          type="primary" 
          size="small" 
          :disabled="!canSave"
          @click="handleSave"
        >
          保存
        </van-button>
      </div>
    </div>

    <!-- 类型选择标签 -->
    <div class="type-tabs">
      <div class="tab-container">
        <div 
          v-for="tab in tabList" 
          :key="tab.name"
          class="tab-item"
          :class="{ active: activeTab === tab.name }"
          @click="setActiveTab(tab.name)"
        >
          {{ tab.title }}
        </div>
      </div>
    </div>

    <!-- 表单内容 -->
    <div class="form-content">
      <div v-if="activeTab === 'expense'" class="tab-content">
        <TransactionForm
          type="expense"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'income'" class="tab-content">
        <TransactionForm
          type="income"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'transfer'" class="tab-content">
        <TransferForm
          :form-data="transferFormData"
          @update="updateTransferFormData"
          @submit="onTransferSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'adjustment'" class="tab-content">
        <TransactionForm
          type="adjustment"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import TransactionForm from '@/views/h5/components/TransactionForm.vue'
import TransferForm from '@/views/h5/components/TransferForm.vue'
import { createTransaction, getTransactions } from '@/api/transactions'

const router = useRouter()
const route = useRoute()

const activeTab = ref('expense')

// 标签列表
const tabList = ref([
  { name: 'expense', title: '支出' },
  { name: 'income', title: '收入' },
  { name: 'transfer', title: '转账' },
  { name: 'adjustment', title: '调整余额' }
])

const formData = ref({
  amount: '',
  payee: '',
  account: '',
  category: '',
  date: new Date(),
  description: '',
  currency: 'CNY',
  flag: '*', // 交易状态标记
  categories: [{ categoryName: '', categoryDisplayName: '', category: '', amount: '' }]
})

const transferFormData = ref({
  amount: '',
  fromAccount: '',
  toAccount: '',
  date: new Date(),
  description: '',
  currency: 'CNY',
  flag: '*'
})

// 计算属性
const canSave = computed(() => {
  if (activeTab.value === 'transfer') {
    return transferFormData.value.amount && 
           transferFormData.value.fromAccount && 
           transferFormData.value.toAccount
  } else {
    return formData.value.amount && 
           formData.value.account
  }
})

// 页面标题
const getPageTitle = () => {
  const titleMap: Record<string, string> = {
    expense: '新增支出',
    income: '新增收入', 
    transfer: '新增转账',
    adjustment: '调整余额'
  }
  return titleMap[activeTab.value] || '新增交易'
}

// 设置活动标签
const setActiveTab = (tabName: string) => {
  if (activeTab.value !== tabName) {
    activeTab.value = tabName
    resetForm()
  }
}

// 处理取消
const handleCancel = () => {
  router.back()
}

// 处理保存
const handleSave = async () => {
  if (activeTab.value === 'transfer') {
    await onTransferSubmit()
  } else {
    await onSubmit()
  }
}

const updateFormData = (data: any) => {
  formData.value = { ...formData.value, ...data }
}

const updateTransferFormData = (data: any) => {
  transferFormData.value = { ...transferFormData.value, ...data }
}

const resetForm = () => {
  formData.value = {
    amount: '',
    payee: '',
    account: '',
    category: '',
    date: new Date(),
    description: '',
    currency: 'CNY',
    flag: '*',
    categories: [{ categoryName: '', categoryDisplayName: '', category: '', amount: '' }]
  }
  
  transferFormData.value = {
    amount: '',
    fromAccount: '',
    toAccount: '',
    date: new Date(),
    description: '',
    currency: 'CNY',
    flag: '*'
  }
}

const onSubmit = async () => {
  try {
    showLoadingToast({
      message: '保存中...',
      forbidClick: true
    })
    
    // 构建交易数据
    const postings = []
    
    // 先添加分类的postings（支出或收入账户）
    for (const category of formData.value.categories) {
      if (category.category && category.amount) {
        const categoryAmount = parseFloat(category.amount)
        postings.push({
          account: category.category,
          amount: activeTab.value === 'expense' ? Math.abs(categoryAmount) : -Math.abs(categoryAmount),
          currency: formData.value.currency || 'CNY'
        })
      }
    }
    
    // 后添加主账户posting（资产或负债账户）
    const totalAmount = parseFloat(formData.value.amount)
    postings.push({
      account: formData.value.account,
      amount: activeTab.value === 'expense' ? -Math.abs(totalAmount) : Math.abs(totalAmount),
      currency: formData.value.currency || 'CNY'
    })
    
    // 验证分录平衡（复式记账规则：所有分录金额合计必须为0）
    const postingsSum = postings.reduce((sum, posting) => sum + posting.amount, 0)
    if (Math.abs(postingsSum) >= 0.01) {
      closeToast()
      showToast(`分录不平衡，差额：¥${postingsSum.toFixed(2)}`)
      console.error('分录不平衡:', postings, '合计:', postingsSum)
      return
    }
    
    const transactionData = {
      date: formData.value.date.toISOString().split('T')[0],
      flag: '*', // 默认标记
      payee: formData.value.payee,
      narration: formData.value.description || formData.value.payee,
      postings
    }
    
    // 调用API保存交易
    await createTransaction(transactionData)
    
    closeToast()
    showToast('保存成功')
    
    // 返回上一页或跳转到交易列表
    router.back()
  } catch (error) {
    closeToast()
    showToast('保存失败')
    console.error('保存交易失败:', error)
  }
}

const onTransferSubmit = async () => {
  try {
    showLoadingToast({
      message: '保存中...',
      forbidClick: true
    })
    
    // 构建转账交易数据
    const transferData = {
      date: transferFormData.value.date.toISOString().split('T')[0],
      flag: '*', // 默认标记
      payee: '转账',
      narration: transferFormData.value.description || '账户转账',
      postings: [
        {
          account: transferFormData.value.fromAccount,
          amount: -Math.abs(parseFloat(transferFormData.value.amount)),
          currency: transferFormData.value.currency || 'CNY'
        },
        {
          account: transferFormData.value.toAccount,
          amount: Math.abs(parseFloat(transferFormData.value.amount)),
          currency: transferFormData.value.currency || 'CNY'
        }
      ]
    }
    
    // 调用API保存转账
    await createTransaction(transferData)
    
    closeToast()
    showToast('转账成功')
    
    router.back()
  } catch (error) {
    closeToast()
    showToast('转账失败')
    console.error('保存转账失败:', error)
  }
}

onMounted(() => {
  // 检查路由参数
  const type = route.query.type as string
  if (type && ['expense', 'income', 'transfer'].includes(type)) {
    activeTab.value = type
  }
  
  // 如果是编辑模式，加载现有数据
  const id = route.query.id as string
  if (id) {
    loadTransactionData()
  }
})

const loadTransactionData = async () => {
  try {
    const id = route.query.id as string
    if (!id) return
    
    // 调用API获取交易数据
    // 注意：实际的API可能需要不同的参数来获取单个交易
    const response = await getTransactions({ page: 1, page_size: 1000 })
    const transactions = response.data || []
    
    // 查找对应的交易（这里简化处理，实际应该有专门的API获取单个交易）
    const transaction = transactions.find((_: any, index: number) => (index + 1).toString() === id)
    
    if (transaction) {
      const posting = transaction.postings?.[0]
      const amount = posting?.amount || 0
      const parsedAmount = typeof amount === 'string' ? parseFloat(amount) : amount
      
      const transactionData = {
        amount: Math.abs(parsedAmount).toString(),
        payee: transaction.payee || '',
        account: posting?.account || '',
        category: '', // API中没有category，暂时留空
        date: new Date(transaction.date),
        description: transaction.narration || '',
        currency: posting?.currency || 'CNY',
        flag: transaction.flag || '*',
        categories: [{ categoryName: '', categoryDisplayName: '', category: '', amount: Math.abs(parsedAmount).toString() }]
      }
      
      const transactionType = parsedAmount > 0 ? 'income' : 'expense'
      activeTab.value = transactionType
      formData.value = transactionData
    }
  } catch (error) {
    showToast('加载交易数据失败')
    console.error('加载交易数据失败:', error)
  }
}
</script>

<style scoped>
.h5-add-transaction {
  height: 100vh;
  background-color: #f7f8fa;
  display: flex;
  flex-direction: column;
}

/* 头部导航 */
.header-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #ee5a52 0%, #f08080 100%);
  color: white;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(238, 90, 82, 0.3);
}

.nav-left,
.nav-right {
  min-width: 60px;
}

.nav-title {
  flex: 1;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.nav-left :deep(.van-button),
.nav-right :deep(.van-button) {
  border-color: rgba(255, 255, 255, 0.3);
  color: white;
  background: rgba(255, 255, 255, 0.1);
}

.nav-right :deep(.van-button--primary) {
  background: rgba(255, 255, 255, 0.9);
  color: #ee5a52;
  border-color: transparent;
}

.nav-right :deep(.van-button--disabled) {
  background: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.6);
}

/* 类型选择标签 */
.type-tabs {
  background: white;
  padding: 0;
  border-bottom: 1px solid #ebedf0;
  position: sticky;
  top: 56px;
  z-index: 99;
}

.tab-container {
  display: flex;
  background: white;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 16px 8px;
  font-size: 16px;
  color: #646566;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
}

.tab-item.active {
  color: #ee5a52;
  font-weight: 600;
  border-bottom-color: #ee5a52;
  background: rgba(238, 90, 82, 0.05);
}

.tab-item:hover {
  background: rgba(238, 90, 82, 0.05);
}

/* 表单内容 */
.form-content {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  height: 100%;
  background: #f7f8fa;
}

/* 响应式设计 */
@media (max-width: 375px) {
  .header-nav {
    padding: 10px 12px;
  }
  
  .nav-title {
    font-size: 16px;
  }
  
  .tab-item {
    padding: 14px 6px;
    font-size: 14px;
  }
}

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .h5-add-transaction {
    background-color: #1a1a1a;
  }
  
  .type-tabs {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }
  
  .tab-container {
    background: #2c2c2c;
  }
  
  .tab-item {
    color: #cccccc;
  }
  
  .tab-item.active {
    background: rgba(238, 90, 82, 0.15);
  }
  
  .tab-content {
    background: #1a1a1a;
  }
}
</style>