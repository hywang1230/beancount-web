from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.ai_schemas import AIChatRequest, AIChatResponse
from app.services.ai_config_service import AIConfigService
import logging
import uuid

logger = logging.getLogger(__name__)


class AIChatService:
    """AI聊天服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config_service = AIConfigService(db)
    
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
            
            elif "anthropic" in provider_url.lower():
                from langchain_anthropic import ChatAnthropic
                llm_params.pop("api_key")  # Anthropic使用不同的参数名
                llm_params["anthropic_api_key"] = api_key
                return ChatAnthropic(**llm_params)
            
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
