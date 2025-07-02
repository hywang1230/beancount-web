<template>
  <div class="page-container">
    <h1 class="page-title">新增交易</h1>
    
    <el-card>
      <el-form
        ref="formRef"
        :model="transactionForm"
        :rules="formRules"
        label-width="100px"
        @submit.prevent="submitTransaction"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="日期" prop="date">
              <el-date-picker
                v-model="transactionForm.date"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="标记" prop="flag">
              <el-select v-model="transactionForm.flag" style="width: 100%">
                <el-option label="已确认 (*)" value="*" />
                <el-option label="待确认 (!)" value="!" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="收付方">
              <el-input v-model="transactionForm.payee" placeholder="收付方名称" />
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="摘要">
              <el-input v-model="transactionForm.narration" placeholder="请输入摘要" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 分录列表 -->
        <el-form-item label="分录明细">
          <div class="posting-tips">
            <el-alert
              title="提示：金额支持公式计算（如 1+2+3），最多只能有一个分录不填金额"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 16px"
            />
          </div>
          <div class="postings-container">
            <div 
              v-for="(posting, index) in transactionForm.postings"
              :key="index"
              class="posting-row"
            >
              <el-row :gutter="16" align="middle">
                <el-col :span="14">
                  <el-select
                    v-model="posting.account"
                    filterable
                    remote
                    placeholder="选择账户"
                    :remote-method="searchAccounts"
                    :loading="accountLoading"
                    @change="onAccountChange(index)"
                    @focus="onAccountFocus"
                    style="width: 100%"
                    popper-class="account-select-dropdown"
                    :no-data-text="accountSuggestions.length === 0 ? '未找到匹配账户' : ''"
                    reserve-keyword
                  >
                    <el-option
                      v-for="account in accountSuggestions"
                      :key="account"
                      :label="account"
                      :value="account"
                    >
                      <span style="float: left">{{ account }}</span>
                      <span style="float: right; color: #8492a6; font-size: 13px">
                        {{ getAccountType(account) }}
                      </span>
                    </el-option>
                  </el-select>
                </el-col>
                
                <el-col :span="5">
                  <el-input
                    v-model="posting.amount"
                    placeholder="金额或公式 (如: 1+2+3, 可为空)"
                    :class="{ 
                      'negative-amount': posting.computedAmount && posting.computedAmount < 0,
                      'formula-input': isFormula(posting.amount),
                      'empty-amount': !posting.amount || posting.amount.trim() === '',
                      'invalid-amount': posting.amount && posting.amount.trim() !== '' && posting.computedAmount === undefined
                    }"
                    @input="(value: string) => onAmountInput(posting, value)"
                    @blur="onAmountBlur(posting)"
                    @keydown="onAmountKeydown(posting, $event)"
                  >
                    <template #suffix v-if="posting.computedAmount !== undefined && posting.amount !== posting.computedAmount.toString()">
                      <span class="computed-result">= {{ posting.computedAmount.toFixed(2) }}</span>
                    </template>
                  </el-input>
                </el-col>
                
                <el-col :span="3">
                  <el-select v-model="posting.currency" style="width: 100%">
                    <el-option label="CNY" value="CNY" />
                    <el-option label="USD" value="USD" />
                  </el-select>
                </el-col>
                
                <el-col :span="2">
                  <el-button
                    type="danger"
                    size="small"
                    :disabled="transactionForm.postings.length <= 2"
                    @click="removePosting(index)"
                  >
                    删除
                  </el-button>
                </el-col>
              </el-row>
            </div>
            
            <el-button type="primary" plain @click="addPosting">
              <el-icon><Plus /></el-icon>
              添加分录
            </el-button>
          </div>
        </el-form-item>
        
        <!-- 标签 -->
        <el-form-item label="标签">
          <el-tag
            v-for="tag in transactionForm.tags"
            :key="tag"
            closable
            @close="removeTag(tag)"
          >
            {{ tag }}
          </el-tag>
          
          <el-input
            v-if="tagInputVisible"
            v-model="tagInputValue"
            ref="tagInputRef"
            size="small"
            style="width: 100px; margin-left: 10px"
            @keyup.enter="addTag"
            @blur="addTag"
          />
          
          <el-button
            v-else
            size="small"
            @click="showTagInput"
          >
            + 新标签
          </el-button>
        </el-form-item>
        
        <!-- 提交按钮 -->
        <el-form-item>
          <el-button type="primary" @click="submitTransaction" :loading="submitting">
            保存交易
          </el-button>
          <el-button @click="resetForm">重置</el-button>
          <el-button @click="$router.go(-1)">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createTransaction } from '@/api/transactions'
