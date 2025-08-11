<template>
  <div class="transaction-form">
    <van-form @submit="onSubmit">
      <!-- 账户选择卡片 -->
      <div
        class="form-card account-card"
        @click="showFullScreenAccountSelector"
      >
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">{{ accountDisplayName || "选择账户" }}</div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 金额输入卡片 -->
      <div class="form-card amount-card">
        <div class="card-icon">
          <van-icon name="plus" />
        </div>
        <div class="amount-input-container">
          <div
            class="currency-selector"
            @click.stop="showCurrencySelector = true"
          >
            <span class="currency-symbol">{{
              getCurrencySymbol(localFormData.currency)
            }}</span>
            <van-icon name="arrow-down" size="12" />
          </div>
          <van-field
            v-model="localFormData.amount"
            placeholder="请输入金额"
            type="text"
            class="amount-field"
            :formatter="formatNumberInput"
            :rules="[
              { validator: validateNumberInput, message: '请输入合法数字' },
            ]"
          />
        </div>
      </div>

      <!-- 分类选择卡片 -->
      <div
        class="form-card category-card"
        @click="() => showFullScreenCategorySelector()"
      >
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
        <van-cell
          title="交易对象"
          :value="localFormData.payee || '选择交易对象（可选）'"
          is-link
          @click="showFullScreenPayeeSelector"
        >
          <template #right-icon v-if="localFormData.payee">
            <van-icon
              name="close"
              class="clear-icon"
              @click.stop="clearPayee"
            />
          </template>
        </van-cell>

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
          clearable
        />
      </van-cell-group>
    </van-form>

    <!-- TreeSelect账户选择器 -->
    <AccountTreeSelector
      ref="accountSelectorRef"
      title="选择账户"
      :account-types="accountTypesForTransaction"
      @confirm="onFullScreenAccountConfirm"
      @close="onFullScreenAccountClose"
    />

    <!-- TreeSelect分类选择器 -->
    <CategoryTreeSelector
      ref="categorySelectorRef"
      title="选择分类"
      :categories="categoryHierarchy"
      @confirm="onFullScreenCategoryConfirm"
      @close="onFullScreenCategoryClose"
    />

    <!-- 全屏交易对象选择器 -->
    <FullScreenSelector
      ref="payeeSelectorRef"
      type="payee"
      title="选择交易对象"
      :show-search="true"
      :payees="payeeList"
      @confirm="onFullScreenPayeeConfirm"
      @close="onFullScreenPayeeClose"
    />

    <!-- 币种选择器 -->
    <van-popup
      v-model:show="showCurrencySelector"
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
            @click-left="showCurrencySelector = false"
          />
        </div>
        <div class="selector-content">
          <van-cell-group inset>
            <van-cell
              v-for="option in currencyOptions"
              :key="option.value"
              :title="option.text"
              clickable
              :is-link="false"
              @click="onCurrencyConfirm(option)"
            >
              <template #right-icon>
                <van-icon
                  v-if="localFormData.currency === option.value"
                  name="success"
                  :color="'var(--van-primary-color)'"
                />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </van-popup>

    <!-- 多类别分配面板 -->
    <van-popup
      v-model:show="showMultiCategorySheet"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :teleport="'body'"
      :overlay="false"
      class="fullscreen-popup"
    >
      <div class="multi-category-content">
        <!-- 全屏导航头部 -->
        <div class="multi-category-header">
          <van-nav-bar
            title="分类分配"
            left-text="取消"
            left-arrow
            @click-left="cancelMultiCategory"
          >
            <template #right>
              <van-button
                type="primary"
                size="small"
                :disabled="!isMultiCategoryValid"
                @click="confirmMultiCategory"
              >
                确认
              </van-button>
            </template>
          </van-nav-bar>
        </div>

        <div class="category-items">
          <div
            v-for="(item, index) in isEditingMultiCategory
              ? tempCategories
              : localFormData.categories"
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
                @click="() => showFullScreenCategorySelector(index)"
              />
              <van-field
                :model-value="item.amount"
                type="text"
                placeholder="0.00"
                class="amount-field-small"
                :formatter="formatNumberInput"
                :rules="[
                  { validator: validateNumberInput, message: '请输入合法数字' },
                ]"
                @update:model-value="
                  (value: string) => onCategoryAmountInput(index, value)
                "
              />
              <van-button
                v-if="
                  (isEditingMultiCategory
                    ? tempCategories
                    : localFormData.categories
                  ).length > 1
                "
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
          <van-button type="primary" size="small" @click="addCategory">
            添加分类
          </van-button>
        </div>

        <div
          class="amount-summary"
          :class="{
            'amount-summary--balanced': Math.abs(remainingAmount) < 0.01,
            'amount-summary--unbalanced': Math.abs(remainingAmount) >= 0.01,
          }"
        >
          <div class="summary-row">
            <span
              >总金额: ¥{{
                parseFloat(localFormData.amount || "0").toFixed(2)
              }}</span
            >
          </div>
          <div class="summary-row">
            <span>已分配: ¥{{ allocatedAmount.toFixed(2) }}</span>
            <span
              :class="{
                'remaining-balanced': Math.abs(remainingAmount) < 0.01,
                'remaining-positive': remainingAmount > 0.01,
                'remaining-negative': remainingAmount < -0.01,
              }"
            >
              {{ remainingAmount >= 0 ? "剩余" : "超出" }}: ¥{{
                Math.abs(remainingAmount).toFixed(2)
              }}
            </span>
          </div>
          <div v-if="Math.abs(remainingAmount) >= 0.01" class="balance-hint">
            {{
              remainingAmount > 0 ? "⚠️ 还需继续分配" : "⚠️ 分配金额超出总额"
            }}
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
import { getAccountsByType } from "@/api/accounts";
import { getPayees } from "@/api/transactions";
import { showToast } from "vant";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import AccountTreeSelector from "./AccountTreeSelector.vue";
import CategoryTreeSelector from "./CategoryTreeSelector.vue";
import FullScreenSelector from "./FullScreenSelector.vue";

