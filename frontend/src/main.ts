import { createPinia } from "pinia";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

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

app.use(createPinia());
app.use(router);

app.mount("#app");

// 应用PWA样式优化
applyPWAStyles();
setupPWAEventListeners();
