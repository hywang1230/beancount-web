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
import { ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const showAbout = ref(false);
const version = ref("1.0.0");

const navigateTo = (path: string) => {
  router.push(path);
};
</script>

<style scoped>
.settings-page {
  padding: 16px;
  background-color: #f7f8fa;
  min-height: 100vh;
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
