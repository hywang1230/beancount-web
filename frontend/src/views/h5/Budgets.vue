<template>
  <div class="h5-budgets-page">
    <!-- 周期选择 -->
    <van-sticky>
      <div class="period-selector">
        <van-dropdown-menu>
          <van-dropdown-item v-model="periodType" :options="periodTypeOptions" @change="onPeriodTypeChange" />
          <van-dropdown-item v-model="periodValue" :options="periodValueOptions" @change="loadBudgetSummary" />
        </van-dropdown-menu>
      </div>
    </van-sticky>

    <!-- 预算汇总 -->
    <div v-if="budgetSummary" class="budget-summary">
      <van-cell-group title="本期预算概览">
        <van-cell title="预算总额" :value="formatAmount(budgetSummary.total_budget)" />
        <van-cell title="已用金额" :value="formatAmount(budgetSummary.total_spent)" />
        <van-cell title="剩余金额" :value="formatAmount(budgetSummary.total_remaining)" />
        <van-cell title="使用进度">
          <template #value>
            <div class="summary-progress-wrapper">
              <van-progress
                :percentage="budgetSummary.overall_percentage"
                :pivot-text="`${budgetSummary.overall_percentage.toFixed(1)}%`"
                :color="getProgressColor(budgetSummary.overall_percentage)"
                class="summary-progress"
              />
            </div>
          </template>
        </van-cell>
      </van-cell-group>
    </div>

    <!-- 预算列表 -->
    <div v-if="budgetSummary && budgetSummary.budgets.length > 0" class="budget-list-container">
      <van-cell-group title="预算明细">
        <van-swipe-cell v-for="item in budgetSummary.budgets" :key="item.budget.id">
          <van-cell @click="showBudgetDetail(item)">
            <template #title>
              <div class="budget-item-title">
                <span>{{ getCategoryName(item.budget.category) }}</span>
                <van-tag v-if="item.is_exceeded" type="danger">超支</van-tag>
              </div>
            </template>
            <template #label>
              <div class="budget-item-info">
                <div>预算: {{ formatAmount(item.budget.amount) }}</div>
                <div>已用: {{ formatAmount(item.spent) }} ({{ item.percentage.toFixed(1) }}%)</div>
                <div v-if="item.days_remaining !== null">剩余: {{ item.days_remaining }} 天</div>
              </div>
            </template>
          <template #value>
            <div class="progress-wrapper">
              <van-progress
                :percentage="Math.min(item.percentage, 100)"
                :color="getProgressColor(item.percentage)"
                :show-pivot="false"
                stroke-width="6px"
                class="budget-progress"
              />
            </div>
          </template>
          </van-cell>
          <template #right>
            <van-button square type="primary" text="编辑" @click="editBudget(item.budget)" />
            <van-button square type="danger" text="删除" @click="handleDeleteBudget(item.budget.id!)" />
          </template>
        </van-swipe-cell>
      </van-cell-group>
    </div>

    <!-- 空状态 -->
    <van-empty v-if="budgetSummary && budgetSummary.budgets.length === 0" description="暂无预算，点击下方按钮添加">
      <van-button type="primary" @click="showAddDialog = true">添加预算</van-button>
    </van-empty>

    <!-- 添加预算按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="showAddDialog = true"
      :style="{ zIndex: 9999 }"
    />

    <!-- 添加/编辑预算对话框 -->
    <van-dialog
      v-model:show="showAddDialog"
      :title="editingBudget ? '编辑预算' : '添加预算'"
      show-cancel-button
      @confirm="handleSaveBudget"
      :before-close="beforeDialogClose"
    >
      <van-form ref="formRef">
        <van-cell-group inset>
          <van-field
            v-if="!editingBudget"
            v-model="budgetForm.category"
            label="支出类别"
            placeholder="点击选择"
            readonly
            is-link
            @click="showCategoryPicker = true"
            required
            :rules="[{ required: true, message: '请选择支出类别' }]"
          />
          <van-field
            v-model="budgetForm.amount"
            label="预算金额"
            type="number"
            placeholder="请输入预算金额"
            required
            :rules="[{ required: true, message: '请输入预算金额' }]"
          />
          <van-field
            v-if="!editingBudget"
            v-model="budgetForm.currency"
            label="货币"
            placeholder="CNY"
          />
        </van-cell-group>
      </van-form>
    </van-dialog>

    <!-- 类别选择器 -->
    <van-popup v-model:show="showCategoryPicker" position="bottom" :style="{ height: '60%' }">
      <van-picker
        :columns="categoryColumns"
        @confirm="onCategoryConfirm"
        @cancel="showCategoryPicker = false"
      />
    </van-popup>

    <!-- 预算详情弹窗 -->
    <van-popup v-model:show="showDetailPopup" position="bottom" :style="{ height: '50%' }">
      <div v-if="selectedBudget" class="budget-detail">
        <van-nav-bar :title="getCategoryName(selectedBudget.budget.category)" left-text="关闭" @click-left="showDetailPopup = false" />
        <van-cell-group>
          <van-cell title="预算金额" :value="formatAmount(selectedBudget.budget.amount)" />
          <van-cell title="已用金额" :value="formatAmount(selectedBudget.spent)" />
          <van-cell title="剩余金额" :value="formatAmount(selectedBudget.remaining)" />
          <van-cell title="使用进度" :value="`${selectedBudget.percentage.toFixed(1)}%`" />
          <van-cell v-if="selectedBudget.days_remaining !== null" title="剩余天数" :value="`${selectedBudget.days_remaining} 天`" />
          <van-cell title="状态">
            <template #value>
              <van-tag v-if="selectedBudget.is_exceeded" type="danger">超支</van-tag>
              <van-tag v-else-if="selectedBudget.percentage > 80" type="warning">接近预算</van-tag>
              <van-tag v-else type="success">正常</van-tag>
            </template>
          </van-cell>
        </van-cell-group>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { showToast, showConfirmDialog } from "vant";
