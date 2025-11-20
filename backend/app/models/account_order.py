from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from app.database import Base
from app.core.config import settings
from typing import List, Dict, Any


class AccountOrder(Base):
    """账户排序配置表"""
    __tablename__ = "account_orders"

    id = Column(Integer, primary_key=True, index=True)
    # 排序类型：category（分类排序）、subcategory（子分类排序）、account（账户排序）
    order_type = Column(String(20), nullable=False, index=True)
    # 分类名称，如 Assets, Liabilities, Income, Expenses, Equity
    category = Column(String(50), nullable=True, index=True)
    # 子分类名称，如 Current, Fixed, etc.
    subcategory = Column(String(100), nullable=True, index=True)
    # 排序顺序（数字越小排序越靠前）
    sort_order = Column(Integer, nullable=False, default=0)
    # 项目名称（分类名、子分类名或账户名）
    item_name = Column(String(200), nullable=False, index=True)
    # 创建时间
    created_at = Column(DateTime, default=lambda: settings.now())
    # 更新时间
    updated_at = Column(DateTime, default=lambda: settings.now(), onupdate=lambda: settings.now())

    # 唯一约束：确保同一类型+分类+子分类下的项目名称唯一
    __table_args__ = (
        UniqueConstraint('order_type', 'category', 'subcategory', 'item_name', name='uq_account_order'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'order_type': self.order_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'sort_order': self.sort_order,
            'item_name': self.item_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_category_order(cls, categories: List[str]) -> List['AccountOrder']:
        """创建分类排序记录"""
        records = []
        for idx, category in enumerate(categories):
            record = cls(
                order_type='category',
                category=None,
                subcategory=None,
                item_name=category,
                sort_order=idx
            )
            records.append(record)
        return records

    @classmethod
    def create_subcategory_order(cls, category: str, subcategories: List[str]) -> List['AccountOrder']:
        """创建子分类排序记录"""
        records = []
        for idx, subcategory in enumerate(subcategories):
            record = cls(
                order_type='subcategory',
                category=category,
                subcategory=None,
                item_name=subcategory,
                sort_order=idx
            )
            records.append(record)
        return records

    @classmethod
    def create_account_order(cls, category: str, subcategory: str, accounts: List[str]) -> List['AccountOrder']:
        """创建账户排序记录"""
        records = []
        for idx, account in enumerate(accounts):
            record = cls(
                order_type='account',
                category=category,
                subcategory=subcategory,
                item_name=account,
                sort_order=idx
            )
            records.append(record)
        return records

    def __repr__(self):
        return f"<AccountOrder(type={self.order_type}, category={self.category}, subcategory={self.subcategory}, item={self.item_name}, order={self.sort_order})>"
