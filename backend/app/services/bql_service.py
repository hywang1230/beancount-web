"""
BQL (Beancount Query Language) 查询服务
提供高级查询功能

注意：Beancount 3.0 已移除内置的 query 模块
此服务提供基于 beancount 核心 API 的简化查询功能
"""
from typing import List, Dict, Any
from beancount.core import data, realization
import re


class BQLService:
    """简化的查询服务，兼容 Beancount 3.0"""
    
    def __init__(self, loader):
        self.loader = loader
    
    def execute_query(self, query_str: str) -> Dict[str, Any]:
        """
        执行简化的查询（支持预定义的查询模式）
        
        Args:
            query_str: 查询语句或查询类型
            
        Returns:
            包含查询结果的字典
        """
        try:
            # 加载账本数据
            entries, errors, options_map = self.loader.load_entries()
            
            if errors:
                error_messages = [str(e) for e in errors[:5]]
                return {
                    'success': False,
                    'error': f"账本加载错误: {'; '.join(error_messages)}",
                    'columns': [],
                    'rows': [],
                    'types': [],
                    'row_count': 0
                }
            
            # 解析查询类型并执行相应的查询
            result = self._execute_simple_query(query_str, entries, options_map)
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f"查询执行失败: {str(e)}",
                'columns': [],
                'rows': [],
                'types': [],
                'row_count': 0
            }
    
    def _execute_simple_query(self, query_str: str, entries: List, options_map: Dict) -> Dict[str, Any]:
        """执行简化查询"""
        query_lower = query_str.lower().strip()
        
        # 账户余额查询
        if 'account' in query_lower and 'sum' in query_lower:
            return self._query_account_balances(entries, query_str)
        
        # 按时间范围查询交易
        elif 'date' in query_lower or 'recent' in query_lower:
            return self._query_transactions_by_date(entries, query_str)
        
        # 默认返回所有账户余额
        else:
            return self._query_account_balances(entries, query_str)
    
    def _query_account_balances(self, entries: List, query_str: str) -> Dict[str, Any]:
        """查询账户余额"""
        try:
            # 使用 realization 来计算账户余额
            real_root = realization.realize(entries)
            
            # 提取账户类型过滤（如果有）
            account_filter = None
            for pattern in ['Assets', 'Liabilities', 'Income', 'Expenses', 'Equity']:
                if pattern.lower() in query_str.lower():
                    account_filter = pattern
                    break
            
            rows = []
            
            def process_node(node, account_name=''):
                """递归处理账户树节点"""
                # 处理当前节点的余额
                if account_name and (not account_filter or account_name.startswith(account_filter)):
                    balance = node.balance
                    if not balance.is_empty():
                        for position in balance:
                            rows.append([
                                account_name,
                                str(position.units.number),
                                position.units.currency
                            ])
                
                # 递归处理子账户
                # RealAccount 对象本身就是类似字典的对象，直接使用 items()
                for child_name, child_node in sorted(node.items()):
                    child_account = f"{account_name}:{child_name}" if account_name else child_name
                    process_node(child_node, child_account)
            
            process_node(real_root)
            
            return {
                'success': True,
                'columns': ['account', 'amount', 'currency'],
                'rows': rows,
                'types': ['str', 'Decimal', 'str'],
                'row_count': len(rows)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"账户余额查询失败: {str(e)}",
                'columns': [],
                'rows': [],
                'types': [],
                'row_count': 0
            }
    
    def _query_transactions_by_date(self, entries: List, query_str: str) -> Dict[str, Any]:
        """按日期查询交易"""
        try:
            rows = []
            
            # 只处理交易类型的条目
            transactions = [e for e in entries if isinstance(e, data.Transaction)]
            
            # 按日期排序（最新的在前）
            transactions.sort(key=lambda x: x.date, reverse=True)
            
            # 限制返回数量
            limit = 100
            if 'limit' in query_str.lower():
                try:
                    limit = int(re.search(r'limit\s+(\d+)', query_str.lower()).group(1))
                except:
                    pass
            
            for txn in transactions[:limit]:
                rows.append([
                    str(txn.date),
                    txn.payee or '',
                    txn.narration or '',
                    str(len(txn.postings))
                ])
            
            return {
                'success': True,
                'columns': ['date', 'payee', 'narration', 'postings_count'],
                'rows': rows,
                'types': ['date', 'str', 'str', 'int'],
                'row_count': len(rows)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"交易查询失败: {str(e)}",
                'columns': [],
                'rows': [],
                'types': [],
                'row_count': 0
            }
    
    def validate_query(self, query_str: str) -> Dict[str, Any]:
        """
        验证查询语法（简化版本）
        
        Returns:
            {
                'valid': True/False,
                'error': '错误信息' (如果有)
            }
        """
        try:
            if not query_str or not query_str.strip():
                return {
                    'valid': False,
                    'error': '查询语句不能为空'
                }
            
            return {
                'valid': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"验证失败: {str(e)}"
            }
    
    def get_query_examples(self) -> List[Dict[str, str]]:
        """
        获取常用查询示例（简化版本）
        """
        return [
            {
                'name': '资产账户余额',
                'description': '查询所有资产账户当前余额',
                'query': 'account sum Assets'
            },
            {
                'name': '负债账户余额',
                'description': '查询所有负债账户余额',
                'query': 'account sum Liabilities'
            },
            {
                'name': '支出账户余额',
                'description': '查询所有支出类别的累计金额',
                'query': 'account sum Expenses'
            },
            {
                'name': '收入账户余额',
                'description': '查询所有收入类别的累计金额',
                'query': 'account sum Income'
            },
            {
                'name': '最近交易',
                'description': '查询最近的交易记录',
                'query': 'recent transactions limit 100'
            },
            {
                'name': '所有账户余额',
                'description': '查询所有账户的当前余额',
                'query': 'account sum'
            }
        ]
    
    def get_available_functions(self) -> List[Dict[str, str]]:
        """
        获取可用的查询类型（简化版本）
        """
        return [
            {
                'name': 'account sum [账户类型]',
                'description': '查询账户余额',
                'example': 'account sum Assets'
            },
            {
                'name': 'recent transactions',
                'description': '查询最近的交易',
                'example': 'recent transactions limit 50'
            },
            {
                'name': 'date',
                'description': '按日期查询交易',
                'example': 'date 2025-01-01'
            }
        ]