import { getAllAccounts } from '@/api/accounts'

const formRef = ref()
const tagInputRef = ref()
const submitting = ref(false)
const accountLoading = ref(false)
const accountSuggestions = ref<string[]>([])
const allAccounts = ref<string[]>([])
const tagInputVisible = ref(false)
const tagInputValue = ref('')

interface Posting {
  account: string
  amount: string
  currency: string
  computedAmount?: number
}

const transactionForm = reactive({
  date: new Date().toISOString().split('T')[0],
  flag: '*',
  payee: '',
  narration: '',
  tags: [] as string[],
  postings: [
    { account: '', amount: '', currency: 'CNY', computedAmount: undefined } as Posting,
    { account: '', amount: '', currency: 'CNY', computedAmount: undefined } as Posting
  ] as Posting[]
})

const formRules = {
  date: [{ required: true, message: '请选择日期', trigger: 'blur' }],
  flag: [{ required: true, message: '请选择标记', trigger: 'blur' }]
}

// 初始化时加载所有账户
onMounted(async () => {
  await loadAllAccounts()
})

// 加载所有账户
const loadAllAccounts = async () => {
  try {
    const response = await getAllAccounts()
    
    // getAllAccounts 直接返回字符串数组，不是包装在data中
    const accounts = response.data || response || []
    
    allAccounts.value = Array.isArray(accounts) ? accounts : []
    accountSuggestions.value = allAccounts.value // 显示所有账户
    
    console.log('加载账户成功，总数:', allAccounts.value.length)
  } catch (error) {
    console.error('加载账户列表失败:', error)
    ElMessage.error('加载账户列表失败')
    // 设置默认值避免后续错误
    allAccounts.value = []
    accountSuggestions.value = []
  }
}

// 搜索账户
const searchAccounts = async (query: string) => {
  if (!query || query.length === 0) {
    // 如果查询为空，显示所有账户
    accountSuggestions.value = allAccounts.value
    return
  }
  
  // 本地搜索，支持更智能的匹配
  const queryLower = query.toLowerCase()
  const filtered = allAccounts.value.filter(account => {
    const accountLower = account.toLowerCase()
    
    // 支持多种匹配方式：
    // 1. 完整包含匹配
    if (accountLower.includes(queryLower)) return true
    
    // 2. 按:分割后的部分匹配
    const parts = account.split(':')
    for (const part of parts) {
      if (part.toLowerCase().includes(queryLower)) return true
    }
    
    // 3. 拼音首字母匹配等可以在这里扩展
    return false
  })
  
  // 按匹配度排序：优先显示精确匹配和前缀匹配
  filtered.sort((a, b) => {
    const aLower = a.toLowerCase()
    const bLower = b.toLowerCase()
    
    // 精确匹配优先
    if (aLower === queryLower && bLower !== queryLower) return -1
    if (bLower === queryLower && aLower !== queryLower) return 1
    
    // 前缀匹配优先
    if (aLower.startsWith(queryLower) && !bLower.startsWith(queryLower)) return -1
    if (bLower.startsWith(queryLower) && !aLower.startsWith(queryLower)) return 1
    
    // 最后按字母顺序
    return a.localeCompare(b)
  })
  
  accountSuggestions.value = filtered
}

// 账户选择器获得焦点时显示所有账户
const onAccountFocus = () => {
  if (accountSuggestions.value.length === 0 && allAccounts.value.length > 0) {
    accountSuggestions.value = allAccounts.value
  }
}

// 获取账户类型
const getAccountType = (account: string): string => {
  if (account.startsWith('Assets:')) return '资产'
  if (account.startsWith('Liabilities:')) return '负债'
  if (account.startsWith('Expenses:')) return '支出'
  if (account.startsWith('Income:')) return '收入'
  if (account.startsWith('Equity:')) return '权益'
  return '其他'
}

// 账户变化处理
const onAccountChange = (_index: number) => {
  // 可以在这里添加账户变化的逻辑
}

// 添加分录
const addPosting = () => {
  transactionForm.postings.push({
    account: '',
    amount: '',
    currency: 'CNY',
    computedAmount: undefined
  } as Posting)
}

