<template>
  <van-popup
    v-model:show="visible"
    position="right"
    :style="{ width: '100%', height: '100%' }"
    :teleport="'body'"
    :overlay="false"
    class="fullscreen-popup"
  >
    <van-nav-bar
      :title="title"
      left-text="取消"
      left-arrow
      @click-left="close"
    />

    <!-- 搜索框 -->
    <div class="search-section">
      <van-search
        v-model="searchKeyword"
        placeholder="搜索账户..."
        @search="onSearch"
        @input="onSearchInput"
      />
    </div>

    <!-- TreeSelect 组件 -->
    <van-tree-select
      v-model:active-id="selectedAccountId"
      v-model:main-active-index="activeMainIndex"
      :items="treeSelectItems"
      :height="treeSelectHeight"
      @click-item="onSelectAccount"
    />
  </van-popup>
</template>

<script setup lang="ts">
import { getAccountsByType } from "@/api/accounts";
import { getFrequentAccounts } from "@/api/transactions";
import { computed, onMounted, ref } from "vue";

interface Account {
  name: string;
  balance?: number;
}

interface TreeSelectItem {
  text: string;
  children?: TreeSelectChild[];
  disabled?: boolean;
}

interface TreeSelectChild {
  text: string;
  id: string;
  disabled?: boolean;
}

interface Props {
  title?: string;
  accountTypes?: string[];
}

interface Emits {
  (e: "confirm", value: string): void;
  (e: "close"): void;
}

const props = withDefaults(defineProps<Props>(), {
  title: "选择账户",
  accountTypes: () => ["Assets", "Liabilities", "Income", "Expenses"],
});

const emit = defineEmits<Emits>();

// 状态
const visible = ref(false);
const loading = ref(false);
const accounts = ref<Account[]>([]);
const selectedAccountId = ref("");
const activeMainIndex = ref(0);
const searchKeyword = ref("");
const frequentAccountNames = ref<string[]>([]);

// TreeSelect 高度计算
const treeSelectHeight = computed(() => {
  return 400; // 固定高度
});

// 获取账户类型
const getAccountType = (accountName: string) => {
  if (accountName.startsWith("Assets:")) return "Assets";
  if (accountName.startsWith("Liabilities:")) return "Liabilities";
  if (accountName.startsWith("Income:")) return "Income";
  if (accountName.startsWith("Expenses:")) return "Expenses";
  if (accountName.startsWith("Equity:")) return "Equity";
  return "Other";
};

// 格式化账户名称
const formatAccountName = (name: string) => {
  // 移除前缀字母和连字符，如 "A-支付宝" -> "支付宝"
  const match = name.match(/^[A-Z]+-(.+)$/);
  if (match) {
    return match[1];
  }
  return name;
};

