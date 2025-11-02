from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date
from app.database import Base
from app.core.config import settings
from typing import Dict, Any
from decimal import Decimal


class Budget(Base):
    """预算表"""
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(200), nullable=False, index=True)  # 支出类别
    period_type = Column(String(20), nullable=False)  # month, quarter, year
    period_value = Column(String(50), nullable=False, index=True)  # 2024-11, 2024-Q1, 2024
    amount = Column(Numeric(precision=15, scale=2), nullable=False)  # 预算金额
    currency = Column(String(10), nullable=False, default="CNY")
    created_at = Column(DateTime, default=lambda: settings.now())
    updated_at = Column(DateTime, default=lambda: settings.now(), onupdate=lambda: settings.now())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'category': self.category,
            'period_type': self.period_type,
            'period_value': self.period_value,
            'amount': float(self.amount) if self.amount else 0,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

