<template>
  <div class="currency-settings">
    <!-- 主币种设置 -->
    <van-cell-group inset title="主币种设置">
      <van-cell
        title="当前主币种"
        :value="currentCurrency"
        is-link
        @click="showCurrencyPicker = true"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">用于统一显示和计算的基准货币</span>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 价格管理 -->
    <van-cell-group inset title="汇率价格管理">
      <van-cell
        title="新增汇率"
        icon="plus"
        is-link
        @click="showAddPrice = true"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">添加货币对的汇率信息</span>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 价格列表 -->
    <van-cell-group inset title="汇率列表" v-if="prices.length > 0">
      <van-cell
        v-for="price in prices"
        :key="`${price.date}-${price.from_currency}-${price.to_currency}`"
        :title="`${price.from_currency} → ${price.to_currency}`"
        :value="Number(price.rate).toFixed(4)"
        @click="editPrice(price)"
      >
        <template #label>
          <span class="cell-desc">{{ price.date }}</span>
        </template>
        <template #right-icon>
          <van-icon
            name="delete-o"
            @click.stop="confirmDeletePrice(price)"
            class="delete-icon"
          />
        </template>
      </van-cell>
      
      <!-- 加载更多 -->
      <van-cell
        v-if="hasMore"
        title="加载更多"
        is-link
        center
        @click="loadMorePrices"
        :border="false"
      />
    </van-cell-group>

    <!-- 空状态 -->
    <van-empty
      v-if="prices.length === 0 && !loading"
      description="暂无汇率数据"
      image="search"
    />

    <!-- 主币种选择弹窗 -->
    <van-popup
      v-model:show="showCurrencyPicker"
      round
      position="bottom"
    >
      <van-picker
        :columns="currencyOptions"
        @confirm="onCurrencyConfirm"
        @cancel="showCurrencyPicker = false"
        title="选择主币种"
      />
    </van-popup>

    <!-- 源货币选择弹窗 -->
    <van-popup
      v-model:show="showFromCurrencyPicker"
      round
      position="bottom"
    >
      <van-picker
        :columns="fromCurrencyOptions"
        @confirm="onFromCurrencyConfirm"
        @cancel="showFromCurrencyPicker = false"
        title="选择源货币"
      />
    </van-popup>

    <!-- 新增/编辑价格弹窗 -->
    <van-popup
      v-model:show="showAddPrice"
      round
      position="bottom"
      :style="{ height: '70%' }"
    >
      <div class="price-form">
        <div class="form-header">
          <van-button
            type="default"
            size="small"
            @click="showAddPrice = false"
          >
            取消
          </van-button>
          <h3>{{ editingPrice ? '编辑汇率' : '新增汇率' }}</h3>
          <van-button
            type="primary"
            size="small"
            @click="savePriceEntry"
            :loading="saving"
          >
            保存
          </van-button>
        </div>

        <div class="form-content">
          <van-cell-group inset>
            <van-field
              v-model="priceForm.date"
              type="date"
              label="日期"
              placeholder="选择日期"
              required
            />
            <van-field
              v-model="priceForm.from_currency"
              label="源货币"
              placeholder="选择源货币"
              required
              readonly
              is-link
              @click="showFromCurrencyPicker = true"
              :disabled="editingPrice !== null"
            >
              <template #input>
                {{ priceForm.from_currency || '选择源货币' }}
              </template>
            </van-field>
            <van-field
              v-model="priceForm.to_currency"
              label="目标货币"
              :placeholder="`主币种 ${currentCurrency}`"
              readonly
              disabled
            />
            <van-field
              v-model="priceForm.rate"
              type="number"
              label="汇率"
              placeholder="输入汇率"
              required
            />
          </van-cell-group>

          <div class="form-tip">
            <van-notice-bar
              left-icon="info-o"
              text="汇率表示 1 单位源货币等于多少主币种。目标货币固定为当前主币种"
              :scrollable="false"
            />
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import { operatingCurrencyApi, pricesApi, type PriceEntry, type PriceCreate } from '@/api/beancount'

// 常用货币列表
const allCurrencyOptions = [
  { text: 'CNY - 人民币', value: 'CNY' },
  { text: 'USD - 美元', value: 'USD' },
  { text: 'EUR - 欧元', value: 'EUR' },
  { text: 'JPY - 日元', value: 'JPY' },
  { text: 'GBP - 英镑', value: 'GBP' },
  { text: 'HKD - 港币', value: 'HKD' },
  { text: 'TWD - 新台币', value: 'TWD' },
  { text: 'SGD - 新加坡元', value: 'SGD' },
  { text: 'AUD - 澳元', value: 'AUD' },
  { text: 'CAD - 加元', value: 'CAD' }
]

// 主币种选择选项（包含所有货币）
const currencyOptions = computed(() => allCurrencyOptions)

// 源货币选择选项（排除当前主币种）
const fromCurrencyOptions = computed(() => 
  allCurrencyOptions.filter(option => option.value !== currentCurrency.value)
)

