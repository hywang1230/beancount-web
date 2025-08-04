<template>
  <div class="transaction-form">
    <van-form @submit="onSubmit">
      <!-- 金额输入 -->
      <div class="amount-section">
        <div class="amount-label">{{ type === 'expense' ? '支出金额' : '收入金额' }}</div>
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

      <!-- 表单字段 -->
      <van-cell-group inset>
        <!-- 收款人/付款人 -->
        <van-field
          v-model="localFormData.payee"
          :label="type === 'expense' ? '收款人' : '付款人'"
          placeholder="请输入"
          right-icon="arrow"
          readonly
          @click="showPayeeSelector = true"
        />

        <!-- 账户 -->
        <van-field
          v-model="accountName"
          label="账户"
          placeholder="请选择账户"
          right-icon="arrow"
          readonly
          @click="showAccountSelector = true"
        />

        <!-- 分类 -->
        <van-field
          v-model="categoryName"
          label="分类"
          placeholder="请选择分类"
          right-icon="arrow"
          readonly
          @click="showCategorySelector = true"
        />

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
          保存
        </van-button>
      </div>
    </van-form>

    <!-- 收款人选择器 -->
    <van-popup v-model:show="showPayeeSelector" position="bottom">
      <van-picker
        :columns="payeeOptions"
        @cancel="showPayeeSelector = false"
        @confirm="onPayeeConfirm"
      />
    </van-popup>

    <!-- 账户选择器 -->
    <van-popup v-model:show="showAccountSelector" position="bottom">
      <van-picker
        :columns="accountOptions"
        @cancel="showAccountSelector = false"
        @confirm="onAccountConfirm"
      />
    </van-popup>

    <!-- 分类选择器 -->
    <van-popup v-model:show="showCategorySelector" position="bottom">
      <van-picker
        :columns="categoryOptions"
        @cancel="showCategorySelector = false"
        @confirm="onCategoryConfirm"
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
  type: 'expense' | 'income'
  formData: {
    amount: string
    payee: string
    account: string
    category: string
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
const showPayeeSelector = ref(false)
const showAccountSelector = ref(false)
const showCategorySelector = ref(false)
const showDatePicker = ref(false)

interface Option {
  text: string
  value: string
}

// 选项数据
const payeeOptions = ref<Option[]>([])
const accountOptions = ref<Option[]>([])
const categoryOptions = ref<Option[]>([])

// 计算属性
const accountName = computed(() => {
  const account = accountOptions.value.find(item => item.value === localFormData.value.account)
  return account?.text || ''
})

const categoryName = computed(() => {
  const category = categoryOptions.value.find(item => item.value === localFormData.value.category)
  return category?.text || ''
})

const dateText = computed(() => {
  return localFormData.value.date.toLocaleDateString('zh-CN')
})

const isFormValid = computed(() => {
  return localFormData.value.amount && 
         localFormData.value.payee && 
         localFormData.value.account && 
         localFormData.value.category
})

// 监听数据变化
watch(localFormData, (newData) => {
  emit('update', newData)
}, { deep: true })

watch(() => props.formData, (newData) => {
  localFormData.value = { ...newData }
}, { deep: true })

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

const onPayeeConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.payee = selectedValues[0]
  showPayeeSelector.value = false
}

const onAccountConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.account = selectedValues[0]
  showAccountSelector.value = false
}

const onCategoryConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.category = selectedValues[0]
  showCategorySelector.value = false
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

  emit('submit', {
    ...localFormData.value,
    amount: props.type === 'expense' ? -amount : amount
  })
}

const loadOptions = async () => {
  try {
    // 加载收款人选项
    payeeOptions.value = [
      { text: '星巴克', value: '星巴克' },
      { text: '麦当劳', value: '麦当劳' },
      { text: '超市', value: '超市' },
      { text: '地铁', value: '地铁' },
      { text: '公司', value: '公司' }
    ]

    // 加载账户选项
    accountOptions.value = [
      { text: '招商银行储蓄卡', value: 'cmb' },
      { text: '支付宝', value: 'alipay' },
      { text: '微信钱包', value: 'wechat' },
      { text: '现金', value: 'cash' }
    ]

    // 加载分类选项
    if (props.type === 'expense') {
      categoryOptions.value = [
        { text: '餐饮美食', value: 'food' },
        { text: '交通出行', value: 'transport' },
        { text: '购物消费', value: 'shopping' },
        { text: '生活缴费', value: 'bills' },
        { text: '医疗健康', value: 'medical' },
        { text: '文化娱乐', value: 'entertainment' }
      ]
    } else {
      categoryOptions.value = [
        { text: '工资收入', value: 'salary' },
        { text: '兼职收入', value: 'parttime' },
        { text: '投资收益', value: 'investment' },
        { text: '其他收入', value: 'other' }
      ]
    }
  } catch (error) {
    console.error('加载选项数据失败:', error)
  }
}

onMounted(() => {
  loadOptions()
})
</script>

<style scoped>
.transaction-form {
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

.submit-section {
  margin-top: 32px;
  padding: 0 16px;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
}
</style>