<template>
  <div class="h5-accounts">
    <!-- 账户统计 -->
    <div class="stats-section">
      <!-- 第一行：资产、负债、权益、收入 -->
      <van-row gutter="12">
        <van-col
          v-for="item in firstRowAccountGroups"
          :key="item.type"
          span="6"
        >
          <div class="stat-item">
            <div class="stat-value">{{ item.group.accounts.length }}</div>
            <div class="stat-label">{{ getTypeLabel(item.type) }}</div>
          </div>
        </van-col>
      </van-row>

      <!-- 第二行：支出 -->
      <van-row gutter="12" v-if="secondRowAccountGroups.length > 0">
        <van-col
          v-for="item in secondRowAccountGroups"
          :key="item.type"
          span="6"
        >
          <div class="stat-item">
            <div class="stat-value">{{ item.group.accounts.length }}</div>
            <div class="stat-label">{{ getTypeLabel(item.type) }}</div>
          </div>
        </van-col>
      </van-row>
    </div>

    <!-- 搜索和操作栏 -->
    <div class="action-bar">
      <van-search
        v-model="searchText"
        placeholder="搜索账户"
        :background="'var(--van-background)'"
        @update:model-value="onSearch"
      />
      <van-button
        type="primary"
        size="small"
        round
        @click="showCreateDialog = true"
      >
        新增
      </van-button>
      <van-button
        :type="sortMode ? 'warning' : 'default'"
        size="small"
        round
        @click="toggleSortMode"
      >
        {{ sortMode ? "完成排序" : "排序" }}
      </van-button>
    </div>

    <!-- 普通模式：账户列表 -->
    <van-pull-refresh
      v-model="refreshing"
      @refresh="onRefresh"
      v-if="!sortMode"
    >
      <van-tabs v-model:active="activeType" sticky offset-top="0">
        <van-tab
          v-for="item in orderedAccountGroups"
          :key="item.type"
          :title="getTypeLabel(item.type)"
          :name="item.type"
        >
          <div class="accounts-list">
            <!-- 普通账户 -->
            <template v-if="item.type !== 'archived'">
              <div
                v-for="account in getAccountsForDisplay(item.group.accounts)"
                :key="account.fullPath || account.name"
                class="account-item"
              >
                <van-cell
                  :title="account.displayName"
                  :class="{
                    'account-level-0': account.level === 0,
                    'account-level-1': account.level === 1,
                    'account-level-2': account.level === 2,
                    'account-level-3': account.level && account.level >= 3,
                    'has-children': account.hasChildren,
                  }"
                  @click="
                    account.hasChildren
                      ? toggleAccountExpand(account)
                      : undefined
                  "
                >
                  <template #icon>
                    <div
                      class="account-icon"
                      :style="{ marginLeft: (account.level || 0) * 16 + 'px' }"
                    >
                      <van-icon
                        v-if="account.hasChildren"
                        :name="account.isExpanded ? 'arrow-down' : 'arrow'"
                        class="expand-icon"
                      />
                      <van-icon
                        :name="getAccountIcon(account.subtype || account.type)"
                      />
                    </div>
                  </template>
                  <template #right-icon>
                    <van-button
                      v-if="account.fullPath && !account.hasChildren"
                      size="mini"
                      type="warning"
                      plain
                      @click.stop="handleArchiveAccount(account.fullPath)"
                    >
                      归档
                    </van-button>
                  </template>
                </van-cell>
              </div>
            </template>

            <!-- 已归档账户 -->
            <template v-else>
              <van-empty
                v-if="filteredArchivedAccounts.length === 0"
                description="暂无已归档账户"
              />
              <div
                v-for="account in filteredArchivedAccounts"
                :key="account"
                class="account-item"
              >
                <van-cell :title="account" label="已归档账户">
                  <template #icon>
                    <div class="account-icon archived">
                      <van-icon name="manager-o" />
                    </div>
                  </template>
                  <template #right-icon>
                    <van-button
                      size="mini"
                      type="primary"
                      plain
                      @click="handleRestoreAccount(account)"
                    >
                      恢复
                    </van-button>
                  </template>
                </van-cell>
              </div>
            </template>
          </div>
        </van-tab>
      </van-tabs>
    </van-pull-refresh>

    <!-- 排序模式界面 -->
    <div v-if="sortMode" class="sort-mode">
      <div class="sort-section">
        <!-- 排序导航栏 -->
        <div class="sort-header">
          <h3>账户排序</h3>
          <div class="sort-breadcrumb">
            <div class="breadcrumb-item-container">
              <van-icon
                v-if="sortLevel === 'account'"
                name="arrow-left"
                class="back-icon"
                @click="backToSubcategorySort"
              />
              <span
                class="breadcrumb-item"
                :class="{
                  active: sortLevel === 'subcategory',
                  clickable: sortLevel === 'account',
                }"
                @click="backToSubcategorySort"
              >
                {{ getTypeLabel(sortActiveType) }}
              </span>
            </div>
            <van-icon
              v-if="sortLevel === 'account'"
              name="arrow"
              class="breadcrumb-arrow"
            />
            <span
              v-if="sortLevel === 'account'"
              class="breadcrumb-item active current"
            >
              {{ selectedSubcategory }}
            </span>
          </div>
        </div>

        <van-tabs v-model:active="sortActiveType">
          <van-tab
            v-for="category in fixedCategoryOrder"
            :key="category"
            :title="getTypeLabel(category)"
            :name="category"
          >
            <!-- 二级分类排序视图 -->
            <div
              v-if="sortLevel === 'subcategory'"
              class="subcategory-sort-container"
            >
              <p class="sort-desc">
                拖拽调整二级分类的显示顺序，点击分类名称可调整其下的三级账户
              </p>

              <div
                v-if="getSubcategoriesForSort(category).length > 0"
                class="sort-list"
              >
                <draggable
                  :model-value="getSubcategoriesForSort(category)"
                  @update:model-value="(newOrder: string[]) => onSubcategoryOrderChange(category, newOrder)"
                  item-key="id"
                >
                  <template #item="{ element, index }">
                    <van-cell
                      :title="element"
                      :value="`第 ${index + 1} 位`"
                      class="subcategory-item"
                      is-link
                      @click="enterAccountSort(category, element)"
                    >
                      <template #icon>
                        <div class="icon-container">
                          <van-icon name="bars" class="drag-handle" />
                        </div>
                      </template>
                      <template #right-icon>
                        <div class="right-content">
                          <div class="account-count">
                            {{
                              getAccountsForSubcategory(category, element)
                                .length
                            }}
                            个账户
                          </div>
                          <van-icon name="arrow" class="enter-icon" />
                        </div>
                      </template>
                    </van-cell>
                  </template>
                </draggable>
              </div>
              <van-empty v-else description="该分类下暂无子分类" size="small" />
            </div>

            <!-- 三级账户排序视图 -->
            <div
              v-else-if="sortLevel === 'account'"
              class="account-sort-container"
            >
              <p class="sort-desc">
                拖拽调整 {{ selectedSubcategory }} 下账户的显示顺序
              </p>

              <div
                v-if="
                  getAccountsForSubcategory(category, selectedSubcategory)
                    .length > 0
                "
                class="sort-list"
              >
                <draggable
                  :model-value="
                    getAccountsForSubcategory(category, selectedSubcategory)
                  "
                  @update:model-value="(newOrder: string[]) => onAccountOrderChangeInSubcategory(category, selectedSubcategory, newOrder)"
                  item-key="id"
                >
                  <template #item="{ element, index }">
                    <van-cell
                      :title="formatAccountNameForSort(element)"
                      :value="`第 ${index + 1} 位`"
                      class="account-item-sort"
                    >
                      <template #icon>
                        <div class="icon-container">
                          <van-icon name="bars" class="drag-handle" />
                        </div>
                      </template>
                    </van-cell>
                  </template>
                </draggable>
              </div>
              <van-empty v-else description="该子分类下暂无账户" size="small" />
            </div>
          </van-tab>
        </van-tabs>
      </div>
    </div>

    <!-- 创建账户弹出层 -->
    <van-popup
      v-model:show="showCreateDialog"
      position="bottom"
      :style="{ height: '100%' }"
      closeable
      close-icon-position="top-right"
    >
      <div class="create-form">
        <div class="form-title">新增账户</div>
        <van-form @submit="handleCreateAccount">
          <van-field
            v-model="createForm.accountType"
            name="accountType"
            label="账户类型"
            placeholder="请选择账户类型"
            readonly
            is-link
            @click="showTypePicker = true"
            :rules="[{ required: true, message: '请选择账户类型' }]"
          />

          <van-field
            v-model="createForm.accountName"
            name="accountName"
            label="账户名称"
            placeholder="请输入账户名称"
            :rules="[
              { required: true, message: '请输入账户名称' },
              {
                pattern: /^[A-Z0-9][\w\u4e00-\u9fa5-:]*$/,
                message: '账户名称必须以大写字母或数字开头',
              },
            ]"
          />

          <van-field
            v-model="createForm.date"
            name="date"
            label="开启日期"
            placeholder="请选择开启日期"
            readonly
            is-link
            @click="showDateCalendar = true"
            :rules="[{ required: true, message: '请选择开启日期' }]"
          />

          <van-field
            v-model="createForm.currencies"
            name="currencies"
            label="约束货币"
            placeholder="选择约束货币（可选）"
            readonly
            is-link
            @click="showCurrencyPicker = true"
          />

          <van-field
            v-model="createForm.bookingMethod"
            name="bookingMethod"
            label="记账方法"
            placeholder="选择记账方法（可选）"
            readonly
            is-link
            @click="showBookingPicker = true"
          />

          <div class="form-actions">
            <van-button
              round
              block
              type="primary"
              native-type="submit"
              :loading="createLoading"
            >
              创建账户
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 账户类型选择器 -->
    <van-popup v-model:show="showTypePicker" position="bottom">
      <van-picker
        :columns="accountTypes"
        @confirm="onTypeConfirm"
        @cancel="showTypePicker = false"
      />
    </van-popup>

    <!-- 日历选择器 -->
    <van-calendar
      v-model:show="showDateCalendar"
      title="选择开启日期"
      :default-date="createForm.date ? new Date(createForm.date) : new Date()"
      :min-date="new Date(2020, 0, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      @confirm="onDateConfirm"
      @cancel="showDateCalendar = false"
      :show-confirm="false"
      teleport="body"
    />

    <!-- 货币选择器 -->
    <van-popup v-model:show="showCurrencyPicker" position="bottom">
      <van-picker
        :columns="currencyOptions"
        @confirm="onCurrencyConfirm"
        @cancel="showCurrencyPicker = false"
      />
    </van-popup>

    <!-- 记账方法选择器 -->
    <van-popup v-model:show="showBookingPicker" position="bottom">
      <van-picker
        :columns="bookingMethods"
        @confirm="onBookingConfirm"
        @cancel="showBookingPicker = false"
      />
    </van-popup>

    <!-- 归档确认对话框 -->
    <van-dialog
      v-model:show="showArchiveDialog"
      title="归档账户"
      :message="`确定要归档账户 「${archiveAccountName}」 吗？\n归档后该账户将不再可用。`"
      :show-cancel-button="true"
      confirm-button-text="归档"
      confirm-button-color="var(--van-danger-color)"
      @confirm="confirmArchiveAccount"
      @cancel="showArchiveDialog = false"
    />

    <!-- 恢复确认对话框 -->
    <van-dialog
      v-model:show="showRestoreDialog"
      title="恢复账户"
      :message="`确定要恢复账户 「${restoreAccountName}」 吗？恢复后该账户将重新可用。`"
      :show-cancel-button="true"
      confirm-button-text="恢复"
      confirm-button-color="#07c160"
      @confirm="confirmRestoreAccount"
      @cancel="showRestoreDialog = false"
    />
  </div>
