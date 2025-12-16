"""
账本查询工具 - 封装LedgerQuery服务供AI服务使用

注意：这是简化版实现，不依赖AgentUniverse框架。
后续可以升级为完整的AgentUniverse Tool组件。
"""
from typing import Optional, Dict, Any
from datetime import datetime


class LedgerTool:
    """
    账本查询工具
    
    提供对Beancount账本数据的查询能力，包括：
    - 获取交易列表
    - 获取账户列表
    - 获取收付方列表
    """
    
    name: str = "ledger_tool"
    description: str = """账本查询工具，用于获取Beancount账本数据。
    支持的操作：
    - get_transactions: 获取交易记录，可按日期、账户、收付方筛选
    - get_accounts: 获取所有账户列表
    - get_payees: 获取所有收付方列表
    """
    
    def execute(self, action: str, start_date: Optional[str] = None, 
                end_date: Optional[str] = None, account: Optional[str] = None,
                payee: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """执行账本查询"""
        from app.services.beancount_service import beancount_service
        from app.models.schemas import TransactionFilter
        
        try:
            if action == "get_transactions":
                # 构建过滤条件
                filter_params = TransactionFilter()
                
                if start_date:
                    filter_params.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                if end_date:
                    filter_params.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                if account:
                    filter_params.account = account
                if payee:
                    filter_params.payee = payee
                
                transactions = beancount_service.get_transactions(filter_params)
                # 限制返回数量
                transactions = transactions[:limit]
                
                return {
                    "success": True,
                    "count": len(transactions),
                    "transactions": [self._format_transaction(t) for t in transactions]
                }
                
            elif action == "get_accounts":
                accounts = beancount_service.get_accounts()
                return {
                    "success": True,
                    "count": len(accounts),
                    "accounts": accounts
                }
                
            elif action == "get_payees":
                payees = beancount_service.get_payees()
                return {
                    "success": True,
                    "count": len(payees),
                    "payees": payees
                }
                
            else:
                return {
                    "success": False,
                    "error": f"不支持的操作类型: {action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_transaction(self, tx) -> Dict[str, Any]:
        """格式化交易数据"""
        return {
            "date": str(tx.date),
            "payee": tx.payee,
            "narration": tx.narration,
            "amount": str(tx.amount) if tx.amount else None,
            "currency": tx.currency,
            "type": tx.type,
            "postings": [
                {
                    "account": p.account,
                    "amount": str(p.amount) if p.amount else None,
                    "currency": p.currency
                }
                for p in (tx.postings or [])
            ]
        }


# 工具实例
ledger_tool = LedgerTool()
