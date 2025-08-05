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
            {{ categoryDisplayText }}
          </div>
          <div class="multi-category-btn" @click.stop="openMultiCategorySheet">
            多类别
            <van-icon name="filter-o" />
          </div>
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
    <van-popup 
      v-model:show="showMultiCategorySheet"
      position="bottom"
      :style="{ height: '80vh' }"
      round
    >
      <div class="multi-category-content">
        <!-- 自定义头部 -->
        <div class="multi-category-header">
          <van-button 
            type="default" 
            size="small"
            @click="cancelMultiCategory"
          >
            取消
          </van-button>
          <div class="header-title">分类分配</div>
          <van-button 
            type="primary" 
            size="small"
            :disabled="!isMultiCategoryValid"
            @click="confirmMultiCategory"
          >
            确认
          </van-button>
        </div>
        
        <div class="category-items">
          <div 
            v-for="(item, index) in (isEditingMultiCategory ? tempCategories : localFormData.categories)" 
            :key="index"
            class="category-item"
            :class="{ 'category-item--incomplete': !isCategoryComplete(item) }"
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
                :model-value="item.amount"
                type="digit"
                placeholder="0.00"
                class="amount-field-small"
                @update:model-value="(value) => onCategoryAmountInput(index, value)"
              />
              <van-button 
                v-if="(isEditingMultiCategory ? tempCategories : localFormData.categories).length > 1"
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
        
        <div class="amount-summary" :class="{ 
          'amount-summary--balanced': Math.abs(remainingAmount) < 0.01,
          'amount-summary--unbalanced': Math.abs(remainingAmount) >= 0.01 
        }">
          <div class="summary-row">
            <span>总金额: ¥{{ parseFloat(localFormData.amount || '0').toFixed(2) }}</span>
          </div>
          <div class="summary-row">
            <span>已分配: ¥{{ allocatedAmount.toFixed(2) }}</span>
            <span :class="{ 
              'remaining-balanced': Math.abs(remainingAmount) < 0.01,
              'remaining-positive': remainingAmount > 0.01,
              'remaining-negative': remainingAmount < -0.01
            }">
              {{ remainingAmount >= 0 ? '剩余' : '超出' }}: ¥{{ Math.abs(remainingAmount).toFixed(2) }}
            </span>
          </div>
          <div v-if="Math.abs(remainingAmount) >= 0.01" class="balance-hint">
            {{ remainingAmount > 0 ? '⚠️ 还需继续分配' : '⚠️ 分配金额超出总额' }}
          </div>
          <div v-else class="balance-hint balance-hint--success">
            ✅ 分配完成
          </div>
        </div>
      </div>
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
const showDateCalendar = ref(false)

// 多类别编辑的临时数据
const tempCategories = ref<CategoryItem[]>([])
const isEditingMultiCategory = ref(false)

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

