"""
财务顾问主 Agent (Finance Master Agent)

负责协调 Planning、Executing、Expressing、Reviewing 四个子 Agent，
实现完整的 PEER 多 Agent 协作模式。
"""
import logging
from typing import Dict, Any, List, AsyncGenerator

from app.ai.agents.base import Agent, AgentInput, AgentOutput
from app.ai.agents.planning_agent import planning_agent
from app.ai.agents.executing_agent import executing_agent
from app.ai.agents.expressing_agent import expressing_agent
from app.ai.agents.reviewing_agent import reviewing_agent

logger = logging.getLogger(__name__)


class FinanceMasterAgent(Agent):
    """
    财务顾问主 Agent
    
    协调 PEER 模式的四个子 Agent：
    - Planning Agent: 问题规划，拆解用户问题
    - Executing Agent: 数据执行，调用工具获取数据
    - Expressing Agent: 结论表达，生成自然语言回答
    - Reviewing Agent: 质量审核，优化最终回答
    """
    
    def __init__(self, enable_review: bool = True):
        """
        初始化主 Agent
        
        Args:
            enable_review: 是否启用审核阶段（可关闭以提高响应速度）
        """
        self.enable_review = enable_review
        self.planning_agent = planning_agent
        self.executing_agent = executing_agent
        self.expressing_agent = expressing_agent
        self.reviewing_agent = reviewing_agent
    
    @property
    def name(self) -> str:
        return "finance_master_agent"
    
    @property
    def description(self) -> str:
        return "财务顾问主 Agent，协调多个子 Agent 完成财务分析任务"
    
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """
        执行完整的 PEER 流程
        
        流程：Plan -> Execute -> Express -> Review
        """
        user_question = agent_input.get("input", "")
        
        if not user_question:
            return AgentOutput(
                success=False,
                error="用户问题不能为空",
                response=""
            )
        
        logger.info(f"="*80)
        logger.info(f"[PEER 流程开始] 用户问题: {user_question}")
        logger.info(f"="*80)
        
        try:
            # Step 1: Planning - 问题规划
            logger.info(f"-"*40)
            logger.info("[Step 1: Planning] 开始问题规划...")
            logger.info(f"[Planning 输入] {user_question}")
            planning_input = AgentInput(input=user_question)
            planning_output = await self.planning_agent.run(planning_input)
            
            if not planning_output.get("success"):
                logger.warning(f"[Planning 失败] {planning_output.get('error')}")
                # 降级处理：使用原问题继续
                sub_questions = [user_question]
                analysis_type = "综合分析"
            else:
                sub_questions = planning_output.get("sub_questions", [user_question])
                analysis_type = planning_output.get("analysis_type", "综合分析")
            
            logger.info(f"[Planning 输出] 分析类型: {analysis_type}")
            logger.info(f"[Planning 输出] 子问题数量: {len(sub_questions)}")
            for i, sq in enumerate(sub_questions):
                logger.info(f"[Planning 输出] 子问题[{i+1}]: {sq}")
            
            # Step 2: Executing - 数据执行
            logger.info(f"-"*40)
            logger.info("[Step 2: Executing] 开始数据执行...")
            logger.info(f"[Executing 输入] 原始问题: {user_question}")
            logger.info(f"[Executing 输入] 分析类型: {analysis_type}")
            executing_input = AgentInput(
                original_question=user_question,
                sub_questions=sub_questions,
                analysis_type=analysis_type
            )
            executing_output = await self.executing_agent.run(executing_input)
            
            if not executing_output.get("success"):
                logger.error(f"[Executing 失败] {executing_output.get('error')}")
                logger.info(f"="*80)
                return AgentOutput(
                    success=False,
                    error=f"数据获取失败: {executing_output.get('error')}",
                    response="抱歉，获取财务数据时出现问题，请稍后重试。"
                )
            
            data_summary = executing_output.get("data_summary", "")
            data_summary_preview = data_summary[:500] + "..." if len(data_summary) > 500 else data_summary
            logger.info(f"[Executing 输出] 数据摘要长度: {len(data_summary)} 字符")
            logger.debug(f"[Executing 输出] 数据摘要预览: {data_summary_preview}")
            
            # Step 3: Expressing - 结论表达
            logger.info(f"-"*40)
            logger.info("[Step 3: Expressing] 开始结论表达...")
            expressing_input = AgentInput(
                original_question=user_question,
                data_summary=data_summary
            )
            expressing_output = await self.expressing_agent.run(expressing_input)
            
            if not expressing_output.get("success"):
                logger.error(f"[Expressing 失败] {expressing_output.get('error')}")
                logger.info(f"="*80)
                return AgentOutput(
                    success=False,
                    error=f"生成回答失败: {expressing_output.get('error')}",
                    response="抱歉，生成分析报告时出现问题。"
                )
            
            response = expressing_output.get("response", "")
            response_preview = response[:300] + "..." if len(response) > 300 else response
            logger.info(f"[Expressing 输出] 回答长度: {len(response)} 字符")
            logger.debug(f"[Expressing 输出] 回答预览: {response_preview}")
            
            # Step 4: Reviewing - 质量审核 (可选)
            if self.enable_review:
                logger.info(f"-"*40)
                logger.info("[Step 4: Reviewing] 开始质量审核...")
                reviewing_input = AgentInput(
                    original_question=user_question,
                    response=response,
                    data_summary=data_summary
                )
                reviewing_output = await self.reviewing_agent.run(reviewing_input)
                
                final_response = reviewing_output.get("final_response", response)
                quality_score = reviewing_output.get("quality_score", 7)
                logger.info(f"[Reviewing 输出] 质量分数: {quality_score}")
            else:
                final_response = response
                quality_score = None
                logger.info("[Step 4: Reviewing] 已跳过（审核已禁用）")
            
            logger.info(f"="*80)
            logger.info(f"[PEER 流程完成] 最终回答长度: {len(final_response)} 字符")
            logger.info(f"="*80)
            
            return AgentOutput(
                success=True,
                response=final_response,
                output=final_response,
                analysis_type=analysis_type,
                sub_questions=sub_questions,
                quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"PEER 流程失败: {e}")
            return AgentOutput(
                success=False,
                error=str(e),
                response=f"分析过程中出现错误：{str(e)}"
            )
    
    async def run_stream(self, agent_input: AgentInput) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式执行 PEER 流程
        
        Plan 和 Execute 阶段正常执行，Express 阶段流式输出
        """
        user_question = agent_input.get("input", "")
        
        if not user_question:
            yield {"type": "error", "content": "用户问题不能为空"}
            return
        
        logger.info(f"开始流式 PEER 流程: {user_question[:50]}...")
        
        try:
            # Step 1: Planning
            logger.info("Step 1: Planning...")
            planning_input = AgentInput(input=user_question)
            planning_output = await self.planning_agent.run(planning_input)
            
            if not planning_output.get("success"):
                sub_questions = [user_question]
                analysis_type = "综合分析"
            else:
                sub_questions = planning_output.get("sub_questions", [user_question])
                analysis_type = planning_output.get("analysis_type", "综合分析")
            
            # Step 2: Executing
            logger.info("Step 2: Executing...")
            executing_input = AgentInput(
                original_question=user_question,
                sub_questions=sub_questions,
                analysis_type=analysis_type
            )
            executing_output = await self.executing_agent.run(executing_input)
            
            if not executing_output.get("success"):
                yield {"type": "error", "content": f"数据获取失败: {executing_output.get('error')}"}
                return
            
            data_summary = executing_output.get("data_summary", "")
            
            # Step 3: Expressing (流式)
            logger.info("Step 3: Expressing (streaming)...")
            expressing_input = AgentInput(
                original_question=user_question,
                data_summary=data_summary
            )
            
            async for chunk in self.expressing_agent.run_stream(expressing_input):
                yield chunk
            
            logger.info("流式 PEER 流程完成")
            
        except Exception as e:
            logger.error(f"流式 PEER 流程失败: {e}")
            yield {"type": "error", "content": str(e)}
    
    async def chat(self, messages: List[Dict[str, str]]) -> AgentOutput:
        """
        多轮对话模式
        
        基于对话历史进行分析
        """
        if not messages:
            return AgentOutput(
                success=False,
                error="对话消息不能为空",
                response=""
            )
        
        # 获取最后一条用户消息作为当前问题
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        if not last_user_message:
            return AgentOutput(
                success=False,
                error="没有找到用户消息",
                response=""
            )
        
        # 构建上下文
        context = "\n".join([
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')}"
            for m in messages[:-1]  # 排除最后一条消息
        ])
        
        # 如果有历史上下文，将其添加到问题中
        if context:
            enhanced_question = f"对话上下文:\n{context}\n\n当前问题: {last_user_message}"
        else:
            enhanced_question = last_user_message
        
        return await self.run(AgentInput(input=enhanced_question))
    
    async def chat_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式多轮对话模式
        """
        if not messages:
            yield {"type": "error", "content": "对话消息不能为空"}
            return
        
        # 获取最后一条用户消息
        last_user_message = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break
        
        if not last_user_message:
            yield {"type": "error", "content": "没有找到用户消息"}
            return
        
        # 构建上下文
        context = "\n".join([
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')}"
            for m in messages[:-1]
        ])
        
        if context:
            enhanced_question = f"对话上下文:\n{context}\n\n当前问题: {last_user_message}"
        else:
            enhanced_question = last_user_message
        
        async for chunk in self.run_stream(AgentInput(input=enhanced_question)):
            yield chunk


# Agent 实例
finance_master_agent = FinanceMasterAgent(enable_review=False)  # 默认关闭审核以提高速度
