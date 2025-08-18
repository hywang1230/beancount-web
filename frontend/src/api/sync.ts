import api from "@/utils/api";

// 同步状态枚举
export enum SyncStatus {
  IDLE = "idle",
  SYNCING = "syncing",
  SUCCESS = "success",
  FAILED = "failed",
  CONFLICT = "conflict",
}

// 冲突解决策略
export enum ConflictResolution {
  MANUAL = "manual",
  AUTO_LOCAL = "auto_local",
  AUTO_REMOTE = "auto_remote",
  SMART_MERGE = "smart_merge",
}

// 数据类型定义
export interface GitHubSyncConfig {
  repository: string;
  branch: string;
  auto_sync: boolean;
  sync_interval: number;
  include_files: string[];
  exclude_files: string[];
  conflict_resolution: ConflictResolution;
  last_sync?: string;
  status: SyncStatus;
}

export interface GitHubSyncConfigRequest {
  repository: string;
  token: string;
  branch?: string;
  auto_sync?: boolean;
  sync_interval?: number;
  include_files?: string[];
  exclude_files?: string[];
  conflict_resolution?: ConflictResolution;
}

export interface FileChangeInfo {
  file_path: string;
  file_type: "added" | "modified" | "deleted";
  size?: number;
  hash?: string;
  last_modified?: string;
}

export interface SyncStatusResponse {
  status: SyncStatus;
  last_sync?: string;
  next_sync?: string;
  pending_files: FileChangeInfo[];
  current_operation?: any;
  progress?: number;
  message?: string;
  total_files: number;
  synced_files: number;
}

export interface SyncHistoryItem {
  timestamp: string;
  operation_type: "manual_sync" | "auto_sync" | "restore" | "conflict_resolve";
  status: SyncStatus;
  files_count: number;
  message?: string;
  duration?: number;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  repository_info?: {
    name: string;
    full_name: string;
    private: boolean;
    default_branch: string;
  };
}

export interface ManualSyncRequest {
  force?: boolean;
  files?: string[];
}

export interface RestoreRequest {
  timestamp?: string;
  commit_hash?: string;
  force?: boolean;
}

// API 接口
export const syncAPI = {
  // 配置同步
  configureSync: (config: GitHubSyncConfigRequest): Promise<GitHubSyncConfig> =>
    api.post("/sync/config", config),

  // 获取同步配置
  getSyncConfig: (): Promise<GitHubSyncConfig> => api.get("/sync/config"),

  // 测试GitHub连接
  testConnection: (): Promise<TestConnectionResponse> =>
    api.post("/sync/test-connection"),

  // 获取同步状态
  getSyncStatus: (): Promise<SyncStatusResponse> => api.get("/sync/status"),

  // 手动同步
  manualSync: (
    params?: ManualSyncRequest
  ): Promise<{ success: boolean; message: string }> =>
    api.post("/sync/manual", params || {}),

  // 从GitHub恢复数据
  restoreFromGitHub: (
    params?: RestoreRequest
  ): Promise<{ success: boolean; message: string }> =>
    api.post("/sync/restore", params || {}),

  // 获取同步历史
  getSyncHistory: (
    page = 1,
    pageSize = 20
  ): Promise<{
    history: SyncHistoryItem[];
    total_count: number;
    page: number;
    page_size: number;
  }> => api.get("/sync/history", { params: { page, page_size: pageSize } }),

  // 删除同步配置
  removeSyncConfig: (): Promise<{ success: boolean; message: string }> =>
    api.delete("/sync/config"),

  // 暂停自动同步
  pauseAutoSync: (): Promise<{ success: boolean; message: string }> =>
    api.post("/sync/pause"),

  // 恢复自动同步
  resumeAutoSync: (): Promise<{ success: boolean; message: string }> =>
    api.post("/sync/resume"),

  // 获取仓库分支列表
  getRepositoryBranches: (): Promise<{
    branches: string[];
    default_branch: string;
  }> => api.get("/sync/branches"),

  // 获取最近提交
  getRecentCommits: (
    limit = 10
  ): Promise<{
    commits: Array<{
      sha: string;
      message: string;
      author: string;
      date: string;
      url: string;
    }>;
  }> => api.get("/sync/commits", { params: { limit } }),
};
