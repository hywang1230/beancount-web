<template>
  <div class="recurring-form">
    <van-form @submit="onSubmit">
      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息">
        <van-field
          v-model="form.name"
          name="name"
          label="名称"
          placeholder="请输入周期记账名称"
          :rules="[{ required: true, message: '请输入名称' }]"
        />
        <van-field
          v-model="form.description"
          name="description"
          label="描述"
          placeholder="可选的描述信息"
          type="textarea"
          rows="2"
        />
        <van-field
          v-model="form.narration"
          name="narration"
          label="摘要"
          placeholder="请输入交易摘要"
          :rules="[{ required: true, message: '请输入摘要' }]"
        />
      </van-cell-group>

      <!-- 周期设置 -->
      <van-cell-group inset title="周期设置">
        <van-field name="recurrence_type" label="周期类型">
          <template #input>
            <van-picker
              v-model="recurrenceTypeValue"
              :columns="recurrenceTypeColumns"
              @confirm="onRecurrenceTypeConfirm"
            >
              <template #default>
                <van-cell
                  :value="getRecurrenceTypeText(form.recurrence_type)"
                  is-link
                  @click="showRecurrenceTypePicker = true"
                />
              </template>
            </van-picker>
          </template>
        </van-field>
        
        <!-- 每周特定几天 -->
        <van-field v-if="form.recurrence_type === 'weekly'" name="weekly_days" label="星期">
          <template #input>
            <van-checkbox-group v-model="form.weekly_days" direction="horizontal">
              <van-checkbox 
                v-for="(day, index) in weekDays" 
                :key="index"
                :name="index"
                :label="day"
                icon-size="14px"
              />
            </van-checkbox-group>
          </template>
        </van-field>
        
        <!-- 每月特定几日 -->
        <van-field v-if="form.recurrence_type === 'monthly'" name="monthly_days" label="日期">
          <template #input>
            <div class="monthly-days-grid">
              <van-checkbox-group v-model="form.monthly_days">
                <van-checkbox 
                  v-for="day in 31" 
                  :key="day"
                  :name="day"
                  :label="day + '日'"
                  icon-size="12px"
                />
              </van-checkbox-group>
            </div>
          </template>
        </van-field>
        
        <van-field
          v-model="form.start_date"
          name="start_date"
          label="开始日期"
          placeholder="选择开始日期"
          readonly
          is-link
          @click="showStartDatePicker = true"
          :rules="[{ required: true, message: '请选择开始日期' }]"
        />
        <van-field
          v-model="form.end_date"
          name="end_date"
          label="结束日期"
          placeholder="可选的结束日期"
          readonly
          is-link
          @click="showEndDatePicker = true"
        />
      </van-cell-group>

      <!-- 交易信息 -->
      <van-cell-group inset title="交易信息">
        <van-field
          v-model="form.payee"
          name="payee"
          label="收付方"
          placeholder="可选的收付方"
        />
      </van-cell-group>

      <!-- 记账分录 -->
      <van-cell-group inset title="记账分录">
        <div v-for="(posting, index) in form.postings" :key="index" class="posting-item">
          <van-field
            v-model="posting.account"
            :name="`posting-${index}-account`"
            label="账户"
            placeholder="选择账户"
            readonly
            is-link
            @click="selectAccount(index)"
            :rules="[{ required: true, message: '请选择账户' }]"
          />
          <van-field
            v-model.number="posting.amount"
            :name="`posting-${index}-amount`"
            label="金额"
            type="number"
            placeholder="请输入金额"
            :rules="[{ required: true, message: '请输入金额' }]"
          />
          <van-field :name="`posting-${index}-currency`" label="货币">
            <template #input>
              <van-cell
                :value="posting.currency"
                is-link
                @click="selectCurrency(index)"
              />
            </template>
          </van-field>
          <van-cell v-if="form.postings.length > 2">
            <template #title>
              <van-button 
                type="danger" 
                size="small" 
                @click="removePosting(index)"
              >
                删除分录
              </van-button>
            </template>
          </van-cell>
        </div>
        
        <van-cell>
          <template #title>
            <van-button type="primary" size="small" @click="addPosting">
              添加分录
            </van-button>
            <div class="balance-info">
              <span class="balance-label">金额合计：</span>
              <span :class="['balance-amount', isBalanced ? 'balanced' : 'unbalanced']">
                {{ totalAmount.toFixed(2) }}
              </span>
              <van-tag :type="isBalanced ? 'success' : 'danger'" size="small">
                {{ isBalanced ? '平衡' : '不平衡' }}
              </van-tag>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 提交按钮 -->
      <div class="submit-section">
        <van-button 
          round 
          block 
          type="primary" 
          native-type="submit"
          :loading="submitLoading"
        >
          {{ isEdit ? '更新周期记账' : '创建周期记账' }}
        </van-button>
      </div>
    </van-form>

    <!-- 周期类型选择器 -->
    <van-popup v-model:show="showRecurrenceTypePicker" position="bottom">
      <van-picker
        :columns="recurrenceTypeColumns"
        @confirm="onRecurrenceTypeConfirm"
        @cancel="showRecurrenceTypePicker = false"
      />
    </van-popup>

    <!-- 开始日期选择器 -->
    <van-popup v-model:show="showStartDatePicker" position="bottom">
      <van-date-picker
        v-model="startDateValue"
        @confirm="onStartDateConfirm"
        @cancel="showStartDatePicker = false"
      />
    </van-popup>

    <!-- 结束日期选择器 -->
    <van-popup v-model:show="showEndDatePicker" position="bottom">
      <van-date-picker
        v-model="endDateValue"
        @confirm="onEndDateConfirm"
        @cancel="showEndDatePicker = false"
      />
    </van-popup>

    <!-- 货币选择器 -->
    <van-popup v-model:show="showCurrencyPicker" position="bottom">
      <van-picker
        :columns="currencyColumns"
        @confirm="onCurrencyConfirm"
        @cancel="showCurrencyPicker = false"
      />
    </van-popup>

    <!-- 账户选择器 -->
    <H5AccountSelector 
      ref="accountSelectorRef"
      @confirm="onAccountSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { recurringApi, type RecurringTransactionCreate } from '@/api/recurring'
