<template>
  <div class="h5-add-transaction">
    <!-- 类型选择 -->
    <van-tabs v-model:active="activeTab" @change="onTabChange">
      <van-tab title="支出" name="expense">
        <div class="tab-content">
          <TransactionForm
            type="expense"
            :form-data="formData"
            @update="updateFormData"
            @submit="onSubmit"
          />
        </div>
      </van-tab>
      <van-tab title="收入" name="income">
        <div class="tab-content">
          <TransactionForm
            type="income"
            :form-data="formData"
            @update="updateFormData"
            @submit="onSubmit"
          />
        </div>
      </van-tab>
      <van-tab title="转账" name="transfer">
        <div class="tab-content">
          <TransferForm
            :form-data="transferFormData"
            @update="updateTransferFormData"
            @submit="onTransferSubmit"
          />
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showLoadingToast, closeToast } from 'vant'
import TransactionForm from './components/TransactionForm.vue'
import TransferForm from './components/TransferForm.vue'
import { createTransaction, getTransactions } from '@/api/transactions'

const router = useRouter()
const route = useRoute()

const activeTab = ref('expense')

const formData = ref({
  amount: '',
  payee: '',
  account: '',
  category: '',
  date: new Date(),
  description: ''
})

const transferFormData = ref({
  amount: '',
  fromAccount: '',
  toAccount: '',
  date: new Date(),
  description: ''
})

const onTabChange = () => {
  // 切换标签时重置表单
  resetForm()
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
    description: ''
  }
  
  transferFormData.value = {
    amount: '',
    fromAccount: '',
    toAccount: '',
    date: new Date(),
    description: ''
  }
}

const onSubmit = async () => {
  try {
    showLoadingToast({
      message: '保存中...',
      forbidClick: true
    })
    
    // 构建交易数据
    const transactionData = {
      date: formData.value.date.toISOString().split('T')[0],
      flag: '*', // 默认标记
      payee: formData.value.payee,
      narration: formData.value.description || formData.value.payee,
      postings: [
        {
          account: formData.value.account,
          amount: activeTab.value === 'expense' ? -Math.abs(parseFloat(formData.value.amount)) : Math.abs(parseFloat(formData.value.amount)),
          currency: 'CNY'
        }
        // 这里可能需要添加第二个posting，比如对应的费用分类账户
      ]
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
          currency: 'CNY'
        },
        {
          account: transferFormData.value.toAccount,
          amount: Math.abs(parseFloat(transferFormData.value.amount)),
          currency: 'CNY'
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
    const transactions = response.data.data || []
    
    // 查找对应的交易（这里简化处理，实际应该有专门的API获取单个交易）
    const transaction = transactions.find((t: any, index: number) => (index + 1).toString() === id)
    
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
        type: parsedAmount > 0 ? 'income' : 'expense'
      }
      
      activeTab.value = transactionData.type
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
}

.tab-content {
  height: calc(100vh - 44px);
  overflow-y: auto;
}

:deep(.van-tabs__wrap) {
  position: sticky;
  top: 0;
  z-index: 99;
}
</style>