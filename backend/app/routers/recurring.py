from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date

from app.models.schemas import (
    RecurringTransactionCreate, RecurringTransactionUpdate,
    RecurringTransactionResponse, RecurringExecutionLog,
    RecurringExecutionResult
)
from app.services.recurring_service import recurring_service
from app.services.scheduler import scheduler

router = APIRouter()

@router.post("/", response_model=RecurringTransactionResponse)
async def create_recurring_transaction(transaction: RecurringTransactionCreate):
    """创建周期记账"""
    try:
        return recurring_service.create_recurring_transaction(transaction)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建周期记账失败: {str(e)}")

@router.get("/", response_model=List[RecurringTransactionResponse])
async def get_recurring_transactions(active_only: bool = Query(False, description="只返回启用的周期记账")):
    """获取周期记账列表"""
    try:
        return recurring_service.get_recurring_transactions(active_only=active_only)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周期记账列表失败: {str(e)}")

@router.get("/{transaction_id}", response_model=RecurringTransactionResponse)
async def get_recurring_transaction(transaction_id: str):
    """获取单个周期记账"""
    try:
        transaction = recurring_service.get_recurring_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="周期记账不存在")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周期记账失败: {str(e)}")

@router.put("/{transaction_id}", response_model=RecurringTransactionResponse)
async def update_recurring_transaction(transaction_id: str, update_data: RecurringTransactionUpdate):
    """更新周期记账"""
    try:
        transaction = recurring_service.update_recurring_transaction(transaction_id, update_data)
        if not transaction:
            raise HTTPException(status_code=404, detail="周期记账不存在")
        return transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新周期记账失败: {str(e)}")

@router.delete("/{transaction_id}")
async def delete_recurring_transaction(transaction_id: str):
    """删除周期记账"""
    try:
        success = recurring_service.delete_recurring_transaction(transaction_id)
        if not success:
            raise HTTPException(status_code=404, detail="周期记账不存在")
        return {"message": "删除成功", "success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除周期记账失败: {str(e)}")

@router.post("/execute", response_model=RecurringExecutionResult)
async def execute_recurring_transactions(execution_date: Optional[date] = Query(None, description="执行日期，默认为今天")):
    """手动执行周期记账"""
    try:
        return recurring_service.execute_pending_transactions(execution_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行周期记账失败: {str(e)}")

@router.get("/logs/execution", response_model=List[RecurringExecutionLog])
async def get_execution_logs(
    transaction_id: Optional[str] = Query(None, description="特定周期记账ID"),
    days: int = Query(30, description="查询天数", ge=1, le=365)
):
    """获取执行日志"""
    try:
        return recurring_service.get_execution_logs(transaction_id, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行日志失败: {str(e)}")

@router.put("/{transaction_id}/toggle", response_model=RecurringTransactionResponse)
async def toggle_recurring_transaction(transaction_id: str):
    """切换周期记账启用状态"""
    try:
        transaction = recurring_service.get_recurring_transaction(transaction_id)
        if not transaction:
            raise HTTPException(status_code=404, detail="周期记账不存在")
        
        # 切换状态
        update_data = RecurringTransactionUpdate(is_active=not transaction.is_active)
        updated_transaction = recurring_service.update_recurring_transaction(transaction_id, update_data)
        
        return updated_transaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换状态失败: {str(e)}")

@router.post("/scheduler/trigger", response_model=dict)
async def trigger_scheduler():
    """手动触发定时任务"""
    try:
        await scheduler.manual_execute()
        return {"message": "定时任务已手动执行", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发定时任务失败: {str(e)}")

@router.get("/scheduler/jobs", response_model=List[dict])
async def get_scheduler_jobs():
    """获取调度器任务状态"""
    try:
        jobs = scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}") 