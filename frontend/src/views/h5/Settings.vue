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
    </van-cell-group>

    <van-cell-group inset title="外观设置">
      <van-cell title="暗黑模式" icon="diamond-o" :border="false">
        <template #label>
          <span class="cell-desc">开启暗黑模式以保护眼睛</span>
        </template>
        <template #right-icon>
          <van-switch
            v-model="isDarkMode"
            @change="handleThemeChange"
            size="20px"
          />
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group inset title="应用信息">
      <van-cell
        title="版本信息"
        icon="info-o"
        :value="version"
        :border="false"
      />

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
      :show-cancel-button="false"
      confirm-button-text="确定"
    >
      <div class="about-content">
        <p>Beancount Web 是一个基于 Beancount 的记账应用</p>
        <p>支持复式记账，帮助您更好地管理个人财务</p>
        <p class="version-text">版本：{{ version }}</p>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { useThemeStore } from "@/stores/theme";
import { showToast } from "vant";
import { computed, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const themeStore = useThemeStore();
const showAbout = ref(false);
const version = ref("1.0.0");

// 暗黑模式状态
const isDarkMode = computed({
  get: () => themeStore.isDark,
  set: (value: boolean) => {
    themeStore.setTheme(value ? "dark" : "light");
  },
});

const navigateTo = (path: string) => {
  router.push(path);
};

const handleThemeChange = (value: boolean) => {
  const themeName = value ? "暗黑模式" : "浅色模式";
  showToast({
    message: `已切换到${themeName}`,
    duration: 1500,
    icon: value ? "moon-o" : "sun-o",
  });
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
  color: #969799;
  font-size: 12px;
  margin-top: 4px;
}

.about-content {
  padding: 16px;
  text-align: center;
  line-height: 1.6;
}

.about-content p {
  margin: 8px 0;
  color: #646566;
}

.version-text {
  margin-top: 16px;
  font-size: 12px;
  color: #969799;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  color: #646566;
  font-size: 14px;
  font-weight: normal;
}

:deep(.van-cell) {
  background-color: #fff;
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
</style>
