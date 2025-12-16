"""
AI分析服务 - AgentUniverse 多 Agent 架构实现

使用 PEER (Plan-Execute-Express-Review) 多 Agent 模式，
通过 AgentUniverse 框架实现财务分析功能。
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List, AsyncGenerator
from datetime import datetime, date
from decimal import Decimal

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """处理Decimal类型的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class AIService:
    """
    AI分析服务
    
    使用 AgentUniverse 的 PEER 多 Agent 架构：
    - Planning Agent: 问题规划，拆解用户问题
    - Executing Agent: 数据执行，调用工具获取数据
    - Expressing Agent: 结论表达，生成自然语言回答
    - Reviewing Agent: 质量审核，优化最终回答 (可选)
    
    Finance Master Agent 负责协调以上四个子 Agent。
    """
    
    def __init__(self):
        from app.core.config import settings
        self.api_key = settings.dashscope_api_key
        self._master_agent = None
        
    @property
    def master_agent(self):
        """延迟加载 Master Agent"""
        if self._master_agent is None:
            from app.ai.agents.finance_master_agent import finance_master_agent
            self._master_agent = finance_master_agent
        return self._master_agent
        
    async def analyze(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行财务分析
        
        使用 PEER 多 Agent 架构进行分析。
        
        Args:
            query: 用户问题
            context: 可选的上下文信息
            
        Returns:
            分析结果
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "未配置DASHSCOPE_API_KEY环境变量"
            }
        
        try:
            from app.ai.agents.base import AgentInput
            
            # 记录入口日志
            logger.info(f"#"*80)
            logger.info(f"[AI服务] analyze() 调用开始")
            logger.info(f"[AI服务] 查询: {query}")
            if context:
                context_str = json.dumps(context, ensure_ascii=False, cls=DecimalEncoder)
                logger.info(f"[AI服务] 上下文: {context_str[:500]}..." if len(context_str) > 500 else f"[AI服务] 上下文: {context_str}")
            
            # 如果有上下文，将其添加到问题中
            enhanced_query = query
            if context:
                context_str = json.dumps(context, ensure_ascii=False, cls=DecimalEncoder)
                enhanced_query = f"{query}\n\n上下文信息: {context_str}"
            
            # 使用 Master Agent 执行 PEER 流程
            agent_input = AgentInput(input=enhanced_query)
            result = await self.master_agent.run(agent_input)
            
            if result.get("success"):
                logger.info(f"[AI服务] analyze() 调用成功")
                logger.info(f"[AI服务] 响应长度: {len(result.get('response', ''))} 字符")
                logger.info(f"#"*80)
                return {
                    "success": True,
                    "query": query,
                    "response": result.get("response", ""),
                    "analysis_type": result.get("analysis_type"),
                    "sub_questions": result.get("sub_questions", []),
                    "quality_score": result.get("quality_score")
                }
            else:
                logger.warning(f"[AI服务] analyze() 分析失败: {result.get('error')}")
                logger.info(f"#"*80)
                return {
                    "success": False,
                    "error": result.get("error", "分析失败")
                }
            
        except Exception as e:
            logger.error(f"[AI服务] analyze() 异常: {e}", exc_info=True)
            logger.info(f"#"*80)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        多轮对话
        
        使用 Master Agent 的 chat 方法处理多轮对话。
        
        Args:
            messages: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Returns:
            回复结果
        """
        if not self.api_key:
            logger.warning("[AI服务] DASHSCOPE_API_KEY 未配置")
            return {
                "success": False,
                "error": "未配置DASHSCOPE_API_KEY环境变量"
            }
        
        logger.info(f"#"*80)
        logger.info(f"[AI服务] chat() 调用开始")
        logger.info(f"[AI服务] 消息数量: {len(messages)}")
        for i, msg in enumerate(messages):
            content_preview = msg.get('content', '')[:100]
            logger.debug(f"[AI服务] Message[{i}] {msg.get('role')}: {content_preview}...")
        
        try:
            result = await self.master_agent.chat(messages)
            
            if result.get("success"):
                logger.info(f"[AI服务] chat() 调用成功")
                logger.info(f"[AI服务] 响应长度: {len(result.get('response', ''))} 字符")
                logger.info(f"#"*80)
                return {
                    "success": True,
                    "response": result.get("response", "")
                }
            else:
                logger.warning(f"[AI服务] chat() 对话失败: {result.get('error')}")
                logger.info(f"#"*80)
                return {
                    "success": False,
                    "error": result.get("error", "对话失败")
                }
            
        except Exception as e:
            logger.error(f"[AI服务] chat() 异常: {e}", exc_info=True)
            logger.info(f"#"*80)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式多轮对话
        
        使用 Master Agent 的 chat_stream 方法进行流式输出。
        
        Args:
            messages: 对话历史，格式为[{"role": "user/assistant", "content": "..."}]
            
        Yields:
            响应文本块
        """
        if not self.api_key:
            yield {"type": "error", "content": "未配置DASHSCOPE_API_KEY环境变量"}
            return
        
        logger.info(f"#"*80)
        logger.info(f"[AI服务] chat_stream() 调用开始")
        logger.info(f"[AI服务] 消息数量: {len(messages)}")
        
        try:
            chunk_count = 0
            async for chunk in self.master_agent.chat_stream(messages):
                chunk_count += 1
                yield chunk
            
            logger.info(f"[AI服务] chat_stream() 完成, 共输出 {chunk_count} 个 chunks")
            logger.info(f"#"*80)
            
        except Exception as e:
            logger.error(f"[AI服务] chat_stream() 异常: {e}", exc_info=True)
            logger.info(f"#"*80)
            yield {"type": "error", "content": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取 AI 服务状态
        
        Returns:
            服务状态信息
        """
        return {
            "enabled": bool(self.api_key),
            "model": "qwen3-max",
            "provider": "dashscope",
            "architecture": "PEER Multi-Agent",
            "agents": [
                "planning_agent",
                "executing_agent",
                "expressing_agent",
                "reviewing_agent",
                "finance_master_agent"
            ]
        }


# 全局AI服务实例
ai_service = AIService()
