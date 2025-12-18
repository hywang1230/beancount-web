"""
执行 Agent (Executing Agent)

负责根据子问题执行数据查询，收集回答问题所需的数据。
实现 PEER 模式中的 Execute 阶段。
"""
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.ai.agents.base import Agent, AgentInput, AgentOutput
from app.ai.tools.base import ToolInput
from app.ai.tools.ledger_tool import ledger_tool
from app.ai.tools.budget_tool import budget_tool
from app.ai.tools.report_tool import report_tool
from app.ai.tools.time_parser_tool import time_parser_tool

logger = logging.getLogger(__name__)


class ExecutingAgent(Agent):
    """
    执行 Agent
    
    根据规划的子问题，调用相应的工具获取数据。
    使用 LLM 进行智能意图识别和参数提取。
    """
    
    def __init__(self):
        """初始化执行 Agent"""
        super().__init__()
        self.tools = {
            "ledger": ledger_tool,
            "budget": budget_tool,
            "report": report_tool,
            "time_parser": time_parser_tool
        }
        # 从配置加载意图识别提示词
        self._intent_prompt_template = None
    
    def _get_intent_recognition_prompt(self) -> str:
        """从 YAML 配置获取意图识别提示词模板"""
        if self._intent_prompt_template is None:
            config = self._load_config()
            profile = config.get('profile', {})
            self._intent_prompt_template = profile.get('intent_recognition_prompt', '')
            
            # 如果配置中没有，使用默认模板
            if not self._intent_prompt_template:
                logger.warning(f"[{self.name}] 配置中未找到 intent_recognition_prompt，使用默认模板")
                self._intent_prompt_template = "分析用户问题: {question}"
        
        return self._intent_prompt_template
    
    @property
    def name(self) -> str:
        return "executing_agent"
    
    @property
    def description(self) -> str:
        """从 YAML 配置读取描述"""
        config = self._load_config()
        return config.get('info', {}).get('description', '执行 Agent')
    
    async def _analyze_intent_with_llm(self, question: str) -> Optional[List[Dict[str, Any]]]:
        """
        使用 LLM 分析用户意图，提取工具调用参数
        
        Args:
            question: 用户问题
            
        Returns:
            工具调用列表，如 [{"tool": "ledger_tool", "action": "get_period_summary", "params": {...}}]
        """
        try:
            from app.ai.llm.dashscope_llm import get_llm
            from app.ai.utils import parse_llm_json_response
            
            llm = get_llm()
            
            # 获取配置化的提示词模板
            prompt_template = self._get_intent_recognition_prompt()
            
            # 格式化提示词
            prompt = prompt_template.format(question=question)
            
            messages = [{"role": "user", "content": prompt}]
            
            # 获取 LLM 参数
            llm_params = self._get_llm_params()
            
            logger.debug(f"[ExecutingAgent] 使用 LLM 分析意图，问题: {question}")
            response = await llm.call(messages, **llm_params)
            
            logger.debug(f"[意图识别] LLM 原始响应: {response}")
            
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                tool_calls = result.get("tool_calls", [])
                
                if tool_calls:
                    logger.info(f"[意图识别] LLM 识别成功: {len(tool_calls)} 个工具调用")
                    for call in tool_calls:
                        logger.info(f"  - {call.get('tool')}.{call.get('action')}: {call.get('params', {})}")
                    return tool_calls
            
            logger.warning(f"[意图识别] 无法从 LLM 响应中提取有效 JSON")
            return None
            
        except Exception as e:
            logger.warning(f"[意图识别] LLM 分析失败: {e}")
            return None
    
    def _determine_tools_needed(self, sub_questions: List[str], analysis_type: str) -> List[Dict[str, Any]]:
        """
        根据子问题确定需要调用的工具
        
        Args:
            sub_questions: 子问题列表
            analysis_type: 分析类型
            
        Returns:
            需要调用的工具和参数列表
        """
        tool_calls = []
        
        # 基于分析类型和关键词确定需要的工具
        keywords_check = " ".join(sub_questions)
        keywords_check_lower = keywords_check.lower()
        
        # 注意：时间解析现在由 LLM 意图识别和 time_parser_tool 处理
        # 此方法仅作为 LLM 意图识别失败时的简单回退逻辑
        
        # 账本/交易相关 - 默认查询当月
        if any(kw in keywords_check_lower for kw in ["交易", "消费", "花", "支出", "收入", "账单", "明细", "多少钱", "开支", "花费", "最大", "最多", "最高"]):
            tool_calls.append({
                "tool": "ledger",
                "action": "get_current_month_summary",
                "params": {}
            })
        
        # 预算相关
        if any(kw in keywords_check_lower for kw in ["预算", "超支", "额度", "控制"]):
            tool_calls.append({
                "tool": "budget",
                "action": "get_budget_summary",
                "params": {}
            })
        
        # 报表/趋势相关
        if any(kw in keywords_check_lower for kw in ["趋势", "变化", "对比", "历史", "走势"]):
            tool_calls.append({
                "tool": "report",
                "action": "get_trends",
                "params": {"months": 6}
            })
        
        # 资产相关
        if any(kw in keywords_check_lower for kw in ["资产", "负债", "净值", "财产"]):
            tool_calls.append({
                "tool": "report",
                "action": "get_balance_sheet",
                "params": {}
            })
        
        # 如果没有匹配到任何工具，默认获取当月摘要（作为回退）
        if not tool_calls:
            tool_calls.append({
                "tool": "ledger",
                "action": "get_current_month_summary",
                "params": {}
            })
        
        return tool_calls
    
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """执行数据查询"""
        sub_questions = agent_input.get("sub_questions", [])
        analysis_type = agent_input.get("analysis_type", "综合分析")
        original_question = agent_input.get("original_question", "")
        
        if not sub_questions:
            return AgentOutput(
                success=False,
                error="没有子问题需要执行",
                data={}
            )
        
        try:
            # 构建完整的查询文本
            full_question = original_question or " ".join(sub_questions)
            
            # 优先尝试使用 LLM 进行意图识别
            tool_calls = await self._analyze_intent_with_llm(full_question)
            
            # 如果 LLM 分析失败，回退到关键词匹配
            if not tool_calls:
                logger.info("[意图识别] LLM 分析未返回结果，回退到关键词匹配")
                tool_calls = self._determine_tools_needed(sub_questions, analysis_type)
            
            logger.info(f"执行数据查询: 子问题数={len(sub_questions)}, 工具调用数={len(tool_calls)}")
            
            # 执行工具调用
            collected_data = {}
            for call in tool_calls:
                tool_name = call.get("tool", "")
                action = call.get("action", "")
                params = call.get("params", {})
                
                # 处理 LLM 可能返回的工具名称格式（如 "ledger_tool" -> "ledger"）
                tool_name = tool_name.replace("_tool", "")
                
                tool = self.tools.get(tool_name)
                if tool:
                    tool_input = ToolInput.from_dict({"action": action, **params})
                    result = tool.execute(tool_input)
                    
                    if result.get("success"):
                        collected_data[f"{tool_name}_{action}"] = result
                        logger.info(f"工具调用成功: {tool_name}.{action}")
                    else:
                        logger.warning(f"工具调用失败: {tool_name}.{action} - {result.get('error')}")
                else:
                    logger.warning(f"未知工具: {tool_name}")
            
            # 构建数据摘要
            data_summary = self._build_data_summary(collected_data)
            
            return AgentOutput(
                success=True,
                original_question=original_question,
                sub_questions=sub_questions,
                collected_data=collected_data,
                data_summary=data_summary,
                output=data_summary
            )
            
        except Exception as e:
            logger.error(f"数据执行失败: {e}")
            return AgentOutput(
                success=False,
                error=str(e),
                data={}
            )
    
    def _build_data_summary(self, collected_data: Dict[str, Any]) -> str:
        """构建数据摘要文本"""
        summary_parts = []
        
        # 处理当月摘要
        if "ledger_get_current_month_summary" in collected_data:
            data = collected_data["ledger_get_current_month_summary"]
            current_month = data.get("current_month", {})
            balance = data.get("balance", {})
            
            summary_parts.append(f"""【当月收支情况】({data.get('period', '本月')})
- 本月收入: {current_month.get('total_income', 0):.2f} 元
- 本月支出: {current_month.get('total_expenses', 0):.2f} 元
- 本月结余: {current_month.get('net_income', 0):.2f} 元
- 交易笔数: {data.get('transactions_count', 0)} 笔""")
            
            summary_parts.append(f"""【资产负债情况】
- 总资产: {balance.get('total_assets', 0):.2f} 元
- 总负债: {balance.get('total_liabilities', 0):.2f} 元
- 净资产: {balance.get('net_worth', 0):.2f} 元""")
            
            # 添加按账户分类的支出汇总（这是分类统计的核心数据）
            expense_by_category = data.get("expense_by_category", [])
            if expense_by_category:
                category_lines = []
                # 按金额降序排列
                sorted_expenses = sorted(expense_by_category, key=lambda x: x.get('amount', 0), reverse=True)
                for cat in sorted_expenses:
                    category_name = cat.get('category', '')
                    amount = cat.get('amount', 0)
                    # 列出子账户明细
                    sub_accounts = cat.get('accounts', [])
                    sub_details = ", ".join([f"{acc.get('name', '')}: {acc.get('amount', 0):.2f}" for acc in sub_accounts])
                    category_lines.append(f"  - {category_name}: {amount:.2f} 元 ({sub_details})")
                
                summary_parts.append(f"""【按账户分类的支出汇总】（此为分类统计的依据）
{chr(10).join(category_lines)}""")
            
            # 添加按账户分类的收入汇总
            income_by_category = data.get("income_by_category", [])
            if income_by_category:
                income_lines = []
                sorted_incomes = sorted(income_by_category, key=lambda x: x.get('amount', 0), reverse=True)
                for cat in sorted_incomes:
                    category_name = cat.get('category', '')
                    amount = cat.get('amount', 0)
                    income_lines.append(f"  - {category_name}: {amount:.2f} 元")
                
                summary_parts.append(f"""【按账户分类的收入汇总】
{chr(10).join(income_lines)}""")
            
            # 添加交易明细摘要
            transactions = data.get("transactions", [])
            if transactions:
                tx_details = []
                for tx in transactions:  # 显示全部交易，不再限制数量
                    date = tx.get("date", "")
                    desc = f"{tx.get('payee', '')} {tx.get('narration', '')}".strip() or ""
                    postings = tx.get("postings", [])
                    # 包含账户信息，帮助 AI 理解每笔交易的分类
                    amounts = [f"{p.get('account', '')}: {p.get('amount', 0):.2f} {p.get('currency', 'CNY')}" for p in postings]
                    tx_details.append(f"  - {date} {desc}: {', '.join(amounts)}")
                
                summary_parts.append(f"""【交易明细】(共{len(transactions)}笔)
{chr(10).join(tx_details)}""")
        
        # 处理时间段摘要 (get_period_summary)
        if "ledger_get_period_summary" in collected_data:
            data = collected_data["ledger_get_period_summary"]
            period_summary = data.get("period_summary", {})
            balance = data.get("balance", {})
            period = data.get("period", "指定时间段")
            
            summary_parts.append(f"""【{period} 收支情况】
- 收入总额: {period_summary.get('total_income', 0):.2f} 元
- 支出总额: {period_summary.get('total_expenses', 0):.2f} 元
- 结余: {period_summary.get('net_income', 0):.2f} 元
- 交易笔数: {data.get('transactions_count', 0)} 笔""")
            
            summary_parts.append(f"""【资产负债情况】(截止 {data.get('end_date', '')})
- 总资产: {balance.get('total_assets', 0):.2f} 元
- 总负债: {balance.get('total_liabilities', 0):.2f} 元
- 净资产: {balance.get('net_worth', 0):.2f} 元""")
            
            # 添加按账户分类的支出汇总
            expense_by_category = data.get("expense_by_category", [])
            if expense_by_category:
                category_lines = []
                sorted_expenses = sorted(expense_by_category, key=lambda x: x.get('amount', 0), reverse=True)
                for cat in sorted_expenses:
                    category_name = cat.get('category', '')
                    amount = cat.get('amount', 0)
                    sub_accounts = cat.get('accounts', [])
                    sub_details = ", ".join([f"{acc.get('name', '')}: {acc.get('amount', 0):.2f}" for acc in sub_accounts])
                    category_lines.append(f"  - {category_name}: {amount:.2f} 元 ({sub_details})")
                
                summary_parts.append(f"""【按账户分类的支出汇总】
{chr(10).join(category_lines)}""")
            
            # 添加按账户分类的收入汇总
            income_by_category = data.get("income_by_category", [])
            if income_by_category:
                income_lines = []
                sorted_incomes = sorted(income_by_category, key=lambda x: x.get('amount', 0), reverse=True)
                for cat in sorted_incomes:
                    category_name = cat.get('category', '')
                    amount = cat.get('amount', 0)
                    income_lines.append(f"  - {category_name}: {amount:.2f} 元")
                
                summary_parts.append(f"""【按账户分类的收入汇总】
{chr(10).join(income_lines)}""")
            
            # 添加交易明细
            transactions = data.get("transactions", [])
            if transactions:
                tx_details = []
                for tx in transactions:
                    date = tx.get("date", "")
                    desc = f"{tx.get('payee', '')} {tx.get('narration', '')}".strip() or ""
                    postings = tx.get("postings", [])
                    amounts = [f"{p.get('account', '')}: {p.get('amount', 0):.2f} {p.get('currency', 'CNY')}" for p in postings]
                    tx_details.append(f"  - {date} {desc}: {', '.join(amounts)}")
                
                summary_parts.append(f"""【交易明细】(共{len(transactions)}笔)
{chr(10).join(tx_details)}""")
        
        # 处理预算摘要
        if "budget_get_budget_summary" in collected_data:
            data = collected_data["budget_get_budget_summary"]
            summary = data.get("summary", {})
            
            summary_parts.append(f"""【预算执行情况】
- 总预算: {summary.get('total_budget', 0):.2f} 元
- 已花费: {summary.get('total_spent', 0):.2f} 元
- 剩余: {summary.get('total_remaining', 0):.2f} 元
- 执行进度: {summary.get('overall_progress', 0):.1f}%
- 超支预算数: {summary.get('over_budget_count', 0)} 个""")
        
        # 处理趋势数据
        if "report_get_trends" in collected_data:
            data = collected_data["report_get_trends"]
            trends = data.get("data", [])
            
            if trends:
                trend_lines = []
                for t in trends[-6:]:  # 显示最近6个月
                    trend_lines.append(f"  - {t.get('period')}: 收入 {t.get('total_income', 0):.0f}, 支出 {t.get('total_expenses', 0):.0f}, 结余 {t.get('net_income', 0):.0f}")
                
                summary_parts.append(f"""【收支趋势】(最近{len(trend_lines)}个月)
{chr(10).join(trend_lines)}""")
        
        # 处理资产负债表
        if "report_get_balance_sheet" in collected_data:
            data = collected_data["report_get_balance_sheet"]
            bs_data = data.get("data", {})
            
            summary_parts.append(f"""【资产负债表】(截止 {data.get('as_of_date', '今日')})
- 总资产: {bs_data.get('total_assets', 0):.2f} 元
- 总负债: {bs_data.get('total_liabilities', 0):.2f} 元
- 净资产: {bs_data.get('net_worth', 0):.2f} 元""")
        
        return "\n\n".join(summary_parts) if summary_parts else "暂无可用数据"


# Agent 实例
executing_agent = ExecutingAgent()
