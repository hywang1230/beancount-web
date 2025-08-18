<template>
  <div class="sync-status-indicator" v-if="isConfigured">
    <van-icon
      :name="statusIcon"
      :color="statusColor"
      size="16"
      @click="handleClick"
    />
    <span class="status-text" @click="handleClick">{{ statusText }}</span>
  </div>
</template>

<script setup lang="ts">
import { syncAPI, SyncStatus, type SyncStatusResponse } from "@/api/sync";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

// 响应式数据
const syncStatus = ref<SyncStatusResponse | null>(null);
const isConfigured = ref(false);
const timer = ref<number | null>(null);

// 计算属性
const statusIcon = computed(() => {
  if (!syncStatus.value) return "clock-o";

  switch (syncStatus.value.status) {
    case SyncStatus.SUCCESS:
      return "success";
    case SyncStatus.SYNCING:
      return "loading";
    case SyncStatus.FAILED:
      return "close";
    case SyncStatus.CONFLICT:
      return "warning-o";
    default:
      return "clock-o";
  }
});

const statusColor = computed(() => {
  if (!syncStatus.value) return "#969799";

  switch (syncStatus.value.status) {
    case SyncStatus.SUCCESS:
      return "#07c160";
    case SyncStatus.SYNCING:
      return "#1989fa";
    case SyncStatus.FAILED:
      return "#ee0a24";
    case SyncStatus.CONFLICT:
      return "#ff976a";
    default:
      return "#969799";
  }
});

const statusText = computed(() => {
  if (!syncStatus.value) return "同步";

  switch (syncStatus.value.status) {
    case SyncStatus.SUCCESS:
      return syncStatus.value.pending_files.length > 0 ? "待同步" : "已同步";
    case SyncStatus.SYNCING:
      return "同步中";
    case SyncStatus.FAILED:
      return "同步失败";
    case SyncStatus.CONFLICT:
      return "有冲突";
    default:
      return "同步";
  }
});

// 方法
const loadSyncStatus = async () => {
  try {
    // 先检查是否配置了同步
    const config = await syncAPI.getSyncConfig();
    isConfigured.value = !!config;

    if (config) {
      const status = await syncAPI.getSyncStatus();
      syncStatus.value = status;
    }
  } catch (error) {
    // 没有配置同步或其他错误
    isConfigured.value = false;
    syncStatus.value = null;
  }
};

const handleClick = () => {
  router.push("/h5/sync");
};

// 定期更新状态
const startPolling = () => {
  timer.value = window.setInterval(() => {
    loadSyncStatus();
  }, 30000); // 每30秒更新一次
};

const stopPolling = () => {
  if (timer.value) {
    clearInterval(timer.value);
    timer.value = null;
  }
};

// 生命周期
onMounted(() => {
  loadSyncStatus();
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.sync-status-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  font-size: 12px;
  color: #646566;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sync-status-indicator:hover {
  background-color: rgba(255, 255, 255, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.status-text {
  white-space: nowrap;
}

.sync-status-indicator .van-icon {
  flex-shrink: 0;
}
</style>
