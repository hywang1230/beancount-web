<template>
  <van-popup
    v-model:show="visible"
    position="right"
    :style="{ width: '100%', height: '100%' }"
    :teleport="'body'"
    :overlay="false"
    class="fullscreen-popup"
  >
    <div class="fullscreen-selector">
      <!-- 顶部导航栏 -->
      <div class="selector-header">
        <van-nav-bar
          :title="title"
          left-text="取消"
          left-arrow
          @click-left="close"
          @click-right="close"
        >
          <template #right>
            <van-icon name="cross" />
          </template>
        </van-nav-bar>
      </div>

      <!-- 搜索栏 -->
      <div class="search-section" v-if="showSearch">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索..."
          @search="onSearch"
          @input="onSearchInput"
        />
      </div>

      <!-- 内容区域 -->
      <div class="content-area">
        <!-- 账户选择 -->
        <div v-if="type === 'account'" class="account-content">
          <!-- 账户类型标签 -->
          <div class="type-tabs" v-if="showAccountTypes">
            <div class="tab-container">
              <div
                v-for="tab in accountTypeTabs"
                :key="tab.type"
                class="tab-item"
                :class="{ active: activeAccountType === tab.type }"
                @click="setActiveAccountType(tab.type)"
              >
                <van-icon :name="tab.icon" />
                <span>{{ tab.title }}</span>
              </div>
            </div>
          </div>

          <!-- 账户树形列表 -->
          <div class="account-tree">
            <van-list
              v-model:loading="loading"
              :finished="finished"
              finished-text="没有更多账户"
            >
              <!-- 渲染账户树形结构 -->
              <template v-for="node in accountTree" :key="node.path">
                <!-- 父级节点 -->
                <div
                  v-if="node.hasChildren"
                  class="tree-node parent-node"
                  :style="{ paddingLeft: node.level * 20 + 16 + 'px' }"
                  @click="toggleNode(node.path)"
                >
                  <van-icon
                    :name="
                      expandedNodes.has(node.path) ? 'arrow-down' : 'arrow'
                    "
                    class="expand-icon"
                  />
                  <van-icon
                    :name="getAccountIcon(node.path)"
                    class="node-icon"
                  />
                  <span class="node-name">{{ node.displayName }}</span>
                </div>

                <!-- 叶子节点（可选择的账户） -->
                <div
                  v-else
                  class="tree-node leaf-node"
                  :style="{ paddingLeft: node.level * 20 + 16 + 'px' }"
                  @click="selectAccount(node.path)"
                >
                  <div class="expand-placeholder"></div>
                  <van-icon
                    :name="getAccountIcon(node.path)"
                    class="node-icon"
                  />
                  <div class="node-content">
                    <div class="node-name">{{ node.displayName }}</div>
                    <div class="node-balance" v-if="node.balance">
                      余额: ¥{{ node.balance.toFixed(2) }}
                    </div>
                  </div>
                </div>
              </template>
            </van-list>
          </div>
        </div>

        <!-- 分类选择 -->
        <div v-else-if="type === 'category'" class="category-content">
          <!-- 分类树形列表 -->
          <div class="category-tree">
            <!-- 渲染分类树形结构 -->
            <template v-for="node in categoryTree" :key="node.path">
              <!-- 父级节点 -->
              <div
                v-if="node.hasChildren"
                class="tree-node parent-node"
                :style="{ paddingLeft: node.level * 20 + 16 + 'px' }"
                @click="toggleNode(node.path)"
              >
                <van-icon
                  :name="expandedNodes.has(node.path) ? 'arrow-down' : 'arrow'"
                  class="expand-icon"
                />
                <van-icon
                  :name="getCategoryIcon(node.path)"
                  class="node-icon category-icon"
                />
                <span class="node-name">{{ node.displayName }}</span>
              </div>

              <!-- 叶子节点（可选择的分类） -->
              <div
                v-else
                class="tree-node leaf-node"
                :style="{ paddingLeft: node.level * 20 + 16 + 'px' }"
                @click="selectCategory(node.path)"
              >
                <div class="expand-placeholder"></div>
                <van-icon
                  :name="getCategoryIcon(node.path)"
                  class="node-icon category-icon"
                />
                <div class="node-content">
                  <div class="node-name">{{ node.displayName }}</div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 交易对象选择 -->
        <div v-else-if="type === 'payee'" class="payee-content">
          <!-- 交易对象列表 -->
          <div class="payee-list">
            <van-list
              v-model:loading="loading"
              :finished="finished"
              finished-text="没有更多交易对象"
            >
              <!-- 新增交易对象选项 -->
              <div class="payee-item new-payee-item" @click="showAddPayeeInput">
                <van-icon name="plus" class="add-icon" />
                <span class="payee-name">添加新的交易对象</span>
              </div>

              <!-- 交易对象列表 -->
              <div
                v-for="payee in filteredPayees"
                :key="payee"
                class="payee-item"
                @click="selectPayee(payee)"
              >
                <van-icon name="user-o" class="payee-icon" />
                <span class="payee-name">{{ payee }}</span>
              </div>
            </van-list>
          </div>

          <!-- 新增交易对象输入框 -->
          <van-popup v-model:show="showNewPayeeInput" position="top">
            <div class="new-payee-popup">
              <div class="popup-header">
                <van-button type="default" @click="showNewPayeeInput = false"
                  >取消</van-button
                >
                <span class="popup-title">添加交易对象</span>
                <van-button type="primary" @click="confirmNewPayee"
                  >确定</van-button
                >
              </div>

              <div class="payee-input-section">
                <van-field
                  v-model="newPayeeName"
                  placeholder="输入交易对象名称"
                  clearable
                  autofocus
                />
              </div>
            </div>
          </van-popup>
        </div>
      </div>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { getAccountsByType } from "@/api/accounts";
