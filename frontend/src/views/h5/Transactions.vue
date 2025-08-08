<template>
  <div class="h5-transactions">
    <!-- 筛选栏 -->
    <div class="filter-fixed-container">
      <div class="filter-bar">
        <van-dropdown-menu>
          <van-dropdown-item v-model="filterType" :options="typeOptions" />
          <van-dropdown-item
            v-model="filterAccount"
            :options="accountOptions"
          />
          <van-dropdown-item
            :title="formatDateRangeDisplay(startDate, endDate)"
            ref="dateFilterDropdown"
          >
            <div class="date-filter-panel">
              <van-cell
                title="日期范围"
                :value="formatDateRangeDisplay(startDate, endDate)"
                is-link
                @click="showDateRangeCalendar = true"
              />
              <van-button
                v-if="startDate || endDate"
                type="default"
                size="small"
                @click="clearDateRange"
                style="margin-top: 12px; width: 100%"
              >
                清除日期筛选
              </van-button>
            </div>
          </van-dropdown-item>
        </van-dropdown-menu>
      </div>
    </div>

    <!-- 交易列表 -->
    <div class="transactions-content-wrapper">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          finished-text="没有更多了"
          @load="onLoad"
        >
          <div
            v-for="group in groupedTransactions"
            :key="group.date"
            class="transaction-group"
          >
            <!-- 日期分组头 - 可点击折叠 -->
            <div
              class="group-header"
              :class="{ collapsed: isGroupCollapsed(group.date) }"
              @click="toggleGroupCollapse(group.date)"
            >
              <div class="group-header-left">
                <van-icon :name="getCollapseIcon()" class="collapse-icon" />
                <span class="group-date">{{ group.date }}</span>
              </div>
              <span
                class="group-amount"
                :class="getGroupAmountClass(group.totalAmount)"
                >{{ formatAmount(group.totalAmount) }}</span
              >
            </div>

            <!-- 交易项 - 支持折叠 -->
            <van-cell-group v-show="!isGroupCollapsed(group.date)">
              <van-swipe-cell
                v-for="transaction in group.transactions"
                :key="transaction.id"
              >
                <van-cell
                  :title="formatAccountName(transaction.account)"
                  :label="transaction.payee || transaction.date"
                  :value="formatTransactionAmount(transaction)"
                  :value-class="getTransactionAmountClass(transaction)"
                  :class="{
                    'highlighted-transaction':
                      transaction.transaction_id === highlightTransactionId,
                  }"
                  is-link
                  @click="viewTransaction(transaction)"
                />

                <!-- 滑动操作 -->
                <template #right>
                  <van-button
                    square
                    type="primary"
                    text="编辑"
                    @click="editTransaction(transaction)"
                  />
                  <van-button
                    square
                    type="danger"
                    text="删除"
                    @click="deleteTransaction(transaction)"
                  />
                </template>
              </van-swipe-cell>
            </van-cell-group>
          </div>
        </van-list>
      </van-pull-refresh>
    </div>

    <!-- 悬浮按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="$router.push('/h5/add-transaction')"
    />

    <!-- 日期范围日历 -->
    <van-calendar
      v-model:show="showDateRangeCalendar"
      title="选择日期范围"
      type="range"
      :min-date="new Date(2025, 5, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      :allow-same-day="true"
      @confirm="onDateRangeConfirm"
      @close="showDateRangeCalendar = false"
    />
  </div>
</template>

<script setup lang="ts">
import {
  deleteTransaction as deleteTransactionApi,
  getAccounts,
} from "@/api/transactions";
import {
  createCancellableGet,
  createDebounce,
  RequestManager,
} from "@/utils/api";
import { showConfirmDialog, showToast } from "vant";
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const router = useRouter();
const route = useRoute();

// 请求管理器
const requestManager = new RequestManager();

// 高亮显示的交易ID（从URL参数获取）
const highlightTransactionId = ref((route.query.highlight as string) || "");

// 响应式数据
const refreshing = ref(false);
const loading = ref(false);
const finished = ref(false);
const fabOffset = ref({ x: -24, y: -100 });

// 折叠状态（记录折叠的日期）
const collapsedGroups = ref<Set<string>>(new Set());

