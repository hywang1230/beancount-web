from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ai_schemas import AIChatRequest, AIChatResponse
from app.services.ai_config_service import AIConfigService
from app.services.context_manager import ContextManager
import logging
import uuid
import asyncio
import os
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


class AIChatService:
    """AI聊天服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = AIConfigService(db)
        self.context_manager = ContextManager(db)
        self._setup_langsmith()
    
    def _setup_langsmith(self):
        """设置LangSmith追踪"""
        try:
            configs = self.config_service.get_configs_dict()
            
            # 检查是否启用LangSmith追踪
            tracing_enabled = configs.get("langsmith_tracing", "false").lower() == "true"
            langsmith_api_key = configs.get("langsmith_api_key", "")
            langsmith_project = configs.get("langsmith_project", "beancount-web-ai")
            
            if tracing_enabled and langsmith_api_key:
                # 设置LangSmith环境变量
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
                os.environ["LANGCHAIN_PROJECT"] = langsmith_project
                os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
                
                logger.info(f"LangSmith追踪已启用，项目: {langsmith_project}")
            else:
                # 禁用LangSmith追踪
                os.environ.pop("LANGCHAIN_TRACING_V2", None)
                os.environ.pop("LANGCHAIN_API_KEY", None)
                os.environ.pop("LANGCHAIN_PROJECT", None)
                os.environ.pop("LANGCHAIN_ENDPOINT", None)
                
                if tracing_enabled and not langsmith_api_key:
                    logger.warning("LangSmith追踪已启用但未配置API密钥")
                
        except Exception as e:
            logger.error(f"设置LangSmith失败: {e}")
    
    def get_llm_config(self) -> Dict[str, str]:
        """获取LLM配置"""
        configs = self.config_service.get_configs_dict()
        
        # 验证必需的配置
        required_keys = ["llm_model", "llm_api_key"]
        for key in required_keys:
            if not configs.get(key):
                raise ValueError(f"LLM配置不完整，缺少必需的配置项: {key}")
        
        return configs
    
    def create_llm_instance(self):
        """创建LLM实例"""
        try:
            config = self.get_llm_config()
            
            # 根据配置创建相应的LLM实例
            model_name = config.get("llm_model", "gpt-3.5-turbo")
            api_key = config.get("llm_api_key")
            
            if not api_key:
                raise ValueError("API密钥未配置")
            
            # 基础配置参数
            llm_params = {
                "model": model_name,
                "api_key": api_key,
                "temperature": float(config.get("temperature", "0.7")),
                "max_tokens": int(config.get("max_tokens", "2000")),
            }
            
            # 根据URL判断使用哪个LLM
            provider_url = config.get("llm_provider_url", "")
            
            if "openai" in provider_url.lower() or not provider_url:
                from langchain_openai import ChatOpenAI
                if provider_url and provider_url != "https://api.openai.com/v1":
                    llm_params["base_url"] = provider_url
                return ChatOpenAI(**llm_params)
            
            else:
                # 默认使用OpenAI兼容接口
                from langchain_openai import ChatOpenAI
                llm_params["base_url"] = provider_url
                return ChatOpenAI(**llm_params)
                
        except ImportError as e:
            logger.error(f"LangChain依赖未安装: {e}")
            raise ValueError("LangChain依赖未正确安装，请检查依赖配置")
        except Exception as e:
            logger.error(f"创建LLM实例失败: {e}")
            raise ValueError(f"LLM配置错误: {e}")
    
    def classify_intent(self, message: str) -> str:
        """分类用户意图"""
        # 简单的关键词匹配，后续可以用LLM改进
        message_lower = message.lower()
        
        # 记账相关关键词
        transaction_keywords = [
            "花了", "支付", "买了", "购买", "花费", "消费", "付款", "转账",
            "收入", "工资", "奖金", "收到", "入账", "存款"
        ]
        
        # 查询相关关键词
        query_keywords = [
            "多少钱", "花了多少", "总共", "统计", "查询", "分析", "报表",
            "余额", "结余", "账单", "明细", "记录"
        ]
        
        # 管理相关关键词
        management_keywords = [
            "设置", "配置", "预算", "同步", "导入", "导出", "备份"
        ]
        
        for keyword in transaction_keywords:
            if keyword in message_lower:
                return "transaction"
        
        for keyword in query_keywords:
            if keyword in message_lower:
                return "query"
        
        for keyword in management_keywords:
            if keyword in message_lower:
                return "management"
        
        # 默认为通用对话
        return "general"
    
    async def process_chat(self, request: AIChatRequest) -> AIChatResponse:
        """处理聊天请求"""
        # 每次处理前重新设置LangSmith（配置可能已更新）
        self._setup_langsmith()
        
        try:
            # 生成会话ID
            chain_id = str(uuid.uuid4())
            
            # 获取或创建对话ID和上下文内存
            conversation_id, memory = self.context_manager.get_or_create_memory(
                request.conversation_id
            )
            
            # 如果提供了历史记录，加载到内存中
            if request.chat_history:
                self.context_manager.load_chat_history(conversation_id, request.chat_history)
            
            logger.info(f"处理聊天请求[{chain_id}] 会话[{conversation_id}]: {request.message}")
            
            # 分类意图
            intent = self.classify_intent(request.message)
            
            # 验证配置
            config_errors = self.config_service.validate_config()
            if config_errors:
                return AIChatResponse(
                    intent=intent,
                    status="failed",
                    message="AI配置不完整，请先完成配置",
                    data={"config_errors": config_errors},
                    chain_id=chain_id,
                    conversation_id=conversation_id
                )
            
            # 根据意图处理不同类型的请求
            if intent == "transaction":
                response = await self._process_transaction_intent(request, chain_id, conversation_id, memory)
            elif intent == "query":
                response = await self._process_query_intent(request, chain_id, conversation_id, memory)
            elif intent == "management":
                response = await self._process_management_intent(request, chain_id, conversation_id, memory)
            else:
                response = await self._process_general_intent(request, chain_id, conversation_id, memory)
            
            # 将当前消息添加到内存中
            self.context_manager.add_message(conversation_id, "user", request.message)
            if response.message:
                self.context_manager.add_message(conversation_id, "assistant", response.message)
            
            return response
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            return AIChatResponse(
                intent="unknown",
                status="failed",
                message=f"处理失败：{str(e)}",
                data={},
                chain_id=chain_id if 'chain_id' in locals() else None,
                conversation_id=request.conversation_id
            )
    
    async def process_chat_stream(self, request: AIChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """处理流式聊天请求"""
        # 每次处理前重新设置LangSmith（配置可能已更新）
        self._setup_langsmith()
        
        chain_id = str(uuid.uuid4())
        conversation_id = None
        memory = None
        
        try:
            # 获取或创建对话ID和上下文内存
            conversation_id, memory = self.context_manager.get_or_create_memory(
                request.conversation_id
            )
            
            # 如果提供了历史记录，加载到内存中
            if request.chat_history:
                self.context_manager.load_chat_history(conversation_id, request.chat_history)
            
            logger.info(f"处理流式聊天请求[{chain_id}] 会话[{conversation_id}]: {request.message}")
            
            # 发送开始信号
            yield {
                "type": "start",
                "chain_id": chain_id,
                "conversation_id": conversation_id,
                "context_enabled": memory is not None,
                "message": "开始处理您的请求..."
            }
            
            # 分类意图
            intent = self.classify_intent(request.message)
            
            # 发送意图识别结果
            yield {
                "type": "intent",
                "intent": intent,
                "conversation_id": conversation_id,
                "message": f"识别意图: {intent}"
            }
            
            # 验证配置
            config_errors = self.config_service.validate_config()
            if config_errors:
                yield {
                    "type": "error",
                    "error": "配置不完整",
                    "message": "AI配置不完整，请先完成配置",
                    "conversation_id": conversation_id,
                    "data": {"config_errors": config_errors}
                }
                return
            
            # 根据意图处理不同类型的请求
            if intent == "general":
                async for chunk in self._process_general_stream(request, chain_id, conversation_id, memory):
                    yield chunk
            else:
                # 其他意图暂时使用非流式处理
                yield {
                    "type": "message",
                    "message": f"识别到{intent}需求，此功能正在开发中，暂不支持流式输出。",
                    "intent": intent,
                    "conversation_id": conversation_id
                }
                
            # 添加消息到内存
            if memory:
                self.context_manager.add_message(conversation_id, "user", request.message)
                
        except Exception as e:
            logger.error(f"流式聊天处理失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "处理失败，请重试",
                "conversation_id": conversation_id
            }
    
    async def _process_general_stream(self, request: AIChatRequest, chain_id: str, conversation_id: str, memory) -> AsyncGenerator[Dict[str, Any], None]:
        """处理通用对话的流式输出"""
        try:
            # 创建LLM实例进行通用对话
            llm = self.create_llm_instance()
            context_used = memory is not None
            
            # 构建系统提示
            system_prompt = """你是Beancount Web记账系统的AI助手。你可以帮助用户：