</template>

<script setup lang="ts">
import type {
  AccountCloseRequest,
  AccountCreateRequest,
  AccountOrderConfig,
  AccountRestoreRequest,
} from "@/api/accounts";
import {
  closeAccount,
  createAccount,
  getAccountOrderConfig,
  getAccountsByType,
  getArchivedAccounts,
  restoreAccount,
  updateAccountOrder,
  updateSubcategoryOrder,
} from "@/api/accounts";
import { showToast } from "vant";
import { computed, onMounted, ref } from "vue";
import draggable from "vuedraggable";

const refreshing = ref(false);
const searchText = ref("");
const activeType = ref("Assets");
const sortMode = ref(false);
const sortActiveType = ref("Assets");
const sortLevel = ref<"subcategory" | "account">("subcategory"); // 当前排序层级
const selectedSubcategory = ref<string>(""); // 选中的子分类
const sortConfig = ref<AccountOrderConfig>({
  category_order: [],
  subcategory_order: {},
  account_order: {},
});

// 固定的分类顺序，不可调整
const fixedCategoryOrder = [
  "Assets",
  "Liabilities",
  "Income",
  "Expenses",
  "Equity",
];

interface Account {
  id: number;
  name: string;
  type: string;
  subtype: string;
  description: string;
  fullPath?: string;
  displayName?: string;
  level?: number;
  hasChildren?: boolean;
  isExpanded?: boolean;
}

