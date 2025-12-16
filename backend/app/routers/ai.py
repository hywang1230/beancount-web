"""
AI分析路由

使用 AgentUniverse PEER 多 Agent 架构提供 AI 服务接口。
"""
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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
    analysis_type: Optional[str] = None
    sub_questions: Optional[List[str]] = None
    quality_score: Optional[int] = None


@router.post("/analyze", response_model=AIResponse)
async def analyze(request: AnalyzeRequest):
    """
    财务分析接口
    
    使用 PEER 多 Agent 架构分析账本数据：
    - Planning Agent: 问题规划
    - Executing Agent: 数据执行
    - Expressing Agent: 结论表达
    - Reviewing Agent: 质量审核 (可选)
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
        analysis_type=result.get("analysis_type"),
        sub_questions=result.get("sub_questions"),
        quality_score=result.get("quality_score")
    )


@router.post("/chat", response_model=AIResponse)
async def chat(request: ChatRequest):
    """
    多轮对话接口
    
    支持上下文连续对话，使用 PEER 多 Agent 架构。
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


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式多轮对话接口
    
    使用 Server-Sent Events (SSE) 返回流式响应。
    PEER 流程的 Plan 和 Execute 阶段正常执行，Express 阶段流式输出。
    """
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    async def generate():
        async for chunk in ai_service.chat_stream(messages):
            # SSE 格式: data: {json}\n\n
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )


@router.get("/status")
async def get_status():
    """
    获取AI服务状态
    
    返回服务配置和可用 Agent 列表。
    """
    return ai_service.get_status()