1. 记录交易和账目
2. 查询和分析财务数据
3. 管理系统设置

请用简洁友好的方式回复用户。如果用户想要记账、查询或设置功能，引导他们使用更具体的描述。
在多轮对话中，请结合之前的对话内容来回复，保持上下文的连贯性。"""
            
            from langchain.schema import HumanMessage, SystemMessage
            
            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]
            
            # 如果有上下文记忆，加入历史对话
            context_length = 0
            if memory:
                try:
                    # 获取历史对话
                    memory_vars = self.context_manager.get_memory_variables(conversation_id)
                    chat_history = memory_vars.get("chat_history", [])
                    context_length = len(chat_history)
                    
                    # 将历史消息添加到消息列表中
                    messages.extend(chat_history)
                    
                    logger.debug(f"流式处理加载了 {len(chat_history)} 条历史消息")
                    
                    # 发送上下文加载状态
                    yield {
                        "type": "context_loaded",
                        "conversation_id": conversation_id,
                        "context_length": context_length,
                        "message": f"已加载 {context_length} 条历史对话"
                    }
                    
                except Exception as e:
                    logger.warning(f"流式处理加载历史对话失败: {e}")
            
            # 添加当前用户消息
            messages.append(HumanMessage(content=request.message))
            
            # 添加LangSmith追踪的上下文信息
            try:
                import langsmith
                
                # 设置当前会话的标签和元数据
                langsmith.trace.current_run_tree.extra["chain_id"] = chain_id
                langsmith.trace.current_run_tree.extra["conversation_id"] = conversation_id
                langsmith.trace.current_run_tree.extra["intent"] = "general"
                langsmith.trace.current_run_tree.extra["user_message"] = request.message
                langsmith.trace.current_run_tree.extra["message_length"] = len(request.message)
                langsmith.trace.current_run_tree.extra["context_used"] = context_used
                langsmith.trace.current_run_tree.extra["context_length"] = context_length
                
            except (ImportError, AttributeError):
                # LangSmith不可用或未正确配置
                pass
            
            # 发送思考状态
            yield {
                "type": "thinking",
                "conversation_id": conversation_id,
                "context_used": context_used,
                "message": "AI正在思考..."
            }
            
            # 记录响应用于添加到内存
            full_response = ""
            
            # 检查LLM是否支持流式输出
            if hasattr(llm, 'astream'):
                # 使用LangChain的流式输出
                async for chunk in llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                        yield {
                            "type": "message_chunk",
                            "content": chunk.content,
                            "full_content": full_response,
                            "conversation_id": conversation_id,
                            "context_used": context_used
                        }
            else:
                # 降级到非流式处理，但模拟流式效果
                response = llm.invoke(messages)
                content = response.content
                full_response = content
                
                # 模拟逐字输出效果
                words = content.split()
                accumulated_text = ""
                
                for i, word in enumerate(words):
                    accumulated_text += word + " "
                    yield {
                        "type": "message_chunk",
                        "content": word + " ",
                        "full_content": accumulated_text.strip(),
                        "conversation_id": conversation_id,
                        "context_used": context_used
                    }
                    # 添加小延迟模拟打字效果
                    await asyncio.sleep(0.05)
            
            # 将AI回复添加到内存
            if memory and full_response:
                self.context_manager.add_message(conversation_id, "assistant", full_response)
            
            # 发送完成信号
            yield {
                "type": "message_complete",
                "intent": "general",
                "chain_id": chain_id,
                "conversation_id": conversation_id,
                "context_used": context_used,
                "context_length": context_length
            }
            
        except Exception as e:
            logger.error(f"通用对话流式处理失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "conversation_id": conversation_id,
                "message": "对话处理失败，请检查AI配置是否正确"
            }
    
    async def _process_transaction_intent(self, request: AIChatRequest, chain_id: str, conversation_id: str, memory) -> AIChatResponse:
        """处理记账意图"""
        # TODO: 实现记账逻辑
        context_used = memory is not None
        return AIChatResponse(
            intent="transaction",
            status="completed",
            message=f"识别到记账需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "transaction", "user_input": request.message},
            chain_id=chain_id,
            conversation_id=conversation_id,
            context_used=context_used
        )
    
    async def _process_query_intent(self, request: AIChatRequest, chain_id: str, conversation_id: str, memory) -> AIChatResponse:
        """处理查询意图"""
        # TODO: 实现查询逻辑
        context_used = memory is not None
        return AIChatResponse(
            intent="query",
            status="completed",
            message=f"识别到查询需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "query", "user_input": request.message},
            chain_id=chain_id,
            conversation_id=conversation_id,
            context_used=context_used
        )
    
    async def _process_management_intent(self, request: AIChatRequest, chain_id: str, conversation_id: str, memory) -> AIChatResponse:
        """处理管理意图"""
        # TODO: 实现管理逻辑
        context_used = memory is not None
        return AIChatResponse(
            intent="management",
            status="completed",
            message=f"识别到管理需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "management", "user_input": request.message},
            chain_id=chain_id,
            conversation_id=conversation_id,
            context_used=context_used
        )
    
    async def _process_general_intent(self, request: AIChatRequest, chain_id: str, conversation_id: str, memory) -> AIChatResponse:
        """处理通用对话意图"""
        try:
            # 创建LLM实例进行通用对话
            llm = self.create_llm_instance()
            context_used = memory is not None
            
            # 构建系统提示
            system_prompt = """你是Beancount Web记账系统的AI助手。你可以帮助用户：
