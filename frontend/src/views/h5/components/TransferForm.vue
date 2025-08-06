<template>
  <div class="transfer-form">
    <van-form @submit="onSubmit">
      <!-- 转出账户卡片 -->
      <div
        class="form-card from-account-card"
        @click="showFullScreenFromAccountSelector"
      >
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">
            {{ fromAccountDisplayName || "转出账户" }}
          </div>
          <van-icon name="arrow" />
        </div>
      </div>

      <!-- 金额输入卡片 -->
      <div class="form-card amount-card">
        <div class="card-icon">
          <van-icon name="exchange" />
        </div>
        <div class="amount-input-container">
          <div class="currency-selector" @click="showCurrencySelector = true">
            <span class="currency-symbol">{{
              getCurrencySymbol(localFormData.currency)
            }}</span>
            <van-icon name="arrow-down" size="12" />
          </div>
          <van-field
            v-model="localFormData.amount"
            type="number"
            placeholder="0.00"
            class="amount-field"
            :border="false"
            @update:model-value="onAmountInput"
          />
        </div>
      </div>

      <!-- 转账箭头 -->
      <div class="transfer-arrow-container">
        <div class="transfer-arrow">
          <van-icon name="arrow-down" size="24" />
        </div>
      </div>

      <!-- 转入账户卡片 -->
      <div
        class="form-card to-account-card"
        @click="showFullScreenToAccountSelector"
      >
        <div class="card-icon">
          <van-icon name="gold-coin-o" />
        </div>
        <div class="card-content">
          <div class="card-label">{{ toAccountDisplayName || "转入账户" }}</div>
          <van-icon name="arrow" />
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

    <!-- TreeSelect转出账户选择器 -->
    <AccountTreeSelector
      ref="fromAccountSelectorRef"
      title="选择转出账户"
      :account-types="['Assets', 'Liabilities']"
      @confirm="onFullScreenFromAccountConfirm"
      @close="onFullScreenFromAccountClose"
    />

    <!-- TreeSelect转入账户选择器 -->
    <AccountTreeSelector
      ref="toAccountSelectorRef"
      title="选择转入账户"
      :account-types="['Assets', 'Liabilities']"
      @confirm="onFullScreenToAccountConfirm"
      @close="onFullScreenToAccountClose"
    />

    <!-- 币种选择器 -->
    <van-popup v-model:show="showCurrencySelector" position="bottom">
      <van-picker
        :columns="currencyOptions"
        @cancel="showCurrencySelector = false"
        @confirm="onCurrencyConfirm"
      />
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
import { showToast } from "vant";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import AccountTreeSelector from "./AccountTreeSelector.vue";

interface Props {
  formData: {
    amount: string;
    fromAccount: string;
    toAccount: string;
    date: Date;
    description: string;
    currency?: string;
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
});

// 弹窗状态
const showCurrencySelector = ref(false);
const showDateCalendar = ref(false);

// 全屏选择器引用
const fromAccountSelectorRef = ref();
const toAccountSelectorRef = ref();

interface Option {
  text: string;
  value: string;
  disabled?: boolean;
}

// 选项数据
const accountOptions = ref<Option[]>([]);
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
  console.log("转账表单构建精细层级选项，输入账户:", accounts);
  console.log("转账表单允许的类型:", allowedTypes);

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
    console.log(`转账表单处理账户: ${accountName}, parts:`, parts);

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
    console.log(`  转账表单remainingParts:`, remainingParts);

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
      console.log(`  转账表单创建子分组: ${subGroupName}`);

      if (!accountsByType[accountType][categoryName].subGroups[subGroupName]) {
        accountsByType[accountType][categoryName].subGroups[subGroupName] = [];
      }

      // 剩余的层级作为子账户名称
      const finalAccountName = remainingParts
        .slice(1)
        .map((part: string) => formatAccountName(part))
        .join("-");
      console.log(`  转账表单子账户名称: ${finalAccountName}`);

      accountsByType[accountType][categoryName].subGroups[subGroupName].push({
        name: finalAccountName,
        value: accountName,
        fullName: accountName,
      });
    }
  });

  console.log("转账表单按类型和分类分组的账户:", accountsByType);

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

  console.log("转账表单最终构建的精细层级选项:", options);
  return options;
};

