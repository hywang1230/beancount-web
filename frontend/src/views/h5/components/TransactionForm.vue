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
      <div class="form-card amount-card" @click="showAmountKeyboard">
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
          <div
            class="amount-display"
            :class="{ placeholder: !localFormData.amount }"
          >
            {{ localFormData.amount || "0.00" }}
          </div>
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

    <!-- 全屏账户选择器 -->
    <FullScreenSelector
      ref="accountSelectorRef"
      type="account"
      title="选择账户"
      :show-search="true"
      :show-account-types="true"
      :account-types="accountTypesForTransaction"
      @confirm="onFullScreenAccountConfirm"
      @close="onFullScreenAccountClose"
    />

    <!-- 全屏分类选择器 -->
    <FullScreenSelector
      ref="categorySelectorRef"
      type="category"
      title="选择分类"
      :show-search="true"
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
          <van-button type="default" size="small" @click="cancelMultiCategory">
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
                type="number"
                placeholder="0.00"
                class="amount-field-small"
                @update:model-value="
                  (value) => onCategoryAmountInput(index, value)
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

    <!-- 数字键盘 -->
    <van-number-keyboard
      v-model:show="showAmountKeyboardVisible"
      theme="custom"
      :extra-key="['.', '-']"
      close-button-text="完成"
      @blur="hideAmountKeyboard"
      @input="onKeyboardInput"
      @delete="onKeyboardDelete"
      @close="hideAmountKeyboard"
    />
  </div>
</template>

<script setup lang="ts">
import { getAccountsByType } from "@/api/accounts";
import { getPayees } from "@/api/transactions";
import { useKeyboard } from "@/utils/useKeyboard";
import { showToast } from "vant";
import { computed, nextTick, onMounted, ref, watch } from "vue";
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
  (e: "keyboard-visible", visible: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 使用键盘管理工具
const { isKeyboardVisible } = useKeyboard();

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
  (newVal, oldVal) => {
    console.log("金额变化:", oldVal, "->", newVal, "新值类型:", typeof newVal);
  },
  { immediate: true }
);

// 弹窗状态
const showCurrencySelector = ref(false);
const showMultiCategorySheet = ref(false);
const showDateCalendar = ref(false);
const showAmountKeyboardVisible = ref(false);

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
  console.log("构建精细层级选项，输入账户:", accounts);
  console.log("允许的类型:", allowedTypes);

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
    console.log(`处理账户: ${accountName}, parts:`, parts);

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
    console.log(`  remainingParts:`, remainingParts);

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
      console.log(`  创建子分组: ${subGroupName}`);

      if (!accountsByType[accountType][categoryName].subGroups[subGroupName]) {
        accountsByType[accountType][categoryName].subGroups[subGroupName] = [];
      }

      // 剩余的层级作为子账户名称
      const finalAccountName = remainingParts
        .slice(1)
        .map((part: string) => formatAccountName(part))
        .join("-");
      console.log(`  子账户名称: ${finalAccountName}`);

      accountsByType[accountType][categoryName].subGroups[subGroupName].push({
        name: finalAccountName,
        value: accountName,
        fullName: accountName,
      });
    }
  });

  console.log("按类型和分类分组的账户:", accountsByType);

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

  console.log("最终构建的精细层级选项:", options);
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

// 分配金额计算
const allocatedAmount = computed(() => {
  return localFormData.value.categories.reduce((sum, item) => {
    const amount = parseFloat(item.amount) || 0;
    return sum + amount;
  }, 0);
});

const remainingAmount = computed(() => {
  const totalAmount = parseFloat(localFormData.value.amount) || 0;
  return totalAmount - allocatedAmount.value;
});

