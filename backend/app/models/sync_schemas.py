from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum

class SyncStatus(str, Enum):
    """同步状态枚举"""
    IDLE = "idle"  # 空闲
    SYNCING = "syncing"  # 同步中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CONFLICT = "conflict"  # 冲突

class ConflictResolution(str, Enum):
    """冲突解决策略"""
    MANUAL = "manual"  # 手动解决
    AUTO_LOCAL = "auto_local"  # 自动本地优先
    AUTO_REMOTE = "auto_remote"  # 自动远程优先
    SMART_MERGE = "smart_merge"  # 智能合并

class GitHubSyncConfig(BaseModel):
    """GitHub同步配置"""
    repository: str = Field(..., description="GitHub仓库地址 (username/repo)")
    token: str = Field(..., description="GitHub Personal Access Token")
    branch: str = Field(default="main", description="目标分支")
    auto_sync: bool = Field(default=True, description="是否启用自动同步")
    sync_interval: int = Field(default=3600, description="同步间隔(秒)")
    include_files: List[str] = Field(default=["*.bean", "*.beancount"], description="包含的文件模式")
    exclude_files: List[str] = Field(default=["*.tmp", "*.log"], description="排除的文件模式")
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.MANUAL, description="冲突解决策略")

class GitHubSyncConfigRequest(BaseModel):
    """GitHub同步配置请求"""
    repository: str = Field(..., description="GitHub仓库地址")
    token: str = Field(..., description="GitHub Personal Access Token")
    branch: str = Field(default="main", description="目标分支")
    auto_sync: bool = Field(default=True, description="是否启用自动同步")
    sync_interval: int = Field(default=3600, description="同步间隔(秒)")
    include_files: List[str] = Field(default=["*.bean", "*.beancount"], description="包含的文件模式")
    exclude_files: List[str] = Field(default=["*.tmp", "*.log"], description="排除的文件模式")
    conflict_resolution: ConflictResolution = Field(default=ConflictResolution.MANUAL, description="冲突解决策略")

class GitHubSyncConfigResponse(BaseModel):
    """GitHub同步配置响应"""
    repository: str
    branch: str
    auto_sync: bool
    sync_interval: int
    include_files: List[str]
    exclude_files: List[str]
    conflict_resolution: ConflictResolution
    last_sync: Optional[datetime] = None
    status: SyncStatus

class FileChangeInfo(BaseModel):
    """文件变更信息"""
    file_path: str
    file_type: Literal["added", "modified", "deleted"]
    size: Optional[int] = None
    hash: Optional[str] = None
    last_modified: Optional[datetime] = None

class SyncOperation(BaseModel):
    """同步操作记录"""
    operation_id: str
    operation_type: Literal["upload", "download", "conflict"]
    file_path: str
    timestamp: datetime
    status: SyncStatus
    message: Optional[str] = None
    conflict_resolution: Optional[ConflictResolution] = None

class SyncStatusResponse(BaseModel):
    """同步状态响应"""
    status: SyncStatus
    last_sync: Optional[datetime] = None
    next_sync: Optional[datetime] = None
    pending_files: List[FileChangeInfo] = []
    current_operation: Optional[SyncOperation] = None
    progress: Optional[int] = Field(None, ge=0, le=100, description="同步进度百分比")
    message: Optional[str] = None
    total_files: int = 0
    synced_files: int = 0

class SyncHistoryItem(BaseModel):
    """同步历史项"""
    timestamp: datetime
    operation_type: Literal["manual_sync", "auto_sync", "restore", "conflict_resolve"]
    status: SyncStatus
    files_count: int
    message: Optional[str] = None
    duration: Optional[float] = None  # 同步耗时(秒)

class SyncHistoryResponse(BaseModel):
    """同步历史响应"""
    history: List[SyncHistoryItem]
    total_count: int
    page: int
    page_size: int

class ManualSyncRequest(BaseModel):
    """手动同步请求"""
    force: bool = Field(default=False, description="是否强制同步")
    files: Optional[List[str]] = Field(None, description="指定同步的文件")

class RestoreRequest(BaseModel):
    """数据恢复请求"""
    timestamp: Optional[datetime] = Field(None, description="恢复到指定时间点")
    commit_hash: Optional[str] = Field(None, description="恢复到指定提交")
    force: bool = Field(default=False, description="是否强制覆盖本地文件")

class ConflictFile(BaseModel):
    """冲突文件信息"""
    file_path: str
    local_hash: str
    remote_hash: str
    local_modified: datetime
    remote_modified: datetime
    size_diff: int  # 大小差异

class ConflictResolutionRequest(BaseModel):
    """冲突解决请求"""
    file_path: str
    resolution: ConflictResolution
    custom_content: Optional[str] = Field(None, description="自定义内容(当选择手动解决时)")

class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    success: bool
    message: str
    repository_info: Optional[Dict] = None

class SyncMetrics(BaseModel):
    """同步指标"""
    total_syncs: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    last_sync_duration: Optional[float] = None
    average_sync_duration: Optional[float] = None
    data_synced_mb: float = 0.0
    conflicts_resolved: int = 0
