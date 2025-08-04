<template>
  <div class="transfer-form">
    <van-form @submit="onSubmit">
      <!-- 金额输入 -->
      <div class="amount-section">
        <div class="amount-label">转账金额</div>
        <div class="amount-input">
          <span class="currency">¥</span>
          <van-field
            v-model="localFormData.amount"
            type="digit"
            placeholder="0.00"
            class="amount-field"
            :border="false"
            @input="onAmountInput"
          />
        </div>
      </div>

      <!-- 转账路径 -->
      <div class="transfer-path">
        <div class="account-selector">
          <div class="account-label">转出账户</div>
          <van-field
            v-model="fromAccountName"
            placeholder="请选择转出账户"
            right-icon="arrow"
            readonly
            @click="showFromAccountSelector = true"
          />
        </div>
        
        <div class="transfer-arrow">
          <van-icon name="arrow-down" />
        </div>
        
        <div class="account-selector">
          <div class="account-label">转入账户</div>
          <van-field
            v-model="toAccountName"
            placeholder="请选择转入账户"
            right-icon="arrow"
            readonly
            @click="showToAccountSelector = true"
          />
        </div>
      </div>

      <!-- 表单字段 -->
      <van-cell-group inset>
        <!-- 日期 -->
        <van-field
          v-model="dateText"
          label="日期"
          placeholder="请选择日期"
          right-icon="arrow"
          readonly
          @click="showDatePicker = true"
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

      <!-- 提交按钮 -->
      <div class="submit-section">
        <van-button
          type="primary"
          size="large"
          round
          :disabled="!isFormValid"
          @click="onSubmit"
        >
          确认转账
        </van-button>
      </div>
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

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom">
      <van-date-picker
        v-model="localFormData.date"
        title="选择日期"
        @cancel="showDatePicker = false"
        @confirm="onDateConfirm"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { showToast } from 'vant'

interface Props {
  formData: {
    amount: string
    fromAccount: string
    toAccount: string
    date: Date
    description: string
  }
}

interface Emits {
  (e: 'update', data: any): void
  (e: 'submit', data: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localFormData = ref({ ...props.formData })

// 弹窗状态
const showFromAccountSelector = ref(false)
const showToAccountSelector = ref(false)
const showDatePicker = ref(false)

interface Option {
  text: string
  value: string
}

// 选项数据
const accountOptions = ref<Option[]>([])

// 计算属性
const fromAccountName = computed(() => {
  const account = accountOptions.value.find(item => item.value === localFormData.value.fromAccount)
  return account?.text || ''
})

const toAccountName = computed(() => {
  const account = accountOptions.value.find(item => item.value === localFormData.value.toAccount)
  return account?.text || ''
})

const toAccountOptions = computed(() => {
  // 排除已选择的转出账户
  return accountOptions.value.filter(item => item.value !== localFormData.value.fromAccount)
})

const dateText = computed(() => {
  return localFormData.value.date.toLocaleDateString('zh-CN')
})

const isFormValid = computed(() => {
  return localFormData.value.amount && 
         localFormData.value.fromAccount && 
         localFormData.value.toAccount &&
         localFormData.value.fromAccount !== localFormData.value.toAccount
})

// 监听数据变化
watch(localFormData, (newData) => {
  emit('update', newData)
}, { deep: true })

watch(() => props.formData, (newData) => {
  localFormData.value = { ...newData }
}, { deep: true })

// 监听转出账户变化，清空转入账户
watch(() => localFormData.value.fromAccount, (newValue, oldValue) => {
  if (newValue !== oldValue && localFormData.value.toAccount === newValue) {
    localFormData.value.toAccount = ''
  }
})

// 方法
const onAmountInput = (value: string) => {
  // 格式化金额输入
  const numericValue = value.replace(/[^\d.]/g, '')
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

const onDateConfirm = () => {
  showDatePicker.value = false
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
  try {
    // 这里应该从API获取账户列表
    accountOptions.value = [
      { text: '招商银行储蓄卡', value: 'cmb' },
      { text: '支付宝', value: 'alipay' },
      { text: '微信钱包', value: 'wechat' },
      { text: '现金', value: 'cash' },
      { text: '建设银行储蓄卡', value: 'ccb' },
      { text: '工商银行储蓄卡', value: 'icbc' }
    ]
  } catch (error) {
    console.error('加载账户选项失败:', error)
  }
}

onMounted(() => {
  loadAccountOptions()
})
</script>

<style scoped>
.transfer-form {
  padding: 16px;
}

.amount-section {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  text-align: center;
}

.amount-label {
  font-size: 14px;
  color: #646566;
  margin-bottom: 16px;
}

.amount-input {
  display: flex;
  align-items: center;
  justify-content: center;
}

.currency {
  font-size: 32px;
  color: #323233;
  margin-right: 8px;
}

.amount-field {
  flex: 1;
  max-width: 200px;
}

.amount-field :deep(.van-field__control) {
  font-size: 32px;
  font-weight: bold;
  text-align: left;
  color: #323233;
}

.amount-field :deep(.van-field__control::placeholder) {
  color: #c8c9cc;
}

.transfer-path {
  background-color: white;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.account-selector {
  margin-bottom: 16px;
}

.account-selector:last-child {
  margin-bottom: 0;
}

.account-label {
  font-size: 14px;
  color: #646566;
  margin-bottom: 8px;
  padding-left: 16px;
}

.transfer-arrow {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 16px 0;
  color: #969799;
  font-size: 20px;
}

.submit-section {
  margin-top: 32px;
  padding: 0 16px;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
}

:deep(.van-field__control) {
  font-size: 16px;
}
</style>