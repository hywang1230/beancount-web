"""
统一的日志配置
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from app.core.config import settings


class BeancountLogger:
    """统一的日志管理器"""
    
    _loggers = {}
    _configured = False
    
    @classmethod
    def setup_logging(cls, log_level: str = "INFO", log_dir: Optional[Path] = None):
        """设置全局日志配置"""
        if cls._configured:
            return
        
        # 设置日志级别
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 创建日志目录
        if log_dir is None:
            log_dir = settings.data_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器 - 应用日志
        app_log_file = log_dir / "app.log"
        file_handler = logging.FileHandler(app_log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志处理器
        error_log_file = log_dir / "error.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取具名日志器"""
        if not cls._configured:
            cls.setup_logging()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def log_exception(cls, logger_name: str, exception: Exception, context: Optional[dict] = None):
        """记录异常信息"""
        logger = cls.get_logger(logger_name)
        
        context_str = ""
        if context:
            context_items = [f"{k}={v}" for k, v in context.items()]
            context_str = f" [Context: {', '.join(context_items)}]"
        
        logger.error(f"Exception occurred: {type(exception).__name__}: {str(exception)}{context_str}", exc_info=True)
    
    @classmethod
    def log_operation(cls, logger_name: str, operation: str, success: bool = True, details: Optional[dict] = None):
        """记录操作信息"""
        logger = cls.get_logger(logger_name)
        
        status = "SUCCESS" if success else "FAILED"
        details_str = ""
        if details:
            details_items = [f"{k}={v}" for k, v in details.items()]
            details_str = f" [Details: {', '.join(details_items)}]"
        
        level = logging.INFO if success else logging.WARNING
        logger.log(level, f"Operation {operation}: {status}{details_str}")


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志器的便捷函数"""
    return BeancountLogger.get_logger(name)


def log_exception(logger_name: str, exception: Exception, context: Optional[dict] = None):
    """记录异常的便捷函数"""
    BeancountLogger.log_exception(logger_name, exception, context)


def log_operation(logger_name: str, operation: str, success: bool = True, details: Optional[dict] = None):
    """记录操作的便捷函数"""
    BeancountLogger.log_operation(logger_name, operation, success, details)


# 初始化日志配置
BeancountLogger.setup_logging()