import {
  getBudgetSummary,
  createBudget,
  updateBudget,
  deleteBudget,
  type BudgetSummary,
  type BudgetProgress,
  type Budget,
} from "@/api/budgets";
import { getAccounts } from "@/api/transactions";

const periodType = ref("month");
const periodValue = ref("");
const budgetSummary = ref<BudgetSummary | null>(null);
const loading = ref(false);
// 设置浮动按钮的初始位置（右下角）
const fabOffset = ref({ 
  x: typeof window !== 'undefined' ? window.innerWidth - 80 : 300, 
  y: typeof window !== 'undefined' ? window.innerHeight - 150 : 600 
});

const showAddDialog = ref(false);
const showCategoryPicker = ref(false);
const showDetailPopup = ref(false);
const selectedBudget = ref<BudgetProgress | null>(null);
const editingBudget = ref<Budget | null>(null);

const budgetForm = ref({
  category: "",
  amount: "",
  currency: "CNY",
});

const categoryColumns = ref<Array<{ text: string; value: string }>>([]);

// 周期类型选项
const periodTypeOptions = [
  { text: "月度", value: "month" },
  { text: "季度", value: "quarter" },
  { text: "年度", value: "year" },
];

// 周期值选项
const periodValueOptions = computed(() => {
  const options: Array<{ text: string; value: string }> = [];
  const today = new Date();
  
  if (periodType.value === "month") {
    // 生成最近12个月
    for (let i = 0; i < 12; i++) {
      const date = new Date(today.getFullYear(), today.getMonth() - i, 1);
      const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const text = `${date.getFullYear()}年${date.getMonth() + 1}月`;
      options.push({ text, value });
    }
  } else if (periodType.value === "quarter") {
    // 生成最近8个季度
    for (let i = 0; i < 8; i++) {
      const year = today.getFullYear() - Math.floor(i / 4);
      const quarter = 4 - (i % 4) - (Math.floor((today.getMonth() / 3)));
      if (quarter <= 0) continue;
      const value = `${year}-Q${quarter}`;
      const text = `${year}年第${quarter}季度`;
      options.push({ text, value });
    }
  } else {
    // 生成最近5年
    for (let i = 0; i < 5; i++) {
      const year = today.getFullYear() - i;
      options.push({ text: `${year}年`, value: String(year) });
    }
  }
  
  return options;
});

