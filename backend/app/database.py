from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

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


def init_database():
    """初始化数据库表"""
    try:
        # 导入所有模型以确保它们被注册到Base.metadata
        from app.models.recurring import Recurring, RecurringExecutionLog
        from app.models.sync import SyncLog
        from app.models.setting import Setting
        from app.models.github_sync import GitHubSync
        
        logger.info("正在初始化数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("数据库表初始化完成")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"数据库中的表: {tables}")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise