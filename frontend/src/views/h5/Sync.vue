<template>
  <div class="sync-page">
    <!-- 同步状态卡片 -->
    <div class="status-card">
      <van-cell-group inset>
        <van-cell title="同步状态" :value="statusText" :label="statusLabel">
          <template #icon>
            <van-icon
              :name="statusIcon"
              :color="statusColor"
              class="status-icon"
            />
          </template>
        </van-cell>

        <van-cell
          v-if="syncStatus?.last_sync"
          title="最后同步"
          :value="formatTime(syncStatus.last_sync)"
        />

        <van-cell
          v-if="
            syncStatus?.pending_files?.length &&
            syncStatus.pending_files.length > 0
          "
          title="待同步文件"
          :value="`${syncStatus.pending_files.length} 个文件`"
        />
      </van-cell-group>

      <!-- 同步进度 -->
      <div v-if="syncStatus?.status === 'syncing'" class="sync-progress">
        <van-progress
          :percentage="syncStatus.progress || 0"
          :show-pivot="false"
          stroke-width="6"
        />
        <div class="progress-text">
          {{ syncStatus.message || "正在同步..." }}
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <van-button
        v-if="!isConfigured"
        type="primary"
        block
        @click="showConfigDialog = true"
      >
        配置GitHub同步
      </van-button>

      <template v-else>
        <van-button
          type="primary"
          block
          :loading="syncing"
          @click="handleManualSync"
        >
          立即同步
        </van-button>

        <div class="button-row">
          <van-button size="small" @click="showConfigDialog = true">
            修改配置
          </van-button>

          <van-button size="small" @click="openHistoryDialog">
            同步历史
          </van-button>

          <van-button size="small" @click="showRestoreDialog = true">
            数据恢复
          </van-button>
        </div>
      </template>
    </div>

    <!-- 配置对话框 -->
    <van-dialog
      v-model:show="showConfigDialog"
      title="GitHub同步配置"
      show-cancel-button
      :before-close="handleConfigSubmit"
      class="config-dialog"
    >
      <div class="config-form">
        <!-- 同步说明 -->
        <div class="sync-info">
          <van-notice-bar
            left-icon="info-o"
            text="仅同步 .bean 和 .beancount 文件，其他文件类型将被忽略"
            color="var(--van-primary-color)"
            background="rgba(25, 137, 250, 0.1)"
            :scrollable="false"
            wrapable
            class="sync-notice"
          />
        </div>

        <van-form @submit="handleConfigSubmit">
          <van-field
            v-model="configForm.repository"
            name="repository"
            label="GitHub仓库"
            placeholder="username/repository-name"
            :rules="[{ required: true, message: '请输入GitHub仓库地址' }]"
          />

          <van-field
            v-model="configForm.token"
            name="token"
            type="password"
            label="访问令牌"
            placeholder="GitHub Personal Access Token"
            :rules="[{ required: true, message: '请输入GitHub访问令牌' }]"
          />

          <van-field
            v-model="configForm.branch"
            name="branch"
            label="目标分支"
            placeholder="main"
          />

          <van-field name="auto_sync" label="自动同步">
            <template #input>
              <van-switch v-model="configForm.auto_sync" />
            </template>
          </van-field>

          <van-field
            v-if="configForm.auto_sync"
            v-model="configForm.sync_interval"
            name="sync_interval"
            type="number"
            label="同步间隔(分钟)"
            placeholder="60"
          />

          <van-field
            name="conflict_resolution"
            label="冲突解决"
            is-link
            readonly
            :value="conflictResolutionText"
            @click="showConflictPicker = true"
          />
        </van-form>

        <div class="config-actions">
          <van-button
            size="small"
            type="default"
            @click="testConnection"
            :loading="testing"
          >
            测试连接
          </van-button>
        </div>
      </div>
    </van-dialog>

    <!-- 冲突解决策略选择器 -->
    <van-popup v-model:show="showConflictPicker" position="bottom">
      <van-picker
        :columns="conflictOptions"
        @confirm="onConflictConfirm"
        @cancel="showConflictPicker = false"
      />
    </van-popup>

    <!-- 同步历史对话框 -->
    <van-dialog
      v-model:show="showHistoryDialog"
      title="同步历史"
      width="90%"
      class="history-dialog"
    >
      <div class="history-list">
        <van-list
          v-model:loading="historyLoading"
          :finished="historyFinished"
          finished-text="没有更多了"
          @load="loadHistory"
        >
          <div
            v-for="item in historyList"
            :key="item.timestamp"
            class="history-item"
          >
            <div class="history-header">
              <span class="operation-type">{{
                getOperationTypeText(item.operation_type)
              }}</span>
              <span :class="['status', item.status]">{{
                getStatusText(item.status)
              }}</span>
            </div>
            <div class="history-content">
              <div class="files-count">{{ item.files_count }} 个文件</div>
              <div class="timestamp">{{ formatTime(item.timestamp) }}</div>
            </div>
            <div v-if="item.message" class="history-message">
              {{ item.message }}
            </div>
          </div>
        </van-list>
      </div>
    </van-dialog>

    <!-- 数据恢复对话框 -->
    <van-dialog
      v-model:show="showRestoreDialog"
      title="数据恢复"
      show-cancel-button
      :before-close="handleRestore"
      class="restore-dialog"
    >
      <div class="restore-form">
        <van-form @submit="handleRestore">
          <van-field
            name="restore_type"
            label="恢复方式"
            is-link
            readonly
            :value="restoreTypeText"
            @click="showRestoreTypePicker = true"
          />

          <van-field
            v-if="restoreForm.restore_type === 'commit'"
            v-model="restoreForm.commit_hash"
            name="commit_hash"
            label="提交哈希"
            placeholder="选择要恢复的提交"
            is-link
            readonly
            @click="showCommitsPicker = true"
          />

          <van-field name="force" label="强制覆盖">
            <template #input>
              <van-switch v-model="restoreForm.force" />
            </template>
          </van-field>
        </van-form>
      </div>
    </van-dialog>

    <!-- 恢复方式选择器 -->
    <van-popup v-model:show="showRestoreTypePicker" position="bottom">
      <van-picker
        :columns="restoreTypeOptions"
        @confirm="onRestoreTypeConfirm"
        @cancel="showRestoreTypePicker = false"
      />
    </van-popup>

    <!-- 提交选择器 -->
    <van-popup v-model:show="showCommitsPicker" position="bottom">
      <van-picker
        :columns="commitOptions"
        @confirm="onCommitConfirm"
        @cancel="showCommitsPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import {
  ConflictResolution,
  syncAPI,
  SyncStatus,
  type GitHubSyncConfig,
  type SyncHistoryItem,
  type SyncStatusResponse,
} from "@/api/sync";
import { showToast } from "vant";
import { computed, onMounted, reactive, ref } from "vue";

// 响应式数据
const syncStatus = ref<SyncStatusResponse | null>(null);
const syncConfig = ref<GitHubSyncConfig | null>(null);
const syncing = ref(false);
const testing = ref(false);

// 对话框显示状态
const showConfigDialog = ref(false);
const showHistoryDialog = ref(false);
const showRestoreDialog = ref(false);
const showConflictPicker = ref(false);
const showRestoreTypePicker = ref(false);
const showCommitsPicker = ref(false);

// 表单数据
const configForm = reactive({
  repository: "",
  token: "",
  branch: "main",
  auto_sync: true,
  sync_interval: 60,
  conflict_resolution: ConflictResolution.MANUAL,
});

const restoreForm = reactive({
  restore_type: "latest",
  commit_hash: "",
  force: false,
});

// 历史记录
const historyList = ref<SyncHistoryItem[]>([]);
const historyLoading = ref(false);
const historyFinished = ref(false);
const historyPage = ref(1);

// 提交列表
const commitsList = ref<any[]>([]);

// 计算属性
const isConfigured = computed(() => !!syncConfig.value);

const statusText = computed(() => {
  if (!syncStatus.value) return "未知";
  return getStatusText(syncStatus.value.status);
});

const statusLabel = computed(() => {
  if (!syncStatus.value) return "";
  if (syncStatus.value.pending_files.length > 0) {
    return `${syncStatus.value.pending_files.length} 个文件待同步`;
  }
  return "数据已同步";
});

