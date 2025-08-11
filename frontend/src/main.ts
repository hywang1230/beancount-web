import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

// Vant 样式 - 手动导入以支持暗黑模式
import "vant/lib/index.css";

// 全局样式
import "./style/global.css";
import "./style/theme.css";

// PWA工具函数
import { applyPWAStyles, setupPWAEventListeners } from "./utils/pwa";

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

// 初始化认证状态
const authStore = useAuthStore();
authStore.loadToken();
// 如果有token但没有用户信息，尝试获取用户信息
if (authStore.isAuthenticated && !authStore.user) {
  authStore.fetchUserInfo().catch(() => {
    // 静默处理错误，路由守卫会处理认证失败的情况
  });
}

// 直接挂载应用，样式通过vite插件自动处理
app.mount("#app");

// 应用PWA样式优化
applyPWAStyles();
setupPWAEventListeners();
