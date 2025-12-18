"""
表达 Agent (Expressing Agent)

负责根据收集的数据生成自然语言回答。
实现 PEER 模式中的 Express 阶段。
"""
import logging
from typing import Dict, Any

from app.ai.agents.base import Agent, AgentInput, AgentOutput
from app.ai.llm.dashscope_llm import get_llm

logger = logging.getLogger(__name__)


class ExpressingAgent(Agent):
    """
    表达 Agent
    
    根据收集的财务数据，生成自然语言的分析回答。
    """
    
    @property
    def name(self) -> str:
        return "expressing_agent"
    
    @property
    def description(self) -> str:
        """从 YAML 配置读取描述"""
        config = self._load_config()
        return config.get('info', {}).get('description', '表达 Agent')
    
    def _build_prompt(self, original_question: str, data_summary: str) -> str:
        """构建表达提示词"""
        return f"""# 身份设定
你是一名专业的个人财务分析师，善于将财务数据转化为通俗易懂的分析结论和建议。

# 目标
根据用户的问题和查询到的财务数据，给出专业、实用、易懂的分析回答。

# 回答要求
1. 直接回答用户的问题，不要重复问题本身
2. 基于提供的数据进行分析，不要编造数据
3. 如果数据不足以完全回答问题，说明需要哪些额外信息
4. 给出具体的数字和分析，避免空泛的描述
5. 适当给出理财建议，但要贴合实际情况
6. 回答使用中文，语言要简洁专业
7. 金额保留2位小数
8. 使用适当的格式（列表、分段）提升可读性

# 查询到的财务数据
{data_summary}

# 用户问题
{original_question}

请给出你的分析回答："""
    
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """生成分析回答"""
        original_question = agent_input.get("original_question", "")
        data_summary = agent_input.get("data_summary", "")
        
        if not original_question:
            return AgentOutput(
                success=False,
                error="用户问题不能为空",
                response=""
            )
        
        if not data_summary or data_summary == "暂无可用数据":
            return AgentOutput(
                success=False,
                error="没有可用的财务数据进行分析",
                response="抱歉，暂时无法获取相关财务数据，请确保账本中有数据记录。"
            )
        
        try:
            llm = get_llm()
            prompt = self._build_prompt(original_question, data_summary)
            
            messages = [{"role": "user", "content": prompt}]
            response = await llm.call(messages, temperature=0.7)
            
            logger.info(f"表达完成: 问题='{original_question[:30]}...', 回答长度={len(response)}")
            
            return AgentOutput(
                success=True,
                original_question=original_question,
                response=response,
                output=response
            )
            
        except Exception as e:
            logger.error(f"表达生成失败: {e}")
            return AgentOutput(
                success=False,
                error=str(e),
                response=f"生成回答时出现错误：{str(e)}"
            )
    
    async def run_stream(self, agent_input: AgentInput):
        """流式生成分析回答"""
        original_question = agent_input.get("original_question", "")
        data_summary = agent_input.get("data_summary", "")
        
        if not original_question:
            yield {"type": "error", "content": "用户问题不能为空"}
            return
        
        if not data_summary or data_summary == "暂无可用数据":
            yield {"type": "error", "content": "没有可用的财务数据进行分析"}
            return
        
        try:
            llm = get_llm()
            prompt = self._build_prompt(original_question, data_summary)
            
            messages = [{"role": "user", "content": prompt}]
            
            async for chunk in llm.stream(messages, temperature=0.7):
                yield {"type": "content", "content": chunk}
            
            yield {"type": "done", "content": ""}
            
        except Exception as e:
            logger.error(f"流式表达生成失败: {e}")
            yield {"type": "error", "content": str(e)}


# Agent 实例
expressing_agent = ExpressingAgent()