interface AccountGroup {
  type: string;
  accounts: Account[];
}

const accounts = ref<Account[]>([]);
const allAccountGroups = ref<Record<string, string[]>>({});
const archivedAccounts = ref<string[]>([]);
const expandedAccounts = ref<Set<string>>(new Set());

// 创建账户相关
const showCreateDialog = ref(false);
const createLoading = ref(false);
const createForm = ref({
  accountType: "",
  accountName: "",
  date: "",
  currencies: "",
  bookingMethod: "",
});

// 选择器状态
const showTypePicker = ref(false);
const showDateCalendar = ref(false);
const showCurrencyPicker = ref(false);
const showBookingPicker = ref(false);

// 归档相关
const showArchiveDialog = ref(false);
const archiveAccountName = ref("");

// 恢复相关
const showRestoreDialog = ref(false);
const restoreAccountName = ref("");

const accountGroups = computed(() => {
  const groups: Record<string, AccountGroup> = {};
  accounts.value.forEach((account) => {
    if (!groups[account.type]) {
      groups[account.type] = {
        type: account.type,
        accounts: [],
      };
    }
    groups[account.type].accounts.push(account);
  });

  // 合并从API获取的账户数据
  Object.keys(allAccountGroups.value).forEach((type) => {
    if (!groups[type]) {
      groups[type] = {
        type,
        accounts: [],
      };
    }

    // 将API账户转换为显示格式
    allAccountGroups.value[type].forEach((accountPath) => {
      const parts = accountPath.split(":");
      const name = parts[parts.length - 1];

      groups[type].accounts.push({
        id: Math.random(),
        name,
        type,
        subtype: "other",
        description: "",
        fullPath: accountPath,
      });
    });
  });

  return groups;
});

// 账户类型顺序定义
const accountTypeOrder = [
  "Assets",
  "Liabilities",
  "Income",
  "Expenses",
  "Equity",
  "archived",
];

// 第一行显示的账户类型
const firstRowTypes = ["Assets", "Liabilities", "Equity", "Income"];
// 第二行显示的账户类型
const secondRowTypes = ["Expenses"];

