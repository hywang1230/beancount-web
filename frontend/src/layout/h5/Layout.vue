<template>
  <div class="h5-layout">
    <!-- 头部导航 -->
    <van-nav-bar
      :title="currentPageTitle"
      :left-arrow="showBackArrow"
      @click-left="onBack"
      class="top-nav"
    >
      <template #right v-if="showMenu">
        <van-icon name="wap-nav" @click="showMenuPopup = true" />
      </template>
    </van-nav-bar>

    <!-- 主内容 -->
    <div class="main-content" ref="mainContentRef">
      <!-- 添加 keep-alive 缓存关键页面 -->
      <router-view v-slot="{ Component, route }">
        <keep-alive include="H5Transactions,H5Reports,H5Accounts,H5Dashboard">
          <component :is="Component" :key="route.fullPath" />
        </keep-alive>
      </router-view>
    </div>

    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" @change="onTabChange" class="bottom-tabbar">
      <van-tabbar-item
        v-for="item in tabbarItems"
        :key="item.name"
        :name="item.name"
        :icon="item.icon"
        :to="item.path"
      >
        {{ item.title }}
      </van-tabbar-item>
    </van-tabbar>

    <!-- 菜单弹窗 -->
    <van-popup
      v-model:show="showMenuPopup"
      position="right"
      :style="{ width: '80%', height: '100%' }"
    >
      <div class="menu-popup">
        <div class="menu-header">
          <h3>Beancount Web</h3>
          <van-icon name="cross" @click="showMenuPopup = false" />
        </div>

        <!-- 用户信息 -->
        <div class="user-section">
          <van-cell
            :title="authStore.user?.username || '用户'"
            icon="user-o"
            :label="`当前登录用户`"
          />
        </div>

        <van-cell-group>
          <van-cell
            v-for="item in allMenuItems"
            :key="item.path"
            :title="item.title"
            :icon="item.icon"
            is-link
            @click="navigateTo(item.path)"
          />

          <!-- 登出选项 -->
          <van-cell
            title="登出"
            icon="sign-out"
            is-link
            @click="handleLogout"
            class="logout-cell"
          />
        </van-cell-group>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { showConfirmDialog, showToast } from "vant";