import H5AccountSelector from './H5AccountSelector.vue'

interface Props {
  isEdit?: boolean
  editId?: string
}

const props = withDefaults(defineProps<Props>(), {
  isEdit: false,
  editId: ''
})

const router = useRouter()
const route = useRoute()

// 表单数据
const form = ref<RecurringTransactionCreate>({
  name: '',
  description: '',
  recurrence_type: 'daily',
  start_date: '',
  end_date: '',
  weekly_days: [],
  monthly_days: [],
  flag: '*',
  payee: '',
  narration: '',
  tags: [],
  links: [],
  postings: [
    { account: '', amount: 0, currency: 'CNY' },
    { account: '', amount: 0, currency: 'CNY' }
  ],
  is_active: true
})

// 界面状态
const submitLoading = ref(false)
const showRecurrenceTypePicker = ref(false)
const showStartDatePicker = ref(false)
const showEndDatePicker = ref(false)
const showCurrencyPicker = ref(false)
const currentAccountIndex = ref(-1)
const currentCurrencyIndex = ref(-1)
const accountSelectorRef = ref()

// 选择器数据
const recurrenceTypeValue = ref(['daily'])
const startDateValue = ref([new Date().getFullYear(), new Date().getMonth() + 1, new Date().getDate()])
const endDateValue = ref([new Date().getFullYear(), new Date().getMonth() + 1, new Date().getDate()])

const recurrenceTypeColumns = [
  { text: '每日', value: 'daily' },
  { text: '工作日', value: 'weekdays' },
  { text: '每周特定几天', value: 'weekly' },
  { text: '每月特定几日', value: 'monthly' }
]

const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const currencyColumns = [
  { text: 'CNY', value: 'CNY' },
  { text: 'USD', value: 'USD' },
  { text: 'EUR', value: 'EUR' },
  { text: 'JPY', value: 'JPY' }
]

// 计算属性
const totalAmount = computed(() => {
  return form.value.postings.reduce((sum, posting) => {
    return sum + (parseFloat(posting.amount?.toString() || '0') || 0)
  }, 0)
})

const isBalanced = computed(() => {
  return Math.abs(totalAmount.value) < 0.01
})

// 方法
const getRecurrenceTypeText = (type: string) => {
  const item = recurrenceTypeColumns.find(col => col.value === type)
  return item?.text || type
}