// 计算属性：第一行账户组
const firstRowAccountGroups = computed(() => {
  const groups = accountGroups.value;
  const result: Array<{ type: string; group: AccountGroup }> = [];

  firstRowTypes.forEach((type) => {
    if (groups[type]) {
      result.push({
        type,
        group: groups[type],
      });
    }
  });

  return result;
});

// 计算属性：第二行账户组
const secondRowAccountGroups = computed(() => {
  const groups = accountGroups.value;
  const result: Array<{ type: string; group: AccountGroup }> = [];

  secondRowTypes.forEach((type) => {
    if (groups[type]) {
      result.push({
        type,
        group: groups[type],
      });
    }
  });

  return result;
});

// 计算属性：排序后的账户分组
const orderedAccountGroups = computed(() => {
  const groups = searchText.value
    ? filteredAccountGroups.value
    : accountGroups.value;
  const ordered: Array<{ type: string; group: AccountGroup }> = [];

  // 按指定顺序添加账户组
  accountTypeOrder.forEach((type) => {
    if (type === "archived") {
      // 特殊处理已归档账户，只有存在归档账户时才添加该标签页
      if (archivedAccounts.value.length > 0) {
        ordered.push({
          type: "archived",
          group: {
            type: "archived",
            accounts: [],
          },
        });
      }
    } else if (groups[type]) {
      ordered.push({
        type,
        group: groups[type],
      });
    }
  });

  // 添加其他未列出的类型
  Object.keys(groups).forEach((type) => {
    if (!accountTypeOrder.includes(type)) {
      ordered.push({
        type,
        group: groups[type],
      });
    }
  });

  return ordered;
});

// 计算属性：过滤后的账户分组
const filteredAccountGroups = computed(() => {
  if (!searchText.value) {
    return accountGroups.value;
  }

  const filtered: Record<string, AccountGroup> = {};

  Object.keys(accountGroups.value).forEach((type) => {
    const filteredAccounts = accountGroups.value[type].accounts.filter(
      (account) =>
        account.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
        (account.fullPath &&
          account.fullPath
            .toLowerCase()
            .includes(searchText.value.toLowerCase()))
    );
    if (filteredAccounts.length > 0) {
      filtered[type] = {
        type,
        accounts: filteredAccounts,
      };
    }
  });

  return filtered;
});

// 过滤后的归档账户
const filteredArchivedAccounts = computed(() => {
  if (!searchText.value) {
    return archivedAccounts.value;
  }

  return archivedAccounts.value.filter((account) =>
    account.toLowerCase().includes(searchText.value.toLowerCase())
  );
});

// 选择器数据
const accountTypes = [
  { text: "资产账户", value: "Assets" },
  { text: "负债账户", value: "Liabilities" },
  { text: "权益账户", value: "Equity" },
  { text: "收入账户", value: "Income" },
  { text: "支出账户", value: "Expenses" },
];

const currencyOptions = [
  { text: "CNY", value: "CNY" },
  { text: "USD", value: "USD" },
  { text: "EUR", value: "EUR" },
  { text: "JPY", value: "JPY" },
];

const bookingMethods = [
  { text: "STRICT", value: "STRICT" },
  { text: "FIFO", value: "FIFO" },
  { text: "LIFO", value: "LIFO" },
];

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    Assets: "资产",
    Liabilities: "负债",
    Equity: "权益",
    Income: "收入",
    Expenses: "支出",
    archived: "已归档",
  };
  return typeMap[type] || type;
};

const getAccountIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    bank: "credit-pay",
    cash: "balance-list-o",
    alipay: "balance-pay",
    wechat: "chat-o",
    investment: "gold-coin-o",
    Assets: "gold-coin-o",
    Liabilities: "credit-pay",
    Equity: "balance-list-o",
    Income: "like-o",
    Expenses: "shopping-cart-o",
  };
  return iconMap[type] || "manager-o";
};