interface CategoryItem {
  categoryName: string;
  categoryDisplayName: string;
  category: string;
  amount: string;
}

interface Props {
  type: "expense" | "income" | "adjustment";
  formData: {
    amount: string;
    payee: string;
    account: string;
    category: string;
    date: Date;
    description: string;
    currency?: string;
    flag?: string;
    categories?: CategoryItem[];
  };
}

interface Emits {
  (e: "update", data: any): void;
  (e: "submit", data: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const localFormData = ref({
  ...props.formData,
  currency: props.formData.currency || "CNY",
  flag: props.formData.flag || "*",
  categories: props.formData.categories || [
    { categoryName: "", categoryDisplayName: "", category: "", amount: "" },
  ],
});

// 调试：监听amount变化
watch(
  () => localFormData.value.amount,
  () => {},
  { immediate: true }
);

// 弹窗状态
const showCurrencySelector = ref(false);
const showMultiCategorySheet = ref(false);
const showDateCalendar = ref(false);

// 多类别编辑的临时数据
const tempCategories = ref<CategoryItem[]>([]);
const isEditingMultiCategory = ref(false);

// 临时数据
const currentCategoryIndex = ref(0);

// 全屏选择器引用
const accountSelectorRef = ref();
const categorySelectorRef = ref();
const payeeSelectorRef = ref();

interface Option {
  text: string;
  value: string;
  disabled?: boolean;
}

// 选项数据
const payeeOptions = ref<Option[]>([]);
const accountOptions = ref<Option[]>([]);
const categoryOptions = ref<Option[]>([]);
const currencyOptions = ref<Option[]>([
  { text: "人民币 (CNY)", value: "CNY" },
  { text: "美元 (USD)", value: "USD" },
  { text: "欧元 (EUR)", value: "EUR" },
  { text: "英镑 (GBP)", value: "GBP" },
  { text: "日元 (JPY)", value: "JPY" },
  { text: "港币 (HKD)", value: "HKD" },
  { text: "台币 (TWD)", value: "TWD" },
  { text: "澳元 (AUD)", value: "AUD" },
  { text: "加元 (CAD)", value: "CAD" },
  { text: "新加坡元 (SGD)", value: "SGD" },
]);

// 账户格式化函数（参考Reports的实现）
const formatAccountNameForDisplay = (accountName: string) => {
  if (!accountName) return "";

  // 去掉第一级账户名称（Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(":");
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(":");

    // 进一步处理：去掉第一个"-"以及前面的字母部分
    const dashIndex = formattedName.indexOf("-");
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1);
    }

    // 将":"替换为"-"以提高可读性
    formattedName = formattedName.replace(/:/g, "-");

    return formattedName;
  }
  return accountName;
};

// 格式化单个账户名称段（去掉字母前缀和连字符）
const formatAccountName = (accountName: string) => {
  if (!accountName) return "未知账户";

  // 处理单个名称段：去掉字母前缀和连字符
  const dashIndex = accountName.indexOf("-");
  if (dashIndex > 0) {
    return accountName.substring(dashIndex + 1);
  }
  return accountName;
};

// 格式化分类名称
const formatCategoryName = (categoryName: string) => {
  return formatAccountName(categoryName);
};

// 获取账户类型
const getAccountType = (accountName: string) => {
  if (accountName.startsWith("Assets:")) return "assets";
  if (accountName.startsWith("Liabilities:")) return "liabilities";
  if (accountName.startsWith("Income:")) return "income";
  if (accountName.startsWith("Expenses:")) return "expenses";
  if (accountName.startsWith("Equity:")) return "equity";
  return "other";
};

