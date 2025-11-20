"""
预算管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.schemas import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetProgress,
    BudgetSummary
)
from app.services.budget_service import BudgetService
from app.database import get_db

router = APIRouter()


@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db)
):
    """
    创建预算
    """
    try:
        service = BudgetService(db)
        return service.create_budget(budget_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建预算失败: {str(e)}")


@router.get("/", response_model=List[BudgetResponse])
async def get_budgets(
    period_type: Optional[str] = Query(None, description="周期类型：month, quarter, year"),
    period_value: Optional[str] = Query(None, description="周期值"),
    db: Session = Depends(get_db)
):
    """
    获取预算列表
    """
    try:
        service = BudgetService(db)
        return service.get_budgets(period_type, period_value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算列表失败: {str(e)}")


@router.get("/summary", response_model=BudgetSummary)
async def get_budget_summary(
    period_type: str = Query("month", description="周期类型：month, quarter, year"),
    period_value: Optional[str] = Query(None, description="周期值，如 2024-11"),
    db: Session = Depends(get_db)
):
    """
    获取预算汇总
    """
    try:
        service = BudgetService(db)
        return service.get_budget_summary(period_type, period_value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算汇总失败: {str(e)}")


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """
    获取特定预算
    """
    try:
        service = BudgetService(db)
        budget = service.get_budget(budget_id)
        if not budget:
            raise HTTPException(status_code=404, detail="预算不存在")
        return budget
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算失败: {str(e)}")


@router.get("/{budget_id}/progress", response_model=BudgetProgress)
async def get_budget_progress(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """
    获取预算执行进度
    """
    try:
        service = BudgetService(db)
        progress = service.get_budget_progress(budget_id)
        if not progress:
            raise HTTPException(status_code=404, detail="预算不存在")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算进度失败: {str(e)}")


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    update_data: BudgetUpdate,
    db: Session = Depends(get_db)
):
    """
    更新预算
    """
    try:
        service = BudgetService(db)
        return service.update_budget(budget_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新预算失败: {str(e)}")


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db)
):
    """
    删除预算
    """
    try:
        service = BudgetService(db)
        success = service.delete_budget(budget_id)
        if not success:
            raise HTTPException(status_code=404, detail="预算不存在")
        return {"success": True, "message": "预算已删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除预算失败: {str(e)}")