const onRecurrenceTypeConfirm = (option: any) => {
  form.value.recurrence_type = option.value
  form.value.weekly_days = []
  form.value.monthly_days = []
  showRecurrenceTypePicker.value = false
}

const onStartDateConfirm = (values: number[]) => {
  const [year, month, day] = values
  form.value.start_date = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`
  startDateValue.value = values
  showStartDatePicker.value = false
}

const onEndDateConfirm = (values: number[]) => {
  const [year, month, day] = values
  form.value.end_date = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`
  endDateValue.value = values
  showEndDatePicker.value = false
}

const selectAccount = (index: number) => {
  currentAccountIndex.value = index
  accountSelectorRef.value?.show()
}

const onAccountSelected = (account: string) => {
  if (currentAccountIndex.value >= 0) {
    form.value.postings[currentAccountIndex.value].account = account
  }
}

const selectCurrency = (index: number) => {
  currentCurrencyIndex.value = index
  showCurrencyPicker.value = true
}

const onCurrencyConfirm = (option: any) => {
  if (currentCurrencyIndex.value >= 0) {
    form.value.postings[currentCurrencyIndex.value].currency = option.value
  }
  showCurrencyPicker.value = false
}

const addPosting = () => {
  form.value.postings.push({ account: '', amount: 0, currency: 'CNY' })
}

const removePosting = (index: number) => {
  if (form.value.postings.length > 2) {
    form.value.postings.splice(index, 1)
  }
}

const validateForm = () => {
  // 检验分录平衡
  if (!isBalanced.value) {
    showToast(`分录金额之和必须为0，当前和为：${totalAmount.value.toFixed(2)}`)
    return false
  }
  
  // 检验至少有两个分录
  if (form.value.postings.length < 2) {
    showToast('至少需要两个分录')
    return false
  }
  
  // 检验分录账户不能为空
  const emptyAccounts = form.value.postings.filter(p => !p.account?.trim())
  if (emptyAccounts.length > 0) {
    showToast('所有分录都必须选择账户')
    return false
  }

  return true
}

const onSubmit = async () => {
  if (!validateForm()) {
    return
  }

  try {
    submitLoading.value = true
    
    const dataToSend = {
      ...form.value,
      postings: form.value.postings.map(p => ({
        account: p.account,
        amount: parseFloat(p.amount?.toString() || '0') || 0,
        currency: p.currency
      }))
    }
    
    if (props.isEdit) {
      await recurringApi.update(props.editId, dataToSend)
      showToast('更新成功')
    } else {
      await recurringApi.create(dataToSend)
      showToast('创建成功')
    }
    
    router.back()
  } catch (error) {
    console.error('保存失败:', error)
    showToast('保存失败')
  } finally {
    submitLoading.value = false
  }
}

// 编辑模式下加载数据
const loadEditData = async () => {
  if (props.isEdit && props.editId) {
    try {
      const data = await recurringApi.get(props.editId)
      Object.assign(form.value, {
        ...data,
        weekly_days: data.weekly_days || [],
        monthly_days: data.monthly_days || [],
        tags: data.tags || [],
        links: data.links || [],
        postings: data.postings.map((p: any) => ({
          account: p.account,
          amount: parseFloat(p.amount) || 0,
          currency: p.currency || 'CNY'
        }))
      })
    } catch (error) {
      console.error('加载数据失败:', error)
      showToast('加载数据失败')
    }
  }
}

onMounted(() => {
  if (props.isEdit) {
    loadEditData()
  }
})
</script>

<style scoped>
.recurring-form {
  padding: 16px;
  background-color: #f7f8fa;
  min-height: 100vh;
}

.posting-item {
  border-bottom: 1px solid #ebedf0;
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.posting-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.monthly-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  padding: 8px 0;
}

.balance-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 12px;
}

.balance-label {
  color: #646566;
}

.balance-amount {
  font-weight: 500;
}

.balance-amount.balanced {
  color: #07c160;
}

.balance-amount.unbalanced {
  color: #ee0a24;
}

.submit-section {
  margin-top: 24px;
  padding: 0 16px;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
}

:deep(.van-checkbox) {
  margin-right: 12px;
  margin-bottom: 8px;
}

:deep(.van-checkbox__label) {
  font-size: 12px;
}
</style>