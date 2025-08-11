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
          :rules="[{ required: false, message: '请输入摘要' }]"
        />
      </van-cell-group>

      <!-- 周期设置 -->
      <van-cell-group inset title="周期设置">
        <van-field
          name="recurrence_type"
          label="周期类型"
          :model-value="getRecurrenceTypeText(form.recurrence_type)"
          readonly
          is-link
          @click="showRecurrenceTypePicker = true"
        />

        <!-- 每周特定几天 -->
        <van-cell
          v-if="form.recurrence_type === 'weekly'"
          title="执行星期"
          :value="getWeeklyDaysText(form.weekly_days)"
          is-link
          @click="showWeeklyDaysSelector = true"
        />

        <!-- 每月特定几日 -->
        <van-cell
          v-if="form.recurrence_type === 'monthly'"
          title="执行日期"
          :value="getMonthlyDaysText(form.monthly_days)"
          is-link
          @click="showMonthlyDaysSelector = true"
        />

        <van-cell
          title="开始日期"
          :value="formatDateDisplay(form.start_date)"
          is-link
          @click="showStartDateCalendar = true"
        />
        <van-cell
          title="结束日期"
          :value="form.end_date ? formatDateDisplay(form.end_date) : '无期限'"
          is-link
          @click="showEndDateCalendar = true"
        >
          <template #right-icon v-if="form.end_date">
            <van-icon
              name="clear"
              @click.stop="clearEndDate"
              style="margin-left: 8px; color: #969799"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 交易信息 -->
      <van-cell-group inset title="交易信息">
        <!-- 交易对象 -->
        <van-cell
          title="交易对象"
          :value="form.payee || '选择交易对象（可选）'"
          is-link
          @click="showPayeeSelector"
        >
          <template #right-icon v-if="form.payee">
            <van-icon
              name="close"
              class="clear-icon"
              @click.stop="clearPayee"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 记账分录 -->
      <van-cell-group inset title="记账分录">
        <div
          v-for="(posting, index) in form.postings"
          :key="index"
          class="posting-item"
        >
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
            v-model="posting.amount"
            :name="`posting-${index}-amount`"
            label="金额"
            type="text"
            placeholder="请输入金额"
            readonly
            :formatter="formatNumberInput"
            :rules="[
              { required: true, message: '请输入金额' },
              { validator: validateNumberInput, message: '请输入合法数字' },
            ]"
            @click="() => showAmountKeyboard(index)"
          />
          <van-field :name="`posting-${index}-currency`" label="货币">
            <template #input>
              <van-cell
                :value="posting.currency"
                is-link
                @click="showCurrencySelector(index)"
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
              <span
                :class="[
                  'balance-amount',
                  isBalanced ? 'balanced' : 'unbalanced',
                ]"
              >
                {{ totalAmount.toFixed(2) }}
              </span>
              <van-tag :type="isBalanced ? 'success' : 'danger'">
                {{ isBalanced ? "平衡" : "不平衡" }}
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
          {{ isEdit ? "更新周期记账" : "创建周期记账" }}
        </van-button>
      </div>
    </van-form>

    <!-- 周期类型选择器 -->
    <van-popup
      v-model:show="showRecurrenceTypePicker"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :teleport="'body'"
      :overlay="false"
      class="fullscreen-popup"
    >
      <div class="fullscreen-selector">
        <div class="selector-header">
          <van-nav-bar
            title="选择周期类型"
            left-text="取消"
            left-arrow
            @click-left="showRecurrenceTypePicker = false"
          />
        </div>
        <div class="selector-content">
          <van-cell-group inset>
            <van-cell
              v-for="option in recurrenceTypeColumns"
              :key="option.value"
              :title="option.text"
              clickable
              :is-link="false"
              @click="selectRecurrenceType(option)"
            >
              <template #right-icon>
                <van-icon
                  v-if="form.recurrence_type === option.value"
                  name="success"
                  color="#1989fa"
                />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </van-popup>

    <!-- 开始日期日历 -->
    <van-calendar
      v-model:show="showStartDateCalendar"
      title="选择开始日期"
      :default-date="form.start_date ? new Date(form.start_date) : new Date()"
      :min-date="new Date(2020, 0, 1)"
      :max-date="new Date(2030, 11, 31)"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onStartDateConfirm"
      @close="showStartDateCalendar = false"
    />

    <!-- 结束日期日历 -->
    <van-calendar
      v-model:show="showEndDateCalendar"
      title="选择结束日期"
      :default-date="form.end_date ? new Date(form.end_date) : new Date()"
      :min-date="
        form.start_date ? new Date(form.start_date) : new Date(2020, 0, 1)
      "
      :max-date="new Date(2030, 11, 31)"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onEndDateConfirm"
      @close="showEndDateCalendar = false"
    />

    <!-- 货币选择器 -->
    <van-popup
      v-model:show="showCurrencyPicker"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :teleport="'body'"
      :overlay="false"
      class="fullscreen-popup"
    >
      <div class="fullscreen-selector">
        <div class="selector-header">
          <van-nav-bar
            title="选择货币"
            left-text="取消"
            left-arrow
            @click-left="showCurrencyPicker = false"
          />
        </div>
        <div class="selector-content">
          <van-cell-group inset>
            <van-cell
              v-for="option in currencyColumns"
              :key="option.value"
              :title="option.text"
              clickable
              :is-link="false"
              @click="selectCurrency(option)"
            >
              <template #right-icon>
                <van-icon
                  v-if="getCurrentCurrency() === option.value"
                  name="success"
                  color="#1989fa"
                />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </van-popup>

    <!-- 账户选择器 -->
    <AccountTreeSelector
      ref="accountSelectorRef"
      title="选择账户"
      :account-types="['Assets', 'Liabilities', 'Income', 'Expenses']"
      @confirm="onAccountSelected"
      @close="onAccountSelectorClose"
    />

    <!-- 交易对象选择器 -->
    <FullScreenSelector
      ref="payeeSelectorRef"
      type="payee"
      title="选择交易对象"
      :show-search="true"
      :payees="payeeList"
      @confirm="onPayeeSelected"
      @close="onPayeeSelectorClose"
    />

    <!-- 每周选择器 -->
    <van-popup
      v-model:show="showWeeklyDaysSelector"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :teleport="'body'"
      :overlay="false"
      class="fullscreen-popup"
    >
      <div class="weekly-selector">
        <div class="selector-header">
          <van-nav-bar
            title="选择执行星期"
            left-text="取消"
            left-arrow
            @click-left="showWeeklyDaysSelector = false"
          />
        </div>
        <div class="weekly-content">
          <van-checkbox-group v-model="form.weekly_days">
            <van-cell
              v-for="(day, index) in weekDays"
              :key="index"
              :title="day"
              clickable
              @click="toggleWeekDay(index)"
            >
              <template #right-icon>
                <van-checkbox
                  :name="index"
                  :checked="(form.weekly_days || []).includes(index)"
                  @click.stop
                />
              </template>
            </van-cell>
          </van-checkbox-group>
        </div>
        <div class="selector-footer">
          <van-button block type="primary" @click="confirmWeeklyDays">
            确定
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 每月选择器 -->
    <van-popup
      v-model:show="showMonthlyDaysSelector"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :teleport="'body'"
      :overlay="false"
      class="fullscreen-popup"
    >
      <div class="monthly-selector">
        <div class="selector-header">
          <van-nav-bar
            title="选择执行日期"
            left-text="取消"
            left-arrow
            @click-left="showMonthlyDaysSelector = false"
          />
        </div>
        <div class="monthly-content">
          <van-checkbox-group v-model="form.monthly_days">
            <div class="monthly-grid">
              <div
                v-for="day in 31"
                :key="day"
                class="monthly-day-item"
                @click="toggleMonthDay(day)"
              >
                <van-checkbox
                  :name="day"
                  :checked="(form.monthly_days || []).includes(day)"
                  @click.stop
                />
                <span class="day-label">{{ day }}</span>
              </div>
            </div>
          </van-checkbox-group>
        </div>
        <div class="selector-footer">
          <van-button block type="primary" @click="confirmMonthlyDays">
            确定
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 数字键盘 - 金额输入 -->
    <NumberKeyboard
      v-model="amountInput"
      v-model:show="showNumberKeyboard"
      title="输入金额"
      placeholder="请输入金额"
      :show-decimal="true"
      :show-negative="true"
      @confirm="onAmountKeyboardConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { recurringApi } from "@/api/recurring";