// 构建层级选项（参考Reports的精细层级结构）
const buildHierarchicalOptions = (
  accounts: string[],
  allowedTypes: string[]
): Option[] => {
  // Building fine-grained level options

  // 按类型和分类分组账户
  const accountsByType: Record<string, any> = {
    assets: {},
    liabilities: {},
    income: {},
    expenses: {},
    equity: {},
    other: {},
  };

  // 按分类分组账户，支持层级结构
  accounts.forEach((accountName: string) => {
    const accountType = getAccountType(accountName);
    if (!allowedTypes.includes(accountType)) return;

    const parts = accountName.split(":");
    // Processing account

    if (parts.length < 2) return;

    // 第二级作为主分类名
    const categoryName = parts[1];

    if (!accountsByType[accountType][categoryName]) {
      accountsByType[accountType][categoryName] = {
        accounts: [],
        subGroups: {},
      };
    }

    // 从第三级开始构建子层级
    const remainingParts = parts.slice(2);
    // Processing remaining parts

    if (remainingParts.length === 0) {
      // 如果没有更多层级，直接添加到accounts中
      accountsByType[accountType][categoryName].accounts.push({
        name: formatAccountName(parts[parts.length - 1]),
        value: accountName,
        fullName: accountName,
      });
    } else if (remainingParts.length === 1) {
      // 只有一级子账户，直接添加
      accountsByType[accountType][categoryName].accounts.push({
        name: formatAccountName(remainingParts[0]),
        value: accountName,
        fullName: accountName,
      });
    } else {
      // 有多级子账户，按第一级分组
      const subGroupName = remainingParts[0];
      // Creating subgroup

      if (!accountsByType[accountType][categoryName].subGroups[subGroupName]) {
        accountsByType[accountType][categoryName].subGroups[subGroupName] = [];
      }

      // 剩余的层级作为子账户名称
      const finalAccountName = remainingParts
        .slice(1)
        .map((part: string) => formatAccountName(part))
        .join("-");
      // Processing sub-account name

      accountsByType[accountType][categoryName].subGroups[subGroupName].push({
        name: finalAccountName,
        value: accountName,
        fullName: accountName,
      });
    }
  });

  // Accounts grouped by type and category

  // 构建分层选项
  const options: Option[] = [];

  // 按类型添加账户（不显示类型标题）
  const typeOrder = [
    "assets",
    "liabilities",
    "income",
    "expenses",
    "equity",
    "other",
  ];

  typeOrder.forEach((type) => {
    const typeCategories = accountsByType[type];
    if (Object.keys(typeCategories).length > 0 && allowedTypes.includes(type)) {
      // 遍历该类型下的所有分类
      Object.keys(typeCategories).forEach((categoryName) => {
        const category = typeCategories[categoryName];

        // 检查是否只有一个直接账户且无子分组（避免重复显示）
        const hasSubGroups = Object.keys(category.subGroups).length > 0;
        const directAccountsCount = category.accounts.length;

        if (!hasSubGroups && directAccountsCount === 1) {
          // 只有一个直接账户且无子分组，直接显示账户（无缩进）
          const account = category.accounts[0];
          options.push({
            text: account.name,
            value: account.value,
          });
        } else {
          // 有多个账户或有子分组，显示分类标题
          options.push({
            text: formatCategoryName(categoryName),
            value: `__category_${type}_${categoryName}__`,
            disabled: true,
          });

          // 添加直接账户（一级缩进）
          category.accounts.forEach((account: any) => {
            options.push({
              text: `　${account.name}`,
              value: account.value,
            });
          });

          // 添加子分组
          Object.keys(category.subGroups).forEach((subGroupName) => {
            const subGroupAccounts = category.subGroups[subGroupName];

            // 添加子分组标题（一级缩进）
            options.push({
              text: `　${formatAccountName(subGroupName)}`,
              value: `__subgroup_${type}_${categoryName}_${subGroupName}__`,
              disabled: true,
            });

            // 添加子分组下的账户（二级缩进）
            subGroupAccounts.forEach((account: any) => {
              options.push({
                text: `　　${account.name}`,
                value: account.value,
              });
            });
          });
        }
      });
    }
  });

  // Final hierarchical options built
  return options;
};

// 计算属性
const accountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.account);
});

// 分类显示名称 - 多个分类用英文逗号隔开
const categoryDisplayText = computed(() => {
  const categories = localFormData.value.categories.filter(
    (cat) => cat.categoryDisplayName
  );

  if (categories.length === 0) {
    return "选择分类";
  }

  if (categories.length === 1) {
    return categories[0].categoryDisplayName;
  }

  // 多个分类用英文逗号隔开
  return categories.map((cat) => cat.categoryDisplayName).join(", ");
});

// 分配金额计算 - 修复多类别编辑模式下分配信息不更新的问题
const allocatedAmount = computed(() => {
  // 在多类别编辑模式下，使用tempCategories，否则使用localFormData.categories
  const targetCategories = isEditingMultiCategory.value
    ? tempCategories.value
    : localFormData.value.categories;

  const total = targetCategories.reduce((sum, item) => {
    const amount = parseFloat(item.amount) || 0;
    return sum + amount;
  }, 0);

  return total;
});

const remainingAmount = computed(() => {
  const totalAmount = parseFloat(localFormData.value.amount) || 0;
  if (props.type === "income") {
    // 收入：期望 分配之和 = -总金额
    return totalAmount + allocatedAmount.value;
  }
  // 支出/调整：期望 分配之和 = 总金额
  return totalAmount - allocatedAmount.value;
});

// 检查单个分类是否完整
const isCategoryComplete = (category: CategoryItem) => {
  return (
    category.category &&
    category.categoryDisplayName &&
    category.amount &&
    !isNaN(parseFloat(category.amount)) &&
    parseFloat(category.amount) !== 0
  );
};

