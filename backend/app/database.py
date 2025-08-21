from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# 设置SQLite时区为东八区
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """设置SQLite连接的时区和其他配置"""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # 设置时区偏移量为+8小时（东八区）
        cursor.execute("PRAGMA timezone = '+08:00'")
        cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