1. 记录交易和账目
2. 查询和分析财务数据
3. 管理系统设置

请用简洁友好的方式回复用户。如果用户想要记账、查询或设置功能，引导他们使用更具体的描述。
在多轮对话中，请结合之前的对话内容来回复，保持上下文的连贯性。"""
            
            from langchain.schema import HumanMessage, SystemMessage
            
            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]
            
            # 如果有上下文记忆，加入历史对话
            if memory:
                try:
                    # 获取历史对话
                    memory_vars = self.context_manager.get_memory_variables(conversation_id)
                    chat_history = memory_vars.get("chat_history", [])
                    
                    # 将历史消息添加到消息列表中
                    messages.extend(chat_history)
                    
                    logger.debug(f"加载了 {len(chat_history)} 条历史消息到对话上下文")
                    
                except Exception as e:
                    logger.warning(f"加载历史对话失败: {e}")
            
            # 添加当前用户消息
            messages.append(HumanMessage(content=request.message))
            
            # 调用LLM生成回复
            response = llm.invoke(messages)
            
            return AIChatResponse(
                intent="general",
                status="completed",
                message=response.content,
                data={
                    "response_type": "general_chat",
                    "context_length": len(messages) - 2,  # 减去系统提示和当前消息
                    "memory_type": self.context_manager.get_context_config()["memory_type"] if context_used else None
                },
                chain_id=chain_id,
                conversation_id=conversation_id,
                context_used=context_used
            )
            
        except Exception as e:
            logger.error(f"通用对话处理失败: {e}")
            return AIChatResponse(
                intent="general",
                status="failed",
                message="抱歉，我现在无法正常回复。请检查AI配置是否正确。",
                data={"error": str(e)},
                chain_id=chain_id,
                conversation_id=conversation_id,
                context_used=False
            )
