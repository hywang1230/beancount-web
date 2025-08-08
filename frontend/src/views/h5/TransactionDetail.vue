<template>
  <div class="h5-transaction-detail">
    <div v-if="loading" class="loading-container">
      <van-loading size="24px" vertical>加载中...</van-loading>
    </div>

    <div v-else-if="transaction" class="transaction-content">
      <!-- 基本信息 -->
      <van-cell-group>
        <van-cell title="日期" :value="transaction.date" />
        <van-cell title="收付方" :value="transaction.payee || '-'" />
        <van-cell title="摘要" :value="transaction.narration || '-'" />
        <van-cell
          v-if="formatFlag(transaction.flag)"
          title="标志"
          :value="formatFlag(transaction.flag)"
        />
      </van-cell-group>

      <!-- 标签和链接 -->
      <van-cell-group
        v-if="transaction.tags?.length || transaction.links?.length"
        title="标签和链接"
      >
        <van-cell v-if="transaction.tags?.length" title="标签">
          <template #value>
            <van-tag
              v-for="tag in transaction.tags"
              :key="tag"
              type="primary"
              style="margin-right: 4px"
            >
              {{ tag }}
            </van-tag>
          </template>
        </van-cell>
        <van-cell v-if="transaction.links?.length" title="链接">
          <template #value>
            <van-tag
              v-for="link in transaction.links"
              :key="link"
              type="success"
              style="margin-right: 4px"
            >
              {{ link }}
            </van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 分录信息 -->
      <van-cell-group title="分录详情">
        <van-cell
          v-for="(posting, index) in transaction.postings"
          :key="index"
          :value="formatAmount(posting.amount, posting.currency)"
          :value-class="
            posting.amount && parseFloat(posting.amount) > 0
              ? 'positive'
              : 'negative'
          "
        >
          <template #title>
            <div class="posting-title">
              <div class="account-name">
                {{ formatAccountName(posting.account) }}
              </div>
              <van-tag
                :type="
                  getAccountType(posting.account) === '资产'
                    ? 'primary'
                    : getAccountType(posting.account) === '负债'
                    ? 'warning'
                    : getAccountType(posting.account) === '收入'
                    ? 'success'
                    : getAccountType(posting.account) === '支出'
                    ? 'danger'
                    : 'default'
                "
                class="account-type-tag"
              >
                {{ getAccountType(posting.account) }}
              </van-tag>
            </div>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 文件信息已隐藏 -->
    </div>

    <div v-else class="error-container">
      <van-empty description="交易不存在或已被删除" />
    </div>

    <!-- 操作按钮 -->
    <div v-if="transaction" class="action-buttons">
      <!-- 编辑和删除按钮 -->
      <div class="edit-delete-buttons">
        <van-button type="primary" size="large" @click="editTransaction">
          编辑
        </van-button>
        <van-button type="danger" size="large" @click="deleteTransaction">
          删除
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getAccountsByType } from "@/api/accounts";
import {
  deleteTransaction as deleteTransactionApi,
  getTransactionById,
} from "@/api/transactions";
import { showConfirmDialog, showToast } from "vant";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

const loading = ref(true);
const transaction = ref<any>(null);
const accountTypes = ref<Record<string, string[]>>({});

const formatAmount = (
  amount: string | number | undefined,
  currency?: string
) => {
  if (amount === undefined || amount === null) return "0.00";

  const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  const formatted = new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: currency || "CNY",
  }).format(numAmount);

  return formatted;
};

