<template>
  <van-overlay :show="showUpdatePrompt" z-index="9999">
    <div class="pwa-update-prompt">
      <div class="prompt-content">
        <van-icon name="info-o" size="40" color="#409EFF" />
        <h3>发现新版本</h3>
        <p>有新的版本可用，是否立即更新？</p>
        <div class="button-group">
          <van-button size="small" @click="dismissUpdate">稍后提醒</van-button>
          <van-button type="primary" size="small" @click="acceptUpdate"
            >立即更新</van-button
          >
        </div>
      </div>
    </div>
  </van-overlay>

  <van-notify
    v-model:show="showOfflineReady"
    type="success"
    message="应用已缓存，可离线使用"
    duration="3000"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

const showUpdatePrompt = ref(false);
const showOfflineReady = ref(false);
let updateSW: ((reloadPage?: boolean) => Promise<void>) | null = null;

const acceptUpdate = async () => {
  showUpdatePrompt.value = false;
  if (updateSW) {
    await updateSW(true);
  }
};

const dismissUpdate = () => {
  showUpdatePrompt.value = false;
};

onMounted(async () => {
  try {
    const { registerSW } = await import("virtual:pwa-register");

    updateSW = registerSW({
      onNeedRefresh() {
        showUpdatePrompt.value = true;
      },
      onOfflineReady() {
        showOfflineReady.value = true;
      },
      onRegistered(r: ServiceWorkerRegistration | undefined) {
        console.log("Service Worker 注册成功", r);
      },
      onRegisterError(error: any) {
        console.error("Service Worker 注册失败", error);
      },
    });
  } catch (error) {
    console.warn("PWA 功能不可用", error);
  }
});
</script>

<style scoped>
.pwa-update-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.prompt-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin: 16px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 320px;
}

.prompt-content h3 {
  margin: 16px 0 8px;
  color: #333;
  font-size: 18px;
  font-weight: 600;
}

.prompt-content p {
  margin: 0 0 24px;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.button-group .van-button {
  flex: 1;
}
</style>
