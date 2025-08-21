"""
报表生成服务
负责生成资产负债表、损益表等各类财务报表
"""
from beancount.core.data import Transaction
from beancount.ops.summarize import conversions
from decimal import Decimal
from datetime import date
from typing import List, Dict, Any, Optional

from app.models.schemas import BalanceResponse, IncomeStatement, AccountInfo
from app.core.config import settings
from .exchange_service import ExchangeService
from .ledger_query import LedgerQuery


class ReportGenerator:
    """报表生成器"""
    
    def __init__(self, loader):
        self.loader = loader
        self.exchange_service = ExchangeService()
        self.query_service = LedgerQuery(loader)
    
    def get_balance_sheet(self, date_filter: Optional[date] = None) -> BalanceResponse:
        """获取资产负债表"""
        entries, _, options_map = self.loader.load_entries()
        
        if date_filter is None:
            date_filter = settings.now().date()
        
        # 获取默认账户名称
        default_accounts = self.loader.get_default_accounts()
        current_conversions_account = default_accounts['current_conversions']
        
        # 运行beancount的转换处理，确保转换账户能够正确生成
        conversion_currency = options_map.get('conversion_currency', 'CNY')
        
        # 如果conversion_currency是'NOTHING'，使用operating_currency
        if conversion_currency == 'NOTHING':
            conversion_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        entries = conversions(entries, current_conversions_account, conversion_currency, date_filter)
        
        # 获取默认货币
        default_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        # 获取所有账户余额
        account_balances = self._calculate_account_balances(entries, date_filter, default_currency)
        
        # 分类账户和计算收支
        assets, liabilities, equity, income_total, expense_total = self._categorize_accounts(
            account_balances, entries, date_filter, default_currency
        )
        
        # 获取当期收益账户名称
        current_earnings_account = default_accounts['current_earnings']
        
        # 计算净收益并添加到权益中
        net_earnings = -income_total - expense_total
        
        # 检查是否已存在当期收益账户
        has_earnings_current = any(acc.name == current_earnings_account for acc in equity)
        
        # 如果不存在且有净收益，则添加当期收益账户
        if not has_earnings_current and abs(net_earnings) > Decimal('0.01'):
            earnings_account = AccountInfo(
                name=current_earnings_account,
                balance=net_earnings,
                currency=default_currency,
                account_type="Equity"
            )
            equity.append(earnings_account)
        
        # 处理资产、负债和权益账户的汇率转换
        processed_assets = self._process_accounts_with_exchange(assets, default_currency, entries, date_filter)
        processed_liabilities = self._process_accounts_with_exchange(liabilities, default_currency, entries, date_filter)
        processed_equity = self._process_equity_accounts(equity, default_currency, entries, date_filter, current_earnings_account, current_conversions_account)
        
        # 计算总计
        total_assets = sum(acc.balance for acc in processed_assets)
        total_liabilities_raw = sum(acc.balance for acc in processed_liabilities)
        total_liabilities = abs(total_liabilities_raw)
        
        total_equity_calculated = sum(acc.balance for acc in processed_equity)
        total_equity = abs(total_equity_calculated) if total_equity_calculated < 0 else total_equity_calculated
        
        # 计算净资产
        net_worth = total_assets - total_liabilities
        
        return BalanceResponse(
            accounts=processed_assets + processed_liabilities + processed_equity,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            net_worth=net_worth,
            currency=default_currency
        )
    
    def get_income_statement(self, start_date: date, end_date: date) -> IncomeStatement:
        """获取损益表"""
        entries, _, options_map = self.loader.load_entries()
        
        account_balances = {}
        
        for entry in entries:
            if entry.date < start_date or entry.date > end_date:
                continue
                
            if isinstance(entry, Transaction):
                for posting in entry.postings:
                    if posting.units:
                        account = posting.account
                        amount_val = posting.units.number
                        currency = posting.units.currency
                        
                        key = (account, currency)
                        if key not in account_balances:
                            account_balances[key] = Decimal('0')
                        account_balances[key] += amount_val
        
        default_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        # 获取汇率信息用于转换
        exchange_rates = self.exchange_service.get_latest_exchange_rates(entries, end_date, default_currency)
        
        # 用于合并同名账户的字典
        merged_income_accounts = {}
        merged_expense_accounts = {}
        
        for (account, currency), balance in account_balances.items():
            # 转换到基础货币
            converted_balance = balance
            if currency != default_currency and currency in exchange_rates:
                converted_balance = balance * exchange_rates[currency]
            
            account_info = AccountInfo(
                name=account,
                balance=converted_balance,
                currency=default_currency,
                account_type=self.query_service.get_account_type(account)
            )
            
            if account.startswith('Income:'):
                # 合并同名收入账户
                if account in merged_income_accounts:
                    merged_income_accounts[account].balance += converted_balance
                else:
                    merged_income_accounts[account] = account_info
            elif account.startswith('Expenses:'):
                # 合并同名支出账户
                if account in merged_expense_accounts:
                    merged_expense_accounts[account].balance += converted_balance
                else:
                    merged_expense_accounts[account] = account_info
        
        # 转换字典为列表
        income_accounts = list(merged_income_accounts.values())
        expense_accounts = list(merged_expense_accounts.values())
        
        # 收入账户：在beancount中负数表示收入，正数表示损失
        # 需要将负数转为正数表示收入金额
        total_income_raw = sum(acc.balance for acc in income_accounts)
        total_income = -total_income_raw
        
        # 支出账户：正数表示支出
        total_expenses = sum(acc.balance for acc in expense_accounts)
        
        return IncomeStatement(
            income_accounts=income_accounts,
            expense_accounts=expense_accounts,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=total_income - total_expenses,
            currency=default_currency
        )
    
    def _calculate_account_balances(self, entries: List[Any], date_filter: date, default_currency: str) -> Dict:
        """计算账户余额"""
        account_balances = {}
        
        # 首先获取所有已定义的账户（通过Open指令）
        all_opened_accounts = {}
        for entry in entries:
            if hasattr(entry, 'account') and hasattr(entry, 'currencies'):
                # 这是一个Open指令
                account = entry.account
                currencies = entry.currencies or [default_currency]
                for currency in currencies:
                    key = (account, currency)
                    if key not in all_opened_accounts:
                        all_opened_accounts[key] = Decimal('0')
        
        # 然后计算账户余额
        for entry in entries:
            if entry.date > date_filter:
                continue
                
            if isinstance(entry, Transaction):
                for posting in entry.postings:
                    if posting.units:
                        account = posting.account
                        amount_val = posting.units.number
                        currency = posting.units.currency
                        
                        key = (account, currency)
                        if key not in account_balances:
                            account_balances[key] = Decimal('0')
                        account_balances[key] += amount_val
        
        # 确保所有已定义的账户都在余额字典中（即使余额为0）
        for key in all_opened_accounts:
            if key not in account_balances:
                account_balances[key] = Decimal('0')
        
        return account_balances
    
    def _categorize_accounts(self, account_balances: Dict, entries: List[Any], date_filter: date, default_currency: str):
        """分类账户并计算收支"""
        assets = []
        liabilities = []
        equity = []
        income_total = Decimal('0')
        expense_total = Decimal('0')
        
        # 获取汇率信息
        exchange_rates = self.exchange_service.get_latest_exchange_rates(entries, date_filter, default_currency)
        
        for (account, currency), balance in account_balances.items():
            account_info = AccountInfo(
                name=account,
                balance=balance,
                currency=currency,
                account_type=self.query_service.get_account_type(account)
            )
            
            if account.startswith('Assets:'):
                assets.append(account_info)
            elif account.startswith('Liabilities:'):
                liabilities.append(account_info)
            elif account.startswith('Equity:'):
                equity.append(account_info)
            elif account.startswith('Income:'):
                # 计算收入总额（用于当期收益计算）
                if currency == default_currency:
                    income_total += balance
                elif currency in exchange_rates:
                    income_total += balance * exchange_rates[currency]
            elif account.startswith('Expenses:'):
                # 计算支出总额（用于当期收益计算）
                if currency == default_currency:
                    expense_total += balance
                elif currency in exchange_rates:
                    expense_total += balance * exchange_rates[currency]
        
        return assets, liabilities, equity, income_total, expense_total
    
    def _process_accounts_with_exchange(self, accounts: List[AccountInfo], default_currency: str, entries: List[Any], date_filter: date) -> List[AccountInfo]:
        """处理账户汇率转换和货币统一"""
        return self._merge_and_convert_accounts(accounts, default_currency, entries, date_filter)
    
    def _merge_and_convert_accounts(self, accounts: List[AccountInfo], default_currency: str, entries: List[Any], date_filter: date) -> List[AccountInfo]:
        """合并相同账户并进行汇率转换的通用方法"""
        merged_accounts = {}
        
        # 获取汇率信息
        exchange_rates = self.exchange_service.get_latest_exchange_rates(entries, date_filter, default_currency)
        
        for acc in accounts:
            # 创建新的账户对象避免修改原始数据
            display_acc = AccountInfo(
                name=acc.name,
                balance=acc.balance,
                currency=acc.currency,
                account_type=acc.account_type
            )
            
            # 转换到基础货币
            if display_acc.currency != default_currency and display_acc.currency in exchange_rates:
                display_acc.balance = display_acc.balance * exchange_rates[display_acc.currency]
                display_acc.currency = default_currency
            
            # 合并相同名称的账户（不同币种的同一账户）
            if display_acc.name in merged_accounts:
                merged_accounts[display_acc.name].balance += display_acc.balance
            else:
                merged_accounts[display_acc.name] = display_acc
        
        return list(merged_accounts.values())
    
    def _process_equity_accounts(self, equity: List[AccountInfo], default_currency: str, entries: List[Any], date_filter: date, current_earnings_account: str, current_conversions_account: str) -> List[AccountInfo]:
        """处理权益账户的特殊显示逻辑"""
        # 先进行通用的合并和转换
        merged_accounts = self._merge_and_convert_accounts(equity, default_currency, entries, date_filter)
        
        # 处理权益账户的特殊显示逻辑
        for account in merged_accounts:
            if account.name == current_earnings_account:
                # 当期收益：反转符号以正确显示
                account.balance = -account.balance
            elif account.name == current_conversions_account:
                # 当期转换账户：保持其原始符号
                pass
            elif account.balance < 0:
                # 其他权益账户：负数显示为正数（符合资产负债表惯例）
                account.balance = abs(account.balance)
        
        return merged_accounts
