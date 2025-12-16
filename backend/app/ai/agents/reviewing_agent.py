"""
审核 Agent (Reviewing Agent)

负责审核和优化最终回答的质量。
实现 PEER 模式中的 Review 阶段。
"""
import json
import logging
from typing import Dict, Any

from app.ai.agents.base import Agent, AgentInput, AgentOutput
from app.ai.llm.dashscope_llm import get_llm

logger = logging.getLogger(__name__)


class ReviewingAgent(Agent):
    """
    审核 Agent
    
    审核表达 Agent 生成的回答，确保质量和准确性。
    """
    
    @property
    def name(self) -> str:
        return "reviewing_agent"
    
    @property
    def description(self) -> str:
        return "审核 Agent，负责审核和优化最终回答的质量"
    
    def _build_prompt(self, original_question: str, response: str, data_summary: str) -> str:
        """构建审核提示词"""
        return f"""# 身份设定
你是一名资深的财务分析审核专家，负责审核回答的质量和准确性。

# 目标
审核以下回答，确保它准确、专业、有帮助。如果发现问题，请优化回答。

# 审核标准
1. 数据准确性：回答中的数字是否与提供的数据一致
2. 逻辑性：分析是否合理，结论是否有依据
3. 完整性：是否充分回答了用户的问题
4. 专业性：表述是否专业、清晰
5. 实用性：建议是否具体、可执行

# 原始数据
{data_summary}

# 用户问题
{original_question}

# 待审核的回答
{response}

# 输出格式
请按以下 JSON 格式输出审核结果：
{{
    "is_approved": true/false,
    "quality_score": 1-10,
    "issues": ["问题1", "问题2"],
    "optimized_response": "如果需要优化，提供优化后的回答；如果不需要优化，返回原回答"
}}

请输出审核结果："""
    
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """执行回答审核"""
        original_question = agent_input.get("original_question", "")
        response = agent_input.get("response", "")
        data_summary = agent_input.get("data_summary", "")
        
        if not response:
            return AgentOutput(
                success=False,
                error="没有回答需要审核",
                final_response=""
            )
        
        try:
            llm = get_llm()
            prompt = self._build_prompt(original_question, response, data_summary)
            
            messages = [{"role": "user", "content": prompt}]
            result = await llm.call(messages, temperature=0.3)
            
            # 解析审核结果
            try:
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:]
                if result.startswith("```"):
                    result = result[3:]
                if result.endswith("```"):
                    result = result[:-3]
                
                review_result = json.loads(result.strip())
                is_approved = review_result.get("is_approved", True)
                quality_score = review_result.get("quality_score", 8)
                issues = review_result.get("issues", [])
                optimized_response = review_result.get("optimized_response", response)
                
            except json.JSONDecodeError:
                logger.warning(f"无法解析审核结果，使用原回答")
                is_approved = True
                quality_score = 7
                issues = []
                optimized_response = response
            
            logger.info(f"审核完成: approved={is_approved}, score={quality_score}, issues={len(issues)}")
            
            return AgentOutput(
                success=True,
                is_approved=is_approved,
                quality_score=quality_score,
                issues=issues,
                final_response=optimized_response,
                output=optimized_response
            )
            
        except Exception as e:
            logger.error(f"审核失败: {e}")
            # 审核失败时返回原回答
            return AgentOutput(
                success=True,
                is_approved=True,
                quality_score=6,
                issues=[f"审核过程出错: {str(e)}"],
                final_response=response,
                output=response
            )


# Agent 实例
reviewing_agent = ReviewingAgent()