// 删除分录
const removePosting = (index: number) => {
  transactionForm.postings.splice(index, 1)
}

// 显示标签输入框
const showTagInput = () => {
  tagInputVisible.value = true
  nextTick(() => {
    tagInputRef.value?.focus()
  })
}

// 添加标签
const addTag = () => {
  const tag = tagInputValue.value.trim()
  if (tag && !transactionForm.tags.includes(tag)) {
    transactionForm.tags.push(tag)
  }
  
  tagInputVisible.value = false
  tagInputValue.value = ''
}

// 删除标签
const removeTag = (tag: string) => {
  const index = transactionForm.tags.indexOf(tag)
  if (index > -1) {
    transactionForm.tags.splice(index, 1)
  }
}

// 验证分录规则
const validatePostings = (): string | null => {
  const postingsWithAccount = transactionForm.postings.filter(p => p.account.trim() !== '')
  
  if (postingsWithAccount.length < 2) {
    return '至少需要两个有效分录（包含账户）'
  }
  
  // 检查金额规则：最多只能有一个分录不填金额
  const emptyAmountPostings = postingsWithAccount.filter(p => 
    p.amount.trim() === '' || p.computedAmount === undefined
  )
  
  if (emptyAmountPostings.length > 1) {
    return '最多只能有一个分录不填金额'
  }
  
  // 检查有金额的分录是否都有有效的计算结果
  const postingsWithAmount = postingsWithAccount.filter(p => 
    p.amount.trim() !== '' && p.computedAmount !== undefined
  )
  
  const invalidAmountPostings = postingsWithAmount.filter(p => p.computedAmount === null)
  if (invalidAmountPostings.length > 0) {
    return '存在无效的金额或公式，请检查输入'
  }
  
  // 如果所有分录都有金额，检查借贷平衡
  if (emptyAmountPostings.length === 0) {
    const sum = postingsWithAmount.reduce((total, posting) => total + (posting.computedAmount || 0), 0)
    if (Math.abs(sum) > 0.01) {
      return '借贷不平衡，请检查金额'
    }
  }
  
  return null
}

