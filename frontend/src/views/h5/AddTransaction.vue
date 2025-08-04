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
    
    // 这里应该调用API保存交易
    // await saveTransactionApi({ ...data, type: activeTab.value })
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
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
    
    // 这里应该调用API保存转账
    // await saveTransferApi(data)
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
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
    // 这里应该调用API获取交易数据
    // const data = await getTransactionApi(id)
    
    // 模拟数据
    const mockData = {
      amount: '45.00',
      payee: '星巴克',
      account: 'cmb',
      category: 'food',
      date: new Date('2024-01-15'),
      description: '早餐咖啡',
      type: 'expense'
    }
    
    activeTab.value = mockData.type
    formData.value = mockData
  } catch (error) {
    showToast('加载数据失败')
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