// 加载预算汇总
const loadBudgetSummary = async () => {
  loading.value = true;
  try {
    budgetSummary.value = await getBudgetSummary({
      period_type: periodType.value,
      period_value: periodValue.value,
    });
  } catch (error) {
    showToast("加载预算失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 加载支出类别
const loadExpenseCategories = async () => {
  try {
    const response = await getAccounts();
    const accounts = Array.isArray(response) ? response : (response?.data || []);
    categoryColumns.value = accounts
      .filter((acc: string) => acc.startsWith("Expenses:"))
      .sort()
      .map((acc: string) => ({ text: acc, value: acc }));
  } catch (error) {
    console.error("加载类别失败:", error);
  }
};

// 格式化金额
const formatAmount = (amount: number): string => {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(amount);
};

// 获取类别名称
const getCategoryName = (category: string): string => {
  const parts = category.split(":");
  return parts[parts.length - 1];
};

// 获取进度条颜色
const getProgressColor = (percentage: number): string => {
  if (percentage >= 100) return "#ee0a24";
  if (percentage >= 80) return "#ff976a";
  return "#07c160";
};

// 周期类型改变
const onPeriodTypeChange = () => {
  // 重置周期值为第一个选项
  if (periodValueOptions.value.length > 0) {
    periodValue.value = periodValueOptions.value[0].value;
    loadBudgetSummary();
  }
};

// 类别选择确认
const onCategoryConfirm = ({ selectedOptions }: any) => {
  budgetForm.value.category = selectedOptions[0].text;
  showCategoryPicker.value = false;
};

// 显示预算详情
const showBudgetDetail = (item: BudgetProgress) => {
  selectedBudget.value = item;
  showDetailPopup.value = true;
};

// 编辑预算
const editBudget = (budget: Budget) => {
  editingBudget.value = budget;
  budgetForm.value = {
    category: budget.category,
    amount: String(budget.amount),
    currency: budget.currency,
  };
  showAddDialog.value = true;
};

// 保存预算
const handleSaveBudget = async () => {
  if (!budgetForm.value.category || !budgetForm.value.amount) {
    showToast("请填写完整信息");
    return;
  }

  try {
    if (editingBudget.value) {
      // 更新预算
      await updateBudget(editingBudget.value.id!, {
        amount: parseFloat(budgetForm.value.amount),
      });
      showToast("预算已更新");
    } else {
      // 创建预算
      await createBudget({
        category: budgetForm.value.category,
        period_type: periodType.value,
        period_value: periodValue.value,
        amount: parseFloat(budgetForm.value.amount),
        currency: budgetForm.value.currency,
      });
      showToast("预算已添加");
    }
    
    showAddDialog.value = false;
    resetForm();
    await loadBudgetSummary();
  } catch (error: any) {
    showToast(error.response?.data?.detail || "操作失败");
    console.error(error);
  }
};

// 删除预算
const handleDeleteBudget = async (id: number) => {
  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这个预算吗？",
    });

    await deleteBudget(id);
    showToast("预算已删除");
    await loadBudgetSummary();
  } catch (error) {
    if (error !== "cancel") {
      showToast("删除失败");
      console.error(error);
    }
  }
};

// 对话框关闭前
const beforeDialogClose = () => {
  resetForm();
  return true;
};

// 重置表单
const resetForm = () => {
  budgetForm.value = {
    category: "",
    amount: "",
    currency: "CNY",
  };
  editingBudget.value = null;
};

onMounted(() => {
  // 设置默认周期为当前月
  if (periodValueOptions.value.length > 0) {
    periodValue.value = periodValueOptions.value[0].value;
  }
  loadBudgetSummary();
  loadExpenseCategories();
  
  // 确保浮动按钮位置正确
  fabOffset.value = {
    x: window.innerWidth - 80,
    y: window.innerHeight - 150
  };
});
</script>

<style scoped>
.h5-budgets-page {
  padding: 0 0 80px 0;
  background-color: var(--van-background);
  min-height: 100vh;
  position: relative;
}

.period-selector {
  background-color: var(--van-background-2);
}

.budget-summary,
.budget-list-container {
  padding: 0 16px;
  margin-bottom: 16px;
}

/* 预算汇总中的进度条样式 */
.summary-progress-wrapper {
  flex: 1;
  min-width: 0; /* 允许flex收缩 */
  display: flex;
  align-items: center;
  margin-left: 20px;
}

.summary-progress {
  width: 100%;
  max-width: 220px;
}

.budget-summary :deep(.van-cell) {
  padding: 14px 16px;
  display: flex;
  align-items: center;
}

.budget-summary :deep(.van-cell__value) {
  flex: 1;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-left: 16px;
  overflow: visible;
}

.budget-summary :deep(.van-cell__title) {
  flex-shrink: 0;
  width: 80px;
  white-space: nowrap;
}

.budget-item-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.budget-item-info {
  margin-top: 6px;
  font-size: 12px;
  color: var(--van-text-color-3);
  line-height: 1.5;
}

.budget-detail {
  padding-bottom: 20px;
}

.progress-wrapper {
  width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.van-progress) {
  width: 100%;
}

.budget-progress {
  margin: 0;
}

.budget-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.4;
}

/* 调整预算列表中的 Cell 布局 */
.budget-list-container :deep(.van-cell) {
  padding: 16px;
  min-height: 80px;
}

.budget-list-container :deep(.van-cell__value) {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  align-self: flex-start;
  padding-top: 4px;
}

.budget-list-container :deep(.van-cell__title) {
  padding-right: 12px;
}

.budget-list-container :deep(.van-cell__label) {
  margin-top: 6px;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
}

/* 确保浮动按钮可见 */
:deep(.van-floating-bubble) {
  z-index: 9999 !important;
  position: fixed !important;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}
</style>