import { getPayees } from "@/api/transactions";
import NumberKeyboard from "@/components/NumberKeyboard.vue";
import { showToast } from "vant";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AccountTreeSelector from "./AccountTreeSelector.vue";
import FullScreenSelector from "./FullScreenSelector.vue";

interface Props {
  isEdit?: boolean;
  editId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  isEdit: false,
  editId: "",
});

const router = useRouter();

// 本地表单数据类型（amount使用string便于输入）
interface LocalFormData {
  name: string;
  description?: string;
  recurrence_type: "daily" | "weekly" | "weekdays" | "monthly";
  start_date: string;
  end_date?: string;
  weekly_days?: number[];
  monthly_days?: number[];
  flag?: string;
  payee?: string;
  narration: string;
  tags?: string[];
  links?: string[];
  postings: Array<{
    account: string;
    amount?: string | number; // 表单中使用string，提交时转换为number
    currency?: string;
  }>;
  is_active?: boolean;
}

// 表单数据
const form = ref<LocalFormData>({
  name: "",
  description: "",
  recurrence_type: "daily" as "daily" | "weekly" | "weekdays" | "monthly", // 初始为每日
  start_date: "",
  end_date: "",
  weekly_days: [],
  monthly_days: [],
  flag: "*",
  payee: "",
  narration: "",
  tags: [],
  links: [],
  postings: [
    { account: "", amount: "", currency: "CNY" },
    { account: "", amount: "", currency: "CNY" },
  ],
  is_active: true,
});