const getAccountType = (accountName: string): string => {
  if (!accountName) return "未知";

  for (const [type, accounts] of Object.entries(accountTypes.value)) {
    if (accounts.includes(accountName)) {
      const typeMap: Record<string, string> = {
        Assets: "资产",
        Liabilities: "负债",
        Equity: "权益",
        Income: "收入",
        Expenses: "支出",
      };
      return typeMap[type] || type;
    }
  }

  // 如果没有在缓存中找到，根据前缀判断
  if (accountName.startsWith("Assets:")) return "资产";
  if (accountName.startsWith("Liabilities:")) return "负债";
  if (accountName.startsWith("Equity:")) return "权益";
  if (accountName.startsWith("Income:")) return "收入";
  if (accountName.startsWith("Expenses:")) return "支出";

  return "未知";
};

const formatFlag = (flag: string): string => {
  if (!flag) return "";

  // 根据beancount规则处理标志
  switch (flag) {
    case "*":
      return "已确认";
    case "!":
      return "待确认";
    case "txn":
      return "已确认";
    default:
      // 对于其他字符，如果是*或!则不显示，否则显示原值
      if (flag === "*" || flag === "!") {
        return "";
      }
      return flag;
  }
};

const formatAccountName = (accountName: string) => {
  if (!accountName) return "未知账户";
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

const loadAccountTypes = async () => {
  try {
    const response = await getAccountsByType();
    accountTypes.value = response.data || response;
  } catch (error) {
    // console.error("加载账户类型失败:", error);
    // 不显示错误提示，因为这不是核心功能
  }
};

const loadTransaction = async () => {
  try {
    const transactionId = route.params.id as string;
    // console.log("Loading transaction with ID:", transactionId);

    const response = await getTransactionById(transactionId);
    transaction.value = response.data || response;

    // console.log("Loaded transaction:", transaction.value);
  } catch (error) {
    // console.error("加载交易详情失败:", error);
    showToast("加载交易详情失败");
  } finally {
    loading.value = false;
  }
};

const editTransaction = () => {
  const transactionId = transaction.value?.transaction_id || route.params.id;
  router.push(`/h5/add-transaction?id=${transactionId}`);
};

const deleteTransaction = async () => {
  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这条交易记录吗？删除后无法恢复。",
    });

    const transactionId =
      transaction.value?.transaction_id || (route.params.id as string);
    await deleteTransactionApi(transactionId);

    showToast("删除成功");
    router.back();
  } catch (error) {
    if (error !== "cancel") {
      // console.error("删除交易失败:", error);
      showToast("删除交易失败");
    }
  }
};

onMounted(async () => {
  await Promise.all([loadAccountTypes(), loadTransaction()]);
});
</script>

<style scoped>
.h5-transaction-detail {
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.transaction-content {
  padding: 16px 0 140px 0; /* 增加底部padding，为固定按钮和底部导航留出空间 */
}

.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.action-buttons {
  position: fixed;
  bottom: 50px; /* 为底部导航栏留出空间 */
  left: 0;
  right: 0;
  padding: 16px;
  background-color: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
  z-index: 999; /* 确保在内容之上，但在导航栏之下 */
  transition: background-color 0.3s ease, border-color 0.3s ease,
    bottom 0.3s ease, transform 0.3s ease; /* 添加过渡动画 */
}

/* 检测到键盘弹出时隐藏固定按钮（通过CSS媒体查询） */
@media (max-height: 600px) {
  .action-buttons {
    transform: translateY(100%); /* 小屏且可能有键盘时隐藏 */
  }
}

.status-buttons {
  margin-bottom: 16px;
}

.edit-delete-buttons {
  display: flex;
  flex-direction: row;
  gap: 12px;
}

.edit-delete-buttons :deep(.van-button--large) {
  height: 46px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
}

/* 响应式设计 */
@media (max-width: 375px) {
  .edit-delete-buttons :deep(.van-button--large) {
    height: 44px;
    font-size: 15px;
  }
}

:deep(.van-cell-group) {
  margin-bottom: 16px;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-tag) {
  margin-right: 4px;
  margin-bottom: 4px;
}

.posting-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.account-name {
  flex: 1;
  margin-right: 8px;
}

.account-type-tag {
  flex-shrink: 0;
}
</style>
