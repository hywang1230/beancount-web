<template>
  <div class="h5-transaction-detail">
    <van-nav-bar
      title="交易详情"
      left-text="返回"
      left-arrow
      @click-left="$router.back()"
    />

    <div v-if="loading" class="loading-container">
      <van-loading size="24px" vertical>加载中...</van-loading>
    </div>

    <div v-else-if="transaction" class="transaction-content">
      <!-- 基本信息 -->
      <van-cell-group>
        <van-cell title="日期" :value="transaction.date" />
        <van-cell title="收付方" :value="transaction.payee || '-'" />
        <van-cell title="摘要" :value="transaction.narration || '-'" />
        <van-cell title="标志" :value="transaction.flag || '*'" />
      </van-cell-group>

      <!-- 标签和链接 -->
      <van-cell-group v-if="transaction.tags?.length || transaction.links?.length" title="标签和链接">
        <van-cell v-if="transaction.tags?.length" title="标签">
          <template #value>
            <van-tag v-for="tag in transaction.tags" :key="tag" type="primary" size="small" style="margin-right: 4px;">
              {{ tag }}
            </van-tag>
          </template>
        </van-cell>
        <van-cell v-if="transaction.links?.length" title="链接">
          <template #value>
            <van-tag v-for="link in transaction.links" :key="link" type="success" size="small" style="margin-right: 4px;">
              {{ link }}
            </van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 分录信息 -->
      <van-cell-group title="分录详情">
        <van-cell
          v-for="(posting, index) in transaction.postings"
          :key="index"
          :title="formatAccountName(posting.account)"
          :value="formatAmount(posting.amount, posting.currency)"
          :value-class="(posting.amount && parseFloat(posting.amount) > 0) ? 'positive' : 'negative'"
        />
      </van-cell-group>

      <!-- 文件信息 -->
      <van-cell-group v-if="transaction.filename || transaction.lineno" title="文件信息">
        <van-cell title="文件名" :value="transaction.filename || '-'" />
        <van-cell title="行号" :value="transaction.lineno?.toString() || '-'" />
        <van-cell title="唯一标识" :value="transaction.transaction_id || '-'" />
      </van-cell-group>
    </div>

    <div v-else class="error-container">
      <van-empty description="交易不存在或已被删除" />
    </div>

    <!-- 操作按钮 -->
    <div v-if="transaction" class="action-buttons">
      <van-button
        type="primary"
        size="large"
        @click="editTransaction"
      >
        编辑交易
      </van-button>
      <van-button
        type="danger"
        size="large"
        @click="deleteTransaction"
        style="margin-top: 12px;"
      >
        删除交易
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import { getTransactionById, deleteTransaction as deleteTransactionApi } from '@/api/transactions'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const transaction = ref<any>(null)

const formatAmount = (amount: string | number | undefined, currency?: string) => {
  if (amount === undefined || amount === null) return '0.00'
  
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount
  const formatted = new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: currency || 'CNY'
  }).format(numAmount)
  
  return formatted
}

const formatAccountName = (accountName: string) => {
  if (!accountName) return '未知账户'
  // 去掉第一级账户名称（通常是Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(':')
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(':')
    
    // 进一步处理：去掉第一个"-"以及前面的字母部分
    // 例如：JT-交通:过路费 -> 交通:过路费，然后替换":"为"-"变成：交通-过路费
    const dashIndex = formattedName.indexOf('-')
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1)
    }
    
    // 将":"替换为"-"以提高可读性
    formattedName = formattedName.replace(/:/g, '-')
    
    return formattedName
  }
  return accountName
}

const loadTransaction = async () => {
  try {
    const transactionId = route.params.id as string
    console.log('Loading transaction with ID:', transactionId)
    
    const response = await getTransactionById(transactionId)
    transaction.value = response.data || response
    
    console.log('Loaded transaction:', transaction.value)
  } catch (error) {
    console.error('加载交易详情失败:', error)
    showToast('加载交易详情失败')
  } finally {
    loading.value = false
  }
}

const editTransaction = () => {
  const transactionId = transaction.value?.transaction_id || route.params.id
  router.push(`/h5/add-transaction?id=${transactionId}`)
}

const deleteTransaction = async () => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这条交易记录吗？删除后无法恢复。'
    })
    
    const transactionId = transaction.value?.transaction_id || route.params.id as string
    await deleteTransactionApi(transactionId)
    
    showToast('删除成功')
    router.back()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除交易失败:', error)
      showToast('删除交易失败')
    }
  }
}

onMounted(() => {
  loadTransaction()
})
</script>

<style scoped>
.h5-transaction-detail {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.transaction-content {
  padding: 16px 0;
}

.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.action-buttons {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background-color: white;
  border-top: 1px solid #ebedf0;
}

:deep(.van-cell-group) {
  margin-bottom: 16px;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-tag) {
  margin-right: 4px;
  margin-bottom: 4px;
}
</style>