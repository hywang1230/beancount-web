import os
import json
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, TYPE_CHECKING
import asyncio
import aiofiles
from cryptography.fernet import Fernet

from github import Github, GithubException
from watchdog.events import FileSystemEventHandler

if TYPE_CHECKING:
    from watchdog.observers import Observer

from app.core.config import settings
from app.models.sync_schemas import (
    GitHubSyncConfig, SyncStatus, ConflictResolution, FileChangeInfo,
    SyncOperation, SyncStatusResponse, SyncHistoryItem, ConflictFile
)


class FileWatcher(FileSystemEventHandler):
    """文件系统监控器"""
    
    def __init__(self, sync_service):
        self.sync_service = sync_service
        self.last_change_time = {}
        self.debounce_time = 2  # 防抖时间(秒)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        # 只监控data目录下的相关文件
        if not self._should_sync_file(file_path):
            return
        
        current_time = datetime.now()
        last_time = self.last_change_time.get(str(file_path))
        
        # 防抖处理
        if last_time and (current_time - last_time).seconds < self.debounce_time:
            return
        
        self.last_change_time[str(file_path)] = current_time
        
        # 异步触发同步检查 - 使用线程安全的方式
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.sync_service._check_auto_sync())
        except RuntimeError:
            # 如果没有运行中的事件循环，使用新的事件循环
            def run_sync_check():
                asyncio.run(self.sync_service._check_auto_sync())
            
            import threading
            thread = threading.Thread(target=run_sync_check)
            thread.daemon = True
            thread.start()
    
    def _should_sync_file(self, file_path: Path) -> bool:
        """检查文件是否应该被同步 - 只监控 beancount 文件"""
        try:
            # 首先检查文件扩展名
            file_path_str = str(file_path).lower()
            if not (file_path_str.endswith('.bean') or file_path_str.endswith('.beancount')):
                return False
            
            # 相对于data目录的路径
            rel_path = file_path.relative_to(settings.data_dir)
            return self.sync_service._match_patterns(str(rel_path))
        except ValueError:
            return False


