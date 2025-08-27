from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json
import asyncio

from app.database import get_db
from app.models.ai_schemas import (
    AIConfigResponse, AIConfigCreate, AIConfigUpdate, AIConfigDict,
    AIChatRequest, AIChatResponse, AIConfirmRequest
)
from app.services.ai_config_service import AIConfigService
from app.services.ai_chat_service import AIChatService
from app.services.context_manager import ContextManager
from app.utils.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/config", response_model=List[AIConfigResponse])
async def get_ai_configs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取所有AI配置"""
    try:
        ai_service = AIConfigService(db)
        configs = ai_service.get_all_configs()
        return configs
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取AI配置失败"
        )


@router.get("/config/dict", response_model=AIConfigDict)
async def get_ai_configs_dict(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取AI配置字典"""
    try:
        ai_service = AIConfigService(db)
        configs_dict = ai_service.get_configs_dict()
        return AIConfigDict(configs=configs_dict)
    except Exception as e:
        logger.error(f"获取AI配置字典失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取AI配置字典失败"
        )


@router.get("/config/{key}", response_model=AIConfigResponse)
async def get_ai_config(
    key: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取单个AI配置"""
    try:
        ai_service = AIConfigService(db)
        config = ai_service.get_config(key)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"配置项 {key} 不存在"
            )
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取AI配置失败"
        )


@router.post("/config", response_model=AIConfigResponse)
async def create_ai_config(
    config_data: AIConfigCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建AI配置"""
    try:
        ai_service = AIConfigService(db)
        
        # 检查配置是否已存在
        existing_config = ai_service.get_config(config_data.key)
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"配置项 {config_data.key} 已存在"
            )
        
        config = ai_service.create_config(config_data)
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建AI配置失败"
        )


@router.put("/config/{key}", response_model=AIConfigResponse)
async def update_ai_config(
    key: str,
    config_data: AIConfigUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新AI配置（如果不存在则创建）"""
    try:
        ai_service = AIConfigService(db)
        
        # 使用upsert方法，如果不存在则创建
        config = ai_service.upsert_config(
            key=key,
            value=config_data.value or "",
            description=config_data.description
        )
        return config
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新AI配置失败"
        )


@router.delete("/config/{key}")
async def delete_ai_config(
    key: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """删除AI配置"""
    try:
        ai_service = AIConfigService(db)
        success = ai_service.delete_config(key)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"配置项 {key} 不存在"
            )
        return {"message": f"配置项 {key} 已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除AI配置失败"
        )





@router.post("/config/validate")
async def validate_ai_config(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """验证AI配置"""
    try:
        ai_service = AIConfigService(db)
        errors = ai_service.validate_config()
        
        if errors:
            return {
                "valid": False,
                "errors": errors,
                "message": "配置验证失败"
            }
        else:
            return {
                "valid": True,
                "errors": {},
                "message": "配置验证通过"
            }
    except Exception as e:
        logger.error(f"验证AI配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证AI配置失败"
        )


@router.post("/config/init-langsmith")
async def init_langsmith_configs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """初始化LangSmith配置项"""
    try:
        ai_service = AIConfigService(db)
        
        # LangSmith配置项
        langsmith_configs = {
            "langsmith_api_key": "",
            "langsmith_project": "beancount-web-ai", 
            "langsmith_tracing": "false"
        }
        
        created_count = 0
        for key, value in langsmith_configs.items():
            existing_config = ai_service.get_config(key)
            if not existing_config:
                from app.models.ai_schemas import DEFAULT_AI_CONFIGS
                description = DEFAULT_AI_CONFIGS.get(key, {}).get("description", "")
                ai_service.upsert_config(key, value, description)
                created_count += 1
                logger.info(f"创建LangSmith配置: {key}")
        
        return {
            "message": f"LangSmith配置初始化完成，创建了 {created_count} 个配置项",
            "created_count": created_count
        }
        
    except Exception as e:
        logger.error(f"初始化LangSmith配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化LangSmith配置失败"
        )


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI聊天接口"""
    try:
        logger.info(f"收到AI聊天请求: {request.message}")
        
        # 创建AI聊天服务实例
        chat_service = AIChatService(db)
        
        # 处理聊天请求
        response = await chat_service.process_chat(request)
        
        return response
        
    except Exception as e:
        logger.error(f"AI聊天处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI聊天处理失败"
        )


@router.post("/chat/stream")
async def ai_chat_stream(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI流式聊天接口"""
    try:
        logger.info(f"收到AI流式聊天请求: {request.message}")
        
        # 创建AI聊天服务实例
        chat_service = AIChatService(db)
        
        # 创建流式响应生成器
        async def generate_stream():
            try:
                async for chunk in chat_service.process_chat_stream(request):
                    # 发送SSE格式的数据
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # 发送结束信号
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                logger.error(f"流式聊天处理失败: {e}")
                error_chunk = {
                    "type": "error",
                    "error": str(e),
                    "message": "处理失败，请重试"
                }
                yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
        
        # 返回流式响应
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用nginx缓存
            }
        )
        
    except Exception as e:
        logger.error(f"AI流式聊天处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI流式聊天处理失败"
        )


@router.post("/confirm")
async def ai_confirm(
    request: AIConfirmRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI确认操作接口"""
    try:
        # TODO: 实现基于令牌的确认机制
        logger.info(f"收到AI确认请求: {request.action}")
        
        return {
            "message": f"确认操作 {request.action} 处理完成",
            "token": request.token,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"AI确认处理失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI确认处理失败"
        )


@router.post("/context/init")
async def init_context_configs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """初始化上下文配置项"""
    try:
        ai_service = AIConfigService(db)
        
        # 上下文配置项
        context_configs = {
            "context_enabled": "true",
            "context_buffer_window": "10"
        }
        
        created_count = 0
        for key, value in context_configs.items():
            existing_config = ai_service.get_config(key)
            if not existing_config:
                from app.models.ai_schemas import DEFAULT_AI_CONFIGS
                description = DEFAULT_AI_CONFIGS.get(key, {}).get("description", "")
                ai_service.upsert_config(key, value, description)
                created_count += 1
                logger.info(f"创建上下文配置: {key}")
        
        return {
            "message": f"上下文配置初始化完成，创建了 {created_count} 个配置项",
            "created_count": created_count
        }
        
    except Exception as e:
        logger.error(f"初始化上下文配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化上下文配置失败"
        )


@router.get("/context/stats")
async def get_context_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取上下文统计信息"""
    try:
        context_manager = ContextManager(db)
        stats = context_manager.get_conversation_stats()
        
        return {
            "stats": stats,
            "message": "获取上下文统计信息成功"
        }
        
    except Exception as e:
        logger.error(f"获取上下文统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取上下文统计失败"
        )


@router.delete("/context/conversation/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """清除指定对话的上下文"""
    try:
        context_manager = ContextManager(db)
        success = context_manager.clear_conversation(conversation_id)
        
        if success:
            return {
                "message": f"对话 {conversation_id} 的上下文已清除",
                "conversation_id": conversation_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"对话 {conversation_id} 不存在"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除对话上下文失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清除对话上下文失败"
        )


@router.post("/context/cleanup")
async def cleanup_expired_conversations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """清理过期的对话缓存"""
    try:
        context_manager = ContextManager(db)
        cleaned_count = context_manager.cleanup_expired_conversations()
        
        return {
            "message": f"清理了 {cleaned_count} 个过期对话",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"清理过期对话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="清理过期对话失败"
        )



