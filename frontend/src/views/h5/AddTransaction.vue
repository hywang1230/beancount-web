<template>
  <div class="h5-add-transaction">
    <!-- 类型选择标签 -->
    <div class="type-tabs">
      <div class="tab-container">
        <div
          v-for="tab in tabList"
          :key="tab.name"
          class="tab-item"
          :class="{ active: activeTab === tab.name }"
          @click="setActiveTab(tab.name)"
        >
          {{ tab.title }}
        </div>
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
          @keyboard-visible="handleKeyboardVisible"
        />
      </div>
      <div v-else-if="activeTab === 'income'" class="tab-content">
        <TransactionForm
          :key="formKey"
          type="income"
          :form-data="formData"
          @update="updateFormData"
          @submit="onSubmit"
          @keyboard-visible="handleKeyboardVisible"
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
          @keyboard-visible="handleKeyboardVisible"
        />
      </div>
    </div>

    <!-- 操作按钮 -->
    <div
      class="action-buttons"
      :class="{ 'keyboard-visible': keyboardVisible }"
      v-show="!keyboardVisible"
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
} from "@/api/transactions";
import TransactionForm from "@/views/h5/components/TransactionForm.vue";
import TransferForm from "@/views/h5/components/TransferForm.vue";
import { closeToast, showLoadingToast, showToast } from "vant";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const activeTab = ref("expense");
const keyboardVisible = ref(false);
const formKey = ref(0); // 用于强制重新渲染表单组件

// 标签列表
const tabList = ref([
  { name: "expense", title: "支出" },
  { name: "income", title: "收入" },
  { name: "transfer", title: "转账" },
  { name: "adjustment", title: "调整余额" },
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
    return formData.value.amount && formData.value.account;
  }
});

// 设置活动标签
const setActiveTab = (tabName: string) => {
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

const handleKeyboardVisible = (visible: boolean) => {
  keyboardVisible.value = visible;
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
      message: "保存中...",
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
          amount:
            activeTab.value === "expense"
              ? Math.abs(categoryAmount)
              : -Math.abs(categoryAmount),
          currency: formData.value.currency || "CNY",
        });
      }
    }

    // 后添加主账户posting（资产或负债账户）
    const totalAmount = parseFloat(formData.value.amount);
    postings.push({
      account: formData.value.account,
      amount:
        activeTab.value === "expense"
          ? -Math.abs(totalAmount)
          : Math.abs(totalAmount),
      currency: formData.value.currency || "CNY",
    });

    // 验证分录平衡（复式记账规则：所有分录金额合计必须为0）
    const postingsSum = postings.reduce(
      (sum, posting) => sum + posting.amount,
      0
    );
    if (Math.abs(postingsSum) >= 0.01) {
      closeToast();
      showToast(`分录不平衡，差额：¥${postingsSum.toFixed(2)}`);
      console.error("分录不平衡:", postings, "合计:", postingsSum);
      return;
    }

    const transactionData = {
      date: formData.value.date.toLocaleDateString("en-CA"),
      flag: "*", // 默认标记
      payee: formData.value.payee,
      narration: formData.value.description || formData.value.payee,
      postings,
    };

    console.log("准备发送的交易数据:", transactionData);
    console.log("postings详情:", postings);

    // 检查是否为编辑模式
    const editId = route.query.id as string;
    if (editId) {
      // 编辑模式：直接更新原交易
      console.log("编辑模式：更新原交易");
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
    console.error("保存交易失败:", error);
  }
};