// 构建TreeSelect数据结构
const treeSelectItems = computed(() => {
  if (!accounts.value || accounts.value.length === 0) {
    return [];
  }

  // 按账户类型过滤
  let filteredAccounts = accounts.value.filter((account) => {
    const accountType = getAccountType(account.name);
    return props.accountTypes.includes(accountType);
  });

  // 应用搜索过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    filteredAccounts = filteredAccounts.filter(
      (account) =>
        account.name.toLowerCase().includes(keyword) ||
        formatAccountName(account.name).toLowerCase().includes(keyword)
    );
  }

  const items: TreeSelectItem[] = [];

  // 1. 添加常用账户（仅在没有搜索关键字时显示）
  if (!searchKeyword.value.trim() && frequentAccountNames.value.length > 0) {
    // 过滤出当前可用类型且存在的常用账户
    const frequentAccounts = frequentAccountNames.value
      .map((name) => accounts.value.find((a) => a.name === name))
      .filter((a): a is Account => {
        if (!a) return false;
        const type = getAccountType(a.name);
        return props.accountTypes.includes(type);
      });

    if (frequentAccounts.length > 0) {
      const frequentChildren: TreeSelectChild[] = frequentAccounts.map(
        (account) => {
          const parts = account.name.split(":");
          const displayName =
            parts.length > 2
              ? formatAccountName(parts.slice(2).join(":"))
              : formatAccountName(parts[parts.length - 1]);

          return {
            text: `${displayName}${
              account.balance !== undefined
                ? ` (¥${account.balance.toFixed(2)})`
                : ""
            }`,
            id: account.name,
            disabled: false,
          };
        }
      );

      items.push({
        text: "常用账户",
        children: frequentChildren,
        disabled: false,
      });
    }
  }

  // 2. 按二级分类分组
  const categorized: Record<string, Account[]> = {};
  filteredAccounts.forEach((account) => {
    const parts = account.name.split(":");
    if (parts.length >= 2) {
      const category = parts[1];
      if (!categorized[category]) {
        categorized[category] = [];
      }
      categorized[category].push(account);
    }
  });

  // 转换为TreeSelect格式
  Object.entries(categorized).forEach(([category, categoryAccounts]) => {
    // 确保有账户数据才创建分类
    if (!categoryAccounts || categoryAccounts.length === 0) {
      return;
    }
    const children: TreeSelectChild[] = categoryAccounts.map((account) => {
      const parts = account.name.split(":");
      const displayName =
        parts.length > 2
          ? formatAccountName(parts.slice(2).join(":"))
          : formatAccountName(parts[parts.length - 1]);

      return {
        text: `${displayName}${
          account.balance !== undefined
            ? ` (¥${account.balance.toFixed(2)})`
            : ""
        }`,
        id: account.name,
        disabled: false,
      };
    });

    items.push({
      text: formatAccountName(category),
      children,
      disabled: false,
    });
  });

  return items;
});

// 搜索相关方法
const onSearch = () => {
  // 搜索在computed中自动处理
};

const onSearchInput = () => {
  // 输入时自动过滤
};

// 选择账户
const onSelectAccount = (item: TreeSelectChild) => {
  emit("confirm", item.id);
  close();
};

// 加载账户
const loadAccounts = async () => {
  try {
    loading.value = true;
    const response = await getAccountsByType();
    const accountData = response.data || response || {};

    // 处理后端返回的按类型分组的数据格式
    let accountsList: string[] = [];
    if (accountData && typeof accountData === "object") {
      // 根据需要的账户类型提取账户
      props.accountTypes.forEach((type) => {
        if (accountData[type] && Array.isArray(accountData[type])) {
          accountsList.push(...accountData[type]);
        }
      });
    }

    // 转换为Account格式
    accounts.value = accountsList.map((accountName) => ({
      name: accountName,
      balance: undefined, // 余额信息暂时不可用，可以后续从其他API获取
    }));
    
    // 同时加载常用账户
    await loadFrequentAccounts();
  } catch (error) {
    console.error("加载账户失败:", error);
    accounts.value = [];
  } finally {
    loading.value = false;
  }
};

// 加载常用账户
const loadFrequentAccounts = async () => {
  try {
    frequentAccountNames.value = await getFrequentAccounts(3);
  } catch (error) {
    console.error("加载常用账户失败:", error);
    frequentAccountNames.value = [];
  }
};

// 显示选择器
const show = () => {
  visible.value = true;
  // 每次显示时重置选中项，以便用户可以看到常用账户
  // 如果有选中的账户，可以尝试定位到该账户，但TreeSelect组件可能不支持自动展开
  // 所以这里保持默认状态，或者如果想让用户看到常用账户，可以将activeMainIndex设为0
  activeMainIndex.value = 0;
  
  if (accounts.value.length === 0) {
    loadAccounts();
  }
};

// 关闭选择器
const close = () => {
  visible.value = false;
  emit("close");
};

// 组件挂载时加载账户
onMounted(() => {
  // 组件挂载时不自动加载，在show()时加载
});

defineExpose({
  show,
  close,
});
</script>

<style scoped>
.fullscreen-popup {
  z-index: 2000;
}

.search-section {
  padding: 8px 16px;
  background: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
}
</style>