const statusIcon = computed(() => {
  if (!syncStatus.value) return "question-o";
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
  if (!syncStatus.value) return "#999";
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

const conflictResolutionText = computed(() => {
  switch (configForm.conflict_resolution) {
    case ConflictResolution.MANUAL:
      return "手动解决";
    case ConflictResolution.AUTO_LOCAL:
      return "本地优先";
    case ConflictResolution.AUTO_REMOTE:
      return "远程优先";
    case ConflictResolution.SMART_MERGE:
      return "智能合并";
    default:
      return "手动解决";
  }
});

const restoreTypeText = computed(() => {
  switch (restoreForm.restore_type) {
    case "latest":
      return "最新版本";
    case "commit":
      return "指定提交";
    default:
      return "最新版本";
  }
});

// 选择器选项
const conflictOptions = [
  { text: "手动解决", value: ConflictResolution.MANUAL },
  { text: "本地优先", value: ConflictResolution.AUTO_LOCAL },
  { text: "远程优先", value: ConflictResolution.AUTO_REMOTE },
  { text: "智能合并", value: ConflictResolution.SMART_MERGE },
];

const restoreTypeOptions = [
  { text: "最新版本", value: "latest" },
  { text: "指定提交", value: "commit" },
];

const commitOptions = computed(() => {
  return commitsList.value.map((commit) => ({
    text: `${commit.message.substring(0, 30)}... (${commit.sha.substring(
      0,
      7
    )})`,
    value: commit.sha,
  }));
});

// 方法
const loadSyncStatus = async () => {
  try {
    syncStatus.value = await syncAPI.getSyncStatus();
  } catch (error) {
    console.error("获取同步状态失败:", error);
  }
};

const loadSyncConfig = async () => {
  try {
    syncConfig.value = await syncAPI.getSyncConfig();
    // 填充表单
    if (syncConfig.value) {
      configForm.repository = syncConfig.value.repository;
      configForm.branch = syncConfig.value.branch;
      configForm.auto_sync = syncConfig.value.auto_sync;
      configForm.sync_interval = syncConfig.value.sync_interval;
      configForm.conflict_resolution = syncConfig.value.conflict_resolution;
    }
  } catch (error) {
    console.error("获取同步配置失败:", error);
    syncConfig.value = null;
  }
};

const testConnection = async () => {
  if (!configForm.repository || !configForm.token) {
    showToast("请填写完整的仓库信息和访问令牌");
    return;
  }

  testing.value = true;
  try {
    const result = await syncAPI.testConnection();
    if (result.success) {
      showToast({
        type: "success",
        message: "连接成功",
      });
    } else {
      showToast({
        type: "fail",
        message: result.message,
      });
    }
  } catch (error: any) {
    showToast({
      type: "fail",
      message: error.message || "连接测试失败",
    });
  } finally {
    testing.value = false;
  }
};

const handleConfigSubmit = async (action: string) => {
  if (action !== "confirm") return true;

  try {
    const config = await syncAPI.configureSync({
      repository: configForm.repository,
      token: configForm.token,
      branch: configForm.branch,
      auto_sync: configForm.auto_sync,
      sync_interval: configForm.sync_interval * 60, // 转换为秒
      conflict_resolution: configForm.conflict_resolution,
    });

    syncConfig.value = config;
    showToast({
      type: "success",
      message: "配置保存成功",
    });

    // 重新加载状态
    await loadSyncStatus();
    return true;
  } catch (error: any) {
    showToast({
      type: "fail",
      message: error.message || "配置保存失败",
    });
    return false;
  }
};

const handleManualSync = async () => {
  syncing.value = true;
  try {
    const result = await syncAPI.manualSync();
    if (result.success) {
      showToast({
        type: "success",
        message: "同步完成",
      });
      await loadSyncStatus();
    } else {
      showToast({
        type: "fail",
        message: result.message,
      });
    }
  } catch (error: any) {
    showToast({
      type: "fail",
      message: error.message || "同步失败",
    });
  } finally {
    syncing.value = false;
  }
};

const openHistoryDialog = async () => {
  // 重置状态
  historyList.value = [];
  historyPage.value = 1;
  historyFinished.value = false;
  historyLoading.value = false;

  // 显示对话框
  showHistoryDialog.value = true;

  // 开始加载历史记录
  await loadHistory();
};

const loadHistory = async () => {
  if (historyLoading.value || historyFinished.value) return;

  historyLoading.value = true;
  try {
    const result = await syncAPI.getSyncHistory(historyPage.value, 20);

    if (result.history.length === 0) {
      historyFinished.value = true;
    } else {
      historyList.value.push(...result.history);
      historyPage.value++;

      // 如果返回的记录数少于请求的数量，说明已经到底了
      if (result.history.length < 20) {
        historyFinished.value = true;
      }
    }
  } catch (error) {
    console.error("加载历史记录失败:", error);
    showToast({
      type: "fail",
      message: "加载历史记录失败",
    });
    // 发生错误时也要停止加载
    historyFinished.value = true;
  } finally {
    historyLoading.value = false;
  }
};

const loadCommits = async () => {
  try {
    const result = await syncAPI.getRecentCommits(20);
    commitsList.value = result.commits;
  } catch (error) {
    console.error("加载提交记录失败:", error);
  }
};

const handleRestore = async (action: string) => {
  if (action !== "confirm") return true;

  try {
    const params: any = {
      force: restoreForm.force,
    };

    if (restoreForm.restore_type === "commit" && restoreForm.commit_hash) {
      params.commit_hash = restoreForm.commit_hash;
    }

    const result = await syncAPI.restoreFromGitHub(params);

    if (result.success) {
      showToast({
        type: "success",
        message: "数据恢复完成",
      });
      await loadSyncStatus();
    } else {
      showToast({
        type: "fail",
        message: result.message,
      });
    }
    return true;
  } catch (error: any) {
    showToast({
      type: "fail",
      message: error.message || "数据恢复失败",
    });
    return false;
  }
};

// 选择器事件处理
const onConflictConfirm = ({ selectedValues }: any) => {
  configForm.conflict_resolution = selectedValues[0];
  showConflictPicker.value = false;
};

const onRestoreTypeConfirm = ({ selectedValues }: any) => {
  restoreForm.restore_type = selectedValues[0];
  showRestoreTypePicker.value = false;

  if (restoreForm.restore_type === "commit") {
    loadCommits();
  }
};

const onCommitConfirm = ({ selectedValues }: any) => {
  restoreForm.commit_hash = selectedValues[0];
  showCommitsPicker.value = false;
};

// 工具函数
const getStatusText = (status: SyncStatus) => {
  switch (status) {
    case SyncStatus.IDLE:
      return "空闲";
    case SyncStatus.SYNCING:
      return "同步中";
    case SyncStatus.SUCCESS:
      return "成功";
    case SyncStatus.FAILED:
      return "失败";
    case SyncStatus.CONFLICT:
      return "冲突";
    default:
      return "未知";
  }
};

const getOperationTypeText = (type: string) => {
  switch (type) {
    case "manual_sync":
      return "手动同步";
    case "auto_sync":
      return "自动同步";
    case "restore":
      return "数据恢复";
    case "conflict_resolve":
      return "冲突解决";
    default:
      return type;
  }
};

const formatTime = (timeStr: string) => {
  const date = new Date(timeStr);
  return date.toLocaleString("zh-CN");
};

// 生命周期
onMounted(async () => {
  await Promise.all([loadSyncConfig(), loadSyncStatus()]);
});
</script>

<style scoped>
.sync-page {
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.status-card {
  margin: 8px 0;
}

.status-icon {
  margin-right: 8px;
}

.sync-progress {
  padding: 16px;
  background-color: var(--van-background-2);
  transition: background-color 0.3s ease;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
  color: var(--van-text-color-3);
  transition: color 0.3s ease;
}

.action-buttons {
  margin: 8px 16px;
}

.button-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.button-row .van-button {
  flex: 1;
}

.config-dialog .config-form {
  padding: 16px;
  background-color: var(--van-background);
  transition: background-color 0.3s ease;
}

.sync-info {
  margin-bottom: 16px;
}

.config-actions {
  margin-top: 16px;
  text-align: center;
}

.history-dialog .history-list {
  max-height: 400px;
  overflow-y: auto;
  background-color: var(--van-background);
  transition: background-color 0.3s ease;
}

.history-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--van-border-color);
  background-color: var(--van-background-2);
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.operation-type {
  font-weight: 500;
  color: var(--van-text-color);
  transition: color 0.3s ease;
}

.status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  color: white;
}

.status.success {
  background-color: var(--van-success-color);
}

.status.failed {
  background-color: var(--van-danger-color);
}

.status.syncing {
  background-color: var(--van-primary-color);
}

.history-content {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--van-text-color-3);
  transition: color 0.3s ease;
}

