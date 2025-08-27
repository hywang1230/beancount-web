from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AIConfig(Base):
    """AI配置表，存储LLM配置参数"""
    __tablename__ = "ai_config"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True, comment="配置键名")
    value = Column(Text, nullable=True, comment="配置值")
    description = Column(Text, nullable=True, comment="配置说明")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<AIConfig(key='{self.key}', value='{self.value[:50]}...')>"
