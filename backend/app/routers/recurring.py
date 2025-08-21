from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import date

from app.models.schemas import (
    RecurringTransactionCreate, RecurringTransactionUpdate,
    RecurringTransactionResponse
)
from app.services.recurring_service import recurring_service
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=RecurringTransactionResponse)
async def create_recurring_transaction(
    transaction: RecurringTransactionCreate, 
    db: Session = Depends(get_db)
):
    """创建周期记账"""
    return recurring_service.create_recurring_transaction(db=db, transaction_in=transaction)

@router.get("/", response_model=List[RecurringTransactionResponse])
async def get_recurring_transactions(
    active_only: bool = Query(False, description="只返回启用的周期记账"),
    db: Session = Depends(get_db)
):
    """获取周期记账列表"""
    return recurring_service.get_recurring_transactions(db=db, active_only=active_only)

@router.get("/{transaction_id}", response_model=RecurringTransactionResponse)
async def get_recurring_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db)
):
    """获取单个周期记账"""
    db_transaction = recurring_service.get_recurring_transaction(db=db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="周期记账不存在")
    return db_transaction

@router.put("/{transaction_id}", response_model=RecurringTransactionResponse)
async def update_recurring_transaction(
    transaction_id: int, 
    update_data: RecurringTransactionUpdate,
    db: Session = Depends(get_db)
):
    """更新周期记账"""
    db_transaction = recurring_service.update_recurring_transaction(
        db=db, transaction_id=transaction_id, transaction_in=update_data
    )
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="周期记账不存在")
    return db_transaction

@router.delete("/{transaction_id}")
async def delete_recurring_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db)
):
    """删除周期记账"""
    success = recurring_service.delete_recurring_transaction(db=db, transaction_id=transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="周期记账不存在")
    return {"message": "删除成功", "success": True}

@router.put("/{transaction_id}/toggle", response_model=RecurringTransactionResponse)
async def toggle_recurring_transaction(
    transaction_id: int, 
    db: Session = Depends(get_db)
):
    """切换周期记账启用状态"""
    transaction = recurring_service.get_recurring_transaction(db, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="周期记账不存在")
    
    update_data = RecurringTransactionUpdate(is_active=not transaction.is_active)
    updated_transaction = recurring_service.update_recurring_transaction(
        db, transaction_id=transaction_id, transaction_in=update_data
    )
    return updated_transaction

@router.post("/execute")
async def execute_recurring_transactions(
    execution_date: Optional[str] = Query(None, description="执行日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """手动执行周期记账"""
    exec_date = None
    if execution_date:
        try:
            exec_date = date.fromisoformat(execution_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用YYYY-MM-DD格式")
    
    try:
        result = recurring_service.execute_pending_transactions(db=db, execution_date=exec_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@router.get("/logs/execution")
async def get_execution_logs(
    transaction_id: Optional[int] = Query(None, description="周期记账ID"),
    days: int = Query(30, description="查询天数"),
    db: Session = Depends(get_db)
):
    """获取执行日志"""
    try:
        logs = recurring_service.get_execution_logs(
            db=db, 
            transaction_id=transaction_id, 
            days=days
        )
        
        # 转换为响应格式
        result = []
        for log in logs:
            result.append({
                "id": str(log.id),
                "recurring_transaction_id": str(log.recurring_transaction_id),
                "execution_date": str(log.execution_date),
                "success": log.success,
                "error_message": log.error_message,
                "created_transaction_id": log.created_transaction_id,
                "created_at": log.created_at.isoformat()
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取执行日志失败: {str(e)}")

@router.post("/scheduler/trigger")
async def trigger_scheduler(db: Session = Depends(get_db)):
    """手动触发定时任务"""
    try:
        # 这里应该调用调度器触发任务
        # 临时实现，待完善
        return {"message": "定时任务已触发", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发失败: {str(e)}")

@router.get("/scheduler/jobs")
async def get_scheduler_jobs(db: Session = Depends(get_db)):
    """获取调度器任务状态"""
    # 临时返回空列表，待实现完整功能
    return [] 