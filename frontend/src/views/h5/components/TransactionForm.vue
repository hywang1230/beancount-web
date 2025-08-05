<template>
  <div class="transaction-form">
    <van-form @submit="onSubmit">
      <!-- 账户选择卡片 -->
      <div class="form-card account-card" @click="showAccountSelector = true">
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">{{ accountDisplayName || '选择账户' }}</div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 金额输入卡片 -->
      <div class="form-card amount-card">
        <div class="card-icon">
          <van-icon name="plus" />
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
            @input="onAmountInput"
          />
        </div>
      </div>

      <!-- 分类选择卡片 -->
      <div class="form-card category-card" @click="showCategorySelector = true; currentCategoryIndex = 0">
        <div class="card-icon">
          <van-icon name="apps-o" />
        </div>
        <div class="card-content">
          <div class="card-label">
            {{ localFormData.categories[0]?.categoryDisplayName || '选择 分类' }}
          </div>
          <div class="multi-category-btn" @click.stop="showMultiCategorySheet = true">
            多类别
            <van-icon name="filter-o" />
          </div>
        </div>
      </div>

      <!-- 使用标准的van-cell-group样式 -->
      <van-cell-group inset>
        <!-- 日期 -->
        <van-field
          v-model="dateValue"
          type="date"
          label="日期"
          placeholder="请选择日期"
        />

        <!-- 交易对象 -->
        <van-field
          v-model="localFormData.payee"
          label="交易对象"
          placeholder="请输入交易对象（可选）"
          :right-icon="localFormData.payee ? 'clear' : 'add-o'"
          readonly
          @click="handlePayeeClick"
          @click-right-icon="handlePayeeRightIcon"
        />

        <!-- 状态选择 -->
        <van-cell title="交易状态">
          <template #value>
            <div class="status-buttons">
              <van-button 
                size="mini"
                :type="localFormData.flag === '*' ? 'primary' : 'default'"
                @click="localFormData.flag = '*'"
              >
                已确认
              </van-button>
              <van-button 
                size="mini"
                :type="localFormData.flag === '!' ? 'warning' : 'default'"
                @click="localFormData.flag = '!'"
              >
                待定中
              </van-button>
            </div>
          </template>
        </van-cell>

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

    <!-- 收款人输入弹窗 -->
    <van-popup v-model:show="showPayeeInput" position="bottom">
      <div class="payee-input-popup">
        <div class="popup-header">
          <van-button type="default" @click="showPayeeInput = false">取消</van-button>
          <span class="popup-title">选择交易对象</span>
          <van-button type="primary" @click="confirmPayee">确定</van-button>
        </div>
        
        <div class="payee-input-section">
          <van-field
            v-model="tempPayee"
            placeholder="输入交易对象名称"
            clearable
          />
        </div>
        
        <div class="payee-history">
          <div class="history-title">历史记录</div>
          <van-cell-group>
            <van-cell
              v-for="payee in payeeOptions"
              :key="payee.value"
              :title="payee.text"
              is-link
              @click="selectPayeeFromHistory(payee.value)"
            />
          </van-cell-group>
        </div>
      </div>
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

    <!-- 币种选择器 -->
    <van-popup v-model:show="showCurrencySelector" position="bottom">
      <van-picker
        :columns="currencyOptions"
        @cancel="showCurrencySelector = false"
        @confirm="onCurrencyConfirm"
      />
    </van-popup>

    <!-- 多类别分配面板 -->
    <van-action-sheet 
      v-model:show="showMultiCategorySheet" 
      title="分类分配"
      closeable
    >
      <div class="multi-category-content">
        <div class="category-items">
          <div 
            v-for="(item, index) in localFormData.categories" 
            :key="index"
            class="category-item"
          >
            <div class="category-row">
              <van-field
                v-model="item.categoryDisplayName"
                placeholder="选择分类"
                readonly
                class="category-field"
                @click="showCategorySelector = true; currentCategoryIndex = index"
              />
              <van-field
                v-model="item.amount"
                type="digit"
                placeholder="0.00"
                class="amount-field-small"
                @input="(value) => onCategoryAmountInput(index, value)"
              />
              <van-button 
                v-if="localFormData.categories.length > 1"
                size="mini" 
                type="danger" 
                plain
                @click="removeCategory(index)"
              >
                删除
              </van-button>
            </div>
          </div>
        </div>
        
        <div class="category-actions">
          <van-button 
            type="primary" 
            size="small"
            @click="addCategory"
          >
            添加分类
          </van-button>
        </div>
        
        <div class="amount-summary">
          <span>已分配: ¥{{ allocatedAmount.toFixed(2) }}</span>
          <span>剩余: ¥{{ remainingAmount.toFixed(2) }}</span>
        </div>
      </div>
    </van-action-sheet>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { showToast } from 'vant'
