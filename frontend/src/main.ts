import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

// Element Plus 样式
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";

// Vant 样式
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

app.mount("#app");

// 应用PWA样式优化
applyPWAStyles();
setupPWAEventListeners();
