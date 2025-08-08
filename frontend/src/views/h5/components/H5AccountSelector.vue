<template>
  <van-popup
    v-model:show="visible"
    position="bottom"
    :style="{ height: '60%' }"
  >
    <div class="account-selector">
      <div class="selector-header">
        <h3>选择账户</h3>
        <van-icon name="cross" @click="close" />
      </div>

      <van-search
        v-model="searchKeyword"
        placeholder="搜索账户"
        @search="onSearch"
      />

      <div class="account-list">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多账户"
        >
          <van-cell
            v-for="account in filteredAccounts"
            :key="account.name"
            :title="formatAccountName(account.name)"
            :label="getAccountType(account.name)"
            is-link
            @click="selectAccount(account.name)"
          >
            <template #icon>
              <van-icon :name="getAccountIcon(account.name)" />
            </template>
          </van-cell>
        </van-list>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { getAllAccounts } from "@/api/accounts";
import { showToast } from "vant";
import { computed, onMounted, ref } from "vue";

interface Account {
  name: string;
  balance?: number;
}

interface Emits {
  (e: "confirm", account: string): void;
}

const emit = defineEmits<Emits>();

// 状态
const visible = ref(false);
const loading = ref(false);
const finished = ref(false);
const searchKeyword = ref("");
const accounts = ref<Account[]>([]);

// 计算属性
const filteredAccounts = computed(() => {
  if (!searchKeyword.value.trim()) {
    return accounts.value;
  }

  const keyword = searchKeyword.value.toLowerCase();
  return accounts.value.filter((account) =>
    account.name.toLowerCase().includes(keyword)
  );
});

// 方法
const formatAccountName = (accountName: string) => {
  if (!accountName) return "未知账户";
  // 去掉第一级账户名称
  const parts = accountName.split(":");
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(":");

    // 处理格式化
    const dashIndex = formattedName.indexOf("-");
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1);
    }

    return formattedName.replace(/:/g, "-");
  }
  return accountName;
};

const getAccountType = (accountName: string) => {
  if (!accountName) return "";
  const parts = accountName.split(":");
  const typeMap: Record<string, string> = {
    Assets: "资产",
    Liabilities: "负债",
    Income: "收入",
    Expenses: "支出",
    Equity: "权益",
  };
  return typeMap[parts[0]] || parts[0];
};

const getAccountIcon = (accountName: string) => {
  if (!accountName) return "manager-o";
  const parts = accountName.split(":");
  const iconMap: Record<string, string> = {
    Assets: "gold-coin-o",
    Liabilities: "credit-pay",
    Income: "arrow-up",
    Expenses: "arrow-down",
    Equity: "balance-o",
  };
  return iconMap[parts[0]] || "manager-o";
};

const selectAccount = (accountName: string) => {
  emit("confirm", accountName);
  close();
};

const close = () => {
  visible.value = false;
  searchKeyword.value = "";
};

const onSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

const loadAccounts = async () => {
  try {
    loading.value = true;
    const accountsData = await getAllAccounts();

    // 转换数据格式
    if (Array.isArray(accountsData)) {
      accounts.value = accountsData.map((item: any) => ({
        name: item.name || item.account,
        balance: item.balance,
      }));
    } else {
      accounts.value = [];
    }

    finished.value = true;
  } catch (error) {
    // console.error("加载账户列表失败:", error);
    showToast("加载账户列表失败");
  } finally {
    loading.value = false;
  }
};

// 公开方法
const show = () => {
  visible.value = true;
};

// 暴露给父组件
defineExpose({
  show,
});

// 生命周期
onMounted(() => {
  loadAccounts();
});
</script>

<style scoped>
.account-selector {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #ebedf0;
  flex-shrink: 0;
}

.selector-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.account-list {
  flex: 1;
  overflow-y: auto;
  /* 确保最后一个项目不被遮挡 */
  padding-bottom: max(60px, calc(20px + env(safe-area-inset-bottom)));
  /* 增强移动端滚动体验 */
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

:deep(.van-search) {
  padding: 8px 16px;
  border-bottom: 1px solid #ebedf0;
}

:deep(.van-cell) {
  padding: 8px 16px;
  min-height: 36px;
}

:deep(.van-cell__left-icon) {
  margin-right: 12px;
  color: #1989fa;
}

:deep(.van-cell__title) {
  font-size: 14px;
  font-weight: 500;
}

:deep(.van-cell__label) {
  font-size: 12px;
  color: #969799;
  margin-top: 4px;
}
</style>