.history-message {
  margin-top: 4px;
  font-size: 12px;
  color: var(--van-text-color-2);
  transition: color 0.3s ease;
}

.restore-dialog .restore-form {
  padding: 16px;
  background-color: var(--van-background);
  transition: background-color 0.3s ease;
}

/* 暗黑模式特定调整 */
.van-theme-dark .config-dialog .config-form {
  background-color: var(--van-background-2);
}

.van-theme-dark .history-dialog .history-list {
  background-color: var(--van-background-2);
}

.van-theme-dark .restore-dialog .restore-form {
  background-color: var(--van-background-2);
}

/* 确保对话框在暗黑模式下正确显示 */
.van-theme-dark .van-dialog {
  background-color: var(--van-background-2);
  color: var(--van-text-color);
}

.van-theme-dark .van-popup {
  background-color: var(--van-background-2);
  color: var(--van-text-color);
}

/* 针对Notice Bar的暗黑模式优化 */
.sync-notice {
  background: rgba(25, 137, 250, 0.1) !important;
  color: var(--van-primary-color) !important;
  border: 1px solid rgba(25, 137, 250, 0.2);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.van-theme-dark .sync-notice {
  background: rgba(25, 137, 250, 0.15) !important;
  color: #409eff !important;
  border-color: rgba(25, 137, 250, 0.3);
}

/* Cell 组件暗黑模式优化 */
.van-theme-dark .van-cell-group {
  background-color: var(--van-background-2);
}

.van-theme-dark .van-cell {
  background-color: var(--van-background-2);
  color: var(--van-text-color);
  border-bottom-color: var(--van-border-color);
}

.van-theme-dark .van-field {
  background-color: var(--van-background-2);
  color: var(--van-text-color);
}

.van-theme-dark .van-field__label {
  color: var(--van-text-color-2);
}

.van-theme-dark .van-field__value {
  color: var(--van-text-color);
}

/* Picker 组件暗黑模式优化 */
.van-theme-dark .van-picker {
  background-color: var(--van-background-2);
}

.van-theme-dark .van-picker-column__item {
  color: var(--van-text-color);
}

/* Form 组件暗黑模式优化 */
.van-theme-dark .van-form {
  background-color: var(--van-background-2);
}

/* Button 组件在暗黑模式下的优化 */
.van-theme-dark .van-button--default {
  background-color: var(--van-background-3);
  color: var(--van-text-color);
  border-color: var(--van-border-color);
}

.van-theme-dark .van-button--default:active {
  background-color: var(--van-active-color);
}

/* List 组件暗黑模式优化 */
.van-theme-dark .van-list {
  background-color: var(--van-background);
}

/* Progress 组件暗黑模式优化 */
.van-theme-dark .van-progress {
  background-color: var(--van-background-3);
}

.van-theme-dark .van-progress__pivot {
  background-color: var(--van-primary-color);
  color: white;
}
</style>