// 分类显示名称 - 多个分类用英文逗号隔开
const categoryDisplayText = computed(() => {
  const categories = localFormData.value.categories.filter(cat => cat.categoryDisplayName)
  
  if (categories.length === 0) {
    return '选择分类'
  }
  
  if (categories.length === 1) {
    return categories[0].categoryDisplayName
  }
  
  // 多个分类用英文逗号隔开
  return categories.map(cat => cat.categoryDisplayName).join(', ')
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

// 检查单个分类是否完整
const isCategoryComplete = (category: CategoryItem) => {
  return category.category && 
         category.categoryDisplayName && 
         category.amount && 
         parseFloat(category.amount) > 0
}

// 检查多类别编辑状态下的有效性
const isMultiCategoryValid = computed(() => {
  if (!isEditingMultiCategory.value) return true
  
  const categories = tempCategories.value.length > 0 ? tempCategories.value : localFormData.value.categories
  
  // 每个分类都必须完整
  const hasValidCategories = categories.length > 0 && 
                            categories.every(cat => isCategoryComplete(cat))
  
  // 金额分配必须匹配
  const totalAmount = parseFloat(localFormData.value.amount) || 0
  const allocatedAmount = categories.reduce((sum, item) => {
    const amount = parseFloat(item.amount) || 0
    return sum + amount
  }, 0)
  const amountsMatch = Math.abs(totalAmount - allocatedAmount) < 0.01
  
  return hasValidCategories && amountsMatch
})

const isFormValid = computed(() => {
  // 基础信息校验
  const hasBasicInfo = localFormData.value.amount && 
                      localFormData.value.account &&
                      parseFloat(localFormData.value.amount) > 0
  
  // 分类校验 - 每个分类都必须有分类名称和有效金额
  const hasValidCategories = localFormData.value.categories.length > 0 && 
                            localFormData.value.categories.every(cat => isCategoryComplete(cat))
  
  // 金额分配校验 - 剩余金额必须为0
  const amountsMatch = Math.abs(remainingAmount.value) < 0.01 // 允许小数误差
  
  return hasBasicInfo && hasValidCategories && amountsMatch
})

// 监听数据变化
watch(localFormData, (newData) => {
  // 只在不是从props更新时才emit
  if (!isUpdatingFromProps) {
    emit('update', newData)
  }
}, { deep: true })

// 监听props.formData变化，用于编辑模式的数据加载
let isUpdatingFromProps = false
watch(() => props.formData, (newData) => {
  // 避免循环更新：只在有实质性变化且不是来自内部更新时更新
  if (newData && newData.amount && newData.account && !isUpdatingFromProps) {
    // 检查是否真的有变化
    const hasSignificantChange = 
      newData.amount !== localFormData.value.amount ||
      newData.account !== localFormData.value.account ||
      newData.category !== localFormData.value.category ||
      newData.payee !== localFormData.value.payee
    
    if (hasSignificantChange) {
      console.log('TransactionForm收到新的formData:', newData)
      
      isUpdatingFromProps = true
      localFormData.value = {
        ...newData,
        currency: newData.currency || 'CNY',
        flag: newData.flag || '*',
        categories: newData.categories || [{ categoryName: '', categoryDisplayName: '', category: '', amount: '' }]
      }
      // 下一个tick后重置标志
      nextTick(() => {
        isUpdatingFromProps = false
      })
    }
  }
}, { deep: true, immediate: false })

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
  
  // 获取当前编辑的分类数组
  const targetCategories = isEditingMultiCategory.value ? tempCategories.value : localFormData.value.categories
  
  // 确保分类数组存在且索引有效
  if (!targetCategories[index]) {
    console.error(`Category at index ${index} does not exist`)
    return
  }
  
  // 直接更新分类金额，不影响总金额
  const stringValue = String(value || '')
  
  // 使用 Vue 3 的响应式更新方式
  targetCategories[index] = {
    ...targetCategories[index],
    amount: stringValue
  }
  
  console.log(`Updated category ${index} amount to:`, stringValue)
  console.log('Current categories:', targetCategories)
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

// 分类管理
const addCategory = () => {
  if (isEditingMultiCategory.value) {
    tempCategories.value.push({ categoryName: '', categoryDisplayName: '', category: '', amount: '' })
  } else {
    localFormData.value.categories.push({ categoryName: '', categoryDisplayName: '', category: '', amount: '' })
  }
}

const removeCategory = (index: number) => {
  const targetCategories = isEditingMultiCategory.value ? tempCategories.value : localFormData.value.categories
  if (targetCategories.length > 1) {
    targetCategories.splice(index, 1)
  }
}

// 多类别弹窗操作
const openMultiCategorySheet = () => {
  // 开始编辑模式，复制当前数据到临时变量
  tempCategories.value = JSON.parse(JSON.stringify(localFormData.value.categories))
  isEditingMultiCategory.value = true
  showMultiCategorySheet.value = true
}

const cancelMultiCategory = () => {
  // 取消编辑，恢复原始数据
  tempCategories.value = []
  isEditingMultiCategory.value = false
  showMultiCategorySheet.value = false
}

const confirmMultiCategory = () => {
  // 确认编辑，应用临时数据
  if (tempCategories.value.length > 0) {
    localFormData.value.categories = [...tempCategories.value]
  }
  tempCategories.value = []
  isEditingMultiCategory.value = false
  showMultiCategorySheet.value = false
}

const onCategoryConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  const index = currentCategoryIndex.value
  const selectedCategory = categoryOptions.value.find(opt => opt.value === selectedValues[0])
  
  if (selectedCategory) {
    // 获取当前编辑的分类数组
    const targetCategories = isEditingMultiCategory.value ? tempCategories.value : localFormData.value.categories
    
    targetCategories[index].category = selectedCategory.value // 原始值用于提交
    targetCategories[index].categoryName = selectedCategory.text // 保持兼容
    targetCategories[index].categoryDisplayName = formatAccountNameForDisplay(selectedCategory.value) // 格式化显示值
  }
  
  showCategorySelector.value = false
}



const onSubmit = () => {
  // 基础信息校验
  if (!localFormData.value.amount) {
    showToast('请输入金额')
    return
  }
  
  if (!localFormData.value.account) {
    showToast('请选择账户')
    return
  }
  
  const amount = parseFloat(localFormData.value.amount)
  if (isNaN(amount) || amount <= 0) {
    showToast('请输入有效金额')
    return
  }
  
  // 分类校验 - 每个分类都必须有值
  const invalidCategories = []
  for (let i = 0; i < localFormData.value.categories.length; i++) {
    const category = localFormData.value.categories[i]
    
    if (!category.category || !category.categoryDisplayName) {
      invalidCategories.push(`第${i + 1}个分类未选择`)
    } else if (!category.amount || parseFloat(category.amount) <= 0) {
      invalidCategories.push(`第${i + 1}个分类金额无效`)
    }
  }
  
  if (invalidCategories.length > 0) {
    showToast(invalidCategories[0]) // 显示第一个错误
    return
  }
  
  // 金额分配校验 - 剩余金额必须为0
  if (Math.abs(remainingAmount.value) >= 0.01) {
    const remaining = remainingAmount.value
    if (remaining > 0) {
      showToast(`还需分配 ¥${remaining.toFixed(2)}`)
    } else {
      showToast(`超出分配 ¥${Math.abs(remaining).toFixed(2)}`)
    }
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
  flex: 1;
  margin-right: 8px;
  line-height: 1.4;
  max-height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
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
  height: 100%;
  display: flex;
  flex-direction: column;
}

.multi-category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
  background: white;
  position: sticky;
  top: 0;
  z-index: 1;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #323233;
}

.category-items {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 8px;
}

.category-item {
  margin-bottom: 12px;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 12px;
  transition: all 0.3s ease;
}

.category-item--incomplete {
  background: #fff2f0;
  border: 1px solid #ffccc7;
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
  padding: 8px 16px;
  border-top: 1px solid #ebedf0;
  background: white;
}

.amount-summary {
  padding: 16px;
  background: #f7f8fa;
  border-radius: 12px 12px 0 0;
  border-top: 1px solid #ebedf0;
  font-size: 14px;
  color: #646566;
  transition: all 0.3s ease;
}

.amount-summary--balanced {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.amount-summary--unbalanced {
  background: #fff2f0;
  border: 1px solid #ffccc7;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.summary-row:last-of-type {
  margin-bottom: 12px;
}

.remaining-balanced {
  color: #52c41a;
  font-weight: 500;
}

.remaining-positive {
  color: #fa8c16;
  font-weight: 500;
}

.remaining-negative {
  color: #ff4d4f;
  font-weight: 500;
}

.balance-hint {
  text-align: center;
  font-size: 13px;
  color: #fa8c16;
  padding: 8px;
  background: #fff7e6;
  border-radius: 8px;
  border: 1px solid #ffd591;
}

.balance-hint--success {
  color: #52c41a;
  background: #f6ffed;
  border-color: #b7eb8f;
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