// 提交交易
const submitTransaction = async () => {
  try {
    await formRef.value.validate()
    
    // 验证分录规则
    const validationError = validatePostings()
    if (validationError) {
      ElMessage.error(validationError)
      return
    }
    
    submitting.value = true
    
    // 准备提交数据
    const validPostings = transactionForm.postings
      .filter(p => p.account.trim() !== '')
      .map(posting => {
        const result = {
          account: posting.account,
          currency: posting.currency
        } as any
        
        // 只有非空金额才添加amount字段
        if (posting.amount.trim() !== '' && posting.computedAmount !== undefined) {
          result.amount = posting.computedAmount
        }
        
        return result
      })
    
    const transactionData = {
      ...transactionForm,
      postings: validPostings
    }
    
    await createTransaction(transactionData)
    ElMessage.success('交易创建成功')
    
    // 重置表单或跳转
    resetForm()
    
  } catch (error) {
    console.error('提交交易失败:', error)
    ElMessage.error('提交交易失败，请重试')
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  transactionForm.date = new Date().toISOString().split('T')[0]
  transactionForm.flag = '*'
  transactionForm.payee = ''
  transactionForm.narration = ''
  transactionForm.tags = []
  transactionForm.postings = [
    { account: '', amount: '', currency: 'CNY', computedAmount: undefined } as Posting,
    { account: '', amount: '', currency: 'CNY', computedAmount: undefined } as Posting
  ]
  
  formRef.value?.clearValidate()
}

// 格式化金额


// 金额输入框失去焦点时的处理
const onAmountBlur = (posting: Posting) => {
  // 如果是空值，不做处理（允许空值）
  if (posting.amount === '' || posting.amount.trim() === '') {
    posting.computedAmount = undefined
    return
  }
  
  // 如果是公式，检查计算结果
  if (isFormula(posting.amount)) {
    const result = evaluateFormula(posting.amount)
    if (result !== null) {
      posting.computedAmount = result
    } else {
      // 公式无效，清除计算结果
      posting.computedAmount = undefined
      ElMessage.warning('公式格式错误，请检查输入')
    }
  } else {
    // 如果是普通数字，格式化
    const numValue = parseFloat(posting.amount)
    if (!isNaN(numValue)) {
      posting.computedAmount = numValue
      // 可选：格式化显示
      // posting.amount = numValue.toFixed(2)
    } else {
      posting.computedAmount = undefined
      ElMessage.warning('金额格式错误，请输入有效数字或公式')
    }
  }
}

// 金额输入框按键处理
const onAmountKeydown = (posting: Posting, event: KeyboardEvent) => {
  // 按Ctrl+Enter或Enter键快速计算公式
  if ((event.ctrlKey && event.key === 'Enter') || event.key === 'Enter') {
    if (isFormula(posting.amount)) {
      event.preventDefault()
      const result = evaluateFormula(posting.amount)
      if (result !== null) {
        posting.amount = result.toFixed(2)
        posting.computedAmount = result
      }
    }
  }
}

// 检查是否为公式
const isFormula = (value: string): boolean => {
  // 添加类型检查
  if (typeof value !== 'string' || !value || value.trim() === '') return false
  // 包含运算符且不只是负号的情况
  return /[+\-*/()]/.test(value) && !/^-?[\d.]*$/.test(value)
}

// 计算公式结果
const evaluateFormula = (formula: string): number | null => {
  try {
    // 清理输入，只允许数字、小数点、基本运算符和括号
    const cleanFormula = formula.replace(/[^0-9+\-*/.() ]/g, '')
    if (cleanFormula !== formula) {
      return null // 包含非法字符
    }
    
    // 使用 Function 构造器安全地计算表达式
    const result = Function(`"use strict"; return (${cleanFormula})`)()
    
    if (typeof result === 'number' && !isNaN(result) && isFinite(result)) {
      return result
    }
    return null
  } catch {
    return null
  }
}

// 金额输入处理
const onAmountInput = (posting: Posting, value: string | number) => {
  // 安全地将输入值转换为字符串
  const stringValue = value?.toString() || ''
  const trimmedValue = stringValue.trim()
  
  posting.amount = trimmedValue
  
  if (trimmedValue === '') {
    posting.computedAmount = undefined
    return
  }
  
  if (isFormula(trimmedValue)) {
    // 如果是公式，尝试计算结果
    const result = evaluateFormula(trimmedValue)
    posting.computedAmount = result || undefined
  } else {
    // 如果是普通数字，直接解析
    const numValue = parseFloat(trimmedValue)
    posting.computedAmount = isNaN(numValue) ? undefined : numValue
  }
}
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.postings-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
  width: 100%;
}

.posting-row {
  margin-bottom: 16px;
}

.posting-row:last-child {
  margin-bottom: 0;
}

.negative-amount :deep(.el-input__inner) {
  color: #f56c6c;
  border-color: #f56c6c;
}

.negative-amount :deep(.el-input__inner):focus {
  border-color: #f56c6c;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.2);
}

.formula-input :deep(.el-input__inner) {
  color: #409eff;
  border-color: #409eff;
}

.formula-input :deep(.el-input__inner):focus {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.computed-result {
  color: #606266;
  font-size: 0.8em;
  margin-left: 4px;
}

.posting-row .el-input :deep(.el-input__inner) {
  transition: all 0.3s ease;
}

.posting-row .el-input :deep(.el-input__inner):focus {
  transform: none;
}

/* 公式输入提示 */
.formula-input :deep(.el-input__inner)::placeholder {
  color: #409eff;
  opacity: 0.7;
}

/* 空金额分录的样式 */
.empty-amount :deep(.el-input__inner) {
  background-color: #f0f9ff;
  border-color: #91d5ff;
}

/* 错误状态样式 */
.invalid-amount :deep(.el-input__inner) {
  border-color: #ff4d4f;
  background-color: #fff2f0;
}

/* 账户下拉列表样式 */
:deep(.account-select-dropdown) {
  max-height: 300px;
}

:deep(.account-select-dropdown .el-select-dropdown__item) {
  height: auto;
  line-height: 1.4;
  padding: 8px 20px;
  white-space: normal;
  word-wrap: break-word;
}

:deep(.account-select-dropdown .el-select-dropdown__item:hover) {
  background-color: #f5f7fa;
}

/* 账户类型标签样式 */
.account-type-tag {
  display: inline-block;
  padding: 2px 6px;
  background-color: #f0f2f5;
  border-radius: 3px;
  font-size: 11px;
  color: #666;
}
</style> 