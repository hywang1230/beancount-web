from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ai_schemas import AIChatRequest, AIChatResponse
from app.services.ai_config_service import AIConfigService
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
            
            logger.info(f"处理聊天请求[{chain_id}]: {request.message}")
            
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
                    chain_id=chain_id
                )
            
            # 根据意图处理不同类型的请求
            if intent == "transaction":
                return await self._process_transaction_intent(request, chain_id)
            elif intent == "query":
                return await self._process_query_intent(request, chain_id)
            elif intent == "management":
                return await self._process_management_intent(request, chain_id)
            else:
                return await self._process_general_intent(request, chain_id)
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            return AIChatResponse(
                intent="unknown",
                status="failed",
                message=f"处理失败：{str(e)}",
                data={},
                chain_id=chain_id if 'chain_id' in locals() else None
            )
    
    async def process_chat_stream(self, request: AIChatRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """处理流式聊天请求"""
        # 每次处理前重新设置LangSmith（配置可能已更新）
        self._setup_langsmith()
        
        chain_id = str(uuid.uuid4())
        
        try:
            logger.info(f"处理流式聊天请求[{chain_id}]: {request.message}")
            
            # 发送开始信号
            yield {
                "type": "start",
                "chain_id": chain_id,
                "message": "开始处理您的请求..."
            }
            
            # 分类意图
            intent = self.classify_intent(request.message)
            
            # 发送意图识别结果
            yield {
                "type": "intent",
                "intent": intent,
                "message": f"识别意图: {intent}"
            }
            
            # 验证配置
            config_errors = self.config_service.validate_config()
            if config_errors:
                yield {
                    "type": "error",
                    "error": "配置不完整",
                    "message": "AI配置不完整，请先完成配置",
                    "data": {"config_errors": config_errors}
                }
                return
            
            # 根据意图处理不同类型的请求
            if intent == "general":
                async for chunk in self._process_general_stream(request, chain_id):
                    yield chunk
            else:
                # 其他意图暂时使用非流式处理
                yield {
                    "type": "message",
                    "message": f"识别到{intent}需求，此功能正在开发中，暂不支持流式输出。",
                    "intent": intent
                }
                
        except Exception as e:
            logger.error(f"流式聊天处理失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "处理失败，请重试"
            }
    
    async def _process_general_stream(self, request: AIChatRequest, chain_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """处理通用对话的流式输出"""
        try:
            # 创建LLM实例进行通用对话
            llm = self.create_llm_instance()
            
            # 简单的对话处理
            system_prompt = """你是Beancount Web记账系统的AI助手。你可以帮助用户：
1. 记录交易和账目
2. 查询和分析财务数据
3. 管理系统设置

请用简洁友好的方式回复用户。如果用户想要记账、查询或设置功能，引导他们使用更具体的描述。"""
            
            from langchain.schema import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.message)
            ]
            
            # 添加LangSmith追踪的上下文信息
            try:
                import langsmith
                
                # 设置当前会话的标签和元数据
                langsmith.trace.current_run_tree.extra["chain_id"] = chain_id
                langsmith.trace.current_run_tree.extra["intent"] = "general"
                langsmith.trace.current_run_tree.extra["user_message"] = request.message
                langsmith.trace.current_run_tree.extra["message_length"] = len(request.message)
                
            except (ImportError, AttributeError):
                # LangSmith不可用或未正确配置
                pass
            
            # 发送思考状态
            yield {
                "type": "thinking",
                "message": "AI正在思考..."
            }
            
            # 检查LLM是否支持流式输出
            if hasattr(llm, 'astream'):
                # 使用LangChain的流式输出
                full_response = ""
                async for chunk in llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        full_response += chunk.content
                        yield {
                            "type": "message_chunk",
                            "content": chunk.content,
                            "full_content": full_response
                        }
            else:
                # 降级到非流式处理，但模拟流式效果
                response = llm.invoke(messages)
                content = response.content
                
                # 模拟逐字输出效果
                words = content.split()
                accumulated_text = ""
                
                for i, word in enumerate(words):
                    accumulated_text += word + " "
                    yield {
                        "type": "message_chunk",
                        "content": word + " ",
                        "full_content": accumulated_text.strip()
                    }
                    # 添加小延迟模拟打字效果
                    await asyncio.sleep(0.05)
            
            # 发送完成信号
            yield {
                "type": "message_complete",
                "intent": "general",
                "chain_id": chain_id
            }
            
        except Exception as e:
            logger.error(f"通用对话流式处理失败: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "message": "对话处理失败，请检查AI配置是否正确"
            }
    
    async def _process_transaction_intent(self, request: AIChatRequest, chain_id: str) -> AIChatResponse:
        """处理记账意图"""
        # TODO: 实现记账逻辑
        return AIChatResponse(
            intent="transaction",
            status="completed",
            message=f"识别到记账需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "transaction", "user_input": request.message},
            chain_id=chain_id
        )
    
    async def _process_query_intent(self, request: AIChatRequest, chain_id: str) -> AIChatResponse:
        """处理查询意图"""
        # TODO: 实现查询逻辑
        return AIChatResponse(
            intent="query",
            status="completed",
            message=f"识别到查询需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "query", "user_input": request.message},
            chain_id=chain_id
        )
    
    async def _process_management_intent(self, request: AIChatRequest, chain_id: str) -> AIChatResponse:
        """处理管理意图"""
        # TODO: 实现管理逻辑
        return AIChatResponse(
            intent="management",
            status="completed",
            message=f"识别到管理需求：{request.message}。此功能正在开发中。",
            data={"detected_intent": "management", "user_input": request.message},
            chain_id=chain_id
        )
    
    async def _process_general_intent(self, request: AIChatRequest, chain_id: str) -> AIChatResponse:
        """处理通用对话意图"""
        try:
            # 创建LLM实例进行通用对话
            llm = self.create_llm_instance()
            
            # 简单的对话处理
            system_prompt = """你是Beancount Web记账系统的AI助手。你可以帮助用户：
1. 记录交易和账目
2. 查询和分析财务数据
3. 管理系统设置

请用简洁友好的方式回复用户。如果用户想要记账、查询或设置功能，引导他们使用更具体的描述。"""
            
            from langchain.schema import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=request.message)
            ]
            
            response = llm.invoke(messages)
            
            return AIChatResponse(
                intent="general",
                status="completed",
                message=response.content,
                data={"response_type": "general_chat"},
                chain_id=chain_id
            )
            
        except Exception as e:
            logger.error(f"通用对话处理失败: {e}")
            return AIChatResponse(
                intent="general",
                status="failed",
                message="抱歉，我现在无法正常回复。请检查AI配置是否正确。",
                data={"error": str(e)},
                chain_id=chain_id
            )