import { showToast } from "vant";
import { computed, onMounted, ref, watch } from "vue";

interface Account {
  name: string;
  balance?: number;
}

interface Category {
  name: string;
  displayName?: string;
  hasChildren?: boolean;
  children?: Category[];
}

interface PathItem {
  name: string;
  fullPath: string;
}

interface Props {
  type: "account" | "category" | "payee";
  title?: string;
  showSearch?: boolean;
  showAccountTypes?: boolean;
  accountTypes?: string[];
  categories?: Category[];
  payees?: string[];
}

interface Emits {
  (e: "confirm", value: string): void;
  (e: "close"): void;
}

const props = withDefaults(defineProps<Props>(), {
  type: "account",
  title: "选择",
  showSearch: true,
  showAccountTypes: true,
  accountTypes: () => ["Assets", "Liabilities", "Income", "Expenses"],
});

const emit = defineEmits<Emits>();

// 状态
const visible = ref(false);
const loading = ref(false);
const finished = ref(false);
const searchKeyword = ref("");
const accounts = ref<Account[]>([]);
const activeAccountType = ref("Assets");
const currentPath = ref<PathItem[]>([]);
const currentCategories = ref<Category[]>([]);
const currentPayees = ref<string[]>([]);
const expandedNodes = ref<Set<string>>(new Set());
const showNewPayeeInput = ref(false);
const newPayeeName = ref("");

// 确保初始状态正确
if (!accounts.value) {
  accounts.value = [];
}
if (!currentCategories.value) {
  currentCategories.value = [];
}

// 账户类型标签
const accountTypeTabs = computed(() =>
  [
    { type: "Assets", title: "资产", icon: "gold-coin-o" },
    { type: "Liabilities", title: "负债", icon: "credit-pay" },
    { type: "Income", title: "收入", icon: "arrow-up" },
    { type: "Expenses", title: "支出", icon: "arrow-down" },
  ].filter((tab) => props.accountTypes.includes(tab.type))
);

// 构建账户树形结构
const accountTree = computed(() => {
  if (!accounts.value || accounts.value.length === 0) {
    return [];
  }

  // 按账户类型过滤
  let filtered = accounts.value;
  if (props.showAccountTypes) {
    filtered = filtered.filter(
      (account) =>
        account &&
        account.name &&
        account.name.startsWith(`${activeAccountType.value}:`)
    );
  }

  // 按搜索关键词过滤
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(
      (account) =>
        account &&
        account.name &&
        (account.name.toLowerCase().includes(keyword) ||
          formatAccountName(account.name).toLowerCase().includes(keyword))
    );
  }

  return buildTreeFromAccounts(filtered);
});