// 检查多类别编辑状态下的有效性
const isMultiCategoryValid = computed(() => {
  if (!isEditingMultiCategory.value) return true;

  const categories =
    tempCategories.value.length > 0
      ? tempCategories.value
      : localFormData.value.categories;

  // 每个分类都必须完整
  const hasValidCategories =
    categories.length > 0 && categories.every((cat) => isCategoryComplete(cat));

  // 金额分配必须匹配
  const totalAmount = parseFloat(localFormData.value.amount) || 0;
  const allocatedAmount = categories.reduce((sum, item) => {
    const amount = parseFloat(item.amount) || 0;
    return sum + amount;
  }, 0);
  const diff =
    props.type === "income"
      ? totalAmount + allocatedAmount
      : totalAmount - allocatedAmount;
  const amountsMatch = Math.abs(diff) < 0.01;

  return hasValidCategories && amountsMatch;
});

// 构建分类层级数据 - 改为计算属性
const categoryHierarchy = computed(() => {
  // 根据交易类型确定分类账户类型
  let targetAccountType = "";
  switch (props.type) {
    case "expense":
      targetAccountType = "Expenses";
      break;
    case "income":
      targetAccountType = "Income";
      break;
    case "adjustment":
      targetAccountType = "Expenses"; // 调整余额默认使用支出分类
      break;
    default:
      targetAccountType = "Expenses";
  }

  // 从现有的分类选项中构建扁平数组，供新的树形结构使用
  const flatCategories: any[] = [];

  categoryOptions.value.forEach((option) => {
    if (option.disabled || !option.value.startsWith(`${targetAccountType}:`)) {
      return;
    }

    flatCategories.push({
      name: option.value,
    });
  });

  return flatCategories;
});

// 构建交易对象列表 - 改为计算属性
const payeeList = computed(() => {
  return payeeOptions.value.map((option) => option.value);
});

// 获取交易类型对应的账户类型 - 改为计算属性
const accountTypesForTransaction = computed(() => {
  switch (props.type) {
    case "expense":
      return ["Assets", "Liabilities"];
    case "income":
      return ["Assets", "Liabilities"];
    case "adjustment":
      return ["Assets", "Liabilities"];
    default:
      return ["Assets", "Liabilities", "Income", "Expenses"];
  }
});

// 监听数据变化 - 使用防抖减少频繁触发
let updateTimeout: ReturnType<typeof setTimeout> | null = null;
const debouncedEmitUpdate = (newData: any) => {
  if (updateTimeout) {
    clearTimeout(updateTimeout);
  }
  updateTimeout = setTimeout(() => {
    if (!isUpdatingFromProps) {
      emit("update", newData);
    }
  }, 800); // 800ms延迟，显著减少触发频率
};

watch(
  localFormData,
  (newData) => {
    debouncedEmitUpdate(newData);
  },
  { deep: true }
);

// 监听props.formData变化，用于编辑模式的数据加载
let isUpdatingFromProps = false;
watch(
  () => props.formData,
  (newData) => {
    // 避免循环更新：只在有实质性变化且不是来自内部更新时更新
    if (newData && !isUpdatingFromProps) {
      // 检查是否真的有变化
      const hasSignificantChange =
        newData.amount !== localFormData.value.amount ||
        newData.account !== localFormData.value.account ||
        newData.category !== localFormData.value.category ||
        newData.payee !== localFormData.value.payee;

      if (hasSignificantChange) {
        // Form data updated

        isUpdatingFromProps = true;
        localFormData.value = {
          ...newData,
          currency: newData.currency || "CNY",
          flag: newData.flag || "*",
          categories: newData.categories || [
            {
              categoryName: "",
              categoryDisplayName: "",
              category: "",
              amount: "",
            },
          ],
        };
        // 下一个tick后重置标志
        nextTick(() => {
          isUpdatingFromProps = false;
        });
      }
    }
  },
  { deep: true, immediate: false }
);

// 监听分类和金额变化，当只有一个分类时自动设置分类金额
watch(
  [
    () => localFormData.value.amount,
    () => localFormData.value.categories,
    () => localFormData.value.categories?.[0]?.category,
  ],
  ([newAmount, newCategories]) => {
    // 只有在非编辑模式且只有一个分类时处理
    if (
      !isEditingMultiCategory.value &&
      newCategories &&
      newCategories.length === 1 &&
      newAmount &&
      !isNaN(parseFloat(newAmount)) &&
      parseFloat(newAmount) !== 0
    ) {
      const firstCategory = newCategories[0];
      const amount = parseFloat(newAmount);

      // 如果分类已选择但金额为空或为0，则自动设置金额
      if (
        firstCategory.category &&
        (!firstCategory.amount || parseFloat(firstCategory.amount) === 0)
      ) {
        // 根据交易类型确定金额符号
        let categoryAmount = amount;

        // 支出：分类金额等于输入金额；收入：分类金额为输入金额相反数
        if (props.type === "expense") {
          categoryAmount = amount;
        } else if (props.type === "income") {
          categoryAmount = -amount;
        }

        firstCategory.amount = String(categoryAmount);
      }
    }
  },
  { deep: true, immediate: false }
);

// 币种相关方法
const getCurrencySymbol = (currency: string) => {
  const symbols: Record<string, string> = {
    CNY: "¥",
    USD: "$",
    EUR: "€",
    GBP: "£",
    JPY: "¥",
    HKD: "HK$",
    TWD: "NT$",
    AUD: "A$",
    CAD: "C$",
    SGD: "S$",
  };
  return symbols[currency] || currency;
};

const onCurrencyConfirm = (option: { value: string }) => {
  localFormData.value.currency = option.value;
  showCurrencySelector.value = false;
};

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