// 界面状态
const submitLoading = ref(false);
const showRecurrenceTypePicker = ref(false);
const showStartDateCalendar = ref(false);
const showEndDateCalendar = ref(false);
const showCurrencyPicker = ref(false);
const showWeeklyDaysSelector = ref(false);
const showMonthlyDaysSelector = ref(false);
const currentAccountIndex = ref(-1);
const currentCurrencyIndex = ref(-1);
const accountSelectorRef = ref();
const payeeSelectorRef = ref();
const payeeList = ref<string[]>([]);

// 数字键盘状态
const showNumberKeyboard = ref(false);
const amountInput = ref("");
const currentAmountPostingIndex = ref(0);

const recurrenceTypeColumns = [
  { text: "每日", value: "daily" },
  { text: "工作日", value: "weekdays" },
  { text: "每周特定几天", value: "weekly" },
  { text: "每月特定几日", value: "monthly" },
];

const weekDays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];

const currencyColumns = [
  { text: "CNY", value: "CNY" },
  { text: "USD", value: "USD" },
  { text: "EUR", value: "EUR" },
  { text: "JPY", value: "JPY" },
];

// 计算属性
const totalAmount = computed(() => {
  return form.value.postings.reduce((sum, posting) => {
    return sum + (parseFloat(posting.amount?.toString() || "0") || 0);
  }, 0);
});

const isBalanced = computed(() => {
  return Math.abs(totalAmount.value) < 0.01;
});