// 分页状态
const currentPage = ref(1);
const totalPages = ref(1);

// 筛选条件
const filterType = ref("all");
const filterAccount = ref("all");
const sortBy = ref("date_desc");

// 日期筛选相关
const startDate = ref("");
const endDate = ref("");
const showDateRangeCalendar = ref(false);

// 选项数据
const typeOptions = [
  { text: "全部类型", value: "all" },
  { text: "收入", value: "income" },
  { text: "支出", value: "expense" },
  { text: "转账", value: "transfer" },
];

interface AccountOption {
  text: string;
  value: string;
  disabled?: boolean;
}

const accountOptions = ref<AccountOption[]>([
  { text: "全部账户", value: "all" },
]);

interface Transaction {
  id: string; // 改为string类型支持transaction_id
  transaction_id?: string; // 添加transaction_id字段
  filename?: string;
  lineno?: number;
  payee: string;
  account: string;
  date: string;
  amount: number;
  type: string;
}

// 使用 shallowRef 减少深层响应式追踪
const transactions = shallowRef<Transaction[]>([]);

// 使用 Map 进行增量分组，避免重复计算
const groupMap = shallowRef(
  new Map<
    string,
    { date: string; transactions: Transaction[]; totalAmount: number }
  >()
);

// 初始化标志
const isInitialized = ref(false);

// 计算属性 - 过滤后的交易（用于前端显示，服务端已过滤大部分）
const filteredTransactions = computed(() => {
  return transactions.value;
});

// 计算交易的显示金额（用于合计计算）- 只统计收入和支出，排除转账
const getTransactionDisplayAmount = (transaction: any) => {
  if (transaction.type === "income") {
    // 收入：计算为正数
    return Math.abs(transaction.amount);
  } else if (transaction.type === "expense") {
    // 支出：计算为负数
    return -Math.abs(transaction.amount);
  } else {
    // 转账：不纳入统计
    return 0;
  }
};

// 优化的分组计算 - 使用增量更新
const groupedTransactions = computed(() => {
  return Array.from(groupMap.value.values()).sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );
});

// 增量更新分组数据
const updateGroupMap = (newTransactions: Transaction[], isRefresh = false) => {
  if (isRefresh) {
    groupMap.value.clear();
  }

  newTransactions.forEach((transaction) => {
    const date = transaction.date;
    let group = groupMap.value.get(date);

    if (!group) {
      group = {
        date,
        transactions: [],
        totalAmount: 0,
      };
      groupMap.value.set(date, group);
    }

    group.transactions.push(transaction);
    group.totalAmount += getTransactionDisplayAmount(transaction);
  });

  // 对每个组内的交易按行号排序
  groupMap.value.forEach((group) => {
    group.transactions.sort((a, b) => {
      const linenoA = a.lineno || 0;
      const linenoB = b.lineno || 0;
      return linenoB - linenoA;
    });
  });

  // 触发响应式更新
  groupMap.value = new Map(groupMap.value);
};

// 创建防抖的加载函数
const debouncedLoadTransactions = createDebounce(
  async (isRefresh = false, pageToLoad?: number) => {
    await loadTransactionsInternal(isRefresh, pageToLoad);
  },
  300
);

// 格式化日期范围显示
const formatDateRangeDisplay = (startDateStr: string, endDateStr: string) => {
  if (!startDateStr && !endDateStr) return "按日期筛选";
  if (startDateStr && endDateStr) {
    const startDate = new Date(startDateStr);
    const endDate = new Date(endDateStr);
    const startFormatted = startDate.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
    });
    const endFormatted = endDate.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
    });
    return `${startFormatted} 至 ${endFormatted}`;
  }
  if (startDateStr) {
    const startDate = new Date(startDateStr);
    const startFormatted = startDate.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
    });
    return `从 ${startFormatted}`;
  }
  if (endDateStr) {
    const endDate = new Date(endDateStr);
    const endFormatted = endDate.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
    });
    return `到 ${endFormatted}`;
  }
  return "按日期筛选";
};

// 方法
const formatAmount = (amount: number) => {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(Math.abs(amount));
};

