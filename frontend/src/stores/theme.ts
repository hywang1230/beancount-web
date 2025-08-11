import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

export type ThemeSetting = "light" | "dark" | "system";

export const useThemeStore = defineStore("theme", () => {
  // 用户的主题设置：'light' | 'dark' | 'system'
  const themeSetting = ref<ThemeSetting>("system");

  // 当前应用的实际主题：'light' | 'dark'
  const currentTheme = ref<"light" | "dark">("light");

  // 是否是暗黑模式
  const isDark = computed(() => currentTheme.value === "dark");

  // 更新当前主题
  const updateTheme = () => {
    let newTheme: "light" | "dark";
    if (themeSetting.value === "system") {
      newTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    } else {
      newTheme = themeSetting.value;
    }
    currentTheme.value = newTheme;
  };

  // 应用主题到文档
  const applyTheme = () => {
    const html = document.documentElement;

    // 移除之前的主题类
    html.classList.remove("light-theme", "dark-theme", "van-theme-dark");

    // 添加新的主题类
    html.classList.add(`${currentTheme.value}-theme`);

    // 设置主题属性，供CSS变量使用
    html.setAttribute("data-theme", currentTheme.value);

    // 为 Vant 组件添加暗黑模式类
    if (currentTheme.value === "dark") {
      html.classList.add("van-theme-dark");
    }

    // 为移动端（H5）特别设置
    if (window.innerWidth <= 768) {
      html.classList.add("mobile-theme");
    }
  };

  // 从本地存储加载主题设置
  const loadThemeSetting = () => {
    const savedThemeSetting = localStorage.getItem(
      "beancount-theme-setting"
    ) as ThemeSetting | null;
    if (savedThemeSetting) {
      themeSetting.value = savedThemeSetting;
    }
    updateTheme();
    applyTheme();
  };

  // 设置用户的主题偏好
  const setThemeSetting = (newSetting: ThemeSetting) => {
    themeSetting.value = newSetting;
    localStorage.setItem("beancount-theme-setting", newSetting);
    updateTheme();
    // applyTheme 会在 currentTheme 变化时自动调用
  };

  // 监听系统主题变化
  const initSystemThemeListener = () => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", () => {
      if (themeSetting.value === "system") {
        updateTheme();
      }
    });
  };

  // 监听 currentTheme 的变化并应用
  watch(currentTheme, applyTheme);

  return {
    themeSetting,
    currentTheme,
    isDark,
    loadThemeSetting,
    setThemeSetting,
    initSystemThemeListener,
  };
});