const onCategoryAmountInput = (index: number, value: string | number) => {
  // Category amount input changed

  // 获取当前编辑的分类数组
  const targetCategories = isEditingMultiCategory.value
    ? tempCategories.value
    : localFormData.value.categories;

  // 确保分类数组存在且索引有效
  if (!targetCategories[index]) {
    // console.error(`Category at index ${index} does not exist`);
    return;
  }

  // 直接更新分类金额，不影响总金额
  const stringValue = String(value || "");

  // 直接更新分类对象的amount属性，确保响应式更新
  targetCategories[index].amount = stringValue;

  // console.log(`Updated category ${index} amount to:`, stringValue);
  // console.log("Current categories:", targetCategories);
  // console.log("Current allocated amount:", allocatedAmount.value);
  // console.log("Current remaining amount:", remainingAmount.value);
};

// 全屏交易对象选择器方法
const showFullScreenPayeeSelector = () => {
  if (payeeSelectorRef.value) {
    payeeSelectorRef.value.show();
  }
};

const onFullScreenPayeeConfirm = (payee: string) => {
  localFormData.value.payee = payee;
  // console.log("选择的交易对象:", payee);
};

const onFullScreenPayeeClose = () => {
  // console.log("交易对象选择器已关闭");
};

// 清除交易对象
const clearPayee = () => {
  localFormData.value.payee = "";
  // console.log("已清除交易对象");
};

// 全屏账户选择器方法
const showFullScreenAccountSelector = () => {
  if (accountSelectorRef.value) {
    accountSelectorRef.value.show();
  }
};

const onFullScreenAccountConfirm = (accountName: string) => {
  localFormData.value.account = accountName;
};

const onFullScreenAccountClose = () => {
  // 关闭回调，可以在这里处理一些状态重置
};

