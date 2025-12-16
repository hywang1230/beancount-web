"""
通义千问 LLM 实现

继承 AgentUniverse LLM 基类，实现 DashScope API 调用。
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any, Union, AsyncGenerator

import httpx

logger = logging.getLogger(__name__)


class DashScopeLLM:
    """
    通义千问 LLM 实现
    
    使用 DashScope OpenAI 兼容接口调用通义千问模型。
    """
    
    def __init__(
        self,
        model_name: str = "qwen3-max",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key: Optional[str] = None
    ):
        """
        初始化 DashScope LLM
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            api_base: API 基础地址
            api_key: API 密钥，如果不提供则从环境变量读取
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 未配置")
    
    @property
    def name(self) -> str:
        return "qwen_llm"
    
    @property
    def description(self) -> str:
        return "通义千问 LLM - 使用 DashScope API"
    
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        return bool(self.api_key)
    
    async def call(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        调用 LLM 生成响应
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/assistant/system", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            生成的响应文本
        """
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")
        
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        request_body = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 详细日志：记录请求信息
        logger.info(f"="*60)
        logger.info(f"[LLM 请求] model={self.model_name}, temperature={temperature}, max_tokens={max_tokens}")
        logger.info(f"[LLM 请求] messages_count={len(messages)}")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # 截断过长的内容以便日志可读
            content_preview = content[:500] + "..." if len(content) > 500 else content
            logger.debug(f"[LLM 请求] Message[{i}] role={role}: {content_preview}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            
            if response.status_code != 200:
                logger.error(f"[LLM 错误] status={response.status_code}, response={response.text}")
                response.raise_for_status()
            
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            
            # 详细日志：记录响应信息
            usage = result.get("usage", {})
            logger.info(f"[LLM 响应] 成功, 字符数={len(answer)}")
            logger.info(f"[LLM 响应] token使用: prompt={usage.get('prompt_tokens', 'N/A')}, completion={usage.get('completion_tokens', 'N/A')}, total={usage.get('total_tokens', 'N/A')}")
            answer_preview = answer[:300] + "..." if len(answer) > 300 else answer
            logger.debug(f"[LLM 响应] 内容预览: {answer_preview}")
            logger.info(f"="*60)
            
            return answer
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式调用 LLM 生成响应
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            生成的响应文本块
        """
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")
        
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        request_body = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        logger.info(f"="*60)
        logger.info(f"[LLM 流式请求] model={self.model_name}, temperature={temperature}, max_tokens={max_tokens}")
        logger.info(f"[LLM 流式请求] messages_count={len(messages)}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request_body
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    logger.error(f"DashScope API 错误: {response.status_code} - {error_text}")
                    raise Exception(f"API调用失败: {response.status_code}")
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        
        logger.info("DashScope LLM 流式响应完成")


# 全局 LLM 实例
_llm_instance: Optional[DashScopeLLM] = None


def get_llm() -> DashScopeLLM:
    """获取 LLM 单例实例"""
    global _llm_instance
    if _llm_instance is None:
        from app.core.config import settings
        _llm_instance = DashScopeLLM(
            api_key=settings.dashscope_api_key
        )
    return _llm_instance
