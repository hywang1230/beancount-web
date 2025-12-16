"""
账本查询工具 - AgentUniverse Tool 实现

继承 Tool 基类，提供对 Beancount 账本数据的查询能力。
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.ai.tools.base import Tool, ToolInput

logger = logging.getLogger(__name__)


class LedgerTool(Tool):
    """
    账本查询工具
    
    提供对 Beancount 账本数据的查询能力，包括：
    - get_transactions: 获取交易记录
    - get_accounts: 获取账户列表
    - get_payees: 获取收付方列表
    - get_current_month_summary: 获取当月摘要
    """
    
    @property
    def name(self) -> str:
        return "ledger_tool"
    
    @property
    def description(self) -> str:
        return """账本查询工具，用于获取 Beancount 账本数据。
支持的操作(action参数)：
- get_transactions: 获取交易记录，可选参数: start_date, end_date, account, payee, limit
- get_accounts: 获取所有账户列表
- get_payees: 获取所有收付方列表
- get_current_month_summary: 获取当月收支摘要和交易明细"""
    
    def execute(self, tool_input: ToolInput) -> Dict[str, Any]:
        """执行账本查询"""
        action = tool_input.get_data("action", "get_current_month_summary")
        
        if action == "get_transactions":
            return self._get_transactions(tool_input)
        elif action == "get_accounts":
            return self._get_accounts()
        elif action == "get_payees":
            return self._get_payees()
        elif action == "get_current_month_summary":
            return self._get_current_month_summary()
        else:
            return {"success": False, "error": f"不支持的操作类型: {action}"}
    
    def _get_transactions(self, tool_input: ToolInput) -> Dict[str, Any]:
        """获取交易记录"""
        from app.services.beancount_service import beancount_service
        from app.models.schemas import TransactionFilter
        
        try:
            filter_params = TransactionFilter()
            
            start_date = tool_input.get_data("start_date")
            end_date = tool_input.get_data("end_date")
            account = tool_input.get_data("account")
            payee = tool_input.get_data("payee")
            limit = tool_input.get_data("limit", 50)
            
            if start_date:
                if isinstance(start_date, str):
                    filter_params.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                else:
                    filter_params.start_date = start_date
            if end_date:
                if isinstance(end_date, str):
                    filter_params.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                else:
                    filter_params.end_date = end_date
            if account:
                filter_params.account = account
            if payee:
                filter_params.payee = payee
            
            transactions = beancount_service.get_transactions(filter_params)
            transactions = transactions[:limit]
            
            return {
                "success": True,
                "count": len(transactions),
                "transactions": [self._format_transaction(t) for t in transactions]
            }
        except Exception as e:
            logger.error(f"获取交易失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_accounts(self) -> Dict[str, Any]:
        """获取账户列表"""
        from app.services.beancount_service import beancount_service
        
        try:
            accounts = beancount_service.get_accounts()
            return {
                "success": True,
                "count": len(accounts),
                "accounts": accounts
            }
        except Exception as e:
            logger.error(f"获取账户失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_payees(self) -> Dict[str, Any]:
        """获取收付方列表"""
        from app.services.beancount_service import beancount_service
        
        try:
            payees = beancount_service.get_payees()
            return {
                "success": True,
                "count": len(payees),
                "payees": payees
            }
        except Exception as e:
            logger.error(f"获取收付方失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_current_month_summary(self) -> Dict[str, Any]:
        """获取当月收支摘要"""
        from app.services.beancount_service import beancount_service
        from app.models.schemas import TransactionFilter
        
        try:
            # 强制重新加载数据
            beancount_service.loader.load_entries(force_reload=True)
            
            today = datetime.now().date()
            start_of_month = today.replace(day=1)
            
            logger.info(f"="*60)
            logger.info(f"[LedgerTool] 获取当月摘要: {start_of_month} ~ {today}")
            
            # 获取损益表
            income_statement = beancount_service.get_income_statement(start_of_month, today)
            
            # 获取资产负债表
            balance_sheet = beancount_service.get_balance_sheet(today)
            
            # 获取交易明细
            filter_params = TransactionFilter(start_date=start_of_month, end_date=today)
            transactions = beancount_service.get_transactions(filter_params)
            
            # 打印摘要信息
            logger.info(f"[LedgerTool] 收入总额: {income_statement.total_income}")
            logger.info(f"[LedgerTool] 支出总额: {income_statement.total_expenses}")
            logger.info(f"[LedgerTool] 净收入: {income_statement.net_income}")
            logger.info(f"[LedgerTool] 总资产: {balance_sheet.total_assets}")
            logger.info(f"[LedgerTool] 总负债: {balance_sheet.total_liabilities}")
            logger.info(f"[LedgerTool] 净资产: {balance_sheet.net_worth}")
            
            # 打印详细流水明细
            logger.info(f"[LedgerTool] 当月交易数量: {len(transactions)}")
            logger.info(f"-"*60)
            logger.info(f"[LedgerTool] === 发送给大模型的流水明细 ({len(transactions)}笔) ===")
            for i, tx in enumerate(transactions):
                postings_str = ", ".join([
                    f"{p.account}: {p.amount} {p.currency or 'CNY'}" 
                    for p in (tx.postings or [])
                ])
                logger.debug(f"[LedgerTool] [{i+1}] {tx.date} | {tx.payee or ''} | {tx.narration or ''} | {postings_str}")
            logger.info(f"-"*60)
            logger.info(f"="*60)
            
            def extract_category_name(raw_category: str) -> str:
                """
                提取分类的中文名称，去除字母前缀
                例如：SM-数码 -> 数码, Food -> Food
                """
                import re
                # 匹配 "字母-中文" 或 "字母数字-中文" 的模式
                match = re.match(r'^[A-Za-z0-9]+-(.+)$', raw_category)
                if match:
                    return match.group(1)
                return raw_category
            
            # 构建支出账户分类汇总（按 Expenses: 下的第二级账户分类）
            expense_by_category = {}
            for acc in income_statement.expense_accounts:
                # 提取分类名称 (Expenses:SM-数码:xxx -> 数码)
                parts = acc.name.split(":")
                if len(parts) >= 2:
                    raw_category = parts[1]  # 获取第二级作为分类
                    category = extract_category_name(raw_category)
                else:
                    category = acc.name
                
                if category not in expense_by_category:
                    expense_by_category[category] = {
                        "category": category,
                        "amount": 0.0,
                        "accounts": []
                    }
                expense_by_category[category]["amount"] += float(acc.balance)
                expense_by_category[category]["accounts"].append({
                    "name": acc.name,
                    "amount": float(acc.balance)
                })
            
            # 构建收入账户分类汇总
            income_by_category = {}
            for acc in income_statement.income_accounts:
                parts = acc.name.split(":")
                if len(parts) >= 2:
                    raw_category = parts[1]
                    category = extract_category_name(raw_category)
                else:
                    category = acc.name
                
                if category not in income_by_category:
                    income_by_category[category] = {
                        "category": category,
                        "amount": 0.0,
                        "accounts": []
                    }
                # 收入账户余额是负数，取绝对值
                income_by_category[category]["amount"] += abs(float(acc.balance))
                income_by_category[category]["accounts"].append({
                    "name": acc.name,
                    "amount": abs(float(acc.balance))
                })
            
            return {
                "success": True,
                "period": f"{today.year}年{today.month}月",
                "current_month": {
                    "total_income": float(income_statement.total_income),
                    "total_expenses": float(income_statement.total_expenses),
                    "net_income": float(income_statement.net_income)
                },
                "balance": {
                    "total_assets": float(balance_sheet.total_assets),
                    "total_liabilities": float(balance_sheet.total_liabilities),
                    "net_worth": float(balance_sheet.net_worth)
                },
                # 按账户分类的支出汇总
                "expense_by_category": list(expense_by_category.values()),
                # 按账户分类的收入汇总
                "income_by_category": list(income_by_category.values()),
                "transactions_count": len(transactions),
                "transactions": [self._format_transaction(t) for t in transactions]
            }
        except Exception as e:
            logger.error(f"获取当月摘要失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _format_transaction(self, tx) -> Dict[str, Any]:
        """格式化交易数据"""
        postings = []
        for p in (tx.postings or []):
            postings.append({
                "account": p.account,
                "amount": float(p.amount) if p.amount else 0,
                "currency": p.currency or "CNY"
            })
        
        return {
            "date": tx.date.isoformat() if hasattr(tx.date, 'isoformat') else str(tx.date),
            "payee": tx.payee or "",
            "narration": tx.narration or "",
            "postings": postings
        }


# 工具实例
ledger_tool = LedgerTool()
