<template>
  <div class="h5-accounts">
    <!-- 总资产概览 -->
    <div class="overview-section">
      <van-card class="total-card">
        <template #title>
          <div class="total-header">
            <span>总资产</span>
            <van-icon name="eye-o" @click="toggleVisibility" />
          </div>
        </template>
        <template #desc>
          <div class="total-amount">
            {{ showAmount ? formatAmount(totalAssets) : '****' }}
          </div>
        </template>
      </van-card>
    </div>

    <!-- 账户列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <div class="accounts-list">
        <div v-for="group in accountGroups" :key="group.type" class="account-group">
          <van-cell-group :title="getTypeLabel(group.type)">
            <van-cell
              v-for="account in group.accounts"
              :key="account.id"
              :title="account.name"
              :label="account.description"
              :value="showAmount ? formatAmount(account.balance) : '****'"
              is-link
              @click="viewAccount(account)"
            >
              <template #icon>
                <div class="account-icon">
                  <van-icon :name="getAccountIcon(account.type)" />
                </div>
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </van-pull-refresh>

    <!-- 添加账户按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="addAccount"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'

const router = useRouter()

const showAmount = ref(true)
const refreshing = ref(false)
const fabOffset = ref({ x: -24, y: -100 })
interface Account {
  id: number
  name: string
  type: string
  subtype: string
  balance: number
  description: string
}

const accounts = ref<Account[]>([])
const totalAssets = ref(0)

const accountGroups = computed(() => {
  const groups: Record<string, { type: string; accounts: Account[] }> = {}
  accounts.value.forEach(account => {
    if (!groups[account.type]) {
      groups[account.type] = {
        type: account.type,
        accounts: []
      }
    }
    groups[account.type].accounts.push(account)
  })
  return Object.values(groups)
})

const toggleVisibility = () => {
  showAmount.value = !showAmount.value
}

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    'Assets': '资产',
    'Liabilities': '负债',
    'Equity': '权益'
  }
  return typeMap[type] || type
}

const getAccountIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'bank': 'credit-pay',
    'cash': 'balance-list-o',
    'alipay': 'balance-pay',
    'wechat': 'chat-o',
    'investment': 'gold-coin-o'
  }
  return iconMap[type] || 'manager-o'
}

const viewAccount = (account: any) => {
  router.push(`/h5/accounts/${account.id}`)
}

const addAccount = () => {
  router.push('/h5/accounts/add')
}

const onRefresh = async () => {
  await loadAccounts()
  refreshing.value = false
}

const loadAccounts = async () => {
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    accounts.value = [
      {
        id: 1,
        name: '招商银行储蓄卡',
        type: 'Assets',
        subtype: 'bank',
        balance: 15680.50,
        description: '尾号1234'
      },
      {
        id: 2,
        name: '支付宝',
        type: 'Assets',
        subtype: 'alipay',
        balance: 8500.00,
        description: '余额'
      },
      {
        id: 3,
        name: '微信钱包',
        type: 'Assets',
        subtype: 'wechat',
        balance: 1500.00,
        description: '零钱'
      },
      {
        id: 4,
        name: '现金',
        type: 'Assets',
        subtype: 'cash',
        balance: 500.00,
        description: '现金'
      }
    ]
    
    totalAssets.value = accounts.value.reduce((total, account) => total + account.balance, 0)
  } catch (error) {
    console.error('加载账户失败:', error)
    showToast('加载失败')
  }
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.h5-accounts {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.overview-section {
  padding: 16px;
}

.total-card {
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.total-card :deep(.van-card__header) {
  padding: 16px;
}

.total-card :deep(.van-card__content) {
  padding: 0 16px 16px;
}

.total-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  opacity: 0.8;
}

.total-amount {
  font-size: 28px;
  font-weight: bold;
  margin-top: 8px;
}

.accounts-list {
  padding: 0 16px;
}

.account-group {
  margin-bottom: 16px;
}

.account-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f7f8fa;
  border-radius: 50%;
  margin-right: 12px;
}

:deep(.van-cell-group) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  font-weight: 500;
}
</style>