import { getPayees } from '@/api/transactions'
import { getAccountsByType } from '@/api/accounts'

interface CategoryItem {
  categoryName: string
  categoryDisplayName: string
  category: string
  amount: string
}

interface Props {
  type: 'expense' | 'income' | 'adjustment'
  formData: {
    amount: string
    payee: string
    account: string
    category: string
    date: Date
    description: string
    currency?: string
    flag?: string
    categories?: CategoryItem[]
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
  currency: props.formData.currency || 'CNY',
  flag: props.formData.flag || '*',
  categories: props.formData.categories || [{ categoryName: '', categoryDisplayName: '', category: '', amount: '' }]
})

// 弹窗状态
const showPayeeInput = ref(false)
const showAccountSelector = ref(false)
const showCategorySelector = ref(false)
const showCurrencySelector = ref(false)
const showMultiCategorySheet = ref(false)

// 临时数据
const tempPayee = ref('')
const currentCategoryIndex = ref(0)

interface Option {
  text: string
  value: string
}

// 选项数据
const payeeOptions = ref<Option[]>([])
const accountOptions = ref<Option[]>([])
const categoryOptions = ref<Option[]>([])
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
const accountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.account)
})

// 日期值计算属性（用于type="date"的field）
const dateValue = computed({
  get: () => {
    const date = localFormData.value.date
    return date.toISOString().split('T')[0] // 格式: YYYY-MM-DD
  },
  set: (value: string) => {
    if (value) {
      localFormData.value.date = new Date(value)
    }
  }
})

// 分配金额计算
const allocatedAmount = computed(() => {
  return localFormData.value.categories.reduce((sum, item) => {
    const amount = parseFloat(item.amount) || 0
    return sum + amount
  }, 0)
})

const remainingAmount = computed(() => {
  const totalAmount = parseFloat(localFormData.value.amount) || 0
  return totalAmount - allocatedAmount.value
})

const isFormValid = computed(() => {
  const hasBasicInfo = localFormData.value.amount && 
                      localFormData.value.account
  
  const hasValidCategories = localFormData.value.categories.length > 0 && 
                            localFormData.value.categories.every(cat => cat.category && cat.amount)
  
  const amountsMatch = Math.abs(remainingAmount.value) < 0.01 // 允许小数误差
  
  return hasBasicInfo && hasValidCategories && amountsMatch
})

// 监听数据变化
watch(localFormData, (newData) => {
  emit('update', newData)
}, { deep: true })

// 暂时禁用 props.formData 的 watch，避免与用户输入冲突
// watch(() => props.formData, (newData) => {
//   // ... watch logic
// }, { deep: true, immediate: false })

// 币种相关方法
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



// 智能分配金额的函数
const updateCategoryAmounts = (totalAmount: string) => {
  // 只在有有效金额时才执行分配
  if (!totalAmount || parseFloat(totalAmount) <= 0) {
    return
  }
  
  // 如果只有一个分类且金额为空，自动分配全部金额
  if (localFormData.value.categories.length === 1 && !localFormData.value.categories[0].amount) {
    localFormData.value.categories[0].amount = totalAmount
    return
  }
}

// 方法  
const onAmountInput = (value: string | number) => {
  console.log('onAmountInput called with:', value, typeof value)
  
  // 延迟执行，避免与分类金额输入冲突
  nextTick(() => {
    const totalAmount = localFormData.value.amount || ''
    
    if (localFormData.value.categories.length === 1) {
      // 单分类情况：总是同步总金额到分类金额
      localFormData.value.categories[0].amount = totalAmount
    } else if (localFormData.value.categories.length > 1) {
      // 多分类情况：分配给第一个空的分类
      const firstEmptyCategory = localFormData.value.categories.find(cat => !cat.amount)
      if (firstEmptyCategory && totalAmount) {
        firstEmptyCategory.amount = totalAmount
      }
    }
  })
}

