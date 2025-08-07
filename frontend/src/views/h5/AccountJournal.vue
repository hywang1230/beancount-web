<template>
  <div class="account-journal">
    <div class="journal-content">
      <div v-if="loading" class="loading-container">
        <van-loading type="spinner" vertical>加载中...</van-loading>
      </div>

      <div v-else-if="transactions.length > 0">
        <!-- 交易列表 -->
        <van-list>
          <div
            v-for="transaction in transactions"
            :key="transaction.transaction_id"
            class="transaction-item"
          >
            <div class="transaction-header">
              <span class="date">{{ transaction.date }}</span>
              <span class="payee">{{ transaction.payee }}</span>
            </div>
            <div class="transaction-body">
              <div
                v-for="(posting, index) in transaction.postings"
                :key="index"
                class="posting-item"
              >
                <span class="account-name">{{ posting.account }}</span>
                <span class="amount" :class="getAmountClass(posting.amount)">{{
                  formatCurrency(posting.amount)
                }}</span>
              </div>
            </div>
          </div>
        </van-list>
      </div>

      <div v-else class="empty-container">
        <van-empty description="没有找到相关交易记录" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getTransactionsByAccount } from "@/api/transactions"; // This function needs to be created
import { showToast } from "vant";
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const accountName = ref(route.params.accountName as string);
const fromDate = ref(route.query.from as string);
const toDate = ref(route.query.to as string);
const transactions = ref<any[]>([]);
const loading = ref(false);

const fetchTransactions = async () => {
  loading.value = true;
  try {
    transactions.value = await getTransactionsByAccount(
      accountName.value,
      fromDate.value,
      toDate.value
    );
  } catch (error) {
    console.error("获取交易记录失败:", error);
    showToast("获取交易记录失败");
  } finally {
    loading.value = false;
  }
};

const formatCurrency = (amount: number) => {
  if (amount === null || amount === undefined) {
    return "";
  }
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(amount);
};

const getAmountClass = (amount: number) => {
  if (amount > 0) return "positive";
  if (amount < 0) return "negative";
  return "";
};

onMounted(() => {
  fetchTransactions();
});
</script>

<style scoped>
.account-journal {
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
}

.journal-content {
  padding: 16px;
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 100px); /* Adjust height as needed */
}

.transaction-item {
  background-color: var(--bg-color);
  border-radius: 8px;
  margin-bottom: 12px;
  padding: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 14px;
}

.date {
  color: var(--text-color-secondary);
}

.payee {
  font-weight: 500;
  color: var(--text-color);
}

.transaction-body {
  border-top: 1px solid var(--border-color-lighter);
  padding-top: 8px;
}

.posting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.account-name {
  color: var(--text-color-secondary);
}

.amount {
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-weight: 500;
}

.positive {
  color: var(--color-success);
}

.negative {
  color: var(--color-danger);
}
</style>
