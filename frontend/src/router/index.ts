import H5Layout from "@/layout/h5/Layout.vue";
import PcLayout from "@/layout/pc/Layout.vue";
import { useAuthStore } from "@/stores/auth";
import { getDefaultRoute } from "@/utils/device";
import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  // 登录页面
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/Login.vue"),
    meta: { requiresAuth: false, title: "登录" },
  },
  // 根路由重定向逻辑，根据设备类型跳转
  {
    path: "/",
    redirect: () => {
      return getDefaultRoute();
    },
  },
  // PC端路由
  {
    path: "/pc",
    redirect: "/dashboard",
  },
  {
    path: "/",
    component: PcLayout,
    children: [
      {
        path: "dashboard",
        name: "PcDashboard",
        component: () => import("@/views/pc/Dashboard.vue"),
        meta: { title: "仪表盘", platform: "pc", requiresAuth: true },
      },
      {
        path: "transactions",
        name: "PcTransactions",
        component: () => import("@/views/pc/Transactions.vue"),
        meta: { title: "交易流水", platform: "pc", requiresAuth: true },
      },
      {
        path: "add-transaction",
        name: "PcAddTransaction",
        component: () => import("@/views/pc/AddTransaction.vue"),
        meta: { title: "新增交易", platform: "pc", requiresAuth: true },
      },
      {
        path: "reports",
        name: "PcReports",
        component: () => import("@/views/pc/Reports.vue"),
        meta: { title: "报表分析", platform: "pc", requiresAuth: true },
      },
      {
        path: "accounts",
        name: "PcAccounts",
        component: () => import("@/views/pc/Accounts.vue"),
        meta: { title: "账户管理", platform: "pc", requiresAuth: true },
      },
      {
        path: "files",
        name: "PcFiles",
        component: () => import("@/views/pc/Files.vue"),
        meta: { title: "文件管理", platform: "pc", requiresAuth: true },
      },
      {
        path: "recurring",
        name: "PcRecurringTransactions",
        component: () => import("@/views/pc/RecurringTransactions.vue"),
        meta: { title: "周期记账", platform: "pc", requiresAuth: true },
      },
    ],
  },
  // 移动端路由
  {
    path: "/h5",
    component: H5Layout,
    redirect: "/h5/dashboard",
    children: [
      {
        path: "dashboard",
        name: "H5Dashboard",
        component: () => import("@/views/h5/Dashboard.vue"),
        meta: { title: "首页", platform: "h5", requiresAuth: true },
      },
      {
        path: "transactions",
        name: "H5Transactions",
        component: () => import("@/views/h5/Transactions.vue"),
        meta: { title: "交易流水", platform: "h5", requiresAuth: true },
      },
      {
        path: "transactions/:id",
        name: "H5TransactionDetail",
        component: () => import("@/views/h5/TransactionDetail.vue"),
        meta: { title: "交易详情", platform: "h5", requiresAuth: true },
      },
      {
        path: "add-transaction",
        name: "H5AddTransaction",
        component: () => import("@/views/h5/AddTransaction.vue"),
        meta: { title: "新增交易", platform: "h5", requiresAuth: true },
      },
      {
        path: "reports",
        name: "H5Reports",
        component: () => import("@/views/h5/Reports.vue"),
        meta: { title: "报表分析", platform: "h5", requiresAuth: true },
      },
      {
        path: "accounts/journal/:accountName",
        name: "AccountJournal",
        component: () => import("@/views/h5/AccountJournal.vue"),
        meta: {
          title: (route: any) => `${route.params.accountName}`,
          platform: "h5",
          requiresAuth: true,
        },
      },
      {
        path: "accounts",
        name: "H5Accounts",
        component: () => import("@/views/h5/Accounts.vue"),
        meta: { title: "账户管理", platform: "h5", requiresAuth: true },
      },
      {
        path: "files",
        name: "H5Files",
        component: () => import("@/views/h5/Files.vue"),
        meta: { title: "文件管理", platform: "h5", requiresAuth: true },
      },
      {
        path: "recurring",
        name: "H5RecurringTransactions",
        component: () => import("@/views/h5/RecurringTransactions.vue"),
        meta: { title: "周期记账", platform: "h5", requiresAuth: true },
      },
      {
        path: "recurring/add",
        name: "H5AddRecurring",
        component: () => import("@/views/h5/AddRecurring.vue"),
        meta: { title: "新增周期记账", platform: "h5", requiresAuth: true },
      },
      {
        path: "recurring/:id",
        name: "H5RecurringDetail",
        component: () => import("@/views/h5/RecurringDetail.vue"),
        meta: { title: "周期记账详情", platform: "h5", requiresAuth: true },
      },
      {
        path: "recurring/edit/:id",
        name: "H5EditRecurring",
        component: () => import("@/views/h5/EditRecurring.vue"),
        meta: { title: "编辑周期记账", platform: "h5", requiresAuth: true },
      },
      {
        path: "settings",
        name: "H5Settings",
        component: () => import("@/views/h5/Settings.vue"),
        meta: { title: "设置", platform: "h5", requiresAuth: true },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    // 如果有保存的位置（比如通过浏览器前进后退），返回到保存的位置
    if (savedPosition) {
      return savedPosition;
    }
    // 对于新的路由导航，滚动到顶部
    return { top: 0, behavior: "smooth" };
  },
});

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();

  // 加载保存的token
  if (!authStore.isAuthenticated) {
    authStore.loadToken();
  }

  // 检查路由是否需要认证
  const requiresAuth = to.matched.some(
    (record) => record.meta.requiresAuth !== false
  );

  if (requiresAuth) {
    if (!authStore.isAuthenticated) {
      // 未登录，重定向到登录页
      next({
        path: "/login",
        query: { redirect: to.fullPath },
      });
      return;
    }

    // 优化：先检查是否有有效的会话缓存
    if (authStore.isValidSession()) {
      // 有效会话，直接放行
      next();
      return;
    }

    // 没有缓存的用户信息，需要验证token有效性
    const isValid = await authStore.checkAuth();
    if (!isValid) {
      // token无效，重定向到登录页
      next({
        path: "/login",
        query: { redirect: to.fullPath },
      });
      return;
    }
  } else if (to.path === "/login" && authStore.isAuthenticated) {
    // 已登录用户访问登录页，根据设备类型重定向到对应首页
    next(getDefaultRoute());
    return;
  }

  next();
});

export default router;
