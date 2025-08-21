"""
统一的API响应格式
"""
from typing import Any, Optional, Dict, List
from pydantic import BaseModel
from datetime import datetime


class APIResponse(BaseModel):
    """统一的API响应格式"""
    success: bool
    message: str
    data: Optional[Any] = None
    code: str = "SUCCESS"
    timestamp: datetime = datetime.now()
    errors: Optional[List[str]] = None
    meta: Optional[Dict[str, Any]] = None


class PaginatedResponse(APIResponse):
    """分页响应格式"""
    pagination: Optional[Dict[str, Any]] = None


def success_response(
    data: Any = None, 
    message: str = "操作成功", 
    code: str = "SUCCESS",
    meta: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """创建成功响应"""
    return APIResponse(
        success=True,
        message=message,
        data=data,
        code=code,
        meta=meta
    )


def error_response(
    message: str = "操作失败",
    code: str = "ERROR",
    errors: Optional[List[str]] = None,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None
) -> APIResponse:
    """创建错误响应"""
    return APIResponse(
        success=False,
        message=message,
        data=data,
        code=code,
        errors=errors,
        meta=meta
    )


def paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "查询成功",
    code: str = "SUCCESS",
    meta: Optional[Dict[str, Any]] = None
) -> PaginatedResponse:
    """创建分页响应"""
    total_pages = (total + page_size - 1) // page_size
    
    pagination = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        code=code,
        pagination=pagination,
        meta=meta
    )