class GitHubSyncService:
    """GitHub同步服务"""
    
    def __init__(self):
        self.data_dir = settings.data_dir
        self.config_file = self.data_dir / ".sync_config.json"
        self.history_file = self.data_dir / ".sync_history.json"
        self.status_file = self.data_dir / ".sync_status.json"
        
        self._config: Optional[GitHubSyncConfig] = None
        self._github_client: Optional[Github] = None
        self._current_status = SyncStatus.IDLE
        self._current_operation: Optional[SyncOperation] = None
        self._file_watcher = None  # Optional[Observer]
        
        # 加密密钥(在生产环境中应该从环境变量读取)
        self._encryption_key = self._get_or_create_encryption_key()
        
        # 标记是否已初始化
        self._initialized = False
    
    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self._load_config()
            self._initialized = True
    
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        key_file = self.data_dir / ".encryption_key"
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            return key
    
    def _encrypt_token(self, token: str) -> str:
        """加密GitHub token"""
        fernet = Fernet(self._encryption_key)
        return fernet.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """解密GitHub token"""
        fernet = Fernet(self._encryption_key)
        return fernet.decrypt(encrypted_token.encode()).decode()
    
    async def _load_config(self):
        """加载同步配置"""
        try:
            if self.config_file.exists():
                async with aiofiles.open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.loads(await f.read())
                
                # 解密token
                if 'token' in config_data:
                    config_data['token'] = self._decrypt_token(config_data['token'])
                
                self._config = GitHubSyncConfig(**config_data)
                self._init_github_client()
                
                # 启动文件监控
                if self._config.auto_sync:
                    await self._start_file_watcher()
        except Exception as e:
            print(f"加载同步配置失败: {e}")
    
    async def _save_config(self):
        """保存同步配置"""
        if not self._config:
            return
        
        config_data = self._config.model_dump()
        # 加密token
        config_data['token'] = self._encrypt_token(config_data['token'])
        
        async with aiofiles.open(self.config_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(config_data, ensure_ascii=False, indent=2))
    
    def _init_github_client(self):
        """初始化GitHub客户端"""
        if self._config and self._config.token:
            self._github_client = Github(self._config.token)
    
    async def _start_file_watcher(self):
        """启动文件监控"""
        if self._file_watcher:
            self._file_watcher.stop()
        
        from watchdog.observers import Observer
        self._file_watcher = Observer()
        event_handler = FileWatcher(self)
        self._file_watcher.schedule(event_handler, str(self.data_dir), recursive=True)
        self._file_watcher.start()
    
    async def _stop_file_watcher(self):
        """停止文件监控"""
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher.join()
            self._file_watcher = None
    
    def _match_patterns(self, file_path: str) -> bool:
        """检查文件是否匹配同步模式 - 只同步 beancount 文件"""
        if not file_path:
            return False
        
        # 直接检查文件扩展名，只同步 .bean 和 .beancount 文件
        file_path_lower = file_path.lower()
        if not (file_path_lower.endswith('.bean') or file_path_lower.endswith('.beancount')):
            return False
        
        # 如果有配置，则额外检查排除模式
        if self._config:
            import fnmatch
            for pattern in self._config.exclude_files:
                if fnmatch.fnmatch(file_path, pattern):
                    return False
        
        return True
    
    async def configure_sync(self, config_request: Dict) -> GitHubSyncConfig:
        """配置GitHub同步"""
        await self._ensure_initialized()
        try:
            # 创建配置对象
            self._config = GitHubSyncConfig(**config_request)
            
            # 测试GitHub连接
            self._init_github_client()
            await self._test_github_connection()
            
            # 保存配置
            await self._save_config()
            
            # 重新启动文件监控
            if self._config.auto_sync:
                await self._start_file_watcher()
            else:
                await self._stop_file_watcher()
            
            return self._config
            
        except Exception as e:
            raise Exception(f"配置同步失败: {str(e)}")
    
    async def _test_github_connection(self):
        """测试GitHub连接"""
        if not self._github_client:
            raise Exception("GitHub客户端未初始化")
        
        try:
            repo = self._github_client.get_repo(self._config.repository)
            # 尝试获取仓库信息来验证权限
            repo.get_contents("")
        except GithubException as e:
            if e.status == 404:
                raise Exception("仓库不存在或没有访问权限")
            elif e.status == 401:
                raise Exception("GitHub token无效")
            else:
                raise Exception(f"GitHub连接失败: {e.data.get('message', str(e))}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试GitHub连接"""
        try:
            await self._test_github_connection()
            
            repo = self._github_client.get_repo(self._config.repository)
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "private": repo.private,
                "default_branch": repo.default_branch
            }
            
            return {
                "success": True,
                "message": "连接成功",
                "repository_info": repo_info
            }
        except Exception as e:
            return {
                "success": False,
                "message": str(e),
                "repository_info": None
            }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def _get_changed_files(self) -> List[FileChangeInfo]:
        """获取变更的文件列表 - 只检查 beancount 文件"""
        changed_files = []
        
        # 使用更高效的方式，直接搜索 .bean 和 .beancount 文件
        bean_patterns = ["*.bean", "*.beancount"]
        
        for pattern in bean_patterns:
            for file_path in self.data_dir.rglob(pattern):
                if file_path.is_file():
                    rel_path = file_path.relative_to(self.data_dir)
                    
                    # 额外检查排除模式
                    if self._match_patterns(str(rel_path)):
                        file_stat = file_path.stat()
                        file_hash = self._calculate_file_hash(file_path)
                        
                        changed_files.append(FileChangeInfo(
                            file_path=str(rel_path),
                            file_type="modified",  # 简化处理，实际应该检查是否为新文件
                            size=file_stat.st_size,
                            hash=file_hash,
                            last_modified=datetime.fromtimestamp(file_stat.st_mtime)
                        ))
        
        return changed_files
    
    async def get_sync_status(self) -> SyncStatusResponse:
        """获取同步状态"""
        await self._ensure_initialized()
        pending_files = await self._get_changed_files()
        
        return SyncStatusResponse(
            status=self._current_status,
            last_sync=None,  # TODO: 从历史记录中获取
            next_sync=None,  # TODO: 计算下次自动同步时间
            pending_files=pending_files,
            current_operation=self._current_operation,
            progress=None,
            total_files=len(pending_files),
            synced_files=0
        )
    
    async def manual_sync(self, force: bool = False, files: Optional[List[str]] = None) -> bool:
        """手动同步"""
        return await self._sync(operation_type="manual_sync", force=force, files=files)
    
    async def _auto_sync(self, force: bool = False, files: Optional[List[str]] = None) -> bool:
        """自动同步"""
        return await self._sync(operation_type="auto_sync", force=force, files=files)
    
    async def _sync(self, operation_type: str, force: bool = False, files: Optional[List[str]] = None) -> bool:
        """通用同步方法"""
        if self._current_status == SyncStatus.SYNCING:
            raise Exception("正在同步中，请稍后再试")
        
        if not self._config or not self._github_client:
            raise Exception("同步配置未设置")
        
        try:
            self._current_status = SyncStatus.SYNCING
            
            # 获取要同步的文件
            if files:
                sync_files = [FileChangeInfo(file_path=f, file_type="modified") for f in files]
            else:
                sync_files = await self._get_changed_files()
            
            if not sync_files and not force:
                self._current_status = SyncStatus.IDLE
                return True
            
            # 执行同步
            await self._sync_files_to_github(sync_files)
            
            self._current_status = SyncStatus.SUCCESS
            await self._add_history_record(operation_type, SyncStatus.SUCCESS, len(sync_files))
            
            return True
            
        except Exception as e:
            self._current_status = SyncStatus.FAILED
            await self._add_history_record(operation_type, SyncStatus.FAILED, 0, str(e))
            raise
    
    async def _sync_files_to_github(self, files: List[FileChangeInfo]):
        """同步文件到GitHub"""
        repo = self._github_client.get_repo(self._config.repository)
        
        for file_info in files:
            file_path = self.data_dir / file_info.file_path
            
            if not file_path.exists():
                continue
            
            # 读取文件内容 - 直接读取为文本，不进行base64编码
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            try:
                # 检查文件是否存在
                try:
                    existing_file = repo.get_contents(file_info.file_path, ref=self._config.branch)
                    # 更新文件
                    repo.update_file(
                        file_info.file_path,
                        f"Update {file_info.file_path}",
                        content,
                        existing_file.sha,
                        branch=self._config.branch
                    )
                except GithubException as e:
                    if e.status == 404:
                        # 文件不存在，创建新文件
                        repo.create_file(
                            file_info.file_path,
                            f"Add {file_info.file_path}",
                            content,
                            branch=self._config.branch
                        )
                    else:
                        raise
                        
            except Exception as e:
                print(f"同步文件 {file_info.file_path} 失败: {e}")
                raise
    
    async def _add_history_record(self, operation_type: str, status: SyncStatus, files_count: int, message: str = None):
        """添加历史记录"""
        try:
            history = []
            if self.history_file.exists():
                async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.loads(await f.read())
            
            history.insert(0, {
                "timestamp": datetime.now().isoformat(),
                "operation_type": operation_type,
                "status": status.value,
                "files_count": files_count,
                "message": message
            })
            
            # 保留最近100条记录
            history = history[:100]
            
            async with aiofiles.open(self.history_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(history, ensure_ascii=False, indent=2))
                
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    async def get_sync_history(self, page: int = 1, page_size: int = 20) -> Dict:
        """获取同步历史"""
        try:
            if not self.history_file.exists():
                return {"history": [], "total_count": 0, "page": page, "page_size": page_size}
            
            async with aiofiles.open(self.history_file, 'r', encoding='utf-8') as f:
                all_history = json.loads(await f.read())
            
            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            page_history = all_history[start:end]
            
            return {
                "history": page_history,
                "total_count": len(all_history),
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            print(f"获取历史记录失败: {e}")
            return {"history": [], "total_count": 0, "page": page, "page_size": page_size}
    
    async def _check_auto_sync(self):
        """检查是否需要自动同步"""
        if not self._config or not self._config.auto_sync:
            return
        
        if self._current_status == SyncStatus.SYNCING:
            return
        
        # 这里可以添加更复杂的自动同步逻辑
        # 比如检查上次同步时间、文件变更数量等
        
        try:
            await self._auto_sync()
        except Exception as e:
            print(f"自动同步失败: {e}")
    
    async def restore_from_github(self, commit_hash: Optional[str] = None, force: bool = False) -> bool:
        """从GitHub恢复数据"""
        if not self._config or not self._github_client:
            raise Exception("同步配置未设置")
        
        try:
            self._current_status = SyncStatus.SYNCING
            
            repo = self._github_client.get_repo(self._config.repository)
            
            # 获取指定提交或最新提交的文件
            if commit_hash:
                commit = repo.get_commit(commit_hash)
                tree = commit.commit.tree
            else:
                tree = repo.get_git_tree(self._config.branch, recursive=True)
            
            restored_count = 0
            
            for item in tree.tree:
                if item.type == "blob" and self._match_patterns(item.path):
                    # 只恢复 beancount 文件
                    item_path_lower = item.path.lower()
                    if not (item_path_lower.endswith('.bean') or item_path_lower.endswith('.beancount')):
                        continue
                    
                    # 下载文件内容
                    blob = repo.get_git_blob(item.sha)
                    
                    # 尝试直接获取文本内容，如果失败则尝试base64解码
                    try:
                        # 首先尝试直接作为文本内容
                        content_bytes = base64.b64decode(blob.content)
                        content_text = content_bytes.decode('utf-8')
                        
                        # 检查是否是有效的beancount文本内容
                        if any(line.strip().startswith(('open ', 'close ', 'option ', ';', '19', '20')) 
                               for line in content_text.split('\n')[:10]):
                            # 直接使用解码后的文本
                            content = content_text
                        else:
                            # 可能是双重编码，尝试再次解码
                            try:
                                content = base64.b64decode(content_text).decode('utf-8')
                            except:
                                content = content_text
                    except Exception:
                        # 如果解码失败，使用原始内容
                        content = base64.b64decode(blob.content).decode('utf-8')
                    
                    # 保存到本地
                    local_path = self.data_dir / item.path
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    async with aiofiles.open(local_path, 'w', encoding='utf-8') as f:
                        await f.write(content)
                    
                    restored_count += 1
            
            self._current_status = SyncStatus.SUCCESS
            await self._add_history_record("restore", SyncStatus.SUCCESS, restored_count)
            
            return True
            
        except Exception as e:
            self._current_status = SyncStatus.FAILED
            await self._add_history_record("restore", SyncStatus.FAILED, 0, str(e))
            raise
    
    async def get_config(self) -> Optional[GitHubSyncConfig]:
        """获取当前配置"""
        await self._ensure_initialized()
        return self._config
    
    async def shutdown(self):
        """关闭服务"""
        await self._stop_file_watcher()


# 全局同步服务实例
github_sync_service = GitHubSyncService()
