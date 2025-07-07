from beancount import loader
from beancount.core import data, amount
from beancount.core.data import Transaction, Posting
from beancount.core import getters
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime
import os
from pathlib import Path

from app.core.config import settings
from app.models.schemas import (
    TransactionResponse, AccountInfo, BalanceResponse, 
    IncomeStatement, TransactionFilter, PostingBase
)

class BeancountService:
    def __init__(self):
        self.data_dir = settings.data_dir
        self.main_file = self.data_dir / settings.default_beancount_file
        self._entries = None
        self._errors = None
        self._options_map = None
        
    def _load_entries(self, force_reload: bool = False):
        """加载Beancount条目"""
        if self._entries is None or force_reload:
            if not self.main_file.exists():
                raise FileNotFoundError(f"主账本文件不存在: {self.main_file}")
            
            self._entries, self._errors, self._options_map = loader.load_file(str(self.main_file))
            
            if self._errors:
                print(f"警告: 加载账本时发现 {len(self._errors)} 个错误")
                for error in self._errors[:5]:  # 只显示前5个错误
                    print(f"  - {error}")
                    
        return self._entries, self._errors, self._options_map
    
    def get_transactions(self, filter_params: Optional[TransactionFilter] = None) -> List[TransactionResponse]:
        """获取交易列表"""
        entries, _, _ = self._load_entries()
        
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
                
                # 转换为响应模型
                postings = []
                for posting in entry.postings:
                    posting_data = PostingBase(
                        account=posting.account,
                        amount=posting.units.number if posting.units else None,
                        currency=posting.units.currency if posting.units else None
                    )
                    postings.append(posting_data)
                
                transaction = TransactionResponse(
                    date=entry.date,
                    flag=entry.flag,
                    payee=entry.payee,
                    narration=entry.narration,
                    tags=list(entry.tags) if entry.tags else [],
                    links=list(entry.links) if entry.links else [],
                    postings=postings
                )
                transactions.append(transaction)
        
        # 按日期降序排列
        transactions.sort(key=lambda x: x.date, reverse=True)
        return transactions
    
    def get_balance_sheet(self, date_filter: Optional[date] = None) -> BalanceResponse:
        """获取资产负债表"""
        entries, _, options_map = self._load_entries()
        
        if date_filter is None:
            date_filter = datetime.now().date()
        
        # 获取所有账户余额
        account_balances = {}
        
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
        
        # 分类账户和计算收支
        assets = []
        liabilities = []
        equity = []
        income_total = Decimal('0')
        expense_total = Decimal('0')
        
        default_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        # 获取汇率信息
        exchange_rates = self._get_latest_exchange_rates(entries, date_filter, default_currency)
        
        for (account, currency), balance in account_balances.items():
            if balance == 0:
                continue
                
            account_info = AccountInfo(
                name=account,
                balance=balance,
                currency=currency,
                account_type=self._get_account_type(account)
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
        
        # 计算净收益并添加到权益中（如果不存在Equity:Earnings:Current）
        # 在 Beancount 中，净收益 = -收入 - 支出
        net_earnings = -income_total - expense_total
        
        # 检查是否已存在 Equity:Earnings:Current
        has_earnings_current = any(acc.name == 'Equity:Earnings:Current' for acc in equity)
        
        # 如果不存在且有净收益，则添加当期收益账户
        if not has_earnings_current and abs(net_earnings) > Decimal('0.01'):
            earnings_account = AccountInfo(
                name="Equity:Earnings:Current",
                balance=net_earnings,
                currency=default_currency,
                account_type="Equity"
            )
            equity.append(earnings_account)
        
        # 计算总计（包含汇率转换）
        total_assets = self._calculate_total_with_currency_conversion(
            assets, default_currency, exchange_rates)
        
        # 负债在beancount中是负数，取绝对值用于显示
        total_liabilities_raw = self._calculate_total_with_currency_conversion(
            liabilities, default_currency, exchange_rates)
        total_liabilities = abs(total_liabilities_raw)  # 显示为正数
        
        # 权益处理：计算包含当期收益的总权益
        # 重新计算权益总计，避免重复计算
        total_equity_before_conversion = Decimal('0')
        
        for acc in equity:
            if acc.currency == default_currency:
                total_equity_before_conversion += acc.balance
            elif acc.currency in exchange_rates:
                converted_amount = acc.balance * exchange_rates[acc.currency]
                total_equity_before_conversion += converted_amount
        
        # 调整权益账户显示，确保汇率转换正确
        processed_accounts = []
        merged_accounts = {}  # 用于合并相同名称的账户
        
        for acc in equity:
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
            
            # 合并相同名称的账户
            if display_acc.name in merged_accounts:
                merged_accounts[display_acc.name].balance += display_acc.balance
            else:
                merged_accounts[display_acc.name] = display_acc
        
        # 处理合并后的账户显示
        for account_name, account in merged_accounts.items():
            # 权益账户显示逻辑：
            # 1. Equity:Earnings:Current 显示为正数（亏损显示为正数）
            # 2. 其他权益账户保持符合会计惯例的显示
            if account.name == "Equity:Earnings:Current":
                # 当期收益：显示绝对值（正数表示收益或亏损的金额）
                account.balance = abs(account.balance)
            elif account.balance < 0:
                # 其他权益账户：负数显示为正数（符合资产负债表惯例）
                account.balance = abs(account.balance)
                
            processed_accounts.append(account)
        
        # 使用转换后的账户计算正确的权益总计
        total_equity_calculated = sum(acc.balance for acc in processed_accounts)
        
        # 在资产负债表中，如果权益总和为负数，显示为正数（会计惯例）
        total_equity = abs(total_equity_calculated) if total_equity_calculated < 0 else total_equity_calculated
        
        # 计算净资产 = 总资产 - 总负债(绝对值)
        net_worth = total_assets - total_liabilities
        
        return BalanceResponse(
            accounts=assets + liabilities + processed_accounts,
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
            net_worth=net_worth,
            currency=default_currency
        )
    
    def get_income_statement(self, start_date: date, end_date: date) -> IncomeStatement:
        """获取损益表"""
        entries, _, options_map = self._load_entries()
        
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
        
        income_accounts = []
        expense_accounts = []
        
        default_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        for (account, currency), balance in account_balances.items():
            if balance == 0:
                continue
                
            account_info = AccountInfo(
                name=account,
                balance=balance,
                currency=currency,
                account_type=self._get_account_type(account)
            )
            
            if account.startswith('Income:'):
                income_accounts.append(account_info)
            elif account.startswith('Expenses:'):
                expense_accounts.append(account_info)
        
        # 获取汇率信息用于收入计算
        exchange_rates = self._get_latest_exchange_rates(entries, end_date, default_currency)
        
        # 收入账户：在beancount中负数表示收入，正数表示损失
        # 需要将负数转为正数表示收入金额
        total_income_raw = self._calculate_total_with_currency_conversion(
            income_accounts, default_currency, exchange_rates)
        total_income = -total_income_raw  # 取负值：负数变正数(收入)，正数变负数(损失)
        
        # 支出账户：正数表示支出
        total_expenses = self._calculate_total_with_currency_conversion(
            expense_accounts, default_currency, exchange_rates)
        
        return IncomeStatement(
            income_accounts=income_accounts,
            expense_accounts=expense_accounts,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=total_income - total_expenses,
            currency=default_currency
        )
    
    def _get_account_type(self, account: str) -> str:
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
    
    def _get_latest_exchange_rates(self, entries, date_filter: date, base_currency: str) -> Dict[str, Decimal]:
        """获取最新汇率信息"""
        from beancount.core.data import Price
        
        exchange_rates = {base_currency: Decimal('1')}  # 基础货币汇率为1
        
        # 收集所有价格信息
        price_entries = []
        for entry in entries:
            if isinstance(entry, Price) and entry.date <= date_filter:
                price_entries.append(entry)
        
        # 按日期排序，获取最新汇率
        price_entries.sort(key=lambda x: x.date)
        
        for price_entry in price_entries:
            from_currency = price_entry.currency
            to_currency = price_entry.amount.currency
            rate = price_entry.amount.number
            
            # 只处理转换到基础货币的汇率
            if to_currency == base_currency:
                exchange_rates[from_currency] = rate
        
        return exchange_rates
    
    def _calculate_total_with_currency_conversion(self, accounts: List[AccountInfo], 
                                                base_currency: str, 
                                                exchange_rates: Dict[str, Decimal]) -> Decimal:
        """计算总额（包含货币转换）"""
        total = Decimal('0')
        
        for acc in accounts:
            if acc.currency == base_currency:
                # 基础货币直接相加
                total += acc.balance
            elif acc.currency in exchange_rates:
                # 使用汇率转换
                converted_amount = acc.balance * exchange_rates[acc.currency]
                total += converted_amount
            # 如果没有汇率信息，暂时忽略该货币的账户
        
        return total
    
    def add_transaction(self, transaction_data: Dict) -> bool:
        """添加新交易到账本文件"""
        try:
            # 构建交易字符串
            transaction_str = self._build_transaction_string(transaction_data)
            
            # 追加到主文件
            with open(self.main_file, 'a', encoding='utf-8') as f:
                f.write('\n' + transaction_str + '\n')
            
            # 重新加载条目
            self._load_entries(force_reload=True)
            return True
            
        except Exception as e:
            print(f"添加交易失败: {e}")
            return False
    
    def _build_transaction_string(self, data: Dict) -> str:
        """构建交易字符串"""
        lines = []
        
        # 交易头部
        date_str = data['date']
        flag = data.get('flag', '*')
        payee = f'"{data["payee"]}"' if data.get('payee') else ''
        narration = f'"{data["narration"]}"'
        
        header = f"{date_str} {flag} {payee} {narration}".strip()
        lines.append(header)
        
        # 添加分录
        for posting in data['postings']:
            account = posting['account']
            
            if posting.get('amount') and posting.get('currency'):
                amount_str = f"  {account}  {posting['amount']} {posting['currency']}"
            else:
                amount_str = f"  {account}"
            
            lines.append(amount_str)
        
        return '\n'.join(lines)
    
    def get_all_accounts(self) -> List[str]:
        """获取所有账户列表（包括所有类型的账户）"""
        entries, _, _ = self._load_entries()
        
        # 使用Beancount的内置方法获取所有账户
        # 这会获取所有在任何条目中出现的账户，包括Open、Transaction等
        all_accounts = getters.get_accounts(entries)
        
        return sorted(list(all_accounts))
    
    def get_all_payees(self) -> List[str]:
        """获取所有收付方列表"""
        entries, _, _ = self._load_entries()
        
        payees = set()
        for entry in entries:
            if isinstance(entry, Transaction) and entry.payee:
                payees.add(entry.payee)
        
        return sorted(list(payees))

# 创建全局服务实例
beancount_service = BeancountService() 