const onTransferSubmit = async () => {
  try {
    showLoadingToast({
      message: "保存中...",
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

    // 检查是否为编辑模式
    const editId = route.query.id as string;
    if (editId) {
      // 编辑模式：直接更新原转账交易
      console.log("编辑转账模式：更新原交易");
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
    console.error("保存转账失败:", error);
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

    console.log("开始加载交易数据，ID:", id);

    // 使用正确的API获取单个交易数据
    const response = await getTransactionById(id);
    const transaction = response.data || response;

    console.log("加载到的交易数据:", transaction);

    if (transaction) {
      // 分析交易类型和数据
      const postings = transaction.postings || [];
      console.log("分析postings:", postings);

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

      console.log("资产分录:", assetPostings);
      console.log("支出分录:", expensePostings);
      console.log("收入分录:", incomePostings);

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
          console.log("设置的转账类型:", "transfer");
          console.log("设置的转账表单数据:", transferFormData.value);
          return;
        }
      } else if (expensePostings.length > 0 && assetPostings.length > 0) {
        // 支出交易：有支出分录和资产分录
        const assetPosting = assetPostings[0]; // 通常只有一个资产账户
        const assetAmount =
          typeof assetPosting.amount === "string"
            ? parseFloat(assetPosting.amount)
            : assetPosting.amount || 0;

        // 计算总支出金额（应该等于资产减少的金额）
        const totalExpenseAmount = Math.abs(assetAmount);

        // 构建分类数组
        const categories = expensePostings.map((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          return {
            categoryName: "",
            categoryDisplayName: formatAccountNameForCategory(p.account),
            category: p.account,
            amount: Math.abs(amt).toString(),
          };
        });

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

        console.log("设置的支出交易类型:", "expense");
        console.log("设置的支出表单数据:", transactionData);
        return;
      } else if (incomePostings.length > 0 && assetPostings.length > 0) {
        // 收入交易：有收入分录和资产分录
        const assetPosting = assetPostings[0];
        const assetAmount =
          typeof assetPosting.amount === "string"
            ? parseFloat(assetPosting.amount)
            : assetPosting.amount || 0;

        // 计算总收入金额（应该等于资产增加的金额）
        const totalIncomeAmount = Math.abs(assetAmount);

        // 构建分类数组
        const categories = incomePostings.map((p: any) => {
          const amt =
            typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
          return {
            categoryName: "",
            categoryDisplayName: formatAccountNameForCategory(p.account),
            category: p.account,
            amount: Math.abs(amt).toString(),
          };
        });

        // 更新收入表单数据
        const transactionData = {
          amount: totalIncomeAmount.toString(),
          payee: transaction.payee || "",
          account: assetPosting.account,
          category: categories[0]?.category || "",
          date: new Date(transaction.date),
          description: transaction.narration || "",
          currency: assetPosting.currency || "CNY",
          flag: transaction.flag || "*",
          categories: categories,
        };

        formData.value = transactionData;
        activeTab.value = "income";

        console.log("设置的收入交易类型:", "income");
        console.log("设置的收入表单数据:", transactionData);
        return;
      }

      // 如果没有匹配到已知模式，使用默认处理
      console.warn("未识别的交易模式，使用默认处理");
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

      console.log("设置的默认交易数据:", defaultData);
    }
  } catch (error) {
    showToast("加载交易数据失败");
    console.error("加载交易数据失败:", error);
  }
};
</script>

<style scoped>
.h5-add-transaction {
  height: 100vh;
  background-color: #f7f8fa;
  display: flex;
  flex-direction: column;
}

/* 头部标题 */
.header-title {
  text-align: center;
  padding: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #323233;
  background: white;
  border-bottom: 1px solid #ebedf0;
}

/* 类型选择标签 */
.type-tabs {
  background: white;
  padding: 0;
  border-bottom: 1px solid #ebedf0;
  position: sticky;
  top: 0;
  z-index: 99;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tab-container {
  display: flex;
  background: white;
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 8px; /* 减小垂直内边距 */
  font-size: 15px; /* 减小字体 */
  color: #646566;
  cursor: pointer;
  position: relative;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
  min-height: 44px; /* 减小最小高度 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-item.active {
  color: #ee5a52;
  font-weight: 600;
  border-bottom-color: #ee5a52;
  background: rgba(238, 90, 82, 0.08);
}

.tab-item:hover {
  background: rgba(238, 90, 82, 0.05);
}

/* 表单内容 */
.form-content {
  flex: 1;
  overflow-y: auto;
}

.tab-content {
  height: 100%;
  background: #f7f8fa;
  padding-bottom: 140px; /* 为底部按钮和导航留出更多空间 */
  padding-top: 8px; /* 增加顶部间距 */
}

/* 操作按钮 */
.action-buttons {
  position: fixed;
  bottom: 60px; /* 为底部导航栏留出更多空间 */
  left: 0;
  right: 0;
  padding: 12px 16px; /* 增加内边距 */
  background-color: white;
  border-top: 1px solid #ebedf0;
  z-index: 998; /* 确保在内容之上，但在导航栏之下 */
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15); /* 增强阴影效果 */
  transition: bottom 0.3s ease; /* 添加过渡动画 */
}

/* 键盘弹出时调整操作按钮位置 */
.action-buttons.keyboard-visible {
  bottom: 0; /* 键盘弹出时贴底显示 */
}

.action-buttons :deep(.van-button--large) {
  height: 46px; /* 减小按钮高度 */
  font-size: 16px; /* 减小字体 */
  font-weight: 600;
  border-radius: 12px;
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

/* 暗色主题支持 */
@media (prefers-color-scheme: dark) {
  .h5-add-transaction {
    background-color: #1a1a1a;
  }

  .header-title {
    background: #2c2c2c;
    color: #cccccc;
    border-bottom-color: #3a3a3a;
  }

  .type-tabs {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }

  .tab-container {
    background: #2c2c2c;
  }

  .tab-item {
    color: #cccccc;
  }

  .tab-item.active {
    background: rgba(238, 90, 82, 0.15);
  }

  .tab-content {
    background: #1a1a1a;
  }

  .action-buttons {
    background-color: #2c2c2c;
    border-top-color: #3a3a3a;
  }
}
</style>
