from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from sqlalchemy.orm import Session

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