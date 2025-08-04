<template>
  <div class="h5-recurring">
    <!-- 筛选和搜索 -->
    <van-sticky>
      <div class="filter-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索周期记账"
          @search="onSearch"
        />
        <van-dropdown-menu>
          <van-dropdown-item v-model="filterStatus" :options="statusOptions" />
          <van-dropdown-item v-model="filterFrequency" :options="frequencyOptions" />
        </van-dropdown-menu>
      </div>
    </van-sticky>

    <!-- 周期记账列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <van-cell-group>
          <van-swipe-cell
            v-for="item in recurringList"
            :key="item.id"
          >
            <van-cell
              :title="item.description"
              :label="getRecurringInfo(item)"
              :value="formatAmount(item.amount)"
              :value-class="item.amount > 0 ? 'positive' : 'negative'"
              is-link
              @click="viewRecurring(item)"
            >
              <template #icon>
                <div class="recurring-icon">
                  <van-icon :name="getRecurringIcon(item.type)" />
                </div>
              </template>
              <template #right-icon>
                <van-tag 
                  :type="getStatusTagType(item.status)"
                >
                  {{ getStatusText(item.status) }}
                </van-tag>
              </template>
            </van-cell>
            
            <!-- 滑动操作 -->
            <template #right>
              <van-button
                square
                type="primary"
                text="编辑"
                @click="editRecurring(item)"
              />
              <van-button
                square
                :type="item.status === 'active' ? 'warning' : 'success'"
                :text="item.status === 'active' ? '暂停' : '启用'"
                @click="toggleStatus(item)"
              />
              <van-button
                square
                type="danger"
                text="删除"
                @click="deleteRecurring(item)"
              />
            </template>
          </van-swipe-cell>
        </van-cell-group>
      </van-list>
    </van-pull-refresh>

    <!-- 添加按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="addRecurring"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'

const router = useRouter()

const searchKeyword = ref('')
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const fabOffset = ref({ x: -24, y: -100 })
const filterStatus = ref('all')
const filterFrequency = ref('all')
interface RecurringItem {
  id: number
  description: string
  type: string
  amount: number
  frequency: string
  status: string
  nextExecuteDate: string
  account: string
  category: string
}

const recurringList = ref<RecurringItem[]>([])

const statusOptions = [
  { text: '全部状态', value: 'all' },
  { text: '启用中', value: 'active' },
  { text: '已暂停', value: 'paused' },
  { text: '已停止', value: 'stopped' }
]

const frequencyOptions = [
  { text: '全部频率', value: 'all' },
  { text: '每日', value: 'daily' },
  { text: '每周', value: 'weekly' },
  { text: '每月', value: 'monthly' },
  { text: '每年', value: 'yearly' }
]

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY'
  }).format(amount)
}

const getRecurringInfo = (item: any) => {
  const frequencyText = getFrequencyText(item.frequency)
  const nextDate = new Date(item.nextExecuteDate).toLocaleDateString('zh-CN')
  return `${frequencyText} • 下次执行: ${nextDate}`
}

const getFrequencyText = (frequency: string) => {
  const textMap: Record<string, string> = {
    'daily': '每日',
    'weekly': '每周',
    'monthly': '每月',
    'yearly': '每年'
  }
  return textMap[frequency] || frequency
}

const getRecurringIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'income': 'arrow-up',
    'expense': 'arrow-down',
    'transfer': 'exchange'
  }
  return iconMap[type] || 'replay'
}

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    'active': '启用',
    'paused': '暂停',
    'stopped': '停止'
  }
  return textMap[status] || status
}

const getStatusTagType = (status: string): 'primary' | 'success' | 'danger' | 'warning' | 'default' => {
  const typeMap: Record<string, 'primary' | 'success' | 'danger' | 'warning' | 'default'> = {
    'active': 'success',
    'paused': 'warning',
    'stopped': 'danger'
  }
  return typeMap[status] || 'default'
}

const viewRecurring = (item: any) => {
  router.push(`/h5/recurring/${item.id}`)
}

const editRecurring = (item: any) => {
  router.push(`/h5/recurring/edit/${item.id}`)
}

const addRecurring = () => {
  router.push('/h5/recurring/add')
}

const toggleStatus = async (item: any) => {
  try {
    const newStatus = item.status === 'active' ? 'paused' : 'active'
    const actionText = newStatus === 'active' ? '启用' : '暂停'
    
    await showConfirmDialog({
      title: `确认${actionText}`,
      message: `确定要${actionText}这个周期记账吗？`
    })
    
    // 这里应该调用API更新状态
    item.status = newStatus
    
    showToast(`${actionText}成功`)
  } catch {
    // 用户取消操作
  }
}

const deleteRecurring = async (item: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这个周期记账吗？删除后无法恢复。'
    })
    
    // 这里应该调用API删除
    const index = recurringList.value.findIndex(r => r.id === item.id)
    if (index > -1) {
      recurringList.value.splice(index, 1)
    }
    
    showToast('删除成功')
  } catch {
    // 用户取消删除
  }
}

const onSearch = () => {
  loadRecurringList(true)
}

const onRefresh = async () => {
  await loadRecurringList(true)
  refreshing.value = false
}

const onLoad = async () => {
  await loadRecurringList(false)
}

const loadRecurringList = async (isRefresh = false) => {
  try {
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const mockData = [
      {
        id: 1,
        description: '房租',
        type: 'expense',
        amount: -3000.00,
        frequency: 'monthly',
        status: 'active',
        nextExecuteDate: '2024-02-01',
        account: '招商银行',
        category: '住房'
      },
      {
        id: 2,
        description: '工资收入',
        type: 'income',
        amount: 8000.00,
        frequency: 'monthly',
        status: 'active',
        nextExecuteDate: '2024-02-05',
        account: '招商银行',
        category: '工资'
      },
      {
        id: 3,
        description: '手机话费',
        type: 'expense',
        amount: -89.00,
        frequency: 'monthly',
        status: 'active',
        nextExecuteDate: '2024-02-10',
        account: '支付宝',
        category: '通讯'
      },
      {
        id: 4,
        description: '健身房会员费',
        type: 'expense',
        amount: -200.00,
        frequency: 'monthly',
        status: 'paused',
        nextExecuteDate: '2024-02-15',
        account: '微信',
        category: '健康'
      }
    ]
    
    if (isRefresh) {
      recurringList.value = mockData
    } else {
      recurringList.value.push(...mockData)
    }
    
    finished.value = recurringList.value.length >= 20
  } catch (error) {
    console.error('加载周期记账列表失败:', error)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRecurringList(true)
})
</script>

<style scoped>
.h5-recurring {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.filter-section {
  background-color: white;
  border-bottom: 1px solid #ebedf0;
}

.filter-section :deep(.van-search) {
  padding: 8px 16px;
}

.recurring-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f7f8fa;
  border-radius: 50%;
  margin-right: 12px;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-cell-group) {
  margin: 0;
}

:deep(.van-tag) {
  margin-left: 8px;
}
</style>