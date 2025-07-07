<template>
  <!--
    PayeeSelector - 通用收付方选择组件
    
    功能特点:
    - 支持从历史记录中下拉选择收付方
    - 支持自由输入新的收付方名称
    - 支持搜索过滤历史记录
    - 自动加载历史收付方数据
    
    使用场景:
    - 新增交易时选择收付方
    - 周期记账设置收付方
    - 其他需要收付方输入的表单
  -->
  <el-select
    v-model="selectedPayee"
    :placeholder="placeholder"
    filterable
    allow-create
    default-first-option
    :reserve-keyword="false"
    clearable
    style="width: 100%"
    @change="handleChange"
    @clear="handleClear"
  >
    <el-option
      v-for="payee in payees"
      :key="payee"
      :label="payee"
      :value="payee"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getPayees } from '@/api/transactions'

interface Props {
  modelValue?: string
  placeholder?: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'change', value: string): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '选择或输入收付方'
})

const emit = defineEmits<Emits>()

const payees = ref<string[]>([])
const loading = ref(false)

// 双向绑定
const selectedPayee = computed({
  get: () => props.modelValue,
  set: (value: string) => {
    emit('update:modelValue', value)
  }
})

// 处理选择变化
const handleChange = (value: string) => {
  emit('change', value)
}

// 处理清除操作
const handleClear = () => {
  emit('update:modelValue', '')
  emit('change', '')
}

// 加载收付方列表
const loadPayees = async () => {
  try {
    loading.value = true
    const response = await getPayees()
    // 由于响应拦截器已经返回了 response.data，所以直接使用 response
    payees.value = response || []
    console.log('获取收付方列表成功，总数:', payees.value.length)
  } catch (error) {
    console.error('获取收付方列表失败:', error)
    payees.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPayees()
})
</script>

<style scoped>
/* PayeeSelector组件样式 */
</style> 