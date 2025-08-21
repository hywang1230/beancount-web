from sqlalchemy import Column, Integer, String, Date, Float, JSON, Boolean, DateTime
from app.database import Base
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_executed = Column(Date)
    next_execution = Column(Date)
