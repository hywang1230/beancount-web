import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

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

// 动态加载平台特定样式
const loadPlatformStyles = async () => {
  const isMobile =
    /Mobile|Android|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(
      navigator.userAgent
    ) || window.innerWidth <= 768;

  if (isMobile) {
    // H5 端只加载 Vant 样式
    await import("vant/lib/index.css");
  } else {
    // PC 端加载 Element Plus 样式
    await import("element-plus/dist/index.css");
    await import("element-plus/theme-chalk/dark/css-vars.css");
  }
};

// 在应用挂载前加载样式
loadPlatformStyles().then(() => {
  app.mount("#app");
});

// 应用PWA样式优化
applyPWAStyles();
setupPWAEventListeners();
