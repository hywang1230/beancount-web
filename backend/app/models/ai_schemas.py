from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AIConfigBase(BaseModel):
    """AI配置基础模型"""
    key: str = Field(..., max_length=100, description="配置键名")
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置说明")


class AIConfigCreate(AIConfigBase):
    """创建AI配置的请求模型"""
    pass


class AIConfigUpdate(BaseModel):
    """更新AI配置的请求模型"""
    value: Optional[str] = Field(None, description="配置值")
    description: Optional[str] = Field(None, description="配置说明")


class AIConfigResponse(AIConfigBase):
    """AI配置响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIConfigDict(BaseModel):
    """AI配置字典模型"""
    configs: Dict[str, str] = Field(default_factory=dict, description="配置字典")


class AIChatRequest(BaseModel):
    """AI聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户输入消息")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")


class AIChatResponse(BaseModel):
    """AI聊天响应模型"""
    intent: Optional[str] = Field(None, description="意图类型")
    status: str = Field(default="completed", description="处理状态")
    data: Dict[str, Any] = Field(default_factory=dict, description="响应数据")
    chain_id: Optional[str] = Field(None, description="LangChain执行ID")
    message: str = Field(default="", description="响应消息")


class AIConfirmRequest(BaseModel):
    """AI确认操作请求模型"""
    token: str = Field(..., description="确认令牌")
    action: str = Field(..., description="确认操作")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作数据")


# 默认AI配置
DEFAULT_AI_CONFIGS = {
    "llm_provider_url": {
        "value": "https://api.openai.com/v1",
        "description": "LLM服务提供商URL"
    },
    "llm_model": {
        "value": "gpt-3.5-turbo",
        "description": "使用的模型名称"
    },
    "llm_api_key": {
        "value": "",
        "description": "API密钥"
    },
    "max_tokens": {
        "value": "2000",
        "description": "最大token数"
    },
    "temperature": {
        "value": "0.7",
        "description": "模型温度"
    },
    "langchain_verbose": {
        "value": "false",
        "description": "LangChain调试模式"
    },
    "langsmith_api_key": {
        "value": "",
        "description": "LangSmith API密钥"
    },
    "langsmith_project": {
        "value": "beancount-web-ai",
        "description": "LangSmith项目名称"
    },
    "langsmith_tracing": {
        "value": "false",
        "description": "是否启用LangSmith追踪"
    }
}
