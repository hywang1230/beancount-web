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

// 主题管理
import { useThemeStore } from "./stores/theme";

const app = createApp(App);

app.use(createPinia());
app.use(router);

// 初始化主题
const themeStore = useThemeStore();
themeStore.loadTheme();
themeStore.initSystemThemeListener();

app.mount("#app");