// 计算属性
const fromAccountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.fromAccount);
});

const toAccountDisplayName = computed(() => {
  return formatAccountNameForDisplay(localFormData.value.toAccount);
});

const isFormValid = computed(() => {
  return (
    localFormData.value.amount &&
    localFormData.value.fromAccount &&
    localFormData.value.toAccount &&
    localFormData.value.fromAccount !== localFormData.value.toAccount
  );
});

// 监听数据变化
watch(
  localFormData,
  (newData) => {
    // 只在不是从props更新时才emit
    if (!isUpdatingFromProps) {
      emit("update", newData);
    }
  },
  { deep: true }
);

// 避免循环更新的标志
let isUpdatingFromProps = false;
watch(
  () => props.formData,
  (newData) => {
    // 避免循环更新：只在有实质性变化且不是来自内部更新时更新
    if (newData && !isUpdatingFromProps) {
      // 检查是否真的有变化
      const hasSignificantChange =
        newData.amount !== localFormData.value.amount ||
        newData.fromAccount !== localFormData.value.fromAccount ||
        newData.toAccount !== localFormData.value.toAccount ||
        newData.description !== localFormData.value.description;

      if (hasSignificantChange) {
        console.log("TransferForm收到新的formData:", newData);

        isUpdatingFromProps = true;
        localFormData.value = {
          ...newData,
          currency: newData.currency || "CNY",
        };
        // 下一个tick后重置标志
        nextTick(() => {
          isUpdatingFromProps = false;
        });
      }
    }
  },
  { deep: true }
);

// 监听转出账户变化，清空转入账户
watch(
  () => localFormData.value.fromAccount,
  (newValue, oldValue) => {
    if (newValue !== oldValue && localFormData.value.toAccount === newValue) {
      localFormData.value.toAccount = "";
    }
  }
);

// 币种符号获取函数
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

// 方法
const onAmountInput = (value: string | number) => {
  // 确保 value 是字符串类型
  const stringValue = String(value || "");

  // 格式化金额输入
  const numericValue = stringValue.replace(/[^\d.]/g, "");
  const parts = numericValue.split(".");
  if (parts.length > 2) {
    parts.splice(2);
  }
  if (parts[1] && parts[1].length > 2) {
    parts[1] = parts[1].substring(0, 2);
  }
  localFormData.value.amount = parts.join(".");
};

// 全屏账户选择器方法
const showFullScreenFromAccountSelector = () => {
  if (fromAccountSelectorRef.value) {
    fromAccountSelectorRef.value.show();
  }
};

const onFullScreenFromAccountConfirm = (accountName: string) => {
  localFormData.value.fromAccount = accountName;
};

const onFullScreenFromAccountClose = () => {
  // 关闭回调
};

const showFullScreenToAccountSelector = () => {
  if (toAccountSelectorRef.value) {
    toAccountSelectorRef.value.show();
  }
};

const onFullScreenToAccountConfirm = (accountName: string) => {
  localFormData.value.toAccount = accountName;
};

const onFullScreenToAccountClose = () => {
  // 关闭回调
};

const onSubmit = () => {
  if (!isFormValid.value) {
    showToast("请填写完整信息");
    return;
  }

  const amount = parseFloat(localFormData.value.amount);
  if (isNaN(amount) || amount <= 0) {
    showToast("请输入有效金额");
    return;
  }

  if (localFormData.value.fromAccount === localFormData.value.toAccount) {
    showToast("转出账户和转入账户不能相同");
    return;
  }

  emit("submit", {
    ...localFormData.value,
    amount,
  });
};

