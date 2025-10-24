<template>
  <div class="h5-add-transaction">
    <!-- 类型选择标签 -->
    <div class="tabs-fixed-container">
      <div class="transaction-type-selector">
        <van-tabs v-model:active="activeTab" @change="onTabChange" swipeable>
          <van-tab
            v-for="tab in tabList"
            :key="tab.name"
            :title="tab.title"
            :name="tab.name"
          />
        </van-tabs>
      </div>
    </div>

    <!-- 表单内容 -->
    <div class="form-content">
      <div v-if="activeTab === 'expense'" class="tab-content">
        <TransactionForm
          :key="formKey"
          type="expense"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'income'" class="tab-content">
        <TransactionForm
          :key="formKey"
          type="income"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'transfer'" class="tab-content">
        <TransferForm
          :key="formKey"
          :form-data="transferFormData"
          @update="updateTransferFormData"
          @submit="onTransferSubmit"
        />
      </div>
      <div v-else-if="activeTab === 'adjustment'" class="tab-content">
        <TransactionForm
          :key="formKey"
          type="adjustment"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
        />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div
      class="action-buttons"
      :class="{ 'pwa-mode': isPWA }"
      :style="{ bottom: buttonPosition }"
    >
      <van-button
        type="primary"
        size="large"
        :disabled="!canSave"
        @click="handleSave"
      >
        保存
      </van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  createTransaction,
  getTransactionById,
  updateTransaction,
  validateTransaction,
} from "@/api/transactions";
import { calculateBottomButtonPosition, isPWAMode } from "@/utils/pwa";
import TransactionForm from "@/views/h5/components/TransactionForm.vue";
import TransferForm from "@/views/h5/components/TransferForm.vue";
import { closeToast, showLoadingToast, showToast } from "vant";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const activeTab = ref("expense");

const formKey = ref(0); // 用于强制重新渲染表单组件

// 标签列表
const tabList = ref([
  { name: "expense", title: "支出" },
  { name: "income", title: "收入" },
  { name: "transfer", title: "转账" },
  // { name: "adjustment", title: "调整余额" },
]);

const formData = ref({
  amount: "",
  payee: "",
  account: "",
  category: "",
  date: new Date(),
  description: "",
  currency: "CNY",
  flag: "*", // 交易状态标记
  categories: [
    { categoryName: "", categoryDisplayName: "", category: "", amount: "" },
  ],
});

const transferFormData = ref({
  amount: "",
  fromAccount: "",
  toAccount: "",
  date: new Date(),
  description: "",
  currency: "CNY",
  flag: "*",
});

// 计算属性
const canSave = computed(() => {
  if (activeTab.value === "transfer") {
    return (
      transferFormData.value.amount &&
      transferFormData.value.fromAccount &&
      transferFormData.value.toAccount
    );
  } else {
    // 检查基本字段
    if (!formData.value.amount || !formData.value.account) {
      return false;
    }

    // 检查分类：至少有一个有效的分类
    const hasValidCategory =
      formData.value.categories &&
      formData.value.categories.length > 0 &&
      formData.value.categories.some(
        (cat) => cat.category && cat.categoryDisplayName
      );

    return hasValidCategory;
  }
});

// PWA模式检测
const isPWA = computed(() => isPWAMode());

// 动态计算按钮位置
const buttonPosition = computed(() => calculateBottomButtonPosition());

// 标签页切换处理
const onTabChange = (tabName: string) => {
  if (activeTab.value !== tabName) {
    activeTab.value = tabName;
    resetForm();
  }
};

// 处理保存
const handleSave = async () => {
  if (activeTab.value === "transfer") {
    await onTransferSubmit();
  } else {
    await onSubmit();
  }
};

const updateFormData = (data: any) => {
  formData.value = { ...formData.value, ...data };
};

const updateTransferFormData = (data: any) => {
  transferFormData.value = { ...transferFormData.value, ...data };
};