// 响应式数据
const currentCurrency = ref<string>('CNY')
const prices = ref<PriceEntry[]>([])
const loading = ref(false)
const saving = ref(false)
const showCurrencyPicker = ref(false)
const showFromCurrencyPicker = ref(false)
const showAddPrice = ref(false)
const editingPrice = ref<PriceEntry | null>(null)
const hasMore = ref(false)
const currentPage = ref(1)

// 表单数据
const priceForm = reactive<PriceCreate>({
  date: new Date().toISOString().split('T')[0],
  from_currency: '',
  to_currency: currentCurrency.value,
  rate: 0
})

// 加载主币种
const loadOperatingCurrency = async () => {
  try {
    const response = await operatingCurrencyApi.getCurrent()
    currentCurrency.value = response.operating_currency
    // 更新表单中的目标货币
    priceForm.to_currency = response.operating_currency
  } catch (error) {
    console.error('获取主币种失败:', error)
    showToast('获取主币种失败')
  }
}

// 加载价格列表
const loadPrices = async (page = 1, append = false) => {
  try {
    loading.value = true
    const response = await pricesApi.getList({
      page,
      page_size: 20
    })
    
    if (append) {
      prices.value = [...prices.value, ...response.prices]
    } else {
      prices.value = response.prices
    }
    
    hasMore.value = response.total > prices.value.length
    currentPage.value = page
  } catch (error) {
    console.error('获取价格列表失败:', error)
    showToast('获取价格列表失败')
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMorePrices = () => {
  loadPrices(currentPage.value + 1, true)
}

// 选择主币种
const onCurrencyConfirm = async ({ selectedValues }: { selectedValues: string[] }) => {
  const newCurrency = selectedValues[0]
  try {
    await operatingCurrencyApi.update({ operating_currency: newCurrency })
    currentCurrency.value = newCurrency
    // 更新表单中的目标货币
    priceForm.to_currency = newCurrency
    showToast(`主币种已更新为 ${newCurrency}`)
    showCurrencyPicker.value = false
    // 重新加载价格列表
    loadPrices()
  } catch (error) {
    console.error('更新主币种失败:', error)
    showToast('更新主币种失败')
  }
}

// 选择源货币
const onFromCurrencyConfirm = ({ selectedValues }: { selectedValues: string[] }) => {
  const selectedCurrency = selectedValues[0]
  priceForm.from_currency = selectedCurrency
  showFromCurrencyPicker.value = false
}

// 编辑价格
const editPrice = (price: PriceEntry) => {
  editingPrice.value = price
  priceForm.date = price.date
  priceForm.from_currency = price.from_currency
  priceForm.to_currency = price.to_currency
  priceForm.rate = Number(price.rate)
  showAddPrice.value = true
}

// 重置表单
const resetForm = () => {
  editingPrice.value = null
  priceForm.date = new Date().toISOString().split('T')[0]
  priceForm.from_currency = ''
  priceForm.to_currency = currentCurrency.value
  priceForm.rate = 0
}

// 保存价格
const savePriceEntry = async () => {
  if (!priceForm.from_currency || !priceForm.rate) {
    showToast('请填写完整信息')
    return
  }

  try {
    saving.value = true
    await pricesApi.create({
      date: priceForm.date,
      from_currency: priceForm.from_currency.toUpperCase(),
      to_currency: priceForm.to_currency?.toUpperCase(),
      rate: Number(priceForm.rate)
    })
    
    showToast(editingPrice.value ? '汇率更新成功' : '汇率添加成功')
    showAddPrice.value = false
    resetForm()
    // 重新加载价格列表
    loadPrices()
  } catch (error) {
    console.error('保存价格失败:', error)
    showToast('保存价格失败')
  } finally {
    saving.value = false
  }
}

// 确认删除价格
const confirmDeletePrice = async (price: PriceEntry) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除 ${price.date} 的 ${price.from_currency} → ${price.to_currency} 汇率吗？`,
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
    
    await pricesApi.delete({
      date: price.date,
      from_currency: price.from_currency,
      to_currency: price.to_currency
    })
    
    showToast('汇率删除成功')
    // 重新加载价格列表
    loadPrices()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除价格失败:', error)
      showToast('删除价格失败')
    }
  }
}

// 页面初始化
onMounted(() => {
  loadOperatingCurrency()
  loadPrices()
})
</script>

<style scoped>
.currency-settings {
  padding: 16px;
  background-color: var(--van-background);
  min-height: 100vh;
}

.cell-desc {
  color: var(--van-text-color-3);
  font-size: 12px;
  margin-top: 4px;
}

.delete-icon {
  color: var(--van-danger-color);
  font-size: 16px;
}

.price-form {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--van-border-color);
}

.form-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.form-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.form-tip {
  margin-top: 16px;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  color: var(--van-text-color-2);
  font-size: 14px;
  font-weight: normal;
}

:deep(.van-cell) {
  background-color: var(--van-background-2);
  padding: 16px;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
}
</style>
