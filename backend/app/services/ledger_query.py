"""
账本查询服务
负责数据查询、筛选和基本数据操作
"""
from beancount.core.data import Transaction
from beancount.core import getters
from datetime import date
from typing import List, Optional, Dict, Any
from decimal import Decimal

from app.models.schemas import (
    TransactionResponse, AccountInfo, TransactionFilter, PostingBase
)
from .exchange_service import ExchangeService


class LedgerQuery:
    """账本查询服务"""
    
    def __init__(self, loader):
        self.loader = loader
        self.exchange_service = ExchangeService()
    
    def get_transactions(self, filter_params: Optional[TransactionFilter] = None) -> List[TransactionResponse]:
        """获取交易列表"""
        entries, _, _ = self.loader.load_entries()
        
        transactions = []
        for entry in entries:
            if isinstance(entry, Transaction):
                # 应用过滤器
                if filter_params:
                    if filter_params.start_date and entry.date < filter_params.start_date:
                        continue
                    if filter_params.end_date and entry.date > filter_params.end_date:
                        continue
                    if filter_params.payee and (not entry.payee or filter_params.payee.lower() not in entry.payee.lower()):
                        continue
                    if filter_params.narration and filter_params.narration.lower() not in entry.narration.lower():
                        continue
                    if filter_params.account:
                        account_match = any(filter_params.account in posting.account 
                                          for posting in entry.postings)
                        if not account_match:
                            continue
                    
                    # 交易类型筛选
                    if filter_params.transaction_type:
                        transaction_type = self._get_transaction_type(entry)
                        if transaction_type != filter_params.transaction_type:
                            continue
                
                # 转换为响应模型
                transaction = self._convert_entry_to_response(entry)
                transactions.append(transaction)
        
        # 按日期降序排列
        transactions.sort(key=lambda x: x.date, reverse=True)
        return transactions
    
    def get_transaction_by_location(self, filename: str, lineno: int) -> Optional[TransactionResponse]:
        """根据文件名和行号获取特定交易"""
        try:
            entries, _, _ = self.loader.load_entries()
            
            for entry in entries:
                if isinstance(entry, Transaction):
                    # 检查元数据中的文件名和行号
                    entry_filename = entry.meta.get('filename') if entry.meta else None
                    entry_lineno = entry.meta.get('lineno') if entry.meta else None
                    
                    if entry_filename and entry_lineno:
                        import os
                        entry_basename = os.path.basename(entry_filename)
                        if entry_basename == filename and entry_lineno == lineno:
                            # 找到匹配的交易，转换为响应格式
                            return self._convert_entry_to_response(entry)
            
            return None
            
        except Exception as e:
            # Transaction retrieval failed
            return None
    
    def get_all_accounts(self) -> List[str]:
        """获取所有账户列表（包括所有类型的账户）"""
        entries, _, _ = self.loader.load_entries()
        
        # 使用Beancount的内置方法获取所有账户
        # 这会获取所有在任何条目中出现的账户，包括Open、Transaction等
        all_accounts = getters.get_accounts(entries)
        
        return sorted(list(all_accounts))
    
    def get_archived_accounts(self) -> List[str]:
        """获取已归档的账户列表"""
        entries, _, _ = self.loader.load_entries()
        
        # 获取已关闭的账户
        from beancount.core.data import Close
        closed_accounts = set()
        for entry in entries:
            if isinstance(entry, Close):
                closed_accounts.add(entry.account)
        
        return sorted(list(closed_accounts))
    
    def get_active_accounts(self) -> List[str]:
        """获取活跃账户列表（排除已归档的账户）"""
        entries, _, _ = self.loader.load_entries()
        
        # 获取所有账户
        all_accounts = getters.get_accounts(entries)
        
        # 获取已关闭的账户
        from beancount.core.data import Close
        closed_accounts = set()
        for entry in entries:
            if isinstance(entry, Close):
                closed_accounts.add(entry.account)
        
        # 过滤掉已关闭的账户
        active_accounts = [account for account in all_accounts if account not in closed_accounts]
        
        return sorted(active_accounts)
    
    def get_all_payees(self) -> List[str]:
        """获取所有收付方列表"""
        entries, _, _ = self.loader.load_entries()
        
        payees = set()
        for entry in entries:
            if isinstance(entry, Transaction) and entry.payee:
                payees.add(entry.payee)
        
        return sorted(list(payees))
    
    def _convert_entry_to_response(self, entry: Transaction) -> TransactionResponse:
        """将Beancount交易条目转换为响应格式"""
        # 获取基础货币设置
        entries, _, options_map = self.loader.load_entries()
        default_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        # 获取汇率信息
        exchange_rates = self.exchange_service.get_latest_exchange_rates(entries, entry.date, default_currency)
        
        # 转换分录
        postings = []
        for posting in entry.postings:
            original_amount = posting.units.number if posting.units else None
            original_currency = posting.units.currency if posting.units else None
            
            # 进行汇率转换
            converted_amount = original_amount
            display_currency = original_currency
            
            if original_amount and original_currency and original_currency != default_currency:
                if original_currency in exchange_rates:
                    # 转换为基础货币
                    converted_amount = original_amount * exchange_rates[original_currency]
                    display_currency = default_currency
            
            posting_data = PostingBase(
                account=posting.account,
                amount=converted_amount,
                currency=display_currency,
                # 保留原始金额和币种信息，用于前端显示
                original_amount=original_amount,
                original_currency=original_currency
            )
            postings.append(posting_data)
        
        # 提取元数据
        filename = entry.meta.get('filename') if entry.meta else None
        lineno = entry.meta.get('lineno') if entry.meta else None
        
        # 如果没有从meta中获取到，尝试直接从entry属性获取
        if filename is None and hasattr(entry, 'meta') and entry.meta:
            filename = entry.meta.get('filename')
        if lineno is None and hasattr(entry, 'meta') and entry.meta:
            lineno = entry.meta.get('lineno')
        
        # 生成唯一的交易ID
        transaction_id = None
        if filename and lineno:
            # 使用相对路径和行号组成唯一ID
            import os
            relative_filename = os.path.basename(filename) if filename else 'unknown'
            transaction_id = f"{relative_filename}:{lineno}"
        
        return TransactionResponse(
            date=entry.date,
            flag=entry.flag,
            payee=entry.payee,
            narration=entry.narration,
            tags=list(entry.tags) if entry.tags else [],
            links=list(entry.links) if entry.links else [],
            postings=postings,
            filename=filename,
            lineno=lineno,
            transaction_id=transaction_id
        )
    
    def _get_transaction_type(self, entry: Transaction) -> str:
        """判断交易类型：income, expense, transfer"""
        # 检查所有posting的账户类型
        account_types = set()
        for posting in entry.postings:
            if posting.account.startswith('Income:'):
                account_types.add('income')
            elif posting.account.startswith('Expenses:'):
                account_types.add('expense')
            elif posting.account.startswith('Assets:') or posting.account.startswith('Liabilities:'):
                account_types.add('asset_liability')
            else:
                account_types.add('other')
        
        # 根据账户类型组合判断交易类型
        if 'income' in account_types:
            return 'income'
        elif 'expense' in account_types:
            return 'expense'
        elif account_types == {'asset_liability'}:
            # 只包含Assets和Liabilities账户的交易为转账
            return 'transfer'
        else:
            # 其他情况，包含Equity等账户，暂时归类为转账
            return 'transfer'
    
    @staticmethod
    def get_account_type(account: str) -> str:
        """获取账户类型"""
        if account.startswith('Assets:'):
            return 'Assets'
        elif account.startswith('Liabilities:'):
            return 'Liabilities'
        elif account.startswith('Equity:'):
            return 'Equity'
        elif account.startswith('Income:'):
            return 'Income'
        elif account.startswith('Expenses:'):
            return 'Expenses'
        else:
            return 'Other'
