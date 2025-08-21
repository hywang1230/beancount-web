"""
统一的异常定义
"""
from typing import Optional, Any, Dict


class BeancountWebException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, code: str = "GENERAL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class FileNotFoundError(BeancountWebException):
    """文件未找到异常"""
    
    def __init__(self, file_path: str, message: Optional[str] = None):
        self.file_path = file_path
        default_message = f"文件不存在: {file_path}"
        super().__init__(
            message=message or default_message,
            code="FILE_NOT_FOUND",
            details={"file_path": file_path}
        )


class ValidationError(BeancountWebException):
    """数据验证异常"""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"validation_errors": validation_errors or []}
        )


class AccountError(BeancountWebException):
    """账户相关异常"""
    
    def __init__(self, message: str, account_name: Optional[str] = None):
        super().__init__(
            message=message,
            code="ACCOUNT_ERROR",
            details={"account_name": account_name}
        )


class TransactionError(BeancountWebException):
    """交易相关异常"""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None):
        super().__init__(
            message=message,
            code="TRANSACTION_ERROR",
            details={"transaction_id": transaction_id}
        )


class SyncError(BeancountWebException):
    """同步相关异常"""
    
    def __init__(self, message: str, sync_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="SYNC_ERROR",
            details={"sync_type": sync_type}
        )


class ConfigurationError(BeancountWebException):
    """配置相关异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )
