"""
自定义JSON响应类，使用orjson提升序列化性能
"""

from typing import Any
from datetime import date, datetime
from decimal import Decimal

import orjson
from fastapi.responses import JSONResponse


def default_serializer(obj: Any) -> Any:
    """自定义序列化器，处理特殊类型"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif hasattr(obj, 'model_dump'):
        # Pydantic 模型
        return obj.model_dump()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class ORJSONResponse(JSONResponse):
    """使用orjson的快速JSON响应类"""
    
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content, 
            default=default_serializer,
            option=orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
        )