const getAccountsForDisplay = (accounts: Account[]) => {
  // 构建层级结构
  const accountMap = new Map<string, Account>();
  const children = new Map<string, Account[]>();
  const roots: Account[] = [];

  // 首先处理所有账户，建立映射关系
  accounts.forEach((account) => {
    if (account.fullPath) {
      const parts = account.fullPath.split(":");
      let currentPath = "";

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];
        const parentPath = currentPath;
        currentPath = currentPath ? `${currentPath}:${part}` : part;

        if (!accountMap.has(currentPath)) {
          // 跳过第一级（如Assets, Liabilities等），level从0开始但显示时减1
          const displayLevel = Math.max(0, i - 1);
          const displayName = part;
          const newAccount: Account = {
            ...account,
            name: part,
            displayName,
            fullPath: currentPath,
            level: displayLevel,
            hasChildren: false,
            isExpanded: expandedAccounts.value.has(currentPath),
          };
          accountMap.set(currentPath, newAccount);

          if (parentPath) {
            if (!children.has(parentPath)) {
              children.set(parentPath, []);
            }
            children.get(parentPath)!.push(newAccount);
            // 标记父节点有子节点
            const parent = accountMap.get(parentPath);
            if (parent) {
              parent.hasChildren = true;
            }
          } else {
            roots.push(newAccount);
          }
        }
      }
    } else {
      // 没有fullPath的账户直接显示
      const displayAccount = {
        ...account,
        displayName: account.name,
        level: 0,
      };
      roots.push(displayAccount);
    }
  });

  // 递归构建显示列表，跳过第一级
  const buildDisplayList = (
    accountsList: Account[],
    skipFirstLevel = true
  ): Account[] => {
    const result: Account[] = [];

    // 保持API返回的顺序，不再强制按字母排序
    // accountsList.sort((a, b) => a.name.localeCompare(b.name));

    accountsList.forEach((account) => {
      // 跳过第一级（如Assets, Liabilities等）
      if (
        skipFirstLevel &&
        account.level === 0 &&
        account.fullPath?.split(":").length === 1
      ) {
        // 直接显示子账户
        const childAccounts = children.get(account.fullPath || "");
        if (childAccounts) {
          result.push(...buildDisplayList(childAccounts, false));
        }
      } else {
        result.push(account);

        if (account.hasChildren && account.isExpanded) {
          const childAccounts = children.get(account.fullPath || "");
          if (childAccounts) {
            result.push(...buildDisplayList(childAccounts, false));
          }
        }
      }
    });

    return result;
  };

  return buildDisplayList(roots);
};

const onSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

const toggleAccountExpand = (account: Account) => {
  if (!account.fullPath) return;

  if (expandedAccounts.value.has(account.fullPath)) {
    expandedAccounts.value.delete(account.fullPath);
  } else {
    expandedAccounts.value.add(account.fullPath);
  }

  // 强制重新渲染
  account.isExpanded = expandedAccounts.value.has(account.fullPath);
};

// 选择器确认事件
const onTypeConfirm = ({ selectedOptions }: any) => {
  createForm.value.accountType = selectedOptions[0]?.value || "";
  showTypePicker.value = false;
};

const onDateConfirm = (date: Date) => {
  createForm.value.date = date.toLocaleDateString("en-CA");
  showDateCalendar.value = false;
};

const onCurrencyConfirm = ({ selectedOptions }: any) => {
  createForm.value.currencies = selectedOptions[0]?.value || "";
  showCurrencyPicker.value = false;
};

const onBookingConfirm = ({ selectedOptions }: any) => {
  createForm.value.bookingMethod = selectedOptions[0]?.value || "";
  showBookingPicker.value = false;
};

// 创建账户
const handleCreateAccount = async () => {
  try {
    createLoading.value = true;

    const fullAccountName = `${createForm.value.accountType}:${createForm.value.accountName}`;

    const requestData: AccountCreateRequest = {
      name: fullAccountName,
      open_date: createForm.value.date,
      currencies: createForm.value.currencies
        ? [createForm.value.currencies]
        : undefined,
      booking_method: createForm.value.bookingMethod || undefined,
    };

    const response = await createAccount(requestData);

    if (response.success) {
      showToast("账户创建成功");
      showCreateDialog.value = false;
      resetCreateForm();
      await loadAccounts();
    } else {
      showToast(response.message || "账户创建失败");
    }
  } catch (error: any) {
    // console.error("创建账户失败:", error);
    showToast(error.response?.data?.detail || "创建账户失败");
  } finally {
    createLoading.value = false;
  }
};

const resetCreateForm = () => {
  createForm.value = {
    accountType: "",
    accountName: "",
    date: "",
    currencies: "",
    bookingMethod: "",
  };
};

// 归档账户
const handleArchiveAccount = (accountName: string) => {
  archiveAccountName.value = accountName;
  showArchiveDialog.value = true;
};

const confirmArchiveAccount = async () => {
  try {
    // 使用当前日期作为归档日期
    const today = new Date();
    const archiveDate = today.toLocaleDateString("en-CA");

    const requestData: AccountCloseRequest = {
      name: archiveAccountName.value,
      close_date: archiveDate,
    };

    const response = await closeAccount(requestData);

    if (response.success) {
      showToast("账户归档成功");
      showArchiveDialog.value = false;
      await loadAccounts();
      return true;
    } else {
      showToast(response.message || "账户归档失败");
      return false;
    }
  } catch (error: any) {
    // console.error("归档账户失败:", error);
    showToast(error.response?.data?.detail || "归档账户失败");
    return false;
  }
};

// 恢复账户
const handleRestoreAccount = (accountName: string) => {
  restoreAccountName.value = accountName;
  showRestoreDialog.value = true;
};

const confirmRestoreAccount = async () => {
  try {
    const requestData: AccountRestoreRequest = {
      name: restoreAccountName.value,
    };

    const response = await restoreAccount(requestData);

    if (response.success) {
      showToast("账户恢复成功");
      showRestoreDialog.value = false;
      await loadAccounts();
    } else {
      showToast(response.message || "账户恢复失败");
    }
  } catch (error: any) {
    // console.error("恢复账户失败:", error);
    showToast(error.response?.data?.detail || "恢复账户失败");
  }
};

