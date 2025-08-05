<template>
  <div class="transfer-form">
    <van-form @submit="onSubmit">
      <!-- 转出账户卡片 -->
      <div class="form-card from-account-card" @click="showFromAccountSelector = true">
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">{{ fromAccountDisplayName || '转出账户' }}</div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 金额输入卡片 -->
      <div class="form-card amount-card">
        <div class="card-icon">
          <van-icon name="exchange" />
        </div>
        <div class="amount-input-container">
          <div class="currency-selector" @click="showCurrencySelector = true">
            <span class="currency-symbol">{{ getCurrencySymbol(localFormData.currency) }}</span>
            <van-icon name="arrow-down" size="12" />
          </div>
          <van-field
            v-model="localFormData.amount"
            type="digit"
            placeholder="0.00"
            class="amount-field"
            :border="false"
            @update:model-value="onAmountInput"
          />
        </div>
      </div>

      <!-- 转账箭头 -->
      <div class="transfer-arrow-container">
        <div class="transfer-arrow">
          <van-icon name="arrow-down" size="24" />
        </div>
      </div>

      <!-- 转入账户卡片 -->
      <div class="form-card to-account-card" @click="showToAccountSelector = true">
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">{{ toAccountDisplayName || '转入账户' }}</div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 使用标准的van-cell-group样式 -->
      <van-cell-group inset>
        <!-- 日期 -->
        <van-cell
          title="日期"
          :value="formatDateDisplay(localFormData.date)"
          is-link
          @click="showDateCalendar = true"
        />

        <!-- 备注 -->
        <van-field
          v-model="localFormData.description"
          label="备注"
          placeholder="请输入备注（可选）"
          type="textarea"
          rows="2"
          autosize
        />
      </van-cell-group>
    </van-form>

    <!-- 转出账户选择器 -->
    <van-popup v-model:show="showFromAccountSelector" position="bottom">
      <van-picker
        :columns="accountOptions"
        @cancel="showFromAccountSelector = false"
        @confirm="onFromAccountConfirm"
      />
    </van-popup>

    <!-- 转入账户选择器 -->
    <van-popup v-model:show="showToAccountSelector" position="bottom">
      <van-picker
        :columns="toAccountOptions"
        @cancel="showToAccountSelector = false"
        @confirm="onToAccountConfirm"
      />
    </van-popup>

    <!-- 币种选择器 -->
    <van-popup v-model:show="showCurrencySelector" position="bottom">
      <van-picker
        :columns="currencyOptions"
        @cancel="showCurrencySelector = false"
        @confirm="onCurrencyConfirm"
      />
    </van-popup>

    <!-- 日历组件 -->
    <van-calendar
      v-model:show="showDateCalendar"
      title="选择日期"
      :default-date="localFormData.date"
      :min-date="new Date(2025, 5, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onDateConfirm"
      @close="showDateCalendar = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { showToast } from 'vant'
import { getAccountsByType } from '@/api/accounts'

interface Props {
  formData: {
    amount: string
    fromAccount: string
    toAccount: string
    date: Date
    description: string
    currency?: string
  }
}

interface Emits {
  (e: 'update', data: any): void
  (e: 'submit', data: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localFormData = ref({ 
  ...props.formData,
  currency: props.formData.currency || 'CNY'
})

// 弹窗状态
const showFromAccountSelector = ref(false)
const showToAccountSelector = ref(false)
const showCurrencySelector = ref(false)
const showDateCalendar = ref(false)

interface Option {
  text: string
  value: string
}

// 选项数据
const accountOptions = ref<Option[]>([])
const currencyOptions = ref<Option[]>([
  { text: '人民币 (CNY)', value: 'CNY' },
  { text: '美元 (USD)', value: 'USD' },
  { text: '欧元 (EUR)', value: 'EUR' },
  { text: '英镑 (GBP)', value: 'GBP' },
  { text: '日元 (JPY)', value: 'JPY' },
  { text: '港币 (HKD)', value: 'HKD' },
  { text: '台币 (TWD)', value: 'TWD' },
  { text: '澳元 (AUD)', value: 'AUD' },
  { text: '加元 (CAD)', value: 'CAD' },
  { text: '新加坡元 (SGD)', value: 'SGD' }
])

// 账户格式化函数（参考首页格式化方式）
const formatAccountNameForDisplay = (accountName: string) => {
  if (!accountName) return ''
  
  // 去掉第一级账户名称（Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(':')
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(':')
    
    // 进一步处理：去掉第一个"-"以及前面的字母部分
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

// 计算属性
const fromAccountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.fromAccount)
})

const toAccountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.toAccount)
})

const toAccountOptions = computed(() => {
  // 排除已选择的转出账户
  return accountOptions.value.filter(item => item.value !== localFormData.value.fromAccount)
})



const isFormValid = computed(() => {
  return localFormData.value.amount && 
         localFormData.value.fromAccount && 
         localFormData.value.toAccount &&
         localFormData.value.fromAccount !== localFormData.value.toAccount
})

// 监听数据变化
watch(localFormData, (newData) => {
  // 只在不是从props更新时才emit
  if (!isUpdatingFromProps) {
    emit('update', newData)
  }
}, { deep: true })

// 避免循环更新的标志
let isUpdatingFromProps = false
watch(() => props.formData, (newData) => {
  // 避免循环更新：只在有实质性变化且不是来自内部更新时更新
  if (newData && !isUpdatingFromProps) {
    // 检查是否真的有变化
    const hasSignificantChange = 
      newData.amount !== localFormData.value.amount ||
      newData.fromAccount !== localFormData.value.fromAccount ||
      newData.toAccount !== localFormData.value.toAccount ||
      newData.description !== localFormData.value.description
    
    if (hasSignificantChange) {
      console.log('TransferForm收到新的formData:', newData)
      
      isUpdatingFromProps = true
      localFormData.value = { 
        ...newData,
        currency: newData.currency || 'CNY'
      }
      // 下一个tick后重置标志
      nextTick(() => {
        isUpdatingFromProps = false
      })
    }
  }
}, { deep: true })

// 监听转出账户变化，清空转入账户
watch(() => localFormData.value.fromAccount, (newValue, oldValue) => {
  if (newValue !== oldValue && localFormData.value.toAccount === newValue) {
    localFormData.value.toAccount = ''
  }
})

// 币种符号获取函数
const getCurrencySymbol = (currency: string) => {
  const symbols: Record<string, string> = {
    'CNY': '¥',
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'HKD': 'HK$',
    'TWD': 'NT$',
    'AUD': 'A$',
    'CAD': 'C$',
    'SGD': 'S$'
  }
  return symbols[currency] || currency
}

const onCurrencyConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.currency = selectedValues[0]
  showCurrencySelector.value = false
}

// 日期处理
const formatDateDisplay = (date: Date) => {
  if (!date) return '选择日期'
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const onDateConfirm = (date: Date) => {
  localFormData.value.date = date
  showDateCalendar.value = false
}

// 方法
const onAmountInput = (value: string | number) => {
  // 确保 value 是字符串类型
  const stringValue = String(value || '')
  
  // 格式化金额输入
  const numericValue = stringValue.replace(/[^\d.]/g, '')
  const parts = numericValue.split('.')
  if (parts.length > 2) {
    parts.splice(2)
  }
  if (parts[1] && parts[1].length > 2) {
    parts[1] = parts[1].substring(0, 2)
  }
  localFormData.value.amount = parts.join('.')
}

const onFromAccountConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.fromAccount = selectedValues[0]
  showFromAccountSelector.value = false
}

const onToAccountConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.toAccount = selectedValues[0]
  showToAccountSelector.value = false
}



const onSubmit = () => {
  if (!isFormValid.value) {
    showToast('请填写完整信息')
    return
  }

  const amount = parseFloat(localFormData.value.amount)
  if (isNaN(amount) || amount <= 0) {
    showToast('请输入有效金额')
    return
  }

  if (localFormData.value.fromAccount === localFormData.value.toAccount) {
    showToast('转出账户和转入账户不能相同')
    return
  }

  emit('submit', {
    ...localFormData.value,
    amount
  })
}