import { computed, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const showMenuPopup = ref(false);
const activeTab = ref("dashboard");
const mainContentRef = ref<HTMLElement>();

const tabbarItems = [
  { name: "dashboard", title: "首页", icon: "home-o", path: "/h5/dashboard" },
  {
    name: "transactions",
    title: "流水",
    icon: "bill-o",
    path: "/h5/transactions",
  },
  { name: "add", title: "记账", icon: "plus", path: "/h5/add-transaction" },
  { name: "reports", title: "报表", icon: "bar-chart-o", path: "/h5/reports" },
  { name: "settings", title: "设置", icon: "setting-o", path: "/h5/settings" },
];

const allMenuItems = [
  { path: "/h5/dashboard", title: "首页", icon: "home-o" },
  { path: "/h5/transactions", title: "交易流水", icon: "bill-o" },
  { path: "/h5/add-transaction", title: "新增交易", icon: "plus" },
  { path: "/h5/reports", title: "报表分析", icon: "bar-chart-o" },
  { path: "/h5/settings", title: "设置", icon: "setting-o" },
  { path: "/h5/recurring", title: "周期记账", icon: "replay" },
  { path: "/h5/files", title: "文件管理", icon: "folder-o" },
  { path: "/h5/accounts", title: "账户管理", icon: "manager-o" },
];

// 监听路由变化，更新当前激活的标签
watch(
  () => route.path,
  (newPath) => {
    const currentItem = tabbarItems.find((item) => item.path === newPath);
    if (currentItem) {
      activeTab.value = currentItem.name;
    }
  },
  { immediate: true }
);

// 监听路由变化，滚动到顶部（仅对非缓存页面）
watch(
  () => route.path,
  () => {
    // 对于缓存页面，不自动滚动到顶部，保持用户的滚动位置
    const cachedPages = [
      "/h5/transactions",
      "/h5/reports",
      "/h5/accounts",
      "/h5/dashboard",
    ];
    const isFromCachedPage = cachedPages.includes(route.path);

    if (!isFromCachedPage) {
      // 使用nextTick确保DOM更新完成后再滚动
      setTimeout(() => {
        if (mainContentRef.value) {
          mainContentRef.value.scrollTo({
            top: 0,
            behavior: "smooth",
          });
        }
      }, 0);
    }
  }
);

const currentPageTitle = computed(() => {
  // 优先从路由元信息获取标题
  if (route.meta && route.meta.title) {
    if (typeof route.meta.title === "function") {
      return route.meta.title(route);
    }
    return route.meta.title as string;
  }

  const currentItem = allMenuItems.find((item) => item.path === route.path);
  if (currentItem) {
    return currentItem.title;
  }

  // 处理动态路由
  if (route.path.startsWith("/h5/transactions/")) {
    return "交易详情";
  }

  if (route.path.startsWith("/h5/accounts/journal/")) {
    return `账户: ${route.params.accountName}`;
  }

  if (route.path.startsWith("/h5/recurring/")) {
    if (route.path.includes("/add")) {
      return "新增周期记账";
    } else if (route.path.includes("/edit")) {
      return "编辑周期记账";
    } else {
      return "周期记账详情";
    }
  }

  return "首页";
});

const showMenu = computed(() => {
  // 底部导航栏的页面不显示菜单按钮
  const isTabbarPage = tabbarItems.some((item) => item.path === route.path);
  if (isTabbarPage) {
    return false;
  }

  // 设置页面的子页面不显示菜单按钮
  const settingsSubPages = ["/h5/recurring", "/h5/files", "/h5/accounts"];
  if (settingsSubPages.includes(route.path)) {
    return false;
  }

  // 动态路由页面不显示菜单按钮
  if (
    route.path.startsWith("/h5/transactions/") ||
    route.path.startsWith("/h5/recurring/")
  ) {
    return false;
  }

  return false; // 默认不显示菜单按钮
});

// 根据当前路由判断是否显示返回箭头
const showBackArrow = computed(() => {
  const isTabbarPage = tabbarItems.some((item) => item.path === route.path);
  return !isTabbarPage;
});

const onBack = () => {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push("/h5/dashboard");
  }
};

const onTabChange = (name: string) => {
  const item = tabbarItems.find((tab) => tab.name === name);
  if (item) {
    router.push(item.path);
  }
};

const navigateTo = (path: string) => {
  showMenuPopup.value = false;
  router.push(path);
};

const handleLogout = async () => {
  try {
    await showConfirmDialog({
      title: "确认登出",
      message: "确定要登出吗？",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    });

    await authStore.logout();
    showMenuPopup.value = false;
    showToast("登出成功");
    router.push("/login");
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("登出失败:", error);
      showToast("登出失败");
    }
  }
};
</script>

<style scoped>
.h5-layout {
  height: 100vh;
  height: 100dvh; /* 使用动态视口高度，避免移动端地址栏影响 */
  display: flex;
  flex-direction: column;
  background-color: var(--van-background);
  position: relative; /* 确保子元素正确定位 */
  transition: background-color 0.3s ease;
}

.top-nav {
  flex-shrink: 0;
  z-index: 1000;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 60px; /* 为底部导航留出更多空间 */
  -webkit-overflow-scrolling: touch; /* 启用iOS平滑滚动 */
  transition: padding-bottom 0.3s ease; /* 添加过渡动画 */
}

/* 底部导航栏样式 */
.bottom-tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000; /* 确保在内容之上，但在弹窗之下 */
  /* 适配安全区域 */
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.menu-popup {
  height: 100%;
  background-color: var(--van-background-2);
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s ease;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--van-border-color);
  transition: border-color 0.3s ease;
}

.menu-header h3 {
  margin: 0;
  color: var(--van-text-color);
  font-size: 18px;
  font-weight: 500;
  transition: color 0.3s ease;
}

.user-section {
  padding: 16px 0;
  border-bottom: 1px solid var(--van-border-color);
  margin-bottom: 8px;
}

.logout-cell {
  color: var(--van-danger-color);
}
</style>