const loadAccounts = async () => {
  try {
    // 同时加载账户列表和归档账户
    const [accountsResponse, archivedResponse] = await Promise.all([
      getAccountsByType().catch(() => ({ data: {} })),
      getArchivedAccounts().catch(() => ({ data: [] })),
    ]);

    // 处理账户列表数据
    const accountData = accountsResponse?.data || accountsResponse || {};
    allAccountGroups.value =
      typeof accountData === "object" && accountData !== null
        ? accountData
        : {};

    // 处理归档账户数据
    const archivedData = archivedResponse?.data || archivedResponse || [];
    archivedAccounts.value = Array.isArray(archivedData) ? archivedData : [];

    // 设置默认激活的类型为Assets
    const availableTypes = orderedAccountGroups.value.map((item) => item.type);
    if (availableTypes.length > 0) {
      // 强制设置为Assets，如果Assets不存在则选择第一个可用类型（但不是archived）
      if (availableTypes.includes("Assets")) {
        activeType.value = "Assets";
      } else {
        // 选择第一个非archived的类型
        const nonArchivedType = availableTypes.find(
          (type) => type !== "archived"
        );
        activeType.value = nonArchivedType || availableTypes[0];
      }
    }
  } catch (error: any) {
    // console.error("加载账户失败:", error);
    if (error?.response?.status === 404) {
      showToast("账户数据文件未找到");
    } else if (error?.response?.status >= 500) {
      showToast("服务器错误，请稍后重试");
    } else {
      showToast("加载账户数据失败");
    }
  }
};

const onRefresh = async () => {
  await loadAccounts();
  refreshing.value = false;
  showToast("刷新成功");
};

// 排序相关方法
const toggleSortMode = () => {
  sortMode.value = !sortMode.value;
  if (sortMode.value) {
    loadSortConfig();
    // 重置到子分类排序层级
    sortLevel.value = "subcategory";
    selectedSubcategory.value = "";
  }
};

// 进入账户排序界面
const enterAccountSort = (category: string, subcategory: string) => {
  sortLevel.value = "account";
  selectedSubcategory.value = subcategory;
  sortActiveType.value = category;
};

// 返回子分类排序界面
const backToSubcategorySort = () => {
  sortLevel.value = "subcategory";
  selectedSubcategory.value = "";
};

const loadSortConfig = async () => {
  try {
    sortConfig.value = await getAccountOrderConfig();
  } catch (error) {
    console.error("加载排序配置失败:", error);
    // 使用默认配置
    sortConfig.value = {
      category_order: ["Assets", "Liabilities", "Income", "Expenses", "Equity"],
      subcategory_order: {
        Assets: [],
        Liabilities: [],
        Income: [],
        Expenses: [],
        Equity: [],
      },
      account_order: {
        Assets: {},
        Liabilities: {},
        Income: {},
        Expenses: {},
        Equity: {},
      },
    };
    showToast("使用默认排序配置");
  }
};

const saveSubcategoryOrder = async (category: string, newOrder: string[]) => {
  try {
    await updateSubcategoryOrder(category, newOrder);
    sortConfig.value.subcategory_order[category] = [...newOrder];
    showToast("子分类排序保存成功");
    // 重新加载账户数据以应用新的排序
    await loadAccounts();
  } catch (error) {
    console.error("保存子分类排序失败:", error);
    showToast("保存子分类排序失败");
  }
};

const saveAccountOrder = async (
  category: string,
  subcategory: string,
  newOrder: string[]
) => {
  try {
    await updateAccountOrder(category, subcategory, newOrder);
    if (!sortConfig.value.account_order[category]) {
      sortConfig.value.account_order[category] = {};
    }
    sortConfig.value.account_order[category][subcategory] = [...newOrder];
    showToast("账户排序保存成功");
    // 重新加载账户数据以应用新的排序
    await loadAccounts();
  } catch (error) {
    console.error("保存账户排序失败:", error);
    showToast("保存账户排序失败");
  }
};

// 子分类排序变化事件
const onSubcategoryOrderChange = (category: string, newOrder: string[]) => {
  saveSubcategoryOrder(category, newOrder);
};

// 账户排序变化事件
const onAccountOrderChangeInSubcategory = (
  category: string,
  subcategory: string,
  newOrder: string[]
) => {
  saveAccountOrder(category, subcategory, newOrder);
};

// 获取用于排序的子分类列表
const getSubcategoriesForSort = (category: string): string[] => {
  const categoryAccounts = Object.keys(allAccountGroups.value).includes(
    category
  )
    ? allAccountGroups.value[category] || []
    : [];

  // 提取所有子分类
  const subcategories = new Set<string>();
  categoryAccounts.forEach((account) => {
    const parts = account.split(":");
    if (parts.length >= 2) {
      subcategories.add(parts[1]);
    }
  });

  const subcategoryList = Array.from(subcategories);

  // 应用排序配置（如果有的话）
  const currentOrder = sortConfig.value.subcategory_order?.[category] || [];

  if (currentOrder.length > 0) {
    // 按配置的顺序排列
    const ordered: string[] = [];
    currentOrder.forEach((sub) => {
      if (subcategoryList.includes(sub)) {
        ordered.push(sub);
      }
    });
    // 添加未配置的子分类（按字母顺序）
    subcategoryList.forEach((sub) => {
      if (!ordered.includes(sub)) {
        ordered.push(sub);
      }
    });
    return ordered;
  } else {
    // 没有配置时，按字母顺序排列
    return subcategoryList.sort();
  }
};

