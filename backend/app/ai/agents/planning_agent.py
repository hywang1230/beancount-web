"""
规划 Agent (Planning Agent)

负责将复杂的用户问题拆解为多个子问题，以便后续处理。
实现 PEER 模式中的 Plan 阶段。
"""
import json
import logging
from typing import List, Dict, Any

from app.ai.agents.base import Agent, AgentInput, AgentOutput
from app.ai.llm.dashscope_llm import get_llm

logger = logging.getLogger(__name__)


class PlanningAgent(Agent):
    """
    规划 Agent
    
    将用户的财务问题拆解为可执行的子问题列表。
    """
    
    @property
    def name(self) -> str:
        return "planning_agent"
    
    @property
    def description(self) -> str:
        """从 YAML 配置读取描述"""
        config = self._load_config()
        return config.get('info', {}).get('description', '规划 Agent')
    
    def _build_prompt(self, user_question: str) -> str:
        """构建规划提示词"""
        return f"""# 身份设定
你是一名专业的个人财务分析规划师，善于分析用户的财务相关问题。

# 目标
将用户提出的财务问题进行拆解，生成多个子问题，以便更好地分析和回答。

# 规则
1. 每个拆分后的子问题应该是独立的、可以单独回答的问题
2. 子问题应该覆盖用户原问题的各个方面
3. 子问题数量通常为 2-4 个，复杂问题可以有 3-5 个
4. 子问题应该明确、具体，便于后续数据查询
5. 如果原问题已经很简单，可以只返回一个子问题（即原问题本身）

# 财务分析相关的子问题类型
- 收入相关：本月收入、收入来源、收入趋势
- 支出相关：本月支出、支出分类、最大支出
- 资产相关：总资产、净资产、资产分布
- 预算相关：预算执行情况、超支情况
- 趋势相关：月度对比、年度趋势

# 输出格式
必须按照以下 JSON 格式输出，只输出 JSON，不要有其他文字：
{{
    "original_question": "用户原问题",
    "sub_questions": ["子问题1", "子问题2", "子问题3"],
    "analysis_type": "分析类型（如：收支分析/资产分析/预算分析/综合分析）"
}}

# 用户问题
{user_question}

请输出拆解后的子问题 JSON："""
    
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """执行问题规划"""
        user_question = agent_input.get("input", "")
        
        if not user_question:
            return AgentOutput(
                success=False,
                error="用户问题不能为空",
                sub_questions=[]
            )
        
        try:
            llm = get_llm()
            prompt = self._build_prompt(user_question)
            
            messages = [{"role": "user", "content": prompt}]
            response = await llm.call(messages, temperature=0.3)
            
            # 解析 JSON 响应
            try:
                # 尝试提取 JSON
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                
                result = json.loads(response.strip())
                sub_questions = result.get("sub_questions", [user_question])
                analysis_type = result.get("analysis_type", "综合分析")
                
            except json.JSONDecodeError:
                logger.warning(f"无法解析规划结果，使用原问题: {response[:200]}")
                sub_questions = [user_question]
                analysis_type = "综合分析"
            
            logger.info(f"问题规划完成: 原问题='{user_question[:50]}', 子问题数={len(sub_questions)}")
            
            return AgentOutput(
                success=True,
                original_question=user_question,
                sub_questions=sub_questions,
                analysis_type=analysis_type,
                output=json.dumps({"sub_questions": sub_questions}, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.error(f"问题规划失败: {e}")
            return AgentOutput(
                success=False,
                error=str(e),
                sub_questions=[user_question]
            )


# Agent 实例
planning_agent = PlanningAgent()