const onCategoryAmountInput = (index: number, value: string | number) => {
  console.log(`Category ${index} amount input:`, value, typeof value)
  
  // 确保分类数组存在且索引有效
  if (!localFormData.value.categories[index]) {
    console.error(`Category at index ${index} does not exist`)
    return
  }
  
  // 直接更新分类金额，不影响总金额
  const stringValue = String(value || '')
  localFormData.value.categories[index].amount = stringValue
  
  console.log(`Updated category ${index} amount to:`, stringValue)
  console.log('Current categories:', localFormData.value.categories)
}

// 收款人相关方法
const handlePayeeClick = () => {
  showPayeeInput.value = true
}

const handlePayeeRightIcon = () => {
  if (localFormData.value.payee) {
    // 清除收款人
    localFormData.value.payee = ''
  } else {
    // 显示选择器
    showPayeeInput.value = true
  }
}

const confirmPayee = () => {
  if (tempPayee.value.trim()) {
    localFormData.value.payee = tempPayee.value.trim()
    showPayeeInput.value = false
    tempPayee.value = ''
  }
}

const selectPayeeFromHistory = (payee: string) => {
  localFormData.value.payee = payee
  showPayeeInput.value = false
  tempPayee.value = ''
}

// 账户选择
const onAccountConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  localFormData.value.account = selectedValues[0]
  showAccountSelector.value = false
}

// 分类管理
const addCategory = () => {
  localFormData.value.categories.push({ categoryName: '', categoryDisplayName: '', category: '', amount: '' })
}

const removeCategory = (index: number) => {
  if (localFormData.value.categories.length > 1) {
    localFormData.value.categories.splice(index, 1)
  }
}

const onCategoryConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  const index = currentCategoryIndex.value
  const selectedCategory = categoryOptions.value.find(opt => opt.value === selectedValues[0])
  
  if (selectedCategory) {
    localFormData.value.categories[index].category = selectedCategory.value // 原始值用于提交
    localFormData.value.categories[index].categoryName = selectedCategory.text // 保持兼容
    localFormData.value.categories[index].categoryDisplayName = formatAccountNameForDisplay(selectedCategory.value) // 格式化显示值
  }
  
  showCategorySelector.value = false
}



