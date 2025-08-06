import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useThemeStore = defineStore("theme", () => {
  // 主题状态：'light' | 'dark'
  const theme = ref<"light" | "dark">("light");

  // 是否是暗黑模式
  const isDark = computed(() => theme.value === "dark");

  // 从本地存储加载主题设置
  const loadTheme = () => {
    const savedTheme = localStorage.getItem("beancount-theme");
    if (savedTheme && (savedTheme === "light" || savedTheme === "dark")) {
      theme.value = savedTheme;
    } else {
      // 检查系统偏好
      const prefersDark = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;
      theme.value = prefersDark ? "dark" : "light";
    }
    applyTheme();
  };

  // 设置主题
  const setTheme = (newTheme: "light" | "dark") => {
    theme.value = newTheme;
    localStorage.setItem("beancount-theme", newTheme);
    applyTheme();
  };

  // 切换主题
  const toggleTheme = () => {
    setTheme(theme.value === "light" ? "dark" : "light");
  };

  // 应用主题到文档
  const applyTheme = () => {
    const html = document.documentElement;

    // 移除之前的主题类
    html.classList.remove("light-theme", "dark-theme");

    // 添加新的主题类
    html.classList.add(`${theme.value}-theme`);

    // 设置主题属性，供CSS变量使用
    html.setAttribute("data-theme", theme.value);

    // 为移动端（H5）特别设置
    if (window.innerWidth <= 768) {
      html.classList.add("mobile-theme");
    }
  };

  // 监听系统主题变化
  const initSystemThemeListener = () => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", (e) => {
      // 只有在用户没有手动设置主题时才跟随系统
      const savedTheme = localStorage.getItem("beancount-theme");
      if (!savedTheme) {
        setTheme(e.matches ? "dark" : "light");
      }
    });
  };

  return {
    theme,
    isDark,
    loadTheme,
    setTheme,
    toggleTheme,
    applyTheme,
    initSystemThemeListener,
  };
});
