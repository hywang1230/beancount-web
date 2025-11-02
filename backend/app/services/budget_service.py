"""
预算管理服务
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from calendar import monthrange

from app.models.budget import Budget
from app.models.schemas import BudgetCreate, BudgetUpdate, BudgetResponse, BudgetProgress, BudgetSummary
from app.services.beancount_service import beancount_service
from beancount.core.data import Transaction


class BudgetService:
    """预算服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_budget(self, budget_data: BudgetCreate) -> BudgetResponse:
        """创建预算"""
        # 不再检查重复，允许为同一类别创建多个预算
        # 用户可以为同一个类别的不同子类别创建预算
        
        budget = Budget(
            category=budget_data.category,
            period_type=budget_data.period_type,
            period_value=budget_data.period_value,
            amount=budget_data.amount,
            currency=budget_data.currency
        )
        
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        
        return self._to_response(budget)
    
    def get_budgets(
        self, 
        period_type: Optional[str] = None,
        period_value: Optional[str] = None
    ) -> List[BudgetResponse]:
        """获取预算列表"""
        query = self.db.query(Budget)
        
        if period_type:
            query = query.filter(Budget.period_type == period_type)
        if period_value:
            query = query.filter(Budget.period_value == period_value)
        
        budgets = query.order_by(Budget.period_value.desc(), Budget.category).all()
        return [self._to_response(b) for b in budgets]
    
    def get_budget(self, budget_id: int) -> Optional[BudgetResponse]:
        """获取特定预算"""
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        return self._to_response(budget) if budget else None
    
    def update_budget(self, budget_id: int, update_data: BudgetUpdate) -> BudgetResponse:
        """更新预算"""
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise ValueError("预算不存在")
        
        if update_data.amount is not None:
            budget.amount = update_data.amount
        
        self.db.commit()
        self.db.refresh(budget)
        
        return self._to_response(budget)
    
    def delete_budget(self, budget_id: int) -> bool:
        """删除预算"""
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return False
        
        self.db.delete(budget)
        self.db.commit()
        return True
    
    def get_budget_progress(self, budget_id: int) -> Optional[BudgetProgress]:
        """获取预算执行进度"""
        budget = self.db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            return None
        
        # 获取实际支出（包含货币参数）
        spent = self._calculate_spent(budget.category, budget.period_type, budget.period_value, budget.currency)
        
        # 计算进度
        remaining = Decimal(budget.amount) - spent
        percentage = float((spent / Decimal(budget.amount)) * 100) if budget.amount > 0 else 0
        is_exceeded = spent > Decimal(budget.amount)
        
        # 计算剩余天数
        days_remaining = self._calculate_days_remaining(budget.period_type, budget.period_value)
        
        return BudgetProgress(
            budget=self._to_response(budget),
            spent=spent,
            remaining=remaining,
            percentage=round(percentage, 2),
            is_exceeded=is_exceeded,
            days_remaining=days_remaining
        )
    
    def get_budget_summary(
        self, 
        period_type: str = "month",
        period_value: Optional[str] = None
    ) -> BudgetSummary:
        """获取预算汇总"""
        # 如果没有指定周期值，使用当前周期
        if not period_value:
            period_value = self._get_current_period(period_type)
        
        # 获取该周期的所有预算
        budgets = self.db.query(Budget).filter(
            Budget.period_type == period_type,
            Budget.period_value == period_value
        ).all()
        
        if not budgets:
            return BudgetSummary(
                total_budget=Decimal(0),
                total_spent=Decimal(0),
                total_remaining=Decimal(0),
                overall_percentage=0,
                budgets=[],
                currency="CNY"
            )
        
        # 计算每个预算的进度
        budget_progresses = []
        total_budget = Decimal(0)
        total_spent = Decimal(0)
        
        for budget in budgets:
            spent = self._calculate_spent(budget.category, budget.period_type, budget.period_value, budget.currency)
            remaining = Decimal(budget.amount) - spent
            percentage = float((spent / Decimal(budget.amount)) * 100) if budget.amount > 0 else 0
            is_exceeded = spent > Decimal(budget.amount)
            days_remaining = self._calculate_days_remaining(budget.period_type, budget.period_value)
            
            budget_progresses.append(BudgetProgress(
                budget=self._to_response(budget),
                spent=spent,
                remaining=remaining,
                percentage=round(percentage, 2),
                is_exceeded=is_exceeded,
                days_remaining=days_remaining
            ))
            
            total_budget += Decimal(budget.amount)
            total_spent += spent
        
        total_remaining = total_budget - total_spent
        overall_percentage = float((total_spent / total_budget) * 100) if total_budget > 0 else 0
        
        return BudgetSummary(
            total_budget=total_budget,
            total_spent=total_spent,
            total_remaining=total_remaining,
            overall_percentage=round(overall_percentage, 2),
            budgets=budget_progresses,
            currency=budgets[0].currency if budgets else "CNY"
        )
    
    def _calculate_spent(self, category: str, period_type: str, period_value: str, currency: str = "CNY") -> Decimal:
        """计算实际支出金额
        
        注意：
        - 只统计支出账户（Expenses）的支出
        - 在Beancount中，支出账户的借方（正值）表示支出
        - 支出账户的贷方（负值）表示退款或冲正，不计入统计
        - 只统计指定货币的支出
        """
        # 解析周期
        start_date, end_date = self._parse_period(period_type, period_value)
        
        # 从 beancount 获取交易数据
        entries, _, _ = beancount_service.loader.load_entries()
        
        spent = Decimal(0)
        for entry in entries:
            if not isinstance(entry, Transaction):
                continue
                
            # 检查日期是否在周期内
            if entry.date < start_date or entry.date > end_date:
                continue
            
            # 遍历交易的所有记账行
            for posting in entry.postings:
                if not posting.units:
                    continue
                
                # 账户匹配：完全匹配或者是子账户
                account_matches = (posting.account == category or 
                                 posting.account.startswith(category + ":"))
                
                if not account_matches:
                    continue
                
                # 检查货币类型
                if posting.units.currency != currency:
                    continue
                
                # 只统计支出账户（Expenses开头）且金额为正的记录
                if posting.account.startswith("Expenses:"):
                    amount = Decimal(str(posting.units.number))
                    # 只累加正值（支出），负值是退款
                    if amount > 0:
                        spent += amount
        
        return spent
    
    def _parse_period(self, period_type: str, period_value: str) -> tuple:
        """解析周期为开始和结束日期"""
        if period_type == "month":
            # 格式: 2024-11
            year, month = map(int, period_value.split('-'))
            start_date = date(year, month, 1)
            _, last_day = monthrange(year, month)
            end_date = date(year, month, last_day)
        elif period_type == "quarter":
            # 格式: 2024-Q1
            year = int(period_value.split('-')[0])
            quarter = int(period_value.split('-Q')[1])
            start_month = (quarter - 1) * 3 + 1
            start_date = date(year, start_month, 1)
            end_month = start_month + 2
            _, last_day = monthrange(year, end_month)
            end_date = date(year, end_month, last_day)
        elif period_type == "year":
            # 格式: 2024
            year = int(period_value)
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        else:
            raise ValueError(f"不支持的周期类型: {period_type}")
        
        return start_date, end_date
    
    def _calculate_days_remaining(self, period_type: str, period_value: str) -> Optional[int]:
        """计算周期剩余天数"""
        try:
            _, end_date = self._parse_period(period_type, period_value)
            today = date.today()
            
            if today > end_date:
                return 0
            
            return (end_date - today).days + 1
        except:
            return None
    
    def _get_current_period(self, period_type: str) -> str:
        """获取当前周期值"""
        today = date.today()
        
        if period_type == "month":
            return today.strftime("%Y-%m")
        elif period_type == "quarter":
            quarter = (today.month - 1) // 3 + 1
            return f"{today.year}-Q{quarter}"
        elif period_type == "year":
            return str(today.year)
        else:
            return today.strftime("%Y-%m")
    
    def _to_response(self, budget: Budget) -> BudgetResponse:
        """转换为响应格式"""
        return BudgetResponse(
            id=budget.id,
            category=budget.category,
            period_type=budget.period_type,
            period_value=budget.period_value,
            amount=Decimal(str(budget.amount)),
            currency=budget.currency,
            created_at=budget.created_at,
            updated_at=budget.updated_at
        )