// 折叠相关方法
const toggleGroupCollapse = (date: string) => {
  if (collapsedGroups.value.has(date)) {
    collapsedGroups.value.delete(date);
  } else {
    collapsedGroups.value.add(date);
  }
};

const isGroupCollapsed = (date: string) => {
  return collapsedGroups.value.has(date);
};

const getCollapseIcon = () => {
  return "arrow-down";
};

// 获取日金额样式类
const getGroupAmountClass = (amount: number) => {
  return amount >= 0 ? "positive" : "negative";
};

// 格式化交易显示金额（转换为用户友好的显示方式）
const formatTransactionAmount = (transaction: any) => {
  let displayAmount = transaction.amount;

  if (transaction.type === "income") {
    // 收入：显示为正数
    displayAmount = Math.abs(transaction.amount);
  } else if (transaction.type === "expense") {
    // 支出：显示为正数
    displayAmount = Math.abs(transaction.amount);
  }

  return formatAmount(displayAmount);
};

// 获取交易显示金额的正负性（用于颜色显示）
const getTransactionAmountClass = (transaction: any) => {
  if (transaction.type === "income") {
    // 收入：显示绿色
    return "positive";
  } else if (transaction.type === "expense") {
    // 支出：显示红色
    return "negative";
  } else {
    // 转账：根据金额正负显示
    return transaction.amount > 0 ? "positive" : "negative";
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

// 通用的交易数据转换函数
const convertTransactionData = (trans: any, fallbackId: string) => {
  // 根据账户类型分组分录
  const incomePostings =
    trans.postings?.filter((p: any) => p.account.startsWith("Income:")) || [];
  const expensePostings =
    trans.postings?.filter((p: any) => p.account.startsWith("Expenses:")) || [];

  let mainAccountName = "";
  let mainAmount = 0;
  let transactionType = "transfer";

  if (expensePostings.length > 0) {
    // 支出类：汇总所有支出分录的账户名和金额
    const accountNames = expensePostings
      .map((p: any) => formatAccountName(p.account))
      .join(",");
    const totalAmount = expensePostings.reduce((sum: number, p: any) => {
      const amount =
        typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
      return sum + Math.abs(amount); // 取绝对值确保显示正数
    }, 0);

    mainAccountName = accountNames;
    mainAmount = totalAmount;
    transactionType = "expense";
  } else if (incomePostings.length > 0) {
    // 收入类：汇总所有收入分录的账户名和金额
    const accountNames = incomePostings
      .map((p: any) => formatAccountName(p.account))
      .join(",");
    const totalAmount = incomePostings.reduce((sum: number, p: any) => {
      const amount =
        typeof p.amount === "string" ? parseFloat(p.amount) : p.amount || 0;
      return sum + Math.abs(amount); // 取绝对值确保显示正数
    }, 0);

    mainAccountName = accountNames;
    mainAmount = totalAmount;
    transactionType = "income";
  } else {
    // 转账：使用第一个分录
    const firstPosting = trans.postings?.[0];
    if (firstPosting) {
      mainAccountName = firstPosting.account;
      const amount =
        typeof firstPosting.amount === "string"
          ? parseFloat(firstPosting.amount)
          : firstPosting.amount || 0;
      mainAmount = amount;
      transactionType = "transfer";
    }
  }

  return {
    id: trans.transaction_id || fallbackId, // 使用唯一ID
    transaction_id: trans.transaction_id, // 文件名+行号组成的唯一标识
    filename: trans.filename,
    lineno: trans.lineno,
    payee: trans.payee || trans.narration || "",
    account: mainAccountName,
    date: trans.date,
    amount: mainAmount,
    type: transactionType,
  };
};

// 已移除交易图标函数，不再需要

const viewTransaction = (transaction: any) => {
  const transactionId = transaction.transaction_id || transaction.id;
  router.push(`/h5/transactions/${transactionId}`);
};

const editTransaction = (transaction: any) => {
  const transactionId = transaction.transaction_id || transaction.id;
  router.push(`/h5/add-transaction?id=${transactionId}`);
};

const deleteTransaction = async (transaction: any) => {
  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这条交易记录吗？删除后无法恢复。",
    });

    // 调用API删除交易
    const transactionId = transaction.transaction_id || transaction.id;
    await deleteTransactionApi(transactionId);

    // 从分组中移除
    const group = groupMap.value.get(transaction.date);
    if (group) {
      const index = group.transactions.findIndex(
        (t) =>
          (t.transaction_id && t.transaction_id === transactionId) ||
          t.id === transaction.id
      );
      if (index > -1) {
        group.transactions.splice(index, 1);
        group.totalAmount -= getTransactionDisplayAmount(transaction);

        // 如果组为空，删除组
        if (group.transactions.length === 0) {
          groupMap.value.delete(transaction.date);
        }

        // 触发响应式更新
        groupMap.value = new Map(groupMap.value);
      }
    }

    // 从原始数组中移除
    const transactionIndex = transactions.value.findIndex(
      (t) =>
        (t.transaction_id && t.transaction_id === transactionId) ||
        t.id === transaction.id
    );
    if (transactionIndex > -1) {
      transactions.value.splice(transactionIndex, 1);
      transactions.value = [...transactions.value]; // 触发响应式更新
    }

    showToast("删除成功");
  } catch (error) {
    if (error !== "cancel") {
      if ((import.meta as any).env?.DEV) {
        console.error("删除交易失败:", error);
      }
      showToast("删除交易失败");
    }
  }
};