// 日期处理
const formatDateDisplay = (date: Date) => {
  if (!date) return "选择日期";
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

const onDateConfirm = (date: Date) => {
  localFormData.value.date = date;
  showDateCalendar.value = false;
};

// 分类管理
const addCategory = () => {
  if (isEditingMultiCategory.value) {
    tempCategories.value.push({
      categoryName: "",
      categoryDisplayName: "",
      category: "",
      amount: "",
    });
  } else {
    localFormData.value.categories.push({
      categoryName: "",
      categoryDisplayName: "",
      category: "",
      amount: "",
    });
  }
};

const removeCategory = (index: number) => {
  const targetCategories = isEditingMultiCategory.value
    ? tempCategories.value
    : localFormData.value.categories;
  if (targetCategories.length > 1) {
    targetCategories.splice(index, 1);
  }
};

// 多类别弹窗操作
const openMultiCategorySheet = () => {
  // 开始编辑模式，复制当前数据到临时变量
  tempCategories.value = JSON.parse(
    JSON.stringify(localFormData.value.categories)
  );

  // 在打开多类别时，如果有输入的总金额且第一个分类没有金额，则自动赋值
  if (localFormData.value.amount && tempCategories.value.length > 0) {
    const totalAmount = parseFloat(localFormData.value.amount);
    if (!isNaN(totalAmount) && totalAmount !== 0) {
      const firstCategory = tempCategories.value[0];
      if (
        firstCategory.category &&
        (!firstCategory.amount || parseFloat(firstCategory.amount) === 0)
      ) {
        // 根据交易类型确定金额符号
        let categoryAmount = totalAmount;

        // 支出：分类金额等于输入金额；收入：分类金额为输入金额相反数
        if (props.type === "expense") {
          categoryAmount = totalAmount;
        } else if (props.type === "income") {
          categoryAmount = -totalAmount;
        }

        firstCategory.amount = String(categoryAmount);
      }
    }
  }

  isEditingMultiCategory.value = true;
  showMultiCategorySheet.value = true;
};

const cancelMultiCategory = () => {
  // 取消编辑，恢复原始数据
  tempCategories.value = [];
  isEditingMultiCategory.value = false;
  showMultiCategorySheet.value = false;
};

const confirmMultiCategory = () => {
  // 确认编辑，应用临时数据
  if (tempCategories.value.length > 0) {
    localFormData.value.categories = [...tempCategories.value];
  }
  tempCategories.value = [];
  isEditingMultiCategory.value = false;
  showMultiCategorySheet.value = false;
};

// 全屏分类选择器方法
const showFullScreenCategorySelector = (index?: number) => {
  if (index !== undefined) {
    currentCategoryIndex.value = index;
  } else {
    currentCategoryIndex.value = 0;
  }

  if (categorySelectorRef.value) {
    categorySelectorRef.value.show();
  }
};

const onFullScreenCategoryConfirm = (categoryName: string) => {
  const index = currentCategoryIndex.value;

  // 获取当前编辑的分类数组
  const targetCategories = isEditingMultiCategory.value
    ? tempCategories.value
    : localFormData.value.categories;

  targetCategories[index].category = categoryName; // 原始值用于提交
  targetCategories[index].categoryName = categoryName; // 保持兼容
  targetCategories[index].categoryDisplayName =
    formatAccountNameForDisplay(categoryName); // 格式化显示值

  // 如果只有一个分类且有输入金额，自动设置分类金额
  if (
    !isEditingMultiCategory.value &&
    targetCategories.length === 1 &&
    localFormData.value.amount &&
    (!targetCategories[0].amount ||
      parseFloat(targetCategories[0].amount) === 0)
  ) {
    const amount = parseFloat(localFormData.value.amount);
    if (!isNaN(amount) && amount !== 0) {
      // 根据交易类型确定金额符号
      let categoryAmount = amount;

      // 支出：分类金额等于输入金额；收入：分类金额为输入金额相反数
      if (props.type === "expense") {
        categoryAmount = amount;
      } else if (props.type === "income") {
        categoryAmount = -amount;
      }

      targetCategories[0].amount = String(categoryAmount);
    }
  }
};

const onFullScreenCategoryClose = () => {
  // 关闭回调，可以在这里处理一些状态重置
};

const onSubmit = () => {
  // 基础信息校验
  if (!localFormData.value.amount) {
    showToast("请输入金额");
    return;
  }

  if (!localFormData.value.account) {
    showToast("请选择账户");
    return;
  }

  const amount = parseFloat(localFormData.value.amount);
  if (isNaN(amount) || amount === 0) {
    showToast("请输入有效金额");
    return;
  }

  // 单个分类时，自动将分类金额设置为总金额（提交前最后检查）
  if (localFormData.value.categories.length === 1) {
    const firstCategory = localFormData.value.categories[0];
    if (
      firstCategory.category &&
      (!firstCategory.amount || parseFloat(firstCategory.amount) === 0)
    ) {
      // 根据交易类型确定金额符号
      let categoryAmount = amount;

      // 支出：分类金额等于输入金额；收入：分类金额为输入金额相反数
      if (props.type === "expense") {
        categoryAmount = amount;
      } else if (props.type === "income") {
        categoryAmount = -amount;
      }

      firstCategory.amount = String(categoryAmount);
    }
  }

  // 分类校验 - 每个分类都必须有值
  const invalidCategories = [];
  for (let i = 0; i < localFormData.value.categories.length; i++) {
    const category = localFormData.value.categories[i];

    if (!category.category || !category.categoryDisplayName) {
      invalidCategories.push(`第${i + 1}个分类未选择`);
    } else if (
      !category.amount ||
      isNaN(parseFloat(category.amount)) ||
      parseFloat(category.amount) === 0
    ) {
      invalidCategories.push(`第${i + 1}个分类金额无效`);
    }
  }

  if (invalidCategories.length > 0) {
    showToast(invalidCategories[0]); // 显示第一个错误
    return;
  }

  // 金额分配校验 - 剩余金额必须为0
  if (Math.abs(remainingAmount.value) >= 0.01) {
    const remaining = remainingAmount.value;
    if (remaining > 0) {
      showToast(`还需分配 ¥${remaining.toFixed(2)}`);
    } else {
      showToast(`超出分配 ¥${Math.abs(remaining).toFixed(2)}`);
    }
    return;
  }

  emit("submit", {
    ...localFormData.value,
    amount: amount,
  });
};

const loadOptions = async () => {
  // console.log("=== TransactionForm loadOptions 开始 ===");
  // console.log("当前交易类型:", props.type);

  try {
    // 加载收款人历史
    try {
      // console.log("正在加载收款人列表...");
      const payeeData = await getPayees();
      // console.log("收款人API原始响应:", payeeData);

      payeeOptions.value = Array.isArray(payeeData)
        ? payeeData.map((p) => ({ text: p, value: p }))
        : [];
      // console.log("处理后的收款人选项:", payeeOptions.value);
    } catch (error) {
      // console.error("获取收款人列表失败:", error);
      payeeOptions.value = [];
    }

    // 加载账户选项 - 资产和负债账户
    try {
      // console.log("正在加载账户列表...");
      const response = await getAccountsByType();
      // console.log("账户API完整响应:", response);
      const accountData = response.data || response;
      // console.log("账户数据:", accountData);
      // console.log("账户数据类型:", typeof accountData);

      // 处理后端返回的按类型分组的数据格式
      let accounts: string[] = [];
      if (accountData && typeof accountData === "object") {
        // console.log("Assets账户:", accountData.Assets);
        // console.log("Liabilities账户:", accountData.Liabilities);

        // 提取 Assets 和 Liabilities 类型的账户
        const assetsAccounts: string[] = accountData.Assets || [];
        const liabilitiesAccounts: string[] = accountData.Liabilities || [];
        accounts = [...assetsAccounts, ...liabilitiesAccounts];

        // console.log("合并后的账户列表:", accounts);
      } else {
        // console.warn("账户数据格式不正确或为空:", accountData);
      }

      // 构建分层账户选项
      accountOptions.value = buildHierarchicalOptions(accounts, [
        "assets",
        "liabilities",
      ]);

      // console.log("最终账户选项:", accountOptions.value);
      // console.log("账户选项数量:", accountOptions.value.length);
    } catch (error) {
      // console.error("获取账户列表失败:", error);
      console.error(
        "错误详情:",
        (error as any).response || (error as any).message || error
      );

      // 备用硬编码数据
      // console.log("使用备用账户数据");
      const fallbackAccounts = [
        "Assets:ZJ-资金:现金",
        "Assets:ZJ-资金:活期存款",
        "Liabilities:XYK-信用卡:招行:8164",
      ];
      accountOptions.value = buildHierarchicalOptions(fallbackAccounts, [
        "assets",
        "liabilities",
      ]);
    }

    // 加载分类选项
    try {
      // console.log("正在加载分类列表...");
      const response = await getAccountsByType();
      // console.log("分类API完整响应:", response);
      const categoryData = response.data || response;
      // console.log("分类数据:", categoryData);

      // 处理后端返回的按类型分组的数据格式
      let categories: string[] = [];
      if (categoryData && typeof categoryData === "object") {
        // 根据交易类型选择对应的分类
        if (props.type === "expense") {
          categories = categoryData.Expenses || [];
          // console.log("支出分类:", categories);
        } else if (props.type === "income") {
          categories = categoryData.Income || [];
          // console.log("收入分类:", categories);
        } else {
          // console.log("调整类型，使用支出分类");
          categories = categoryData.Expenses || [];
        }
      } else {
        // console.warn("分类数据格式不正确或为空:", categoryData);
      }

      // 构建分层分类选项
      const categoryTypes =
        props.type === "expense"
          ? ["expenses"]
          : props.type === "income"
          ? ["income"]
          : ["expenses"];
      categoryOptions.value = buildHierarchicalOptions(
        categories,
        categoryTypes
      );

      // console.log("最终分类选项:", categoryOptions.value);
      // console.log("分类选项数量:", categoryOptions.value.length);
    } catch (error) {
      // console.error("获取分类列表失败:", error);
      console.error(
        "错误详情:",
        (error as any).response || (error as any).message || error
      );

      // 备用硬编码数据
      // console.log("使用备用分类数据");
      if (props.type === "expense") {
        const fallbackCategories = [
          "Expenses:CY-餐饮",
          "Expenses:JT-交通:公交",
          "Expenses:JT-交通:打车",
          "Expenses:YL-娱乐:其他",
        ];
        categoryOptions.value = buildHierarchicalOptions(fallbackCategories, [
          "expenses",
        ]);
      } else {
        const fallbackCategories = [
          "Income:GZ-工资",
          "Income:TZ-投资",
          "Income:QT-其他",
        ];
        categoryOptions.value = buildHierarchicalOptions(fallbackCategories, [
          "income",
        ]);
      }
    }
  } catch (error) {
    // console.error("加载选项数据失败:", error);
  }

  // console.log("=== TransactionForm loadOptions 结束 ===");
};

onMounted(() => {
  loadOptions();
});
</script>

<style scoped>
.transaction-form {
  padding: 0;
  background: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

/* 表单卡片基础样式 */
.form-card {
  display: flex;
  align-items: center;
  background: var(--van-background-2);
  border-radius: 16px;
  padding: 12px; /* 进一步减小内边距 */
  margin: 10px 16px; /* 进一步减小上下间距 */
  margin-bottom: 6px; /* 进一步减小底部间距 */
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 50px; /* 进一步减小最小高度 */
  position: relative;
}

.form-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.form-card:active {
  transform: scale(0.98);
  transition: all 0.1s ease;
}

.card-icon {
  width: 36px; /* 进一步减小图标容器 */
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--van-background);
  border-radius: 10px; /* 进一步减小圆角 */
  margin-right: 12px; /* 进一步减小右边距 */
  color: var(--van-text-color-2);
  font-size: 16px; /* 进一步减小图标 */
  flex-shrink: 0;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.card-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-label {
  font-size: 16px; /* 适中字体大小 */
  color: var(--van-text-color);
  font-weight: 500;
  flex: 1;
  margin-right: 10px; /* 减小右边距 */
  line-height: 1.4; /* 减小行高 */
  word-wrap: break-word; /* 允许长单词换行 */
  word-break: break-all; /* 在任何字符间断行 */
  white-space: normal; /* 允许换行 */
  transition: color 0.3s ease;
}

/* 账户卡片 */
.account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: var(--van-warning-color);
}

/* 金额卡片 */
.amount-card {
  background: var(--van-background-2);
}

.amount-card .card-icon {
  background: rgba(238, 90, 82, 0.1);
  color: var(--van-danger-color);
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
  padding: 6px 10px; /* 进一步减小内边距 */
  background: var(--van-background);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  min-height: 32px; /* 进一步减小最小高度 */
}

.currency-selector:hover {
  background: #ebedf0;
  transform: scale(1.02);
}

.currency-selector:active {
  transform: scale(0.98);
}

.currency-symbol {
  font-size: 20px; /* 进一步减小字体 */
  font-weight: bold;
  color: var(--van-text-color);
  transition: color 0.3s ease;
}

.amount-field {
  flex: 1;
}

.amount-field :deep(.van-field__control) {
  font-size: 20px;
  font-weight: bold;
  text-align: left;
  color: var(--van-text-color);
  min-height: 32px;
  line-height: 1.2;
  border: none;
  background: transparent;
  padding: 0;
  transition: color 0.3s ease;
}

.amount-field :deep(.van-field__control::placeholder) {
  color: var(--van-text-color-3);
  transition: color 0.3s ease;
}

.amount-field :deep(.van-field__body) {
  padding: 0;
}

.amount-field :deep(.van-field__label) {
  display: none;
}

/* 分类卡片 */
.category-card .card-icon {
  background: rgba(52, 168, 83, 0.1);
  color: #34a853;
}

.multi-category-btn {
  display: flex;
  align-items: center;
  gap: 3px; /* 进一步减小间距 */
  padding: 5px 10px; /* 进一步减小内边距 */
  background: rgba(238, 90, 82, 0.1);
  border-radius: 14px; /* 进一步减小圆角 */
  font-size: 11px; /* 进一步减小字体大小 */
  color: #ee5a52;
  cursor: pointer;
  min-height: 28px; /* 进一步减小最小高度 */
  transition: all 0.2s ease;
}

.multi-category-btn:hover {
  background: rgba(238, 90, 82, 0.15);
  transform: scale(1.02);
}

.multi-category-btn:active {
  transform: scale(0.98);
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

.selector-header {
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.selector-header .van-nav-bar {
  background: var(--bg-color);
}

.selector-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
}

/* 多类别面板样式 */
.multi-category-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--van-background);
  transition: background-color 0.3s ease;
}