const onSubmit = () => {
  if (!isFormValid.value) {
    if (!localFormData.value.amount) {
      showToast('请输入金额')
    } else if (!localFormData.value.account) {
      showToast('请选择账户')
    } else if (Math.abs(remainingAmount.value) >= 0.01) {
      showToast('分类金额分配不匹配')
    } else {
      showToast('请填写完整信息')
    }
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
    // 加载收款人历史
    try {
      const payeeData = await getPayees()
      payeeOptions.value = Array.isArray(payeeData) 
        ? payeeData.map(p => ({ text: p, value: p }))
        : []
    } catch (error) {
      console.error('获取收款人列表失败:', error)
      payeeOptions.value = []
    }

    // 加载账户选项 - 资产和负债账户
    try {
      const accountData = await getAccountsByType()
      console.log('获取到的账户数据:', accountData)
      
      // 处理后端返回的按类型分组的数据格式
      let accounts = []
      if (accountData && typeof accountData === 'object') {
        // 提取 Assets 和 Liabilities 类型的账户
        const assetsAccounts = accountData.Assets || []
        const liabilitiesAccounts = accountData.Liabilities || []
        accounts = [...assetsAccounts, ...liabilitiesAccounts]
      }
      
      accountOptions.value = accounts.map((acc: string) => ({
        text: formatAccountNameForDisplay(acc),
        value: acc
      }))
        
      console.log('处理后的账户选项:', accountOptions.value)
    } catch (error) {
      console.error('获取账户列表失败:', error)
      // 备用硬编码数据
      accountOptions.value = [
        { text: formatAccountNameForDisplay('Assets:ZJ-资金:现金'), value: 'Assets:ZJ-资金:现金' },
        { text: formatAccountNameForDisplay('Assets:ZJ-资金:活期存款'), value: 'Assets:ZJ-资金:活期存款' },
        { text: formatAccountNameForDisplay('Liabilities:XYK-信用卡:招行:8164'), value: 'Liabilities:XYK-信用卡:招行:8164' }
      ]
    }

    // 加载分类选项
    try {
      const categoryData = await getAccountsByType()
      console.log('获取到的分类数据:', categoryData)
      
      // 处理后端返回的按类型分组的数据格式
      let categories = []
      if (categoryData && typeof categoryData === 'object') {
        // 根据交易类型选择对应的分类
        if (props.type === 'expense') {
          categories = categoryData.Expenses || []
        } else {
          categories = categoryData.Income || []
        }
      }
      
      categoryOptions.value = categories.map((acc: string) => ({
        text: formatAccountNameForDisplay(acc),
        value: acc
      }))
        
      console.log('处理后的分类选项:', categoryOptions.value)
    } catch (error) {
      console.error('获取分类列表失败:', error)
      // 备用硬编码数据
      if (props.type === 'expense') {
        categoryOptions.value = [
          { text: formatAccountNameForDisplay('Expenses:CY-餐饮'), value: 'Expenses:CY-餐饮' },
          { text: formatAccountNameForDisplay('Expenses:JT-交通:公交'), value: 'Expenses:JT-交通:公交' },
          { text: formatAccountNameForDisplay('Expenses:JT-交通:打车'), value: 'Expenses:JT-交通:打车' },
          { text: formatAccountNameForDisplay('Expenses:YL-娱乐:其他'), value: 'Expenses:YL-娱乐:其他' }
        ]
      } else {
        categoryOptions.value = [
          { text: formatAccountNameForDisplay('Income:GZ-工资'), value: 'Income:GZ-工资' },
          { text: formatAccountNameForDisplay('Income:TZ-投资'), value: 'Income:TZ-投资' },
          { text: formatAccountNameForDisplay('Income:QT-其他'), value: 'Income:QT-其他' }
        ]
      }
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

/* 账户卡片 */
.account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

/* 金额卡片 */
.amount-card {
  background: linear-gradient(135deg, #fff 0%, #f9f9f9 100%);
}

.amount-card .card-icon {
  background: rgba(238, 90, 82, 0.1);
  color: #ee5a52;
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

/* 分类卡片 */
.category-card .card-icon {
  background: rgba(52, 168, 83, 0.1);
  color: #34a853;
}

.multi-category-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: #f7f8fa;
  border-radius: 8px;
  font-size: 14px;
  color: #646566;
  cursor: pointer;
}

/* 多类别面板样式 */
.multi-category-content {
  padding: 16px;
}

.category-items {
  margin-bottom: 16px;
}

.category-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 12px;
}

.category-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.category-field {
  flex: 2;
}

.amount-field-small {
  flex: 1;
  min-width: 80px;
}

.category-actions {
  text-align: center;
  margin-bottom: 16px;
}

.amount-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f7f8fa;
  border-radius: 12px;
  font-size: 14px;
  color: #646566;
}

/* 收款人输入弹窗样式 */
.payee-input-popup {
  background: white;
  border-radius: 16px 16px 0 0;
  max-height: 70vh;
  overflow: hidden;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
}

.popup-title {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.payee-input-section {
  padding: 16px;
}

.payee-history {
  max-height: 300px;
  overflow-y: auto;
}

.history-title {
  padding: 16px;
  font-size: 14px;
  color: #646566;
  background: #f7f8fa;
}

/* 状态按钮样式 */
.status-buttons {
  display: flex;
  gap: 8px;
}

.status-buttons :deep(.van-button--mini) {
  min-width: 60px;
  height: 28px;
  font-size: 12px;
  border-radius: 14px;
}



/* 使用标准 van-cell-group 样式 */
:deep(.van-cell-group--inset) {
  margin: 16px;
}

:deep(.van-button--mini) {
  min-width: 60px;
  height: 28px;
  font-size: 12px;
}
</style>