const loadAccountOptions = async () => {
  console.log("=== TransferForm loadAccountOptions 开始 ===");

  try {
    // 从API获取资产和负债账户列表
    console.log("正在加载转账账户列表...");
    const response = await getAccountsByType();
    console.log("转账表单API完整响应:", response);
    const accountData = response.data || response;
    console.log("转账表单账户数据:", accountData);
    console.log("转账表单账户数据类型:", typeof accountData);

    // 处理后端返回的按类型分组的数据格式
    let accounts: string[] = [];
    if (accountData && typeof accountData === "object") {
      console.log("转账表单Assets账户:", accountData.Assets);
      console.log("转账表单Liabilities账户:", accountData.Liabilities);

      // 提取 Assets 和 Liabilities 类型的账户
      const assetsAccounts: string[] = accountData.Assets || [];
      const liabilitiesAccounts: string[] = accountData.Liabilities || [];
      accounts = [...assetsAccounts, ...liabilitiesAccounts];

      console.log("转账表单合并后的账户列表:", accounts);
    } else {
      console.warn("转账表单账户数据格式不正确或为空:", accountData);
    }

    // 构建分层账户选项
    accountOptions.value = buildHierarchicalOptions(accounts, [
      "assets",
      "liabilities",
    ]);

    console.log("转账表单最终账户选项:", accountOptions.value);
    console.log("转账表单账户选项数量:", accountOptions.value.length);
  } catch (error) {
    console.error("转账表单获取账户列表失败:", error);
    console.error(
      "转账表单错误详情:",
      (error as any).response || (error as any).message || error
    );

    // 备用硬编码数据
    console.log("转账表单使用备用账户数据");
    const fallbackAccounts = [
      "Assets:ZJ-资金:现金",
      "Assets:ZJ-资金:活期存款",
      "Assets:ZJ-资金:香港招行",
      "Liabilities:XYK-信用卡:招行:8164",
      "Liabilities:XYK-信用卡:招行:经典白",
    ];
    accountOptions.value = buildHierarchicalOptions(fallbackAccounts, [
      "assets",
      "liabilities",
    ]);
  }

  console.log("=== TransferForm loadAccountOptions 结束 ===");
};

onMounted(() => {
  loadAccountOptions();
});
</script>

<style scoped>
.transfer-form {
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
  padding: 14px; /* 进一步减小内边距 */
  margin: 10px 16px; /* 进一步减尊上下间距 */
  margin-bottom: 6px; /* 进一步减小底部间距 */
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  min-height: 54px; /* 进一步减小最小高度 */
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
}

/* 转出账户卡片 */
.from-account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

/* 金额卡片 */
.amount-card {
  background: linear-gradient(135deg, #fff 0%, #f9f9f9 100%);
}

.amount-card .card-icon {
  background: rgba(52, 168, 83, 0.1);
  color: #34a853;
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

/* 转账箭头 */
.transfer-arrow-container {
  display: flex;
  justify-content: center;
  margin: -5px 16px; /* 进一步减小重叠效果 */
  position: relative;
  z-index: 1;
}

.transfer-arrow {
  width: 40px; /* 进一步减小箭头 */
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #34a853 0%, #4caf50 100%);
  border-radius: 50%;
  color: white;
  box-shadow: 0 3px 10px rgba(52, 168, 83, 0.25); /* 进一步减弱阴影 */
  transition: all 0.3s ease;
}

.transfer-arrow:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 20px rgba(52, 168, 83, 0.4);
}

/* 转入账户卡片 */
.to-account-card .card-icon {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
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

:deep(.van-field__control) {
  font-size: 16px; /* 增大输入框字体 */
}

/* 移动端响应式优化 */
@media (max-width: 375px) {
  .form-card {
    margin: 8px 12px; /* 进一步减小间距 */
    padding: 12px; /* 进一步减小内边距 */
    min-height: 50px; /* 进一步减小最小高度 */
  }

  .card-icon {
    width: 34px; /* 进一步减小图标 */
    height: 34px;
    margin-right: 10px;
    font-size: 14px;
  }

  .card-label {
    font-size: 14px; /* 进一步减小字体 */
  }

  .currency-symbol {
    font-size: 18px; /* 进一步减小字体 */
  }

  .amount-field :deep(.van-field__control) {
    font-size: 18px; /* 进一步减小字体 */
    min-height: 30px;
  }

  .transfer-arrow {
    width: 36px; /* 进一步减小箭头 */
    height: 36px;
  }

  :deep(.van-cell) {
    min-height: 40px; /* 进一步减小单元格高度 */
    padding: 6px 16px; /* 进一步减小内边距 */
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

  .transfer-arrow {
    width: 36px; /* 减小箭头 */
    height: 36px;
  }

  :deep(.van-cell) {
    min-height: 40px; /* 减小单元格高度 */
    padding: 6px 16px; /* 减小内边距 */
  }
}
</style>
