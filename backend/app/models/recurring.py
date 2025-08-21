from sqlalchemy import Column, Integer, String, Date, Float, JSON, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.config import settings
import datetime


class Recurring(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    recurrence_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    weekly_days = Column(JSON)  # List of weekdays (0-6)
    monthly_days = Column(JSON) # List of month days (1-31)
    
    flag = Column(String, default="*")
    payee = Column(String)
    narration = Column(String, nullable=False)
    tags = Column(JSON)
    links = Column(JSON)
    postings = Column(JSON, nullable=False) # The actual transaction postings

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: settings.now())
    updated_at = Column(DateTime, default=lambda: settings.now(), onupdate=lambda: settings.now())
    last_executed = Column(Date)
    next_execution = Column(Date)
    
    # 关联关系
    execution_logs = relationship("RecurringExecutionLog", back_populates="recurring_transaction")


class RecurringExecutionLog(Base):
    """周期记账执行日志"""
    __tablename__ = "recurring_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    recurring_transaction_id = Column(Integer, ForeignKey("recurring_transactions.id", ondelete="CASCADE"), nullable=False)
    execution_date = Column(Date, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    created_transaction_id = Column(String)  # 创建的交易ID
    created_at = Column(DateTime, default=lambda: settings.now())
    
    # 关联关系
    recurring_transaction = relationship("Recurring", back_populates="execution_logs")
