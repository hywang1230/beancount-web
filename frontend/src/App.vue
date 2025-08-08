<template>
  <div id="app">
    <!-- 统一使用移动端UI组件 -->
    <van-config-provider :locale="zhCn">
      <router-view />
    </van-config-provider>

    <!-- PWA 更新提示 -->
    <PWAUpdatePrompt />
  </div>
</template>

<script setup lang="ts">
import PWAUpdatePrompt from "@/components/PWAUpdatePrompt.vue";
import { useThemeStore } from "@/stores/theme";
import zhCn from "vant/es/locale/lang/zh-CN";
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
// VanConfigProvider 通过自动导入配置自动引入

const router = useRouter();
const route = useRoute();
const themeStore = useThemeStore();

onMounted(() => {
  // 初始化主题
  themeStore.loadThemeSetting();
  themeStore.initSystemThemeListener();

  // 仅处理根路径重定向到H5页面
  if (route.path === "/") {
    router.replace("/h5/dashboard");
  }
});
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
}
</style>