const onRefresh = async () => {
  if ((import.meta as any).env?.DEV) {
    console.log("🔄 onRefresh called: resetting state and loading page 1");
  }

  // 取消所有进行中的请求
  requestManager.cancelAll();

  // 重置到初始状态
  currentPage.value = 1;
  finished.value = false;
  loading.value = false;
  totalPages.value = 1;
  transactions.value = [];
  groupMap.value.clear();

  try {
    await loadTransactionsInternal(true);
  } catch (error) {
    if (!(error as any)?.cancelled) {
      console.error("刷新失败:", error);
    }
  } finally {
    refreshing.value = false;
  }
};

const onLoad = async () => {
  if ((import.meta as any).env.DEV) {
    console.log("🔄 onLoad called:", {
      finished: finished.value,
      loading: loading.value,
      currentPage: currentPage.value,
      totalPages: totalPages.value,
      transactionsCount: transactions.value.length,
    });
  }

  if (finished.value) {
    if ((import.meta as any).env.DEV) {
      console.log("⛔ onLoad early return: finished");
    }
    return;
  }

  if (currentPage.value >= totalPages.value && totalPages.value > 0) {
    if ((import.meta as any).env.DEV) {
      console.log("⛔ onLoad: no more pages to load");
    }
    finished.value = true;
    return;
  }

  loading.value = true;

  try {
    const nextPage = currentPage.value + 1;
    await loadTransactionsInternal(false, nextPage);
  } catch (error) {
    if (!(error as any)?.cancelled) {
      console.error("onLoad failed:", error);
    }
    loading.value = false;
  }
};