// 获取指定子分类下的账户列表
const getAccountsForSubcategory = (
  category: string,
  subcategory: string
): string[] => {
  const categoryAccounts = Object.keys(allAccountGroups.value).includes(
    category
  )
    ? allAccountGroups.value[category] || []
    : [];

  const subcategoryAccounts = categoryAccounts.filter((account) =>
    account.startsWith(`${category}:${subcategory}:`)
  );

  // 应用排序配置（如果有的话）
  const currentOrder =
    sortConfig.value.account_order?.[category]?.[subcategory] || [];

  if (currentOrder.length > 0) {
    // 按配置的顺序排列
    const ordered: string[] = [];
    currentOrder.forEach((acc) => {
      if (subcategoryAccounts.includes(acc)) {
        ordered.push(acc);
      }
    });
    // 添加未配置的账户（按字母顺序）
    subcategoryAccounts.forEach((acc) => {
      if (!ordered.includes(acc)) {
        ordered.push(acc);
      }
    });
    return ordered;
  } else {
    // 没有配置时，按字母顺序排列
    return subcategoryAccounts.sort();
  }
};

// 格式化账户名称用于排序显示
const formatAccountNameForSort = (accountName: string): string => {
  if (!accountName) return "未知账户";
  const parts = accountName.split(":");
  // 返回三级名称（去掉一级分类和二级分类）
  return parts.length > 2 ? parts[2] : accountName;
};

onMounted(() => {
  loadAccounts();
});
</script>

<style scoped>
.h5-accounts {
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
  padding-bottom: 60px; /* 为底部导航留出空间 */
  transition: background-color 0.3s ease;
}

.stats-section {
  padding: 16px;
}

.stats-section :deep(.van-row) {
  margin-bottom: 12px; /* 为行添加底部间距 */
}

.stats-section :deep(.van-row:last-child) {
  margin-bottom: 0; /* 最后一行不需要底部间距 */
}

.stat-item {
  background: var(--bg-color);
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  box-shadow: var(--shadow-light);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-color-secondary);
  font-weight: normal;
}

/* 操作栏样式 */
.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px 16px;
  background-color: var(--bg-color-secondary);
}

.action-bar :deep(.van-search) {
  flex: 1;
  border-radius: 20px;
  background-color: var(--bg-color-secondary) !important;
}
.action-bar :deep(.van-search__content) {
  background-color: var(--bg-color);
}

/* 账户列表样式 */
.accounts-list {
  padding: 0 16px;
}

.account-item {
  margin-bottom: 8px;
}

.account-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--bg-color-tertiary);
  border-radius: 50%;
  margin-right: 12px;
}
.account-icon .van-icon {
  color: var(--text-color);
}

.account-icon.archived {
  background-color: var(--bg-color-tertiary);
  opacity: 0.6;
}

/* 层级显示样式 */
.account-level-0 {
  font-weight: 600;
  color: var(--van-text-color);
}

.account-level-1 {
  font-weight: 500;
  color: var(--van-text-color-2);
}

.account-level-2 {
  font-weight: 400;
  color: var(--van-text-color-3);
}

.account-level-3 {
  font-weight: 300;
  color: var(--van-text-color-3);
}

.has-children {
  background-color: var(--van-background-2);
}

.expand-icon {
  margin-right: 4px;
  transition: transform 0.2s ease;
}

/* 创建表单样式 */
.create-form {
  padding: 20px;
  background-color: var(--bg-color-secondary);
}

.form-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 20px;
  text-align: center;
}

.form-actions {
  margin-top: 24px;
}

/* 移除所有自定义Dialog样式，使用Vant原生样式 */

/* 标签页样式覆盖 */
:deep(.van-tabs__nav) {
  background: var(--bg-color);
  margin: 0 16px;
  border-radius: 12px 12px 0 0;
}

:deep(.van-tabs__line) {
  background-color: var(--color-primary);
}

:deep(.van-tab) {
  font-size: 14px;
  color: var(--text-color-secondary);
}

:deep(.van-tab--active) {
  color: var(--color-primary);
  font-weight: 500;
}

:deep(.van-tabs__content) {
  background: var(--bg-color);
  margin: 0 16px;
  border-radius: 0 0 12px 12px;
  padding-top: 16px;
}

/* Cell 样式覆盖 */
:deep(.van-cell) {
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-color-lighter);
}

:deep(.van-cell:last-child) {
  margin-bottom: 0;
}

:deep(.van-cell__title) {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

:deep(.van-cell__label) {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin-top: 2px;
}

:deep(.van-cell__value) {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color-secondary);
}

/* 弹出层样式覆盖 - 排除Dialog */
:deep(.van-popup:not(.van-dialog)) {
  border-radius: 16px 16px 0 0;
  z-index: 2001; /* 确保弹窗在最上层 */
  background-color: var(--bg-color-secondary);
}

/* 专门针对新增账户弹窗的样式优化 */
:deep(.van-popup) {
  color: var(--text-color) !important;
}