.multi-category-header {
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.multi-category-header .van-nav-bar {
  background: var(--van-background-2);
  transition: background-color 0.3s ease;
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
  background: var(--van-background-2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.category-item--incomplete {
  background: var(--van-red-light);
  border: 1px solid var(--van-red);
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
  border-top: 1px solid var(--van-border-color);
  background: var(--van-background-2);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.amount-summary {
  padding: 16px;
  background: var(--van-background-2);
  border-radius: 12px 12px 0 0;
  border-top: 1px solid var(--van-border-color);
  font-size: 14px;
  color: var(--van-text-color-2);
  transition: all 0.3s ease;
}

.amount-summary--balanced {
  background: var(--van-green-light);
  border: 1px solid var(--van-green);
}

.amount-summary--unbalanced {
  background: var(--van-red-light);
  border: 1px solid var(--van-red);
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
  color: var(--van-orange);
  padding: 8px;
  background: var(--van-orange-light);
  border-radius: 8px;
  border: 1px solid var(--van-orange);
}

.balance-hint--success {
  color: var(--van-green);
  background: var(--van-green-light);
  border-color: var(--van-green);
}

.history-title {
  padding: 16px;
  font-size: 14px;
  color: var(--van-text-color-2);
  background: var(--van-background);
  transition: background-color 0.3s ease, color 0.3s ease;
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
  margin: 12px 16px; /* 减小上下间距 */
  border-radius: 16px;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
}

:deep(.van-cell) {
  min-height: 46px; /* 减小单元格最小高度 */
  padding: 10px 16px; /* 减小内边距 */
}

:deep(.van-field__label) {
  font-size: 16px; /* 增大标签字体 */
  font-weight: 600; /* 增加字体粗细，与其他标签保持一致 */
}

/* 专门为日期单元格添加样式 */
:deep(.van-cell__title) {
  font-weight: 600; /* 为日期标题添加加粗 */
}

/* 清除图标样式 */
.clear-icon {
  color: #969799;
  font-size: 16px;
  padding: 4px;
  transition: color 0.2s ease;
}

.clear-icon:hover {
  color: #323233;
}

.clear-icon:active {
  color: #ee0a24;
}

/* 为交易状态标题添加样式 */
:deep(.van-cell__title) {
  font-weight: 600; /* 确保所有cell标题都加粗 */
}

:deep(.van-field__control) {
  font-size: 16px; /* 增大输入框字体 */
}

:deep(.van-button--mini) {
  min-width: 65px; /* 减小最小宽度 */
  height: 34px; /* 减小按钮高度 */
  font-size: 12px; /* 减小字体 */
  border-radius: 18px; /* 减小圆角 */
}

/* 移动端响应式优化 */
@media (max-width: 375px) {
  .form-card {
    margin: 10px 12px; /* 减小间距 */
    padding: 14px; /* 减小内边距 */
    min-height: 56px; /* 减小最小高度 */
  }

  .card-icon {
    width: 38px; /* 减小图标 */
    height: 38px;
    margin-right: 12px; /* 减小右边距 */
    font-size: 16px;
  }

  .card-label {
    font-size: 15px; /* 减小字体 */
  }

  .currency-symbol {
    font-size: 20px; /* 减小字体 */
  }

  .amount-field :deep(.van-field__control) {
    font-size: 20px; /* 减小字体 */
    min-height: 32px;
  }

  :deep(.van-cell) {
    min-height: 42px; /* 减小单元格高度 */
    padding: 8px 16px; /* 减小内边距 */
  }
}

@media (max-width: 320px) {
  .form-card {
    margin: 8px 10px; /* 减小间距 */
    padding: 12px; /* 减小内边距 */
    min-height: 52px; /* 减小最小高度 */
  }

  .card-icon {
    width: 36px; /* 减小图标 */
    height: 36px;
    margin-right: 12px;
    font-size: 14px;
  }

  .card-label {
    font-size: 14px; /* 减小字体 */
  }

  .currency-symbol {
    font-size: 18px; /* 减小字体 */
  }

  .amount-field :deep(.van-field__control) {
    font-size: 18px; /* 减小字体 */
    min-height: 30px;
  }

  :deep(.van-cell) {
    min-height: 40px; /* 减小单元格高度 */
    padding: 6px 16px; /* 减小内边距 */
  }
}
</style>
