<template>
  <div class="settings-page">
    <van-cell-group inset>
      <van-cell
        title="周期记账"
        icon="replay"
        is-link
        @click="navigateTo('/h5/recurring')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">管理周期性收支记录</span>
        </template>
      </van-cell>

      <van-cell
        title="账户管理"
        icon="manager-o"
        is-link
        @click="navigateTo('/h5/accounts')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">管理收支账户信息</span>
        </template>
      </van-cell>

      <van-cell
        title="文件管理"
        icon="balance-list-o"
        is-link
        @click="navigateTo('/h5/files')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">查看和验证账本文件</span>
        </template>
      </van-cell>

      <van-cell
        title="数据同步"
        icon="circle"
        is-link
        @click="navigateTo('/h5/sync')"
        :border="false"
      >
        <template #label>
          <span class="cell-desc">同步账本到GitHub仓库</span>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="外观设置">
      <van-cell title="主题模式" icon="diamond-o" :border="false">
        <template #label>
          <van-radio-group
            v-model="themeSetting"
            @change="handleThemeChange"
            direction="horizontal"
            class="theme-radio-group"
          >
            <van-radio name="light">亮色</van-radio>
            <van-radio name="dark">暗色</van-radio>
            <van-radio name="system">跟随系统</van-radio>
          </van-radio-group>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="账户管理">
      <van-cell
        title="登出"
        icon="sign-out"
        is-link
        :border="false"
        @click="handleLogout"
        class="logout-cell"
      />
    </van-cell-group>

    <van-cell-group inset title="应用信息">
      <van-cell title="版本信息" icon="info-o" value="1.0.0" :border="false" />

      <van-cell
        title="关于我们"
        icon="question-o"
        is-link
        :border="false"
        @click="showAbout = true"
      />
    </van-cell-group>

    <!-- 关于弹窗 -->
    <van-dialog
      v-model:show="showAbout"
      title="关于 Beancount Web"
      message="Beancount Web 是一个基于 Beancount 的记账应用，支持复式记账，帮助您更好地管理个人财务。"
      :show-cancel-button="false"
      confirm-button-text="确定"
    />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useThemeStore, type ThemeSetting } from "@/stores/theme";
import { showConfirmDialog, showToast } from "vant";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const showAbout = ref(false);

// 主题设置
const themeSetting = computed({
  get: () => themeStore.themeSetting,
  set: (value: ThemeSetting) => {
    themeStore.setThemeSetting(value);
  },
});

const navigateTo = (path: string) => {
  router.push(path);
};

const handleThemeChange = (value: ThemeSetting) => {
  const themeNames = {
    light: "亮色模式",
    dark: "暗黑模式",
    system: "跟随系统",
  };
  showToast({
    message: `已切换到${themeNames[value]}`,
    duration: 1500,
  });
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
    showToast("登出成功");
    router.push("/login");
  } catch (error: any) {
    if (error !== "cancel") {
      // console.error("登出失败:", error);
      showToast("登出失败");
    }
  }
};
</script>

<style scoped>
.settings-page {
  padding: 16px;
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.cell-desc {
  color: var(--van-text-color-3);
  font-size: 12px;
  margin-top: 4px;
}

.theme-radio-group {
  margin-top: 8px;
  gap: 16px;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  color: var(--van-text-color-2);
  font-size: 14px;
  font-weight: normal;
}

:deep(.van-cell) {
  background-color: var(--van-background-2);
  padding: 16px;
}

:deep(.van-cell:last-child::after) {
  display: none;
}

:deep(.van-cell-group--inset) {
  margin: 16px 0;
  border-radius: 8px;
  overflow: hidden;
}

.logout-cell {
  color: var(--van-danger-color);
}
</style>
