"""
AI分析路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.ai.service import ai_service

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """分析请求"""
    query: str
    context: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """对话消息"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """对话请求"""
    messages: List[ChatMessage]


class AIResponse(BaseModel):
    """AI响应"""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    data_summary: Optional[Dict[str, Any]] = None


@router.post("/analyze", response_model=AIResponse)
async def analyze(request: AnalyzeRequest):
    """
    财务分析接口
    
    根据用户问题分析账本数据，给出建议
    """
    result = await ai_service.analyze(request.query, request.context)
    
    if not result["success"]:
        return AIResponse(
            success=False,
            error=result.get("error", "分析失败")
        )
    
    return AIResponse(
        success=True,
        response=result["response"],
        data_summary=result.get("data_summary")
    )


@router.post("/chat", response_model=AIResponse)
async def chat(request: ChatRequest):
    """
    多轮对话接口
    
    支持上下文连续对话
    """
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    result = await ai_service.chat(messages)
    
    if not result["success"]:
        return AIResponse(
            success=False,
            error=result.get("error", "对话失败")
        )
    
    return AIResponse(
        success=True,
        response=result["response"]
    )


@router.get("/status")
async def get_status():
    """
    获取AI服务状态
    """
    has_api_key = hasattr(ai_service, "api_key")
    
    return {
        "enabled": has_api_key,
        "model": "qwen-plus",
        "provider": "dashscope"
    }