// 格式化账户名称用于分类显示
const formatAccountNameForCategory = (accountName: string) => {
  if (!accountName) return "未知分类";

  // 去掉第一级账户名称（通常是Assets、Liabilities、Income、Expenses等）
  const parts = accountName.split(":");
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(":");

    // 进一步处理：去掉第一个"-"以及前面的字母部分
    // 例如：JT-交通:过路费 -> 交通:过路费，然后替换":"为"-"变成：交通-过路费
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

const resetForm = () => {
  formData.value = {
    amount: "",
    payee: "",
    account: "",
    category: "",
    date: new Date(),
    description: "",
    currency: "CNY",
    flag: "*",
    categories: [
      { categoryName: "", categoryDisplayName: "", category: "", amount: "" },
    ],
  };

  transferFormData.value = {
    amount: "",
    fromAccount: "",
    toAccount: "",
    date: new Date(),
    description: "",
    currency: "CNY",
    flag: "*",
  };

  // 强制重新渲染表单组件
  formKey.value++;
};

const onSubmit = async () => {
  try {
    showLoadingToast({
      message: "校验中...",
      forbidClick: true,
    });

    // 构建交易数据
    const postings = [];

    // 先添加分类的postings（支出或收入账户）
    for (const category of formData.value.categories) {
      if (category.category && category.amount) {
        const categoryAmount = parseFloat(category.amount);
        postings.push({
          account: category.category,
          amount: categoryAmount,
          currency: formData.value.currency || "CNY",
        });
      }
    }

    // 后添加主账户posting（资产或负债账户）
    const totalAmount = parseFloat(formData.value.amount);
    postings.push({
      account: formData.value.account,
      amount: activeTab.value === "income" ? totalAmount : -totalAmount,
      currency: formData.value.currency || "CNY",
    });

    // 先校验分类分配与总金额关系
    const categoriesSum = formData.value.categories.reduce(
      (sum, cat) => sum + (parseFloat(cat.amount) || 0),
      0
    );
    const expectedCategoriesSum =
      activeTab.value === "income" ? -totalAmount : totalAmount;
    const categoriesDiff = categoriesSum - expectedCategoriesSum;
    if (Math.abs(categoriesDiff) >= 0.01) {
      closeToast();
      showToast(
        `分类分配与总额不匹配，应为¥${expectedCategoriesSum.toFixed(
          2
        )}，实际¥${categoriesSum.toFixed(2)}`
      );
      return;
    }

    // 再校验分录平衡（所有分录金额合计必须为0）
    const postingsSum = postings.reduce(
      (sum, posting) => sum + posting.amount,
      0
    );
    if (Math.abs(postingsSum) >= 0.01) {
      closeToast();
      showToast(`分录不平衡，差额：¥${Math.abs(postingsSum).toFixed(2)}`);
      return;
    }

    const transactionData = {
      date: formData.value.date.toLocaleDateString("en-CA"),
      flag: "*", // 默认标记
      payee: formData.value.payee,
      narration: formData.value.description || formData.value.payee,
      postings,
    };

    // console.log("准备发送的交易数据:", transactionData);
    // console.log("postings详情:", postings);

    // 先进行校验
    try {
      const validationResult = await validateTransaction(transactionData);
      const validation = validationResult.data || validationResult;

      if (!validation.valid) {
        closeToast();

        // 处理多个错误信息
        if (validation.errors && validation.errors.length > 0) {
          if (validation.errors.length === 1) {
            // 单个错误直接显示
            showToast(validation.errors[0]);
          } else {
            // 多个错误，显示主要错误和提示
            const mainError = validation.errors[0];
            const additionalCount = validation.errors.length - 1;
            showToast(
              `${mainError}${
                additionalCount > 0 ? ` (还有${additionalCount}个错误)` : ""
              }`
            );
          }
        } else {
          showToast("交易数据校验失败");
        }

        // console.error("交易校验失败:", validation.errors);
        return;
      }
    } catch (validationError) {
      closeToast();
      showToast("交易校验失败，请检查数据格式");
      // console.error("校验接口调用失败:", validationError);
      return;
    }

    // 校验通过，更新加载提示
    showLoadingToast({
      message: "保存中...",
      forbidClick: true,
    });

    // 检查是否为编辑模式
    const editId = route.query.id as string;
    if (editId) {
      // 编辑模式：直接更新原交易
      // console.log("编辑模式：更新原交易");
      await updateTransaction(editId, transactionData);
      showToast("更新成功");
    } else {
      // 新增模式：调用创建API
      await createTransaction(transactionData);
      showToast("保存成功");
    }

    closeToast();

    // 编辑模式返回上一页，新增模式重置表单继续记账
    if (editId) {
      router.back();
    } else {
      resetForm();
    }
  } catch (error) {
    closeToast();
    showToast(route.query.id ? "更新失败" : "保存失败");
    // console.error("保存交易失败:", error);
  }
};

const onTransferSubmit = async () => {
  try {
    showLoadingToast({
      message: "校验中...",
      forbidClick: true,
    });

    // 构建转账交易数据
    const transferData = {
      date: transferFormData.value.date.toLocaleDateString("en-CA"),
      flag: "*", // 默认标记
      payee: "转账",
      narration: transferFormData.value.description || "账户转账",
      postings: [
        {
          account: transferFormData.value.fromAccount,
          amount: -Math.abs(parseFloat(transferFormData.value.amount)),
          currency: transferFormData.value.currency || "CNY",
        },
        {
          account: transferFormData.value.toAccount,
          amount: Math.abs(parseFloat(transferFormData.value.amount)),
          currency: transferFormData.value.currency || "CNY",
        },
      ],
    };

    // 先进行校验
    try {
      const validationResult = await validateTransaction(transferData);
      const validation = validationResult.data || validationResult;

      if (!validation.valid) {
        closeToast();

        // 处理多个错误信息
        if (validation.errors && validation.errors.length > 0) {
          if (validation.errors.length === 1) {
            // 单个错误直接显示
            showToast(validation.errors[0]);
          } else {
            // 多个错误，显示主要错误和提示
            const mainError = validation.errors[0];
            const additionalCount = validation.errors.length - 1;
            showToast(
              `${mainError}${
                additionalCount > 0 ? ` (还有${additionalCount}个错误)` : ""
              }`
            );
          }
        } else {
          showToast("转账数据校验失败");
        }

        // console.error("转账校验失败:", validation.errors);
        return;
      }
    } catch (validationError) {
      closeToast();
      showToast("转账校验失败，请检查数据格式");
      // console.error("校验接口调用失败:", validationError);
      return;
    }

    // 校验通过，更新加载提示
    showLoadingToast({
      message: "保存中...",
      forbidClick: true,
    });

    // 检查是否为编辑模式
    const editId = route.query.id as string;
    if (editId) {
      // 编辑模式：直接更新原转账交易
      // console.log("编辑转账模式：更新原交易");
      await updateTransaction(editId, transferData);
      showToast("更新成功");
    } else {
      // 新增模式：调用创建API
      await createTransaction(transferData);
      showToast("转账成功");
    }

    closeToast();

    // 编辑模式返回上一页，新增模式重置表单继续记账
    if (editId) {
      router.back();
    } else {
      resetForm();
    }
  } catch (error) {
    closeToast();
    showToast(route.query.id ? "更新失败" : "转账失败");
    // console.error("保存转账失败:", error);
  }
};

onMounted(() => {
  // 检查路由参数
  const type = route.query.type as string;
  if (type && ["expense", "income", "transfer"].includes(type)) {
    activeTab.value = type;
  }

  // 如果是编辑模式，加载现有数据
  const id = route.query.id as string;
  if (id) {
    loadTransactionData();
  }
});

const loadTransactionData = async () => {
  try {
    const id = route.query.id as string;
    if (!id) return;

    // console.log("开始加载交易数据，ID:", id);

    // 使用正确的API获取单个交易数据
    const response = await getTransactionById(id);
    const transaction = response.data || response;

    // console.log("加载到的交易数据:", transaction);

    if (transaction) {
      // 分析交易类型和数据
      const postings = transaction.postings || [];
      // console.log("分析postings:", postings);

      // 分离不同类型的分录
      const assetPostings = postings.filter(
        (p: any) =>
          p.account?.startsWith("Assets:") ||
          p.account?.startsWith("Liabilities:")
      );
      const expensePostings = postings.filter((p: any) =>
        p.account?.startsWith("Expenses:")
      );
      const incomePostings = postings.filter((p: any) =>
        p.account?.startsWith("Income:")
      );

      // console.log("资产分录:", assetPostings);
      // console.log("支出分录:", expensePostings);
      // console.log("收入分录:", incomePostings);

      // 判断交易类型
      if (
        assetPostings.length === 2 &&
        expensePostings.length === 0 &&
        incomePostings.length === 0
      ) {
        // 转账：只有两个资产/负债账户
        const fromPosting = assetPostings.find((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          return amt < 0;
        });
        const toPosting = assetPostings.find((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          return amt > 0;
        });

        if (fromPosting && toPosting) {
          const transferAmount =
            typeof toPosting.amount === "string"
              ? parseFloat(toPosting.amount)
              : toPosting.amount || 0;

          // 更新转账表单数据
          transferFormData.value = {
            amount: Math.abs(transferAmount).toString(),
            fromAccount: fromPosting.account,
            toAccount: toPosting.account,
            date: new Date(transaction.date),
            description: transaction.narration || "",
            currency: toPosting.currency || "CNY",
            flag: transaction.flag || "*",
          };

          activeTab.value = "transfer";
          // console.log("设置的转账类型:", "transfer");
          // console.log("设置的转账表单数据:", transferFormData.value);
          return;
        }
      } else if (expensePostings.length > 0 && assetPostings.length > 0) {
        // 支出交易：有支出分录和资产分录
        const assetPosting = assetPostings[0]; // 通常只有一个资产账户

        // 构建分类数组（保留原始符号）
        const categories = expensePostings.map((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          return {
            categoryName: "",
            categoryDisplayName: formatAccountNameForCategory(p.account),
            category: p.account,
            amount: String(amt),
          };
        });

        // 计算总金额为分类金额之和（可为正负，保持一致性）
        const totalExpenseAmount = categories.reduce(
          (sum: number, c: any) => sum + (parseFloat(c.amount) || 0),
          0
        );

        // 更新支出表单数据
        const transactionData = {
          amount: totalExpenseAmount.toString(),
          payee: transaction.payee || "",
          account: assetPosting.account,
          category: categories[0]?.category || "", // 主分类
          date: new Date(transaction.date),
          description: transaction.narration || "",
          currency: assetPosting.currency || "CNY",
          flag: transaction.flag || "*",
          categories: categories,
        };

        formData.value = transactionData;
        activeTab.value = "expense";

        // console.log("设置的支出交易类型:", "expense");
        // console.log("设置的支出表单数据:", transactionData);
        return;
      } else if (incomePostings.length > 0 && assetPostings.length > 0) {
        // 收入交易：有收入分录和资产分录
        const assetPosting = assetPostings[0];

        // 构建分类数组（将负数取反为正数用于前端显示）
        const categories = incomePostings.map((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          // 收入账户通常是负数，取绝对值显示
          return {
            categoryName: "",
            categoryDisplayName: formatAccountNameForCategory(p.account),
            category: p.account,
            amount: String(Math.abs(amt)),
          };
        });

        // 计算总金额为分类金额之和（都是正数）
        const totalIncomeAmount = categories.reduce(
          (sum: number, c: any) => sum + (parseFloat(c.amount) || 0),
          0
        );


        // 获取原始货币信息，用于编辑显示
        const originalCurrency = assetPosting.original_currency;
        const displayCurrency = assetPosting.currency;
        
        // 当有原始货币信息且与显示货币不同时，使用原始金额和原始货币
        let displayAmount = totalIncomeAmount;
        let editCurrency = displayCurrency || "CNY";
        
        if (originalCurrency && originalCurrency !== displayCurrency && assetPosting.original_amount !== undefined && assetPosting.original_amount !== null) {
          // 使用原始金额和原始货币
          displayAmount = Math.abs(
            typeof assetPosting.original_amount === "string" 
              ? parseFloat(assetPosting.original_amount) 
              : assetPosting.original_amount
          );
          editCurrency = originalCurrency;
        }
        // 更新收入表单数据
        const transactionData = {
          amount: displayAmount.toString(),
          payee: transaction.payee || "",
          account: assetPosting.account,
          category: categories[0]?.category || "",
          date: new Date(transaction.date),
          description: transaction.narration || "",
          currency: editCurrency,
          flag: transaction.flag || "*",
          categories: categories,
        };

        formData.value = transactionData;
        activeTab.value = "income";

        // console.log("设置的收入交易类型:", "income");
        // console.log("设置的收入表单数据:", transactionData);
        return;
      }

      // 如果没有匹配到已知模式，使用默认处理
      // console.warn("未识别的交易模式，使用默认处理");
      const defaultData = {
        amount: "0",
        payee: transaction.payee || "",
        account: "",
        category: "",
        date: new Date(transaction.date),
        description: transaction.narration || "",
        currency: "CNY",
        flag: transaction.flag || "*",
        categories: [
          {
            categoryName: "",
            categoryDisplayName: "",
            category: "",
            amount: "",
          },
        ],
      };

      formData.value = defaultData;
      activeTab.value = "expense";

      // console.log("设置的默认交易数据:", defaultData);
    }
  } catch (error) {
    showToast("加载交易数据失败");
    // console.error("加载交易数据失败:", error);
  }
};
</script>

<style scoped>
.h5-add-transaction {
  height: 100vh;
  background-color: var(--van-background);
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s ease;
}

/* 头部标题 */
.header-title {
  text-align: center;
  padding: 16px;
  font-size: 18px;
  font-weight: 600;
  color: var(--van-text-color);
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  transition: background-color 0.3s ease, color 0.3s ease,
    border-color 0.3s ease;
}

/* 固定标签页容器 */
.tabs-fixed-container {
  position: sticky;
  top: 0;
  z-index: 999;
  background-color: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

/* 交易类型选择器 */
.transaction-type-selector {
  background-color: transparent;
}

.transaction-type-selector :deep(.van-tabs__nav) {
  background-color: var(--van-background-2);
}

.transaction-type-selector :deep(.van-tab) {
  color: var(--van-text-color-2);
}

.transaction-type-selector :deep(.van-tab--active) {
  color: #ee5a52;
}

.transaction-type-selector :deep(.van-tabs__line) {
  background-color: #ee5a52;
}

/* 表单内容 */
.form-content {
  flex: 1;
  overflow-y: auto;
  margin-top: 1px; /* 减少顶部间距 */
}

.tab-content {
  height: 100%;
  background: var(--van-background);
  padding-bottom: 140px; /* 为底部按钮和导航留出更多空间 */
  padding-top: 1px; /* 适中的顶部间距 */
  transition: background-color 0.3s ease;
}

/* 操作按钮 */
.action-buttons {
  position: fixed;
  bottom: calc(
    60px + env(safe-area-inset-bottom, 0px)
  ); /* 适配安全区域和底部导航栏 */
  left: 0;
  right: 0;
  padding: 12px 16px; /* 增加内边距 */
  background-color: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
  z-index: 998; /* 确保在内容之上，但在导航栏之下 */
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15); /* 增强阴影效果 */
  transition: background-color 0.3s ease, border-color 0.3s ease,
    bottom 0.3s ease; /* 添加过渡动画 */
}

.action-buttons :deep(.van-button--large) {
  height: 46px; /* 减小按钮高度 */
  font-size: 16px; /* 减小字体 */
  font-weight: 600;
  border-radius: 12px;
}

/* PWA模式优化 */
@media (display-mode: standalone) {
  .action-buttons {
    /* PWA模式下，进一步调整底部按钮位置 */
    bottom: calc(70px + env(safe-area-inset-bottom, 0px));
  }

  .tab-content {
    /* PWA模式下为底部按钮留出更多空间 */
    padding-bottom: 160px;
  }
}

/* iOS Safari PWA优化 */
@supports (-webkit-appearance: none) {
  @media (display-mode: standalone) {
    .action-buttons {
      /* iOS PWA模式下的特殊处理 */
      bottom: calc(65px + env(safe-area-inset-bottom, 5px));
      transition: all 0.3s ease-in-out;
    }
  }
}

/* 响应式设计 */
@media (max-width: 375px) {
  .tab-item {
    padding: 14px 8px; /* 增加小屏幕的内边距 */
    font-size: 15px; /* 保持较大的字体 */
    min-height: 48px;
  }

  .action-buttons {
    padding: 14px 16px; /* 增加小屏幕的内边距 */
  }

  .action-buttons :deep(.van-button--large) {
    height: 44px; /* 小屏幕按钮高度 */
    font-size: 15px; /* 减小字体 */
  }
}

/* iPhone X 及以上设备优化 */
@media (max-width: 414px) and (min-height: 812px) {
  .action-buttons {
    bottom: calc(70px + env(safe-area-inset-bottom, 10px));
  }

  .tab-content {
    padding-bottom: 170px;
  }
}
</style>