const loadAccountOptions = async () => {
  console.log('=== TransferForm loadAccountOptions 开始 ===')
  
  try {
    // 从API获取资产和负债账户列表
    console.log('正在加载转账账户列表...')
    const response = await getAccountsByType()
    console.log('转账表单API完整响应:', response)
    const accountData = response.data || response
    console.log('转账表单账户数据:', accountData)
    console.log('转账表单账户数据类型:', typeof accountData)
    
    // 处理后端返回的按类型分组的数据格式
    let accounts: string[] = []
    if (accountData && typeof accountData === 'object') {
      console.log('转账表单Assets账户:', accountData.Assets)
      console.log('转账表单Liabilities账户:', accountData.Liabilities)
      
      // 提取 Assets 和 Liabilities 类型的账户
      const assetsAccounts: string[] = accountData.Assets || []
      const liabilitiesAccounts: string[] = accountData.Liabilities || []
      accounts = [...assetsAccounts, ...liabilitiesAccounts]
      
      console.log('转账表单合并后的账户列表:', accounts)
    } else {
      console.warn('转账表单账户数据格式不正确或为空:', accountData)
    }
    
    accountOptions.value = accounts.map((acc: string) => ({
      text: formatAccountNameForDisplay(acc),
      value: acc
    }))
    
    console.log('转账表单最终账户选项:', accountOptions.value)
    console.log('转账表单账户选项数量:', accountOptions.value.length)
  } catch (error) {
    console.error('转账表单获取账户列表失败:', error)
    console.error('转账表单错误详情:', (error as any).response || (error as any).message || error)
    
    // 备用硬编码数据
    console.log('转账表单使用备用账户数据')
    accountOptions.value = [
      { text: formatAccountNameForDisplay('Assets:ZJ-资金:现金'), value: 'Assets:ZJ-资金:现金' },
      { text: formatAccountNameForDisplay('Assets:ZJ-资金:活期存款'), value: 'Assets:ZJ-资金:活期存款' },
      { text: formatAccountNameForDisplay('Assets:ZJ-资金:香港招行'), value: 'Assets:ZJ-资金:香港招行' },
      { text: formatAccountNameForDisplay('Liabilities:XYK-信用卡:招行:8164'), value: 'Liabilities:XYK-信用卡:招行:8164' },
      { text: formatAccountNameForDisplay('Liabilities:XYK-信用卡:招行:经典白'), value: 'Liabilities:XYK-信用卡:招行:经典白' }
    ]
  }
  
  console.log('=== TransferForm loadAccountOptions 结束 ===')
}

onMounted(() => {
  loadAccountOptions()
})
</script>

<style scoped>
.transfer-form {
  padding: 0;
  background: #f7f8fa;
  min-height: 100vh;
}

/* 表单卡片基础样式 */
.form-card {
  display: flex;
  align-items: center;
  background: white;
  border-radius: 16px;
  padding: 16px;
  margin: 16px;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
  cursor: pointer;
}

.form-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7f8fa;
  border-radius: 12px;
  margin-right: 16px;
  color: #646566;
  font-size: 20px;
}

.card-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-label {
  font-size: 16px;
  color: #323233;
  font-weight: 500;
}

/* 转出账户卡片 */
.from-account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

/* 金额卡片 */
.amount-card {
  background: linear-gradient(135deg, #fff 0%, #f9f9f9 100%);
}

.amount-card .card-icon {
  background: rgba(52, 168, 83, 0.1);
  color: #34a853;
}

.amount-input-container {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.currency-selector {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.currency-selector:hover {
  background: #ebedf0;
}

.currency-symbol {
  font-size: 24px;
  font-weight: bold;
  color: #323233;
}

.amount-field {
  flex: 1;
}

.amount-field :deep(.van-field__control) {
  font-size: 24px;
  font-weight: bold;
  text-align: left;
  color: #323233;
}

.amount-field :deep(.van-field__control::placeholder) {
  color: #c8c9cc;
}

/* 转账箭头 */
.transfer-arrow-container {
  display: flex;
  justify-content: center;
  margin: -6px 16px;
  position: relative;
  z-index: 1;
}

.transfer-arrow {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #34a853 0%, #4caf50 100%);
  border-radius: 50%;
  color: white;
  box-shadow: 0 4px 12px rgba(52, 168, 83, 0.3);
}

/* 转入账户卡片 */
.to-account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}



/* 使用标准 van-cell-group 样式 */
:deep(.van-cell-group--inset) {
  margin: 16px;
}
</style>