const loadTransactionsInternal = async (
  isRefresh = false,
  pageToLoad?: number
) => {
  if ((import.meta as any).env.DEV) {
    console.log("📥 loadTransactionsInternal called:", {
      isRefresh,
      pageToLoad,
      currentLoading: loading.value,
      currentPage: currentPage.value,
      finished: finished.value,
    });
  }

  // 如果不是刷新，且还没有设置 loading 状态，则设置它
  if (!isRefresh && !loading.value) {
    loading.value = true;
  }

  // 如果是刷新，总是设置 loading 状态
  if (isRefresh) {
    loading.value = true;
  }

  try {
    // 确定要加载的页码
    const targetPage = pageToLoad || currentPage.value;

    // 如果是刷新，重置状态
    if (isRefresh) {
      finished.value = false;
    }

    // 构建筛选参数
    const params: any = {
      page: targetPage,
      page_size: 20,
    };

    console.log("🚀 About to call API with params:", params);
    console.log("🔍 Current filter state:", {
      filterType: filterType.value,
      filterAccount: filterAccount.value,
      sortBy: sortBy.value,
      startDate: startDate.value,
      endDate: endDate.value,
      isRefresh,
      targetPage,
    });

    // 类型筛选
    if (filterType.value !== "all") {
      params.transaction_type = filterType.value;
    }

    // 账户筛选
    if (filterAccount.value !== "all") {
      params.account = filterAccount.value;
    }

    // 日期范围筛选
    if (startDate.value) {
      params.start_date = startDate.value;
    }
    if (endDate.value) {
      params.end_date = endDate.value;
    }

    // 如果没有设置日期范围，默认获取最近3个月的数据
    if (!startDate.value && !endDate.value) {
      const today = new Date();
      const threeMonthsAgo = new Date();
      threeMonthsAgo.setMonth(today.getMonth() - 3);
      params.start_date = threeMonthsAgo.toLocaleDateString("en-CA");
      params.end_date = today.toLocaleDateString("en-CA");
    }

    // 创建可取消的请求
    const requestKey = `load-transactions-${targetPage}`;
    const request = createCancellableGet<any>("/transactions/", { params });
    requestManager.add(requestKey, request);

    const response = await request.promise;

    if ((import.meta as any).env.DEV) {
      console.log("📡 API response received:", {
        requested_page: targetPage,
        current_page: currentPage.value,
        total_pages: response.total_pages,
        total: response.total,
        data_length: response.data?.length,
      });
    }

    // 更新分页信息
    totalPages.value = response.total_pages;

    // 只有API调用成功后才更新当前页码
    if (pageToLoad) {
      currentPage.value = pageToLoad;
    }

    // 转换API数据格式
    const convertedTransactions = (response.data || []).map(
      (trans: any, index: number) =>
        convertTransactionData(
          trans,
          `transaction-${currentPage.value}-${index + 1}`
        )
    );

    if (isRefresh) {
      transactions.value = convertedTransactions;
      updateGroupMap(convertedTransactions, true);
    } else {
      transactions.value.push(...convertedTransactions);
      transactions.value = [...transactions.value]; // 触发响应式更新
      updateGroupMap(convertedTransactions, false);
    }

    // 判断是否还有更多数据
    const hasMoreData = currentPage.value < response.total_pages;

    // 设置finished状态
    if (
      response.total_pages === 0 ||
      (currentPage.value === 1 && convertedTransactions.length === 0)
    ) {
      finished.value = true;
      if ((import.meta as any).env.DEV) {
        console.log("📄 No data available, marking as finished");
      }
    } else {
      finished.value = !hasMoreData;
    }

    if ((import.meta as any).env.DEV) {
      console.log("📊 Pagination check:", {
        currentPage: currentPage.value,
        totalPages: response.total_pages,
        convertedTransactions: convertedTransactions.length,
        hasMoreData,
        finished: finished.value,
        totalTransactions: transactions.value.length,
        isRefresh,
      });
    }
  } catch (error) {
    if (!(error as any)?.cancelled) {
      console.error("加载交易数据失败:", error);
      showToast("加载交易数据失败");
      if (!isRefresh && pageToLoad && pageToLoad > currentPage.value) {
        finished.value = true;
      }
    }
  } finally {
    loading.value = false;
  }
};

// 立即加载函数（不防抖）
const loadTransactions = (isRefresh = false, pageToLoad?: number) => {
  return loadTransactionsInternal(isRefresh, pageToLoad);
};