:deep(.van-popup .create-form) {
  background-color: var(--bg-color-secondary) !important;
  color: var(--text-color) !important;
}

:deep(.van-popup .form-title) {
  color: var(--text-color) !important;
}

:deep(.van-popup .van-field) {
  background-color: var(--bg-color) !important;
  color: var(--text-color) !important;
}

:deep(.van-popup .van-field__label) {
  color: var(--text-color-secondary) !important;
}

:deep(.van-popup .van-field__control) {
  color: var(--text-color) !important;
}

:deep(.van-popup .van-field__control::placeholder) {
  color: var(--text-color-placeholder) !important;
}

/* Picker 样式优化 */
:deep(.van-picker__toolbar) {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-color) !important;
}

:deep(.van-picker) {
  background-color: var(--bg-color) !important;
}

:deep(.van-picker-column__item) {
  color: var(--text-color) !important;
}

:deep(.van-picker__confirm) {
  color: var(--color-primary) !important;
}

:deep(.van-picker__cancel) {
  color: var(--text-color-secondary) !important;
}

:deep(.van-field__label) {
  width: 80px;
  color: var(--text-color-secondary);
  font-weight: 500;
}

:deep(.van-field__control) {
  color: var(--text-color);
}

/* 空状态样式 */
:deep(.van-empty) {
  padding: 40px 20px;
}

:deep(.van-empty__description) {
  color: var(--text-color-placeholder);
  font-size: 14px;
}

/* 按钮样式覆盖 */
:deep(.van-button--mini) {
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
}

:deep(.van-button--plain) {
  background: transparent;
}

/* 弹窗中的主要按钮样式 */
:deep(.van-popup .van-button--primary) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: var(--color-white) !important;
}

/* 日历组件样式优化 */
:deep(.van-calendar) {
  background-color: var(--bg-color) !important;
  color: var(--text-color) !important;
}

:deep(.van-calendar__header) {
  background-color: var(--bg-color) !important;
  color: var(--text-color) !important;
}

:deep(.van-calendar__day) {
  color: var(--text-color) !important;
}

:deep(.van-calendar__day--selected) {
  background-color: var(--color-primary) !important;
  color: var(--color-white) !important;
}

/* 响应式优化 */
@media (max-width: 375px) {
  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 11px;
  }

  .action-bar {
    padding: 0 12px 12px;
  }

  .accounts-list {
    padding: 0 12px;
  }

  .overview-section {
    padding: 12px;
  }

  .stats-section {
    padding: 0 12px 12px;
  }
}

/* 排序模式样式 */
.sort-mode {
  padding: 16px;
  background-color: var(--bg-color);
}

.sort-section {
  margin-bottom: 24px;
}

.sort-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 8px;
}

.sort-desc {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin-bottom: 16px;
}

.sort-header {
  padding: 16px 16px 8px 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 16px;
}

.sort-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.sort-breadcrumb {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.breadcrumb-item-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-icon {
  color: var(--color-primary);
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.back-icon:hover {
  background-color: var(--bg-color-secondary);
}

.breadcrumb-item {
  cursor: pointer;
  transition: color 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
}

.breadcrumb-item.clickable {
  color: var(--color-primary);
  background-color: var(--bg-color-secondary);
  font-weight: 500;
}

.breadcrumb-item.clickable:hover {
  background-color: var(--color-primary);
  color: var(--color-white);
}

.breadcrumb-item.active {
  color: var(--color-primary);
  font-weight: 500;
}

.breadcrumb-item.current {
  background-color: var(--color-primary);
  color: var(--color-white);
  cursor: default;
}

.breadcrumb-arrow {
  margin: 0 8px;
  font-size: 12px;
  transform: rotate(90deg);
  color: var(--text-color-tertiary);
}

.subcategory-sort-container,
.account-sort-container {
  padding: 0 16px 16px 16px;
}

.sort-list {
  margin-top: 16px;
}

.icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.right-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-count {
  font-size: 12px;
  color: var(--text-color-secondary);
  background-color: var(--bg-color-secondary);
  padding: 2px 8px;
  border-radius: 12px;
  white-space: nowrap;
}

.enter-icon {
  color: var(--color-primary);
  font-size: 14px;
  transform: rotate(90deg);
}

.subcategory-item {
  background-color: var(--bg-color);
  border: 1px solid var(--border-color);
  margin-bottom: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.subcategory-item:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.account-item-sort {
  background-color: var(--bg-color-tertiary);
  border: 1px solid var(--border-color-lighter);
  margin-bottom: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.account-item-sort:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.drag-handle {
  color: var(--text-color-secondary);
  cursor: grab;
}

.drag-handle:active {
  cursor: grabbing;
}

/* 层级样式 */
.account-level-0 {
  font-weight: 600;
  background-color: var(--bg-color);
}

.account-level-1 {
  font-weight: 500;
  background-color: var(--bg-color-secondary);
}

.account-level-2 {
  font-weight: 400;
  background-color: var(--bg-color-tertiary);
}

/* 拖拽时的样式 */
.sortable-ghost {
  opacity: 0.8;
  background-color: var(--bg-color-secondary);
}

.sortable-chosen {
  background-color: var(--bg-color-secondary);
}
</style>