// 输入格式化函数：只允许输入数字、负号和小数点，限制最多两位小数
const formatNumberInput = (value: string) => {
  if (!value) return value;

  // 先清除非数字、非负号、非小数点字符
  let formatted = value.replace(/[^\d.-]/g, "");

  // 处理负号：只允许在开头有一个负号
  if (formatted.includes("-")) {
    const isNegative = formatted.charAt(0) === "-";
    // 移除所有负号，然后在开头添加负号（如果原来是负数）
    formatted = formatted.replace(/-/g, "");
    if (isNegative) {
      formatted = "-" + formatted;
    }
  }

  // 处理小数点：只允许一个小数点，且限制最多两位小数
  const parts = formatted.split(".");
  if (parts.length > 2) {
    // 如果有多个小数点，只保留第一个
    formatted = parts[0] + "." + parts.slice(1).join("");
  } else if (parts.length === 2) {
    // 如果有小数部分，限制最多两位小数
    const decimalPart = parts[1].slice(0, 2);
    formatted = parts[0] + "." + decimalPart;
  }

  return formatted;
};

// 输入验证函数
const validateNumberInput = (value: string) => {
  if (!value) return true; // 允许空值
  // 验证格式：可选负号 + 数字 + 可选小数部分（最多两位小数）
  return /^-?\d*(\.\d{0,2})?$/.test(value);
};

// 方法
const getRecurrenceTypeText = (type: string) => {
  const item = recurrenceTypeColumns.find((col) => col.value === type);
  return item?.text || "请选择周期类型";
};