// 格式化单个账户名称段（去掉字母前缀和连字符）
const formatAccountNameSegment = (accountName: string) => {
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
  return formatAccountNameSegment(categoryName);
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

// 获取账户类型的显示名称
const getAccountTypeLabel = (type: string) => {
  const typeLabels: Record<string, string> = {
    assets: "💰 资产",
    liabilities: "📝 负债",
    income: "💵 收入",
    expenses: "💸 支出",
    equity: "⚖️ 权益",
    other: "📁 其他",
  };
  return typeLabels[type] || "📁 其他";
};

// 加载账户选项
const loadAccountOptions = async () => {
  try {
    const response = await getAccounts();
    const accounts = response.data || response || [];

    // 按类型和分类分组账户，支持精细层级结构
    const accountsByType: Record<string, any> = {
      assets: {},
      liabilities: {},
      income: {},
      expenses: {},
      equity: {},
      other: {},
    };

    // 按分类分组账户，支持层级结构
    accounts.forEach((account: any) => {
      const accountName =
        typeof account === "string"
          ? account
          : account.name || account.full_path;
      const accountType = getAccountType(accountName);

      const parts = accountName.split(":");
      console.log(`处理筛选账户: ${accountName}, parts:`, parts);

      if (parts.length < 2) {
        // 如果层级不够，归类到其他
        if (!accountsByType["other"]["其他"]) {
          accountsByType["other"]["其他"] = {
            accounts: [],
            subGroups: {},
          };
        }
        accountsByType["other"]["其他"].accounts.push({
          name: formatAccountNameSegment(accountName),
          value: accountName,
          fullName: accountName,
        });
        return;
      }

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
      console.log(`  筛选remainingParts:`, remainingParts);

      if (remainingParts.length === 0) {
        // 如果没有更多层级，直接添加到accounts中
        accountsByType[accountType][categoryName].accounts.push({
          name: formatAccountNameSegment(parts[parts.length - 1]),
          value: accountName,
          fullName: accountName,
        });
      } else if (remainingParts.length === 1) {
        // 只有一级子账户，直接添加
        accountsByType[accountType][categoryName].accounts.push({
          name: formatAccountNameSegment(remainingParts[0]),
          value: accountName,
          fullName: accountName,
        });
      } else {
        // 有多级子账户，按第一级分组
        const subGroupName = remainingParts[0];
        console.log(`  筛选创建子分组: ${subGroupName}`);

        if (
          !accountsByType[accountType][categoryName].subGroups[subGroupName]
        ) {
          accountsByType[accountType][categoryName].subGroups[subGroupName] =
            [];
        }

        // 剩余的层级作为子账户名称
        const finalAccountName = remainingParts
          .slice(1)
          .map((part: string) => formatAccountNameSegment(part))
          .join("-");
        console.log(`  筛选子账户名称: ${finalAccountName}`);

        accountsByType[accountType][categoryName].subGroups[subGroupName].push({
          name: finalAccountName,
          value: accountName,
          fullName: accountName,
        });
      }
    });

    console.log("筛选按类型和分类分组的账户:", accountsByType);

    // 构建分层选项
    const options: AccountOption[] = [{ text: "全部账户", value: "all" }];

    // 按类型添加账户（保留类型标识）
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
      if (Object.keys(typeCategories).length > 0) {
        // 添加类型标题（保留）
        options.push({
          text: getAccountTypeLabel(type),
          value: `__type_${type}__`,
          disabled: true,
        });

        // 遍历该类型下的所有分类
        Object.keys(typeCategories).forEach((categoryName) => {
          const category = typeCategories[categoryName];

          // 检查是否只有一个直接账户且无子分组（避免重复显示）
          const hasSubGroups = Object.keys(category.subGroups).length > 0;
          const directAccountsCount = category.accounts.length;

          if (!hasSubGroups && directAccountsCount === 1) {
            // 只有一个直接账户且无子分组，直接显示账户（一级缩进）
            const account = category.accounts[0];
            options.push({
              text: `　${account.name}`,
              value: account.value,
            });
          } else {
            // 有多个账户或有子分组，显示分类标题
            options.push({
              text: `　${formatCategoryName(categoryName)}`,
              value: `__category_${type}_${categoryName}__`,
              disabled: true,
            });

            // 添加直接账户（二级缩进）
            category.accounts.forEach((account: any) => {
              options.push({
                text: `　　${account.name}`,
                value: account.value,
              });
            });

            // 添加子分组
            Object.keys(category.subGroups).forEach((subGroupName) => {
              const subGroupAccounts = category.subGroups[subGroupName];

              // 添加子分组标题（二级缩进）
              options.push({
                text: `　　${formatAccountNameSegment(subGroupName)}`,
                value: `__subgroup_${type}_${categoryName}_${subGroupName}__`,
                disabled: true,
              });

              // 添加子分组下的账户（三级缩进）
              subGroupAccounts.forEach((account: any) => {
                options.push({
                  text: `　　　${account.name}`,
                  value: account.value,
                });
              });
            });
          }
        });
      }
    });

    accountOptions.value = options;
    console.log(
      "账户筛选选项加载成功:",
      accounts.length,
      "个账户，按",
      typeOrder.filter((type) => Object.keys(accountsByType[type]).length > 0)
        .length,
      "种类型分组"
    );
  } catch (error) {
    console.error("加载账户筛选选项失败:", error);
  }
};