// 构建分类树形结构
const categoryTree = computed(() => {
  console.log("categoryTree - 开始计算");
  console.log(
    "categoryTree - currentCategories.value:",
    currentCategories.value
  );
  console.log(
    "categoryTree - currentCategories.value 长度:",
    currentCategories.value?.length
  );

  if (!currentCategories.value || currentCategories.value.length === 0) {
    console.log("categoryTree - 分类数据为空，返回空数组");
    return [];
  }

  // 搜索过滤
  let filtered = currentCategories.value;
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(
      (category) =>
        category &&
        category.name &&
        (category.name.toLowerCase().includes(keyword) ||
          formatCategoryName(category.name).toLowerCase().includes(keyword))
    );
  }

  console.log("categoryTree - 过滤后的分类:", filtered);
  const result = buildTreeFromCategories(filtered);
  console.log("categoryTree - 构建的树结构:", result);
  console.log("categoryTree - 树结构数量:", result.length);
  if (result.length > 0) {
    console.log("categoryTree - 第一个节点:", result[0]);
    console.log(
      "categoryTree - 第一个节点是否有子节点:",
      result[0].hasChildren
    );
  }
  return result;
});

// 过滤后的交易对象
const filteredPayees = computed(() => {
  if (!searchKeyword.value.trim()) {
    return currentPayees.value;
  }

  const keyword = searchKeyword.value.toLowerCase();
  return currentPayees.value.filter(
    (payee) => payee && payee.toLowerCase().includes(keyword)
  );
});

// 方法
const formatAccountName = (accountName: string) => {
  if (!accountName) return "未知账户";
  const parts = accountName.split(":");
  if (parts.length > 1) {
    let formattedName = parts.slice(1).join(":");

    const dashIndex = formattedName.indexOf("-");
    if (dashIndex > 0) {
      formattedName = formattedName.substring(dashIndex + 1);
    }

    return formattedName.replace(/:/g, "-");
  }
  return accountName;
};