// 检查单个分类是否完整
const isCategoryComplete = (category: CategoryItem) => {
  return (
    category.category &&
    category.categoryDisplayName &&
    category.amount &&
    parseFloat(category.amount) > 0
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
  const amountsMatch = Math.abs(totalAmount - allocatedAmount) < 0.01;

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
    if (newData && newData.amount && newData.account && !isUpdatingFromProps) {
      // 检查是否真的有变化
      const hasSignificantChange =
        newData.amount !== localFormData.value.amount ||
        newData.account !== localFormData.value.account ||
        newData.category !== localFormData.value.category ||
        newData.payee !== localFormData.value.payee;

      if (hasSignificantChange) {
        console.log("TransactionForm收到新的formData:", newData);

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
      parseFloat(newAmount) > 0
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

        // 对于支出类型，分类金额为正数
        // 对于收入类型，分类金额为正数
        // 对于调整类型，保持原金额符号
        if (props.type === "expense" || props.type === "income") {
          categoryAmount = Math.abs(amount);
        }

        firstCategory.amount = String(categoryAmount);
        console.log(
          `单分类自动设置金额: ${categoryAmount}, 交易类型: ${props.type}`
        );
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

const onCurrencyConfirm = ({
  selectedValues,
}: {
  selectedValues: string[];
}) => {
  localFormData.value.currency = selectedValues[0];
  showCurrencySelector.value = false;
};

// 方法
const onAmountInput = (value: string | number) => {
  console.log("onAmountInput called with:", value, typeof value);
  // 去掉自动联动逻辑，只记录金额输入，不自动更新分类金额
};

// 数字键盘相关方法
const showAmountKeyboard = () => {
  showAmountKeyboardVisible.value = true;
  emit("keyboard-visible", true);
};

const hideAmountKeyboard = () => {
  showAmountKeyboardVisible.value = false;
  emit("keyboard-visible", false);
};

// 监听全局键盘状态变化
watch(isKeyboardVisible, (visible) => {
  emit("keyboard-visible", visible);
});

const onKeyboardInput = (key: string | number) => {
  console.log("键盘输入:", key, "类型:", typeof key);
  const currentAmount = String(localFormData.value.amount || "0");
  console.log("当前金额:", currentAmount, "类型:", typeof currentAmount);

  // 确保key是字符串
  const keyStr = String(key);

  // 处理不同类型的输入
  if (keyStr === ".") {
    // 处理小数点
    handleDecimalPoint();
    return;
  } else if (keyStr === "-") {
    // 处理负号
    handleMinusSign();
    return;
  } else {
    // 处理数字输入
    let newAmount = "";
    if (currentAmount === "0" || currentAmount === "0.00") {
      newAmount = keyStr;
    } else {
      newAmount = currentAmount + keyStr;
    }

    console.log("计算的新金额:", newAmount);
    localFormData.value.amount = newAmount;
    console.log("设置后的金额:", localFormData.value.amount);
  }

  // 触发原有的输入处理逻辑
  onAmountInput(localFormData.value.amount);
};

const onKeyboardDelete = () => {
  const currentAmount = localFormData.value.amount || "";
  if (currentAmount.length > 0) {
    if (currentAmount.length === 1) {
      localFormData.value.amount = "0";
    } else {
      localFormData.value.amount = currentAmount.slice(0, -1);
    }
  }

  // 触发原有的输入处理逻辑
  onAmountInput(localFormData.value.amount);
};

const handleDecimalPoint = () => {
  const currentAmount = String(localFormData.value.amount || "0");

  // 检查是否已有小数点
  if (currentAmount.includes(".")) {
    return; // 已经有小数点了，不再添加
  }

  // 添加小数点
  if (currentAmount === "0" || currentAmount === "") {
    localFormData.value.amount = "0.";
  } else {
    localFormData.value.amount = currentAmount + ".";
  }

  console.log("添加小数点后:", localFormData.value.amount);

  // 触发原有的输入处理逻辑
  onAmountInput(localFormData.value.amount);
};

const handleMinusSign = () => {
  const currentAmount = String(localFormData.value.amount || "0");

  // 如果已经是负数，则转为正数
  if (currentAmount.startsWith("-")) {
    localFormData.value.amount = currentAmount.substring(1);
  } else {
    // 如果是正数或零，则转为负数
    if (
      currentAmount === "0" ||
      currentAmount === "0.00" ||
      currentAmount === ""
    ) {
      localFormData.value.amount = "-0";
    } else {
      localFormData.value.amount = "-" + currentAmount;
    }
  }

  console.log("切换正负号后:", localFormData.value.amount);

  // 触发原有的输入处理逻辑
  onAmountInput(localFormData.value.amount);
};

const onCategoryAmountInput = (index: number, value: string | number) => {
  console.log(`Category ${index} amount input:`, value, typeof value);

  // 获取当前编辑的分类数组
  const targetCategories = isEditingMultiCategory.value
    ? tempCategories.value
    : localFormData.value.categories;

  // 确保分类数组存在且索引有效
  if (!targetCategories[index]) {
    console.error(`Category at index ${index} does not exist`);
    return;
  }

  // 直接更新分类金额，不影响总金额
  const stringValue = String(value || "");

  // 使用 Vue 3 的响应式更新方式
  targetCategories[index] = {
    ...targetCategories[index],
    amount: stringValue,
  };

  console.log(`Updated category ${index} amount to:`, stringValue);
  console.log("Current categories:", targetCategories);
};

// 全屏交易对象选择器方法
const showFullScreenPayeeSelector = () => {
  if (payeeSelectorRef.value) {
    payeeSelectorRef.value.show();
  }
};

const onFullScreenPayeeConfirm = (payee: string) => {
  localFormData.value.payee = payee;
  console.log("选择的交易对象:", payee);
};

const onFullScreenPayeeClose = () => {
  console.log("交易对象选择器已关闭");
};

// 清除交易对象
const clearPayee = () => {
  localFormData.value.payee = "";
  console.log("已清除交易对象");
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
    if (!isNaN(totalAmount) && totalAmount > 0) {
      const firstCategory = tempCategories.value[0];
      if (
        firstCategory.category &&
        (!firstCategory.amount || parseFloat(firstCategory.amount) === 0)
      ) {
        // 根据交易类型确定金额符号
        let categoryAmount = totalAmount;

        // 对于支出类型，分类金额为正数
        // 对于收入类型，分类金额为正数
        // 对于调整类型，保持原金额符号
        if (props.type === "expense" || props.type === "income") {
          categoryAmount = Math.abs(totalAmount);
        }

        firstCategory.amount = String(categoryAmount);
        console.log(
          `多类别模式：自动将总金额赋值给第一个分类: ${categoryAmount}, 交易类型: ${props.type}`
        );
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
    if (!isNaN(amount) && amount > 0) {
      // 根据交易类型确定金额符号
      let categoryAmount = amount;

      // 对于支出类型，分类金额为正数
      // 对于收入类型，分类金额为正数
      // 对于调整类型，保持原金额符号
      if (props.type === "expense" || props.type === "income") {
        categoryAmount = Math.abs(amount);
      }

      targetCategories[0].amount = String(categoryAmount);
      console.log(
        `分类选择后自动设置金额: ${categoryAmount}, 交易类型: ${props.type}`
      );
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
  if (isNaN(amount) || amount <= 0) {
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

      // 对于支出类型，分类金额为正数
      // 对于收入类型，分类金额为正数
      // 对于调整类型，保持原金额符号
      if (props.type === "expense" || props.type === "income") {
        categoryAmount = Math.abs(amount);
      }

      firstCategory.amount = String(categoryAmount);
      console.log(
        `提交前单个分类自动赋值金额: ${categoryAmount}, 交易类型: ${props.type}`
      );
    }
  }

  // 分类校验 - 每个分类都必须有值
  const invalidCategories = [];
  for (let i = 0; i < localFormData.value.categories.length; i++) {
    const category = localFormData.value.categories[i];

    if (!category.category || !category.categoryDisplayName) {
      invalidCategories.push(`第${i + 1}个分类未选择`);
    } else if (!category.amount || parseFloat(category.amount) <= 0) {
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
    amount: props.type === "expense" ? -amount : amount,
  });
};

const loadOptions = async () => {
  console.log("=== TransactionForm loadOptions 开始 ===");
  console.log("当前交易类型:", props.type);

  try {
    // 加载收款人历史
    try {
      console.log("正在加载收款人列表...");
      const payeeData = await getPayees();
      console.log("收款人API原始响应:", payeeData);

      payeeOptions.value = Array.isArray(payeeData)
        ? payeeData.map((p) => ({ text: p, value: p }))
        : [];
      console.log("处理后的收款人选项:", payeeOptions.value);
    } catch (error) {
      console.error("获取收款人列表失败:", error);
      payeeOptions.value = [];
    }

    // 加载账户选项 - 资产和负债账户
    try {
      console.log("正在加载账户列表...");
      const response = await getAccountsByType();
      console.log("账户API完整响应:", response);
      const accountData = response.data || response;
      console.log("账户数据:", accountData);
      console.log("账户数据类型:", typeof accountData);

      // 处理后端返回的按类型分组的数据格式
      let accounts: string[] = [];
      if (accountData && typeof accountData === "object") {
        console.log("Assets账户:", accountData.Assets);
        console.log("Liabilities账户:", accountData.Liabilities);

        // 提取 Assets 和 Liabilities 类型的账户
        const assetsAccounts: string[] = accountData.Assets || [];
        const liabilitiesAccounts: string[] = accountData.Liabilities || [];
        accounts = [...assetsAccounts, ...liabilitiesAccounts];

        console.log("合并后的账户列表:", accounts);
      } else {
        console.warn("账户数据格式不正确或为空:", accountData);
      }

      // 构建分层账户选项
      accountOptions.value = buildHierarchicalOptions(accounts, [
        "assets",
        "liabilities",
      ]);

      console.log("最终账户选项:", accountOptions.value);
      console.log("账户选项数量:", accountOptions.value.length);
    } catch (error) {
      console.error("获取账户列表失败:", error);
      console.error(
        "错误详情:",
        (error as any).response || (error as any).message || error
      );

      // 备用硬编码数据
      console.log("使用备用账户数据");
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
      console.log("正在加载分类列表...");
      const response = await getAccountsByType();
      console.log("分类API完整响应:", response);
      const categoryData = response.data || response;
      console.log("分类数据:", categoryData);

      // 处理后端返回的按类型分组的数据格式
      let categories: string[] = [];
      if (categoryData && typeof categoryData === "object") {
        // 根据交易类型选择对应的分类
        if (props.type === "expense") {
          categories = categoryData.Expenses || [];
          console.log("支出分类:", categories);
        } else if (props.type === "income") {
          categories = categoryData.Income || [];
          console.log("收入分类:", categories);
        } else {
          console.log("调整类型，使用支出分类");
          categories = categoryData.Expenses || [];
        }
      } else {
        console.warn("分类数据格式不正确或为空:", categoryData);
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

      console.log("最终分类选项:", categoryOptions.value);
      console.log("分类选项数量:", categoryOptions.value.length);
    } catch (error) {
      console.error("获取分类列表失败:", error);
      console.error(
        "错误详情:",
        (error as any).response || (error as any).message || error
      );

      // 备用硬编码数据
      console.log("使用备用分类数据");
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
    console.error("加载选项数据失败:", error);
  }

  console.log("=== TransactionForm loadOptions 结束 ===");
};

onMounted(() => {
  loadOptions();
});
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
  background: #f7f8fa;
  border-radius: 10px; /* 进一步减小圆角 */
  margin-right: 12px; /* 进一步减小右边距 */
  color: #646566;
  font-size: 16px; /* 进一步减小图标 */
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-label {
  font-size: 16px; /* 适中字体大小 */
  color: #323233;
  font-weight: 500;
  flex: 1;
  margin-right: 10px; /* 减小右边距 */
  line-height: 1.4; /* 减小行高 */
  max-height: 2.8em; /* 减小最大高度 */
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
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
  padding: 6px 10px; /* 进一步减小内边距 */
  background: #f7f8fa;
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
  color: #323233;
}

.amount-field {
  flex: 1;
}

.amount-field :deep(.van-field__control) {
  font-size: 20px; /* 进一步减小字体 */
  font-weight: bold;
  text-align: left;
  color: #323233;
  min-height: 32px; /* 进一步减小最小高度 */
  line-height: 1.2; /* 减小行高 */
}

.amount-field :deep(.van-field__control::placeholder) {
  color: #c8c9cc;
}

/* 金额显示区域样式 */
.amount-display {
  flex: 1;
  font-size: 20px;
  font-weight: bold;
  text-align: left;
  color: #323233;
  min-height: 32px;
  line-height: 32px;
  cursor: pointer;
  padding: 0;
  border: none;
  background: transparent;
  user-select: none;
}

.amount-display.placeholder {
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

/* 多类别面板样式 */
.multi-category-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 2003;
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
