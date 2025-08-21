from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from app.database import Base
import datetime


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    end_time = Column(DateTime)
    status = Column(String)  # e.g., 'SUCCESS', 'FAILED'
    operation_type = Column(String) # e.g., 'manual_sync', 'auto_sync', 'restore'
    files_count = Column(Integer, default=0)
    duration = Column(Float) # in seconds
    logs = Column(Text)