// 格式化日期显示
const formatDateDisplay = (dateStr: string) => {
  if (!dateStr) return "请选择日期";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

const selectRecurrenceType = (option: any) => {
  form.value.recurrence_type = option.value;
  // 重置相关字段
  form.value.weekly_days = [];
  form.value.monthly_days = [];
  showRecurrenceTypePicker.value = false;
};

const onStartDateConfirm = (date: Date) => {
  form.value.start_date = date.toLocaleDateString("en-CA"); // 格式: YYYY-MM-DD
  showStartDateCalendar.value = false;
};

const onEndDateConfirm = (date: Date) => {
  form.value.end_date = date.toLocaleDateString("en-CA"); // 格式: YYYY-MM-DD
  showEndDateCalendar.value = false;
};

const clearEndDate = () => {
  form.value.end_date = "";
};

// 周期选择相关方法
const getWeeklyDaysText = (days?: number[]) => {
  if (!days || days.length === 0) return "请选择星期";
  const dayNames = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
  return days.map((day) => dayNames[day]).join("、");
};

const getMonthlyDaysText = (days?: number[]) => {
  if (!days || days.length === 0) return "请选择日期";
  return days.map((day) => `${day}日`).join("、");
};

const toggleWeekDay = (index: number) => {
  if (!form.value.weekly_days) {
    form.value.weekly_days = [];
  }
  if (form.value.weekly_days.includes(index)) {
    form.value.weekly_days = form.value.weekly_days.filter(
      (day) => day !== index
    );
  } else {
    form.value.weekly_days.push(index);
  }
};

const confirmWeeklyDays = () => {
  if (!form.value.weekly_days || form.value.weekly_days.length === 0) {
    showToast("请至少选择一个星期");
    return;
  }
  showWeeklyDaysSelector.value = false;
};

const toggleMonthDay = (day: number) => {
  if (!form.value.monthly_days) {
    form.value.monthly_days = [];
  }
  if (form.value.monthly_days.includes(day)) {
    form.value.monthly_days = form.value.monthly_days.filter((d) => d !== day);
  } else {
    form.value.monthly_days.push(day);
  }
};

const confirmMonthlyDays = () => {
  if (!form.value.monthly_days || form.value.monthly_days.length === 0) {
    showToast("请至少选择一个日期");
    return;
  }
  showMonthlyDaysSelector.value = false;
};

const selectAccount = (index: number) => {
  currentAccountIndex.value = index;
  accountSelectorRef.value?.show();
};

const onAccountSelected = (account: string) => {
  if (currentAccountIndex.value >= 0) {
    form.value.postings[currentAccountIndex.value].account = account;
  }
};

const onAccountSelectorClose = () => {
  // 账户选择器关闭时的处理
};

const showPayeeSelector = () => {
  if (payeeSelectorRef.value) {
    payeeSelectorRef.value.show();
  }
};

const onPayeeSelected = (payee: string) => {
  form.value.payee = payee;
};

const onPayeeSelectorClose = () => {
  // 交易对象选择器关闭时的处理
};

const clearPayee = () => {
  form.value.payee = "";
};

const selectCurrency = (option: any) => {
  if (currentCurrencyIndex.value >= 0) {
    form.value.postings[currentCurrencyIndex.value].currency = option.value;
  }
  showCurrencyPicker.value = false;
};

const getCurrentCurrency = () => {
  if (currentCurrencyIndex.value >= 0) {
    return form.value.postings[currentCurrencyIndex.value]?.currency || "CNY";
  }
  return "CNY";
};

const showCurrencySelector = (index: number) => {
  currentCurrencyIndex.value = index;
  showCurrencyPicker.value = true;
};

const addPosting = () => {
  form.value.postings.push({ account: "", amount: "", currency: "CNY" });
};

const removePosting = (index: number) => {
  if (form.value.postings.length > 2) {
    form.value.postings.splice(index, 1);
  }
};

const validateForm = () => {
  // 检验基本信息
  if (!form.value.name?.trim()) {
    showToast("请输入周期记账名称");
    return false;
  }

  if (!form.value.start_date) {
    showToast("请选择开始日期");
    return false;
  }

  // 周期类型现在有默认值，无需检验

  // 检验周期设置
  if (
    form.value.recurrence_type === "weekly" &&
    (!form.value.weekly_days || form.value.weekly_days.length === 0)
  ) {
    showToast("请选择执行的星期");
    return false;
  }

  if (
    form.value.recurrence_type === "monthly" &&
    (!form.value.monthly_days || form.value.monthly_days.length === 0)
  ) {
    showToast("请选择执行的日期");
    return false;
  }

  // 检验至少有两个分录
  if (form.value.postings.length < 2) {
    showToast("至少需要两个分录");
    return false;
  }

  // 检验分录账户不能为空
  const emptyAccounts = form.value.postings.filter((p) => !p.account?.trim());
  if (emptyAccounts.length > 0) {
    showToast("所有分录都必须选择账户");
    return false;
  }

  // 检验分录金额
  const emptyAmounts = form.value.postings.filter((p) => {
    if (!p.amount) return true;
    const amountStr = p.amount.toString().trim();
    if (amountStr === "") return true;
    const amountNum = parseFloat(amountStr);
    return isNaN(amountNum) || amountNum === 0;
  });
  if (emptyAmounts.length > 0) {
    showToast("所有分录都必须输入金额");
    return false;
  }

  // 检验分录平衡
  if (!isBalanced.value) {
    showToast(`分录金额之和必须为0，当前和为：${totalAmount.value.toFixed(2)}`);
    return false;
  }

  return true;
};

const onSubmit = async () => {
  if (!validateForm()) {
    return;
  }

  try {
    submitLoading.value = true;

    const dataToSend = {
      ...form.value,
      end_date: form.value.end_date || null, // 空字符串转为null，避免422错误
      postings: form.value.postings.map((p) => ({
        account: p.account,
        amount: parseFloat(p.amount?.toString() || "0") || 0,
        currency: p.currency,
      })),
    };

    if (props.isEdit) {
      await recurringApi.update(props.editId, dataToSend);
      showToast("更新成功");
    } else {
      await recurringApi.create(dataToSend);
      showToast("创建成功");
    }

    router.back();
  } catch (error) {
    // console.error("保存失败:", error);
    showToast("保存失败");
  } finally {
    submitLoading.value = false;
  }
};

// 编辑模式下加载数据
const loadEditData = async () => {
  if (props.isEdit && props.editId) {
    try {
      const data = await recurringApi.get(props.editId);
      Object.assign(form.value, {
        ...data,
        weekly_days: data.weekly_days || [],
        monthly_days: data.monthly_days || [],
        tags: data.tags || [],
        links: data.links || [],
        postings: data.postings.map((p: any) => ({
          account: p.account,
          amount: parseFloat(p.amount) || 0,
          currency: p.currency || "CNY",
        })),
      });
    } catch (error) {
      // console.error("加载数据失败:", error);
      showToast("加载数据失败");
    }
  }
};

// 数字键盘相关方法
const showAmountKeyboard = (index: number) => {
  currentAmountPostingIndex.value = index;
  amountInput.value = String(form.value.postings[index]?.amount || "");
  showNumberKeyboard.value = true;
};

const onAmountKeyboardConfirm = (value: string) => {
  const index = currentAmountPostingIndex.value;
  if (form.value.postings[index]) {
    form.value.postings[index].amount = value;
  }
  showNumberKeyboard.value = false;
  amountInput.value = "";
};

onMounted(async () => {
  // 设置默认开始日期为今天
  if (!props.isEdit) {
    const today = new Date();
    form.value.start_date = `${today.getFullYear()}-${String(
      today.getMonth() + 1
    ).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
    // 设置默认周期类型
    form.value.recurrence_type = "daily";
  } else {
    loadEditData();
  }

  // 加载交易对象列表
  await loadPayees();
});

// 加载交易对象列表
const loadPayees = async () => {
  try {
    // console.log("正在加载交易对象列表...");
    const payeeData = await getPayees();
    // console.log("交易对象API原始响应:", payeeData);

    if (Array.isArray(payeeData)) {
      payeeList.value = payeeData;
    } else if (payeeData && Array.isArray(payeeData.data)) {
      payeeList.value = payeeData.data;
    } else {
      payeeList.value = [];
    }
    // console.log("处理后的交易对象列表:", payeeList.value);
  } catch (error) {
    // console.error("获取交易对象列表失败:", error);
    payeeList.value = [];
    showToast("获取交易对象列表失败");
  }
};
</script>

<style scoped>
.recurring-form {
  padding: 16px;
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
}

.posting-item {
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 8px;
  padding-bottom: 8px;
}

.posting-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.balance-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 12px;
  font-size: 12px;
}

.balance-label {
  color: var(--text-color-secondary);
}

.balance-amount {
  font-weight: 500;
}

.balance-amount.balanced {
  color: var(--color-success);
}
html[data-theme="dark"] .balance-amount.balanced {
  color: #95d475;
}

.balance-amount.unbalanced {
  color: var(--color-danger);
}
html[data-theme="dark"] .balance-amount.unbalanced {
  color: #ff7875;
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

/* 全屏弹窗样式 */
.fullscreen-popup {
  z-index: 3000;
}

.fullscreen-selector {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-secondary);
}

.selector-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

.picker-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
}

/* 周期选择器样式 */
.weekly-selector,
.monthly-selector {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-secondary);
}

.selector-header {
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.selector-header .van-nav-bar {
  background: var(--bg-color);
}

.weekly-content,
.monthly-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.monthly-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  padding: 0 16px;
}

.monthly-day-item {
  margin: 0;
  padding: 8px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-color);
  border-radius: 4px;
  text-align: center;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  position: relative;
  min-height: 48px;
  justify-content: center;
}

.monthly-day-item .day-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-color);
  font-weight: 500;
}

.monthly-day-item:deep(.van-checkbox) {
  margin-bottom: 0;
}

.monthly-day-item:deep(.van-checkbox__label) {
  font-size: 12px;
}

.selector-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
  background-color: var(--bg-color);
  flex-shrink: 0;
}

.clear-icon {
  color: var(--text-color-placeholder);
  margin-left: 8px;
}
</style>
