from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List

from app.models.sync_schemas import (
    GitHubSyncConfigRequest, GitHubSyncConfigResponse, SyncStatusResponse,
    SyncHistoryResponse, SyncHistoryItem, ManualSyncRequest, RestoreRequest, TestConnectionResponse,
    ConflictResolutionRequest, SyncMetrics
)
from app.services.github_sync_service import github_sync_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/sync", tags=["同步管理"])


@router.post("/config", response_model=GitHubSyncConfigResponse)
async def configure_sync(
    config_request: GitHubSyncConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """配置GitHub同步设置"""
    try:
        config = await github_sync_service.configure_sync(config_request.model_dump())
        
        return GitHubSyncConfigResponse(
            repository=config.repository,
            branch=config.branch,
            auto_sync=config.auto_sync,
            sync_interval=config.sync_interval,
            include_files=config.include_files,
            exclude_files=config.exclude_files,
            conflict_resolution=config.conflict_resolution,
            last_sync=None,  # TODO: 从历史记录获取
            status=github_sync_service._current_status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置同步失败: {str(e)}")


@router.get("/config", response_model=GitHubSyncConfigResponse)
async def get_sync_config(current_user: dict = Depends(get_current_user)):
    """获取当前同步配置"""
    config = await github_sync_service.get_config()
    
    if not config:
        raise HTTPException(status_code=404, detail="同步配置未设置")
    
    return GitHubSyncConfigResponse(
        repository=config.repository,
        branch=config.branch,
        auto_sync=config.auto_sync,
        sync_interval=config.sync_interval,
        include_files=config.include_files,
        exclude_files=config.exclude_files,
        conflict_resolution=config.conflict_resolution,
        last_sync=None,  # TODO: 从历史记录获取
        status=github_sync_service._current_status
    )


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_github_connection(current_user: dict = Depends(get_current_user)):
    """测试GitHub连接"""
    try:
        result = await github_sync_service.test_connection()
        return TestConnectionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"测试连接失败: {str(e)}")


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(current_user: dict = Depends(get_current_user)):
    """获取同步状态"""
    try:
        status = await github_sync_service.get_sync_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态失败: {str(e)}")


@router.post("/manual")
async def manual_sync(
    request: ManualSyncRequest,
    current_user: dict = Depends(get_current_user)
):
    """手动触发同步"""
    try:
        result = await github_sync_service.manual_sync(
            force=request.force,
            files=request.files
        )
        
        return {
            "success": result,
            "message": "同步完成" if result else "同步失败"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"同步失败: {str(e)}")


@router.post("/restore")
async def restore_from_github(
    request: RestoreRequest,
    current_user: dict = Depends(get_current_user)
):
    """从GitHub恢复数据"""
    try:
        result = await github_sync_service.restore_from_github(
            commit_hash=request.commit_hash,
            force=request.force
        )
        
        return {
            "success": result,
            "message": "恢复完成" if result else "恢复失败"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"恢复失败: {str(e)}")


@router.get("/history", response_model=SyncHistoryResponse)
async def get_sync_history(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """获取同步历史"""
    try:
        if page < 1 or page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="无效的分页参数")
        
        result = await github_sync_service.get_sync_history(page, page_size)
        
        # 转换历史数据为SyncHistoryItem对象
        from datetime import datetime
        history_items = []
        for item in result["history"]:
            # 解析时间戳字符串为datetime对象
            timestamp_str = item["timestamp"]
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
            
            history_items.append(SyncHistoryItem(
                timestamp=timestamp,
                operation_type=item["operation_type"],
                status=item["status"],
                files_count=item["files_count"],
                message=item.get("message"),
                duration=item.get("duration")
            ))
        
        return SyncHistoryResponse(
            history=history_items,
            total_count=result["total_count"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


@router.post("/resolve-conflict")
async def resolve_conflict(
    request: ConflictResolutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """解决同步冲突"""
    try:
        # TODO: 实现冲突解决逻辑
        return {
            "success": True,
            "message": f"冲突解决完成: {request.file_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解决冲突失败: {str(e)}")


@router.get("/metrics", response_model=SyncMetrics)
async def get_sync_metrics(current_user: dict = Depends(get_current_user)):
    """获取同步指标"""
    try:
        # TODO: 实现指标统计
        return SyncMetrics(
            total_syncs=0,
            successful_syncs=0,
            failed_syncs=0,
            last_sync_duration=None,
            average_sync_duration=None,
            data_synced_mb=0.0,
            conflicts_resolved=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.delete("/config")
async def remove_sync_config(current_user: dict = Depends(get_current_user)):
    """删除同步配置"""
    try:
        await github_sync_service._ensure_initialized()
        # 停止文件监控
        await github_sync_service._stop_file_watcher()
        
        # 删除配置文件
        if github_sync_service.config_file.exists():
            github_sync_service.config_file.unlink()
        
        # 重置服务状态
        github_sync_service._config = None
        github_sync_service._github_client = None
        
        return {"success": True, "message": "同步配置已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除配置失败: {str(e)}")


@router.post("/pause")
async def pause_auto_sync(current_user: dict = Depends(get_current_user)):
    """暂停自动同步"""
    try:
        await github_sync_service._ensure_initialized()
        await github_sync_service._stop_file_watcher()
        
        if github_sync_service._config:
            github_sync_service._config.auto_sync = False
            await github_sync_service._save_config()
        
        return {"success": True, "message": "自动同步已暂停"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停自动同步失败: {str(e)}")


@router.post("/resume")
async def resume_auto_sync(current_user: dict = Depends(get_current_user)):
    """恢复自动同步"""
    try:
        await github_sync_service._ensure_initialized()
        if github_sync_service._config:
            github_sync_service._config.auto_sync = True
            await github_sync_service._save_config()
            await github_sync_service._start_file_watcher()
        
        return {"success": True, "message": "自动同步已恢复"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复自动同步失败: {str(e)}")


@router.get("/branches")
async def get_repository_branches(current_user: dict = Depends(get_current_user)):
    """获取仓库分支列表"""
    try:
        if not github_sync_service._github_client or not github_sync_service._config:
            raise HTTPException(status_code=400, detail="GitHub连接未配置")
        
        repo = github_sync_service._github_client.get_repo(github_sync_service._config.repository)
        branches = [branch.name for branch in repo.get_branches()]
        
        return {
            "branches": branches,
            "default_branch": repo.default_branch
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取分支列表失败: {str(e)}")


@router.get("/commits")
async def get_recent_commits(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """获取最近的提交记录"""
    try:
        if not github_sync_service._github_client or not github_sync_service._config:
            raise HTTPException(status_code=400, detail="GitHub连接未配置")
        
        if limit < 1 or limit > 50:
            raise HTTPException(status_code=400, detail="limit参数必须在1-50之间")
        
        repo = github_sync_service._github_client.get_repo(github_sync_service._config.repository)
        commits = repo.get_commits(sha=github_sync_service._config.branch)[:limit]
        
        commit_list = []
        for commit in commits:
            commit_list.append({
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "url": commit.html_url
            })
        
        return {"commits": commit_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取提交记录失败: {str(e)}")