const formatCategoryName = (categoryName: string) => {
  if (!categoryName) return "未知分类";
  const parts = categoryName.split(":");
  if (parts.length > 0) {
    let name = parts[parts.length - 1];

    const dashIndex = name.indexOf("-");
    if (dashIndex > 0) {
      name = name.substring(dashIndex + 1);
    }

    return name;
  }
  return categoryName;
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

const getCategoryIcon = (categoryName: string) => {
  // 根据分类名称返回相应图标
  const name = categoryName.toLowerCase();
  if (
    name.includes("餐饮") ||
    name.includes("食品") ||
    name.includes("meals") ||
    name.includes("food")
  )
    return "food-bank-card";
  if (
    name.includes("交通") ||
    name.includes("车费") ||
    name.includes("transport") ||
    name.includes("travel")
  )
    return "logistics";
  if (
    name.includes("购物") ||
    name.includes("商品") ||
    name.includes("shopping") ||
    name.includes("goods")
  )
    return "shopping-cart-o";
  if (
    name.includes("娱乐") ||
    name.includes("电影") ||
    name.includes("entertainment") ||
    name.includes("movie")
  )
    return "music";
  if (
    name.includes("住房") ||
    name.includes("房租") ||
    name.includes("housing") ||
    name.includes("rent")
  )
    return "home-o";
  if (
    name.includes("医疗") ||
    name.includes("健康") ||
    name.includes("medical") ||
    name.includes("health")
  )
    return "medic";
  if (
    name.includes("教育") ||
    name.includes("学习") ||
    name.includes("education") ||
    name.includes("study")
  )
    return "education";
  if (
    name.includes("投资") ||
    name.includes("理财") ||
    name.includes("investment") ||
    name.includes("finance")
  )
    return "chart-trending-o";
  if (
    name.includes("服装") ||
    name.includes("clothing") ||
    name.includes("apparel")
  )
    return "gift-o";
  if (
    name.includes("通讯") ||
    name.includes("手机") ||
    name.includes("communication") ||
    name.includes("phone")
  )
    return "phone-o";
  if (
    name.includes("水电") ||
    name.includes("公用") ||
    name.includes("utilities")
  )
    return "fire-o";
  return "apps-o";
};

const setActiveAccountType = (type: string) => {
  activeAccountType.value = type;
};

const selectAccount = (accountName: string) => {
  emit("confirm", accountName);
  close();
};

// 树形结构构建方法
const buildTreeFromAccounts = (accountList: Account[]) => {
  const tree: any[] = [];
  const nodeMap = new Map();

  // 为每个账户创建所有层级的节点，但跳过顶级分类
  accountList.forEach((account) => {
    const parts = account.name.split(":");

    // 跳过顶级分类（Assets、Liabilities等），从第二级开始
    if (parts.length < 2) return;

    for (let i = 1; i < parts.length; i++) {
      // 从索引1开始，跳过顶级
      const path = parts.slice(0, i + 1).join(":");
      let displayName = parts[i];

      // 如果是第一层（level = 0），去掉前缀字母和"-"
      if (i === 1) {
        const match = displayName.match(/^[A-Z]+-(.+)$/);
        if (match) {
          displayName = match[1];
        }
      }

      const level = i - 1; // 重新计算层级，从0开始
      const isLeaf = i === parts.length - 1;

      if (!nodeMap.has(path)) {
        nodeMap.set(path, {
          path,
          displayName,
          level,
          hasChildren: !isLeaf,
          children: [],
          balance: isLeaf ? account.balance : undefined,
          visible: false,
        });
      }

      // 如果是叶子节点，更新余额
      if (isLeaf) {
        nodeMap.get(path).balance = account.balance;
      }
    }
  });

  // 构建层级关系和可见性
  const allNodes = Array.from(nodeMap.values());

  // 默认展开所有父节点
  allNodes.forEach((node) => {
    if (node.hasChildren) {
      expandedNodes.value.add(node.path);
    }
  });

  // 第二级作为根节点（level = 0）默认可见
  allNodes.forEach((node) => {
    if (node.level === 0) {
      node.visible = true;
      tree.push(node);
    }
  });

  // 根据展开状态显示子节点
  const getVisibleNodes = (nodes: any[]): any[] => {
    const visible: any[] = [];

    nodes.forEach((node) => {
      visible.push(node);

      // 如果节点已展开，添加其直接子节点
      if (expandedNodes.value.has(node.path)) {
        const children = allNodes.filter(
          (n) =>
            n.level === node.level + 1 &&
            n.path.startsWith(node.path + ":") &&
            !n.path.substring(node.path.length + 1).includes(":")
        );
        visible.push(...getVisibleNodes(children));
      }
    });

    return visible;
  };

  return getVisibleNodes(tree);
};

const buildTreeFromCategories = (categoryList: Category[]) => {
  console.log("buildTreeFromCategories - 开始构建，输入数据:", categoryList);
  if (!categoryList || categoryList.length === 0) {
    console.log("buildTreeFromCategories - 输入数据为空");
    return [];
  }

  const tree: any[] = [];
  const nodeMap = new Map();

  // 为每个分类创建节点，跳过顶级分类（Expenses、Income等）
  categoryList.forEach((category) => {
    console.log("buildTreeFromCategories - 处理分类:", category);
    const parts = category.name.split(":");
    console.log("buildTreeFromCategories - 分割结果:", parts);

    // 跳过顶级分类，从第二级开始
    if (parts.length < 2) {
      console.log(
        "buildTreeFromCategories - 跳过分类，层级不足:",
        category.name
      );
      return;
    }

    for (let i = 1; i < parts.length; i++) {
      // 从索引1开始，跳过顶级
      const path = parts.slice(0, i + 1).join(":");
      let displayName = parts[i];

      // 如果是第一层（level = 0），去掉前缀字母和"-"
      if (i === 1) {
        const match = displayName.match(/^[A-Z]+-(.+)$/);
        if (match) {
          displayName = match[1];
        }
      }

      const level = i - 1; // 重新计算层级，从0开始

      if (!nodeMap.has(path)) {
        const hasChildrenInList = categoryList.some(
          (cat) => cat.name !== path && cat.name.startsWith(path + ":")
        );

        const node = {
          path,
          displayName,
          level,
          hasChildren: hasChildrenInList,
          children: [],
          visible: false,
        };

        console.log(
          `buildTreeFromCategories - 创建节点: ${path} (level: ${level}, hasChildren: ${hasChildrenInList})`
        );
        if (hasChildrenInList) {
          const children = categoryList.filter(
            (cat) => cat.name !== path && cat.name.startsWith(path + ":")
          );
          console.log(
            `buildTreeFromCategories - 节点 ${path} 的子节点:`,
            children.map((c) => c.name)
          );
        }
        nodeMap.set(path, node);
      }
    }
  });

  // 构建可见节点
  const allNodes = Array.from(nodeMap.values());
  console.log("buildTreeFromCategories - 所有节点:", allNodes);

  // 默认展开所有父节点
  allNodes.forEach((node) => {
    if (node.hasChildren) {
      expandedNodes.value.add(node.path);
    }
  });

  // 第二级作为根节点（level = 0）默认可见
  allNodes.forEach((node) => {
    if (node.level === 0) {
      node.visible = true;
      tree.push(node);
    }
  });
  console.log("buildTreeFromCategories - 根节点:", tree);

  const getVisibleNodes = (nodes: any[]): any[] => {
    const visible: any[] = [];

    nodes.forEach((node) => {
      visible.push(node);

      if (expandedNodes.value.has(node.path)) {
        const children = allNodes.filter(
          (n) =>
            n.level === node.level + 1 &&
            n.path.startsWith(node.path + ":") &&
            !n.path.substring(node.path.length + 1).includes(":")
        );
        visible.push(...getVisibleNodes(children));
      }
    });

    return visible;
  };

  const result = getVisibleNodes(tree);
  console.log("buildTreeFromCategories - 最终结果:", result);
  return result;
};

// 节点操作方法
const toggleNode = (nodePath: string) => {
  if (expandedNodes.value.has(nodePath)) {
    expandedNodes.value.delete(nodePath);
  } else {
    expandedNodes.value.add(nodePath);
  }
};

const selectCategory = (categoryPath: string) => {
  emit("confirm", categoryPath);
  close();
};

// 选择交易对象
const selectPayee = (payee: string) => {
  emit("confirm", payee);
  close();
};

// 显示添加新交易对象输入框
const showAddPayeeInput = () => {
  newPayeeName.value = "";
  showNewPayeeInput.value = true;
};

// 确认添加新交易对象
const confirmNewPayee = () => {
  if (newPayeeName.value.trim()) {
    const newPayee = newPayeeName.value.trim();
    // 添加到当前交易对象列表
    if (!currentPayees.value.includes(newPayee)) {
      currentPayees.value.unshift(newPayee);
    }
    // 选择新添加的交易对象
    emit("confirm", newPayee);
    showNewPayeeInput.value = false;
    newPayeeName.value = "";
    close();
  } else {
    showToast("请输入交易对象名称");
  }
};

const onSearch = () => {
  // 搜索逻辑已在计算属性中处理
};

const onSearchInput = () => {
  // 实时搜索
};

const close = () => {
  visible.value = false;
  searchKeyword.value = "";
  currentPath.value = [];
  expandedNodes.value.clear(); // 清除展开状态
  emit("close");
};

const loadAccounts = async () => {
  try {
    loading.value = true;

    // 使用getAccountsByType API，与TransactionForm保持一致
    const response = await getAccountsByType();
    console.log("FullScreenSelector - API完整响应:", response);

    const accountData = response.data || response;
    console.log("FullScreenSelector - 账户数据:", accountData);

    // 处理后端返回的按类型分组的数据格式
    let accountsList: string[] = [];
    if (accountData && typeof accountData === "object") {
      console.log("FullScreenSelector - Assets账户:", accountData.Assets);
      console.log(
        "FullScreenSelector - Liabilities账户:",
        accountData.Liabilities
      );
      console.log("FullScreenSelector - Income账户:", accountData.Income);
      console.log("FullScreenSelector - Expenses账户:", accountData.Expenses);

      // 根据需要的账户类型提取账户
      const extractedTypes = [];
      if (props.accountTypes.includes("Assets") && accountData.Assets) {
        extractedTypes.push(...accountData.Assets);
      }
      if (
        props.accountTypes.includes("Liabilities") &&
        accountData.Liabilities
      ) {
        extractedTypes.push(...accountData.Liabilities);
      }
      if (props.accountTypes.includes("Income") && accountData.Income) {
        extractedTypes.push(...accountData.Income);
      }
      if (props.accountTypes.includes("Expenses") && accountData.Expenses) {
        extractedTypes.push(...accountData.Expenses);
      }

      accountsList = extractedTypes;
      console.log("FullScreenSelector - 合并后的账户列表:", accountsList);
    } else {
      console.warn(
        "FullScreenSelector - 账户数据格式不正确或为空:",
        accountData
      );
    }

    // 转换为Account格式
    accounts.value = accountsList
      .filter(
        (accountName: string) => accountName && typeof accountName === "string"
      )
      .map((accountName: string) => ({
        name: accountName,
        balance: 0, // 暂时设为0，如果需要真实余额可以后续添加API
      }));

    console.log("FullScreenSelector - 最终处理的账户数据:", accounts.value);
    console.log("FullScreenSelector - 账户数量:", accounts.value.length);

    finished.value = true;
  } catch (error) {
    console.error("FullScreenSelector - 加载账户列表失败:", error);
    console.error(
      "FullScreenSelector - 错误详情:",
      (error as any).response || (error as any).message || error
    );
    showToast("加载账户列表失败");

    // 使用备用数据
    console.log("FullScreenSelector - 使用备用账户数据");
    const fallbackAccounts = [
      "Assets:ZJ-资金:现金",
      "Assets:ZJ-资金:活期存款",
      "Liabilities:XYK-信用卡:招行:8164",
    ];
    accounts.value = fallbackAccounts.map((name) => ({ name, balance: 0 }));
  } finally {
    loading.value = false;
  }
};

// 公开方法
const show = () => {
  console.log("FullScreenSelector - show方法被调用");
  console.log("FullScreenSelector - 当前账户数据:", accounts.value);
  console.log("FullScreenSelector - 当前分类数据:", currentCategories.value);
  console.log("FullScreenSelector - props.type:", props.type);
  console.log("FullScreenSelector - props.categories:", props.categories);

  visible.value = true;

  // 如果是分类类型，设置分类数据
  if (props.type === "category") {
    console.log("FullScreenSelector - 设置分类数据");
    currentCategories.value = props.categories || [];
    console.log(
      "FullScreenSelector - 分类数据设置完成:",
      currentCategories.value
    );

    // 如果没有分类数据，提供一些测试数据
    if (currentCategories.value.length === 0) {
      console.log("FullScreenSelector - 分类数据为空，使用测试数据");
      currentCategories.value = [
        { name: "Expenses:CY-餐饮" },
        { name: "Expenses:CY-餐饮:早餐" },
        { name: "Expenses:CY-餐饮:午餐" },
        { name: "Expenses:CY-餐饮:晚餐" },
        { name: "Expenses:CY-餐饮:聚餐" },
        { name: "Expenses:JT-交通" },
        { name: "Expenses:JT-交通:公交" },
        { name: "Expenses:JT-交通:地铁" },
        { name: "Expenses:JT-交通:打车" },
        { name: "Expenses:JT-交通:停车" },
        { name: "Expenses:GW-购物" },
        { name: "Expenses:GW-购物:服装" },
        { name: "Expenses:GW-购物:数码" },
        { name: "Expenses:YL-娱乐" },
        { name: "Expenses:YL-娱乐:电影" },
        { name: "Expenses:YL-娱乐:游戏" },
      ];
      console.log(
        "FullScreenSelector - 设置测试数据完成:",
        currentCategories.value
      );
    }
  }

  // 如果是交易对象类型，设置交易对象数据
  if (props.type === "payee") {
    console.log("FullScreenSelector - 设置交易对象数据");
    currentPayees.value = props.payees || [];
    console.log(
      "FullScreenSelector - 交易对象数据设置完成:",
      currentPayees.value
    );

    // 如果没有交易对象数据，提供一些测试数据
    if (currentPayees.value.length === 0) {
      console.log("FullScreenSelector - 交易对象数据为空，使用测试数据");
      currentPayees.value = [
        "张三",
        "李四",
        "王五",
        "赵六",
        "星巴克",
        "麦当劳",
        "超市",
        "加油站",
        "出租车",
        "地铁",
      ];
      console.log(
        "FullScreenSelector - 设置测试数据完成:",
        currentPayees.value
      );
    }
  }

  // 如果是账户类型但没有数据，立即加载
  if (props.type === "account" && accounts.value.length === 0) {
    console.log("FullScreenSelector - 账户数据为空，立即加载");
    loadAccounts();
  }
};

// 暴露给父组件
defineExpose({
  show,
});

// 监听类型变化
watch(
  () => props.type,
  (newType) => {
    console.log("FullScreenSelector - 类型变化:", newType);
  },
  { immediate: true }
);

// 监听分类数据变化
watch(
  () => props.categories,
  (newCategories) => {
    console.log("FullScreenSelector - 分类数据变化:", newCategories);
    if (props.type === "category") {
      currentCategories.value = newCategories || [];
      console.log(
        "FullScreenSelector - 更新分类数据:",
        currentCategories.value
      );
      console.log(
        "FullScreenSelector - 分类数据长度:",
        currentCategories.value.length
      );

      // 如果没有分类数据，提供一些测试数据
      if (currentCategories.value.length === 0) {
        console.log("FullScreenSelector - 分类数据为空，使用测试数据");
        currentCategories.value = [
          { name: "Expenses:CY-餐饮" },
          { name: "Expenses:CY-餐饮:早餐" },
          { name: "Expenses:CY-餐饮:午餐" },
          { name: "Expenses:CY-餐饮:晚餐" },
          { name: "Expenses:CY-餐饮:聚餐" },
          { name: "Expenses:JT-交通" },
          { name: "Expenses:JT-交通:公交" },
          { name: "Expenses:JT-交通:地铁" },
          { name: "Expenses:JT-交通:打车" },
          { name: "Expenses:JT-交通:停车" },
          { name: "Expenses:GW-购物" },
          { name: "Expenses:GW-购物:服装" },
          { name: "Expenses:GW-购物:数码" },
          { name: "Expenses:YL-娱乐" },
          { name: "Expenses:YL-娱乐:电影" },
          { name: "Expenses:YL-娱乐:游戏" },
        ];
        console.log(
          "FullScreenSelector - 设置测试数据完成:",
          currentCategories.value
        );
      }
    }
  },
  { immediate: true, deep: true }
);

// 监听交易对象数据变化
watch(
  () => props.payees,
  (newPayees) => {
    console.log("FullScreenSelector - 交易对象数据变化:", newPayees);
    if (props.type === "payee") {
      currentPayees.value = newPayees || [];
      console.log(
        "FullScreenSelector - 更新交易对象数据:",
        currentPayees.value
      );
    }
  },
  { immediate: true, deep: true }
);

// 生命周期
onMounted(() => {
  if (props.type === "account") {
    loadAccounts();
  } else if (props.type === "category") {
    currentCategories.value = props.categories || [];
  } else if (props.type === "payee") {
    currentPayees.value = props.payees || [];
  }
});
</script>

<style scoped>
.fullscreen-popup {
  z-index: 9999 !important;
}

.fullscreen-selector {
  height: 100vh;
  background-color: #f7f8fa;
  display: flex;
  flex-direction: column;
}

.selector-header {
  flex-shrink: 0;
  background: white;
  border-bottom: 1px solid #ebedf0;
}

.search-section {
  flex-shrink: 0;
  background: white;
  border-bottom: 1px solid #ebedf0;
}

.content-area {
  flex: 1;
  overflow-y: auto;
}

/* 账户类型标签 */
.type-tabs {
  background: white;
  border-bottom: 1px solid #ebedf0;
  padding: 8px 0;
}

.tab-container {
  display: flex;
  justify-content: space-around;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 0 4px;
}

.tab-item.active {
  background: rgba(25, 137, 250, 0.1);
  color: #1989fa;
}

.tab-item .van-icon {
  font-size: 20px;
  margin-bottom: 4px;
}

.tab-item span {
  font-size: 12px;
}

/* 面包屑导航 */
.breadcrumb {
  background: white;
  padding: 12px 16px;
  border-bottom: 1px solid #ebedf0;
}

.breadcrumb-container {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  color: #1989fa;
  font-size: 14px;
  cursor: pointer;
  margin-right: 8px;
}

.breadcrumb-item .van-icon {
  margin: 0 4px;
  font-size: 12px;
  color: #969799;
}

/* 树形结构样式 */
.account-tree,
.category-tree {
  padding: 8px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: white;
  margin: 0 16px 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 48px;
}

.tree-node:hover {
  background: #f5f5f5;
}

.tree-node.parent-node {
  background: rgba(25, 137, 250, 0.04);
  font-weight: 500;
}

.tree-node.parent-node:hover {
  background: rgba(25, 137, 250, 0.08);
}

.tree-node.leaf-node {
  background: white;
}

.tree-node.leaf-node:hover {
  background: rgba(25, 137, 250, 0.05);
}

.expand-icon {
  width: 20px;
  font-size: 14px;
  color: #1989fa;
  margin-right: 8px;
  transition: transform 0.3s ease;
}

.expand-placeholder {
  width: 20px;
  margin-right: 8px;
}

.node-icon {
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: rgba(25, 137, 250, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 14px;
  color: #1989fa;
}

.node-icon.category-icon {
  background: rgba(238, 90, 82, 0.1);
  color: #ee5a52;
}

.node-name {
  font-size: 15px;
  color: #323233;
  margin-right: 8px;
}

.node-content {
  flex: 1;
  min-width: 0;
}

.node-balance {
  font-size: 11px;
  color: #1989fa;
  font-weight: 500;
  margin-top: 2px;
}

/* 层级缩进背景 */
.tree-node[style*="padding-left: 36px"] {
  background: rgba(0, 0, 0, 0.01);
}

.tree-node[style*="padding-left: 56px"] {
  background: rgba(0, 0, 0, 0.02);
}

.tree-node[style*="padding-left: 76px"] {
  background: rgba(0, 0, 0, 0.03);
}

/* 账户列表 */
.account-list {
  padding: 8px 0;
}

.account-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
  margin-bottom: 8px;
  margin: 0 16px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.account-item:hover {
  background: #f5f5f5;
}

.account-icon {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: rgba(25, 137, 250, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.account-icon .van-icon {
  font-size: 20px;
  color: #1989fa;
}

.account-info {
  flex: 1;
}

.account-name {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
  margin-bottom: 4px;
}

.account-type {
  font-size: 12px;
  color: #969799;
  margin-bottom: 2px;
}

.account-balance {
  font-size: 12px;
  color: #1989fa;
}

.account-arrow {
  margin-left: 8px;
}

.account-arrow .van-icon {
  font-size: 16px;
  color: #c8c9cc;
}

/* 分类列表 */
.category-list {
  padding: 8px 0;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
  margin-bottom: 8px;
  margin: 0 16px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-item:hover {
  background: #f5f5f5;
}

.category-item.back-item {
  background: #f7f8fa;
  border: 1px dashed #c8c9cc;
}

.category-icon {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: rgba(238, 90, 82, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.category-icon .van-icon {
  font-size: 20px;
  color: #ee5a52;
}

.back-item .category-icon {
  background: rgba(200, 201, 204, 0.1);
}

.back-item .category-icon .van-icon {
  color: #969799;
}

.category-info {
  flex: 1;
}

.category-name {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
  margin-bottom: 4px;
}

.category-path {
  font-size: 12px;
  color: #969799;
}

.category-arrow {
  margin-left: 8px;
}

.category-arrow .van-icon {
  font-size: 16px;
  color: #c8c9cc;
}

/* 响应式设计 */
@media (max-width: 375px) {
  .account-item,
  .category-item {
    margin: 0 12px 8px;
    padding: 12px;
  }

  .account-name,
  .category-name {
    font-size: 15px;
  }
}

/* 暗色主题 */
@media (prefers-color-scheme: dark) {
  .fullscreen-selector {
    background-color: #1a1a1a;
  }

  .selector-header {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }

  .search-section {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }

  .type-tabs {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }

  .breadcrumb {
    background: #2c2c2c;
    border-bottom-color: #3a3a3a;
  }

  .account-item,
  .category-item {
    background: #2c2c2c;
  }

  .account-item:hover,
  .category-item:hover {
    background: #3a3a3a;
  }

  .account-name,
  .category-name {
    color: #cccccc;
  }

  .category-item.back-item {
    background: #1a1a1a;
    border-color: #5a5a5a;
  }
}

/* 交易对象选择样式 */
.payee-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.payee-list {
  flex: 1;
  overflow-y: auto;
}

.payee-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  background: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.payee-item:hover {
  background-color: #f5f5f5;
}

.payee-item:last-child {
  border-bottom: none;
}

.new-payee-item {
  background-color: #f8f9fa;
  border: 1px dashed #ddd;
  color: #666;
}

.new-payee-item:hover {
  background-color: #e9ecef;
}

.add-icon,
.payee-icon {
  font-size: 20px;
  margin-right: 12px;
  color: #1989fa;
}

.payee-name {
  font-size: 16px;
  color: #323233;
}

.new-payee-item .payee-name {
  color: #666;
}

/* 新增交易对象弹窗样式 */
.new-payee-popup {
  background: white;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.popup-title {
  font-size: 16px;
  font-weight: 500;
  color: #323233;
}

.payee-input-section {
  padding: 16px;
}
</style>