// 日期范围确认处理函数
const onDateRangeConfirm = (dates: Date[]) => {
  if (dates && dates.length === 2) {
    startDate.value = dates[0].toLocaleDateString("en-CA");
    endDate.value = dates[1].toLocaleDateString("en-CA");
    showDateRangeCalendar.value = false;
  }
};

// 清除日期范围
const clearDateRange = () => {
  startDate.value = "";
  endDate.value = "";

  // 关闭下拉菜单
  const dropdown = document.querySelector(".van-dropdown-item__content") as any;
  if (dropdown) {
    dropdown.style.display = "none";
  }
};

// 监听筛选条件变化，使用防抖
watch(
  [filterType, filterAccount, startDate, endDate],
  () => {
    if (!isInitialized.value) return;

    if ((import.meta as any).env.DEV) {
      console.log("🔄 Filter changed, triggering debounced load");
    }

    // 取消当前请求
    requestManager.cancelAll();

    // 重置状态
    currentPage.value = 1;
    finished.value = false;
    loading.value = false;

    // 防抖加载
    debouncedLoadTransactions(true);
  },
  { deep: true }
);

onMounted(async () => {
  if ((import.meta as any).env.DEV) {
    console.log("🚀 H5Transactions component mounted");
  }

  loadAccountOptions();
  await loadTransactions(true);
  isInitialized.value = true;

  if ((import.meta as any).env.DEV) {
    console.log("✅ Component initialization completed:", {
      finished: finished.value,
      loading: loading.value,
      currentPage: currentPage.value,
      totalPages: totalPages.value,
      transactionsLength: transactions.value.length,
    });
  }
});

// 组件卸载时清理
onUnmounted(() => {
  requestManager.cancelAll();
  debouncedLoadTransactions.cancel();
});
</script>

<style scoped>
.h5-transactions {
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

/* 固定筛选栏容器 */
.filter-fixed-container {
  position: fixed;
  top: 46px; /* 导航栏的高度 */
  left: 0;
  right: 0;
  z-index: 999;
  background-color: var(--van-background-2);
  border-bottom: 1px solid var(--van-border-color);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.filter-bar {
  background-color: transparent;
}

/* 交易内容包装器 */
.transactions-content-wrapper {
  margin-top: 50px; /* 为固定筛选栏留出空间 */
}

/* 日期筛选面板 */
.date-filter-panel {
  padding: 16px;
  background-color: var(--van-background-2);
  transition: background-color 0.3s ease;
}

/* 账户分组样式 */
:deep(.van-dropdown-item__option) {
  padding: 10px 16px;
}

/* 账户类型标题样式 */
:deep(.van-dropdown-item__option[disabled]) {
  background-color: #f7f8fa !important;
  color: #646566 !important;
  font-weight: 500;
  font-size: 13px;
  padding: 8px 16px;
  cursor: default;
}

/* 账户选项缩进样式 */
:deep(.van-dropdown-item__option:not([disabled])) {
  border-left: 2px solid transparent;
}

:deep(.van-dropdown-item__option:hover:not([disabled])) {
  border-left-color: #1989fa;
}

.transaction-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background-color: var(--van-background);
  font-size: 14px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.group-header:hover {
  background-color: var(--van-active-color);
}

.group-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-icon {
  font-size: 12px;
  color: #969799;
  transition: transform 0.2s;
}

.group-header .collapse-icon {
  transform: rotate(0deg);
}

.group-header.collapsed .collapse-icon {
  transform: rotate(-90deg);
}

.group-date {
  color: #646566;
}

.group-amount {
  font-weight: 500;
}

.group-amount.positive {
  color: #07c160;
}

.group-amount.negative {
  color: #ee0a24;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

/* 高亮显示的交易 */
.highlighted-transaction {
  background-color: var(--van-yellow-light) !important;
  border-left: 4px solid var(--van-yellow) !important;
}
</style>
