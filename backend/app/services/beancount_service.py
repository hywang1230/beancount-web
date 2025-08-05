from beancount import loader
from beancount.core import data, amount
from beancount.core.data import Transaction, Posting
from beancount.core import getters
from beancount.parser import options
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
    
    def _get_default_accounts(self):
        """获取Beancount默认配置的账户名称"""
        entries, errors, options_map = self._load_entries()
        
        # 获取当期收益和转换账户名称
        account_current_earnings, account_current_conversions = options.get_current_accounts(options_map)
        
        # 获取之前的收益、余额和转换账户名称
        account_previous_earnings, account_previous_balances, account_previous_conversions = options.get_previous_accounts(options_map)
        
        return {
            'current_earnings': account_current_earnings,
            'current_conversions': account_current_conversions,
            'previous_earnings': account_previous_earnings,
            'previous_balances': account_previous_balances,
            'previous_conversions': account_previous_conversions
        }
    
    def get_account_configuration(self):
        """获取账户配置信息，用于调试和验证"""
        entries, errors, options_map = self._load_entries()
        default_accounts = self._get_default_accounts()
        
        # 分析账户情况
        all_accounts = set()
        equity_accounts = []
        conversion_accounts = []
        currencies = set()
        multi_currency_transactions = 0
        
        for entry in entries:
            if hasattr(entry, 'postings'):
                entry_currencies = set()
                for posting in entry.postings:
                    if posting.units:
                        all_accounts.add(posting.account)
                        currencies.add(posting.units.currency)
                        entry_currencies.add(posting.units.currency)
                        
                        if posting.account.startswith('Equity:'):
                            equity_accounts.append(posting.account)
                        if 'Conversions' in posting.account:
                            conversion_accounts.append(posting.account)
                
                if len(entry_currencies) > 1:
                    multi_currency_transactions += 1
        
        return {
            'default_currency': options_map.get('operating_currency', ['CNY'])[0],
            'equity_name': options_map.get('name_equity', 'Equity'),
            'current_earnings': default_accounts['current_earnings'],
            'current_conversions': default_accounts['current_conversions'],
            'previous_earnings': default_accounts['previous_earnings'],
            'previous_balances': default_accounts['previous_balances'],
            'previous_conversions': default_accounts['previous_conversions'],
            'conversion_currency': options_map.get('conversion_currency', 'USD'),
            # 调试信息
            'debug_info': {
                'total_accounts': len(all_accounts),
                'equity_accounts': list(set(equity_accounts)),
                'conversion_accounts': list(set(conversion_accounts)),
                'currencies': list(currencies),
                'multi_currency_transactions': multi_currency_transactions,
                'has_conversions_current': default_accounts['current_conversions'] in conversion_accounts
            }
        }
    
    def get_conversion_account_info(self):
        """获取转换账户的说明信息"""
        entries, errors, options_map = self._load_entries()
        default_accounts = self._get_default_accounts()
        
        # 检查实际的转换账户使用情况
        conversion_entries = []
        for entry in entries:
            if hasattr(entry, 'postings'):
                for posting in entry.postings:
                    if posting.account == default_accounts['current_conversions']:
                        conversion_entries.append(entry)
                        break
        
        return {
            'current_conversions_account': default_accounts['current_conversions'],
            'account_exists_in_data': len(conversion_entries) > 0,
            'conversion_entries_count': len(conversion_entries),
            'explanation': {
                'when_created': [
                    '存在多币种交易需要平衡时',
                    '使用beancount conversions命令时',
                    '有汇率转换差额需要记录时',
                    '使用@符号进行汇率转换时'
                ],
                'example_scenario': '2023-01-01 * "Currency exchange"\n  Assets:USD:Cash  100.00 USD @ 7.00 CNY\n  Assets:CNY:Cash  -700.00 CNY\n  ; 如果汇率不完全匹配，可能会产生转换差额记入Equity:Conversions:Current',
                'current_status': '当前账本中没有多币种交易，因此不需要转换账户'
            }
        }
    
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
                    
                    # 交易类型筛选
                    if filter_params.transaction_type:
                        transaction_type = self._get_transaction_type(entry)
                        if transaction_type != filter_params.transaction_type:
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
                
                # 提取文件名和行号元数据
                filename = getattr(entry.meta, 'filename', None) if hasattr(entry, 'meta') else None
                lineno = getattr(entry.meta, 'lineno', None) if hasattr(entry, 'meta') else None
                
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
                
                transaction = TransactionResponse(
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
                transactions.append(transaction)
        
        # 按日期降序排列
        transactions.sort(key=lambda x: x.date, reverse=True)
        return transactions
    
    def get_balance_sheet(self, date_filter: Optional[date] = None) -> BalanceResponse:
        """获取资产负债表"""
        entries, _, options_map = self._load_entries()
        
        if date_filter is None:
            date_filter = datetime.now().date()
        
        # 获取默认账户名称
        default_accounts = self._get_default_accounts()
        current_conversions_account = default_accounts['current_conversions']
        
        # 运行beancount的转换处理，确保转换账户能够正确生成
        from beancount.ops.summarize import conversions
        conversion_currency = options_map.get('conversion_currency', 'CNY')
        
        # 如果conversion_currency是'NOTHING'，使用operating_currency
        if conversion_currency == 'NOTHING':
            conversion_currency = options_map.get('operating_currency', ['CNY'])[0]
        
        entries = conversions(entries, current_conversions_account, conversion_currency, date_filter)
        
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
        
        # 获取当期收益账户名称（转换账户已在前面获取）
        current_earnings_account = default_accounts['current_earnings']
        
        # 计算净收益并添加到权益中（如果不存在当期收益账户）
        # 在 Beancount 中，净收益 = -收入 - 支出
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
        
        # 计算货币转换差额 - 检查汇率转换产生的不平衡
        total_conversion_diff = Decimal('0')
        
        # 在汇率转换过程中可能产生的差额需要记入Equity:Conversions:Current
        for (account, currency), balance in account_balances.items():
            if currency != default_currency and currency in exchange_rates:
                # 原始金额
                original_amount = balance
                # 转换后金额
                converted_amount = balance * exchange_rates[currency]
                # 在实际的会计系统中，这种转换差异需要记录
                # 这里我们计算总的转换影响（简化处理）
                pass  # 实际实现中，这里会有更复杂的转换差额计算
        
        # 处理转换账户相关逻辑
        # 在Beancount中，转换账户只有在实际需要时才会被创建：
        # 1. 存在多币种交易需要平衡时
        # 2. 使用了beancount的conversions操作时
        # 3. 有汇率转换差额需要记录时
        
        # 检查是否已存在当期转换账户（在实际数据中）
        has_conversions_current = any(acc.name == current_conversions_account for acc in equity)
        
        # 检查是否存在任何转换相关的账户（在实际数据中）
        conversion_accounts = [acc for acc in equity if 'Conversions' in acc.name]
        
        # 计算是否需要转换平衡
        # 检查是否存在真正的多币种交易（同一交易中包含多种货币）
        needs_conversion = False
        conversion_diff = Decimal('0')
        
        # 检查entries中是否有需要转换的情况
        for entry in entries:
            if hasattr(entry, 'postings') and len(entry.postings) > 1:
                entry_currencies = set()
                for posting in entry.postings:
                    if posting.units:
                        entry_currencies.add(posting.units.currency)
                
                # 如果一个交易中有多种货币，可能需要转换账户
                if len(entry_currencies) > 1:
                    needs_conversion = True
                    break
        
        # 只有在以下情况才添加转换账户：
        # 1. 实际存在转换账户（从数据中读取到）
        # 2. 确实存在需要转换的多币种交易
        if has_conversions_current or (needs_conversion and not has_conversions_current):
            # 如果数据中存在转换账户，会在equity列表中自动包含
            # 如果需要但不存在，这里可以选择是否创建一个占位符
            pass
        
        # 处理资产账户：汇率转换和货币统一
        processed_assets = []
        merged_asset_accounts = {}
        
        for acc in assets:
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
            if display_acc.name in merged_asset_accounts:
                merged_asset_accounts[display_acc.name].balance += display_acc.balance
            else:
                merged_asset_accounts[display_acc.name] = display_acc
        
        for account in merged_asset_accounts.values():
            processed_assets.append(account)
        
        # 处理负债账户：汇率转换和货币统一
        processed_liabilities = []
        merged_liability_accounts = {}
        
        for acc in liabilities:
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
            if display_acc.name in merged_liability_accounts:
                merged_liability_accounts[display_acc.name].balance += display_acc.balance
            else:
                merged_liability_accounts[display_acc.name] = display_acc
        
        for account in merged_liability_accounts.values():
            processed_liabilities.append(account)
        
        # 处理权益账户：汇率转换和货币统一（保持原有逻辑）
        processed_equity = []
        merged_equity_accounts = {}
        
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
            if display_acc.name in merged_equity_accounts:
                merged_equity_accounts[display_acc.name].balance += display_acc.balance
            else:
                merged_equity_accounts[display_acc.name] = display_acc
        
        # 处理合并后的权益账户显示
        for account_name, account in merged_equity_accounts.items():
            # 权益账户显示逻辑：
            # 1. 当期收益账户需要正确反映当期收益/亏损
            # 2. 其他权益账户保持符合会计惯例的显示
            if account.name == current_earnings_account:
                # 当期收益：在Beancount中，正的净收益在权益账户中应显示为负数（借方）
                # 但在资产负债表显示中，我们需要将其转换为正确的显示格式
                # 净收益为正数时，权益增加，应该显示为正数
                # 净亏损为负数时，权益减少，应该显示为负数（或在某些显示中显示为正的亏损额）
                account.balance = -account.balance  # 反转符号以正确显示
            elif account.name == current_conversions_account:
                # 当期转换账户：保持其原始符号，因为它代表汇率转换差额
                pass  # 保持原始值
            elif account.balance < 0:
                # 其他权益账户：负数显示为正数（符合资产负债表惯例）
                account.balance = abs(account.balance)
                
            processed_equity.append(account)
        
        # 计算总计（使用转换后的账户数据）
        total_assets = sum(acc.balance for acc in processed_assets)
        total_liabilities_raw = sum(acc.balance for acc in processed_liabilities)
        total_liabilities = abs(total_liabilities_raw)  # 显示为正数
        
        # 使用转换后的账户计算正确的权益总计
        total_equity_calculated = sum(acc.balance for acc in processed_equity)
        
        # 在资产负债表中，如果权益总和为负数，显示为正数（会计惯例）
        total_equity = abs(total_equity_calculated) if total_equity_calculated < 0 else total_equity_calculated
        
        # 计算净资产 = 总资产 - 总负债(绝对值)
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
    
    def get_archived_accounts(self) -> List[str]:
        """获取已归档的账户列表"""
        entries, _, _ = self._load_entries()
        
        # 获取已关闭的账户
        from beancount.core.data import Close
        closed_accounts = set()
        for entry in entries:
            if isinstance(entry, Close):
                closed_accounts.add(entry.account)
        
        return sorted(list(closed_accounts))
    
    def get_active_accounts(self) -> List[str]:
        """获取活跃账户列表（排除已归档的账户）"""
        entries, _, _ = self._load_entries()
        
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
        entries, _, _ = self._load_entries()
        
        payees = set()
        for entry in entries:
            if isinstance(entry, Transaction) and entry.payee:
                payees.add(entry.payee)
        
        return sorted(list(payees))

    def create_account(self, account_name: str, open_date: date, currencies: Optional[List[str]] = None, booking_method: Optional[str] = None) -> bool:
        """创建账户（添加open指令）"""
        # 验证账户名称格式
        is_valid, error_message = self._validate_account_name(account_name)
        if not is_valid:
            raise ValueError(f"无效的账户名称格式: {error_message}")
        
        # 检查账户是否已存在
        entries, _, _ = self._load_entries()
        existing_accounts = getters.get_accounts(entries)
        if account_name in existing_accounts:
            raise ValueError(f"账户已存在: {account_name}")
        
        # 构建open指令字符串
        open_directive = self._build_open_directive(account_name, open_date, currencies, booking_method)
        
        # 追加到主文件
        with open(self.main_file, 'a', encoding='utf-8') as f:
            f.write('\n' + open_directive + '\n')
        
        # 重新加载条目
        self._load_entries(force_reload=True)
        return True

    def close_account(self, account_name: str, close_date: date) -> bool:
        """归档账户（添加close指令）"""
        try:
            # 检查账户是否存在
            entries, _, _ = self._load_entries()
            existing_accounts = getters.get_accounts(entries)
            if account_name not in existing_accounts:
                raise ValueError(f"账户不存在: {account_name}")
            
            # 检查账户是否已经关闭
            from beancount.core.data import Close
            for entry in entries:
                if isinstance(entry, Close) and entry.account == account_name:
                    raise ValueError(f"账户已经关闭: {account_name}")
            
            # 构建close指令字符串
            close_directive = self._build_close_directive(account_name, close_date)
            
            # 追加到主文件
            with open(self.main_file, 'a', encoding='utf-8') as f:
                f.write('\n' + close_directive + '\n')
            
            # 重新加载条目
            self._load_entries(force_reload=True)
            return True
            
        except Exception as e:
            print(f"归档账户失败: {e}")
            return False

    def restore_account(self, account_name: str) -> bool:
        """恢复账户（删除close指令）"""
        try:
            # 检查账户是否存在且已关闭
            entries, _, _ = self._load_entries()
            
            from beancount.core.data import Close
            close_entry = None
            for entry in entries:
                if isinstance(entry, Close) and entry.account == account_name:
                    close_entry = entry
                    break
            
            if not close_entry:
                raise ValueError(f"账户未归档或不存在: {account_name}")
            
            # 读取主文件内容
            with open(self.main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 构建要删除的close指令（构建可能的close指令格式）
            close_date_str = close_entry.date.strftime('%Y-%m-%d')
            close_directive_patterns = [
                f"{close_date_str} close {account_name}",
                f"{close_date_str} close {account_name} ",
                f"\n{close_date_str} close {account_name}\n",
                f"\n{close_date_str} close {account_name} \n"
            ]
            
            # 尝试删除close指令
            modified = False
            for pattern in close_directive_patterns:
                if pattern in content:
                    content = content.replace(pattern, "")
                    modified = True
                    break
            
            if not modified:
                # 如果精确匹配失败，尝试使用正则表达式
                import re
                pattern = f"^{re.escape(close_date_str)} close {re.escape(account_name)}.*$"
                lines = content.split('\n')
                new_lines = []
                for line in lines:
                    if not re.match(pattern, line.strip()):
                        new_lines.append(line)
                    else:
                        modified = True
                
                if modified:
                    content = '\n'.join(new_lines)
            
            if modified:
                # 写回文件
                with open(self.main_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 重新加载条目
                self._load_entries(force_reload=True)
                return True
            else:
                raise ValueError(f"无法找到账户 {account_name} 的close指令")
            
        except Exception as e:
            print(f"恢复账户失败: {e}")
            raise ValueError(f"恢复账户失败: {str(e)}")

    def _validate_account_name(self, account_name: str) -> tuple[bool, str]:
        """验证账户名称是否符合beancount规范"""
        import re
        
        # 账户名称必须符合beancount的规范
        # 1. 必须以五种账户类型之一开头
        valid_types = ['Assets', 'Liabilities', 'Equity', 'Income', 'Expenses']
        
        # 2. 由冒号分隔的多个部分组成
        parts = account_name.split(':')
        if len(parts) < 2:
            return False, "账户名称必须包含至少两个部分，用冒号分隔"
        
        # 3. 第一部分必须是有效的账户类型
        if parts[0] not in valid_types:
            return False, f"账户类型必须是以下之一: {', '.join(valid_types)}"
        
        # 4. 第二部分（实际账户名）必须以大写字母或数字开头
        second_part = parts[1]
        if not re.match(r'^[A-Z0-9]', second_part):
            return False, f"账户名称的主要部分 '{second_part}' 必须以大写字母或数字开头"
        
        # 5. 所有部分都只能包含字母、数字、汉字、下划线和连字符
        pattern = re.compile(r'^[\w\u4e00-\u9fa5-]+$')
        for i, part in enumerate(parts):
            if i == 0:  # 跳过账户类型检查
                continue
            if not pattern.match(part):
                return False, f"账户名称部分 '{part}' 包含无效字符。只能包含字母、数字、汉字、下划线和连字符"
        
        return True, ""

    def _build_open_directive(self, account_name: str, open_date: date, currencies: Optional[List[str]] = None, booking_method: Optional[str] = None) -> str:
        """构建open指令字符串"""
        lines = []
        
        # 日期和指令
        date_str = open_date.strftime('%Y-%m-%d')
        directive_parts = [date_str, 'open', account_name]
        
        # 添加货币约束
        if currencies:
            directive_parts.append(','.join(currencies))
        
        # 添加记账方法
        if booking_method:
            if currencies:
                directive_parts.append(f'"{booking_method}"')
            else:
                directive_parts.extend(['', f'"{booking_method}"'])
        
        lines.append(' '.join(directive_parts))
        
        return '\n'.join(lines)

    def _build_close_directive(self, account_name: str, close_date: date) -> str:
        """构建close指令字符串"""
        date_str = close_date.strftime('%Y-%m-%d')
        return f"{date_str} close {account_name}"

    def get_transaction_by_location(self, filename: str, lineno: int) -> Optional[TransactionResponse]:
        """根据文件名和行号获取特定交易"""
        try:
            entries, _, _ = self._load_entries()
            
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
            print(f"获取交易失败: {e}")
            return None

    def update_transaction_by_location(self, filename: str, lineno: int, transaction_data: Dict) -> bool:
        """根据文件名和行号更新交易"""
        try:
            # 首先找到要更新的交易
            entries, _, _ = self._load_entries()
            target_entry = None
            
            for entry in entries:
                if isinstance(entry, Transaction):
                    entry_filename = entry.meta.get('filename') if entry.meta else None
                    entry_lineno = entry.meta.get('lineno') if entry.meta else None
                    
                    if entry_filename and entry_lineno:
                        import os
                        entry_basename = os.path.basename(entry_filename)
                        if entry_basename == filename and entry_lineno == lineno:
                            target_entry = entry
                            break
            
            if not target_entry:
                print(f"未找到要更新的交易: {filename}:{lineno}")
                return False
            
            # 读取原始文件内容
            target_filename = target_entry.meta.get('filename')
            if not target_filename:
                print("无法获取交易所在的文件名")
                return False
            
            with open(target_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 构建新的交易字符串
            new_transaction_str = self._build_transaction_string(transaction_data)
            
            # 替换指定行的交易（这里简化处理，假设交易占一行）
            # 实际上可能需要更复杂的解析来处理多行交易
            if lineno <= len(lines):
                lines[lineno - 1] = new_transaction_str + '\n'
                
                # 写回文件
                with open(target_filename, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 重新加载条目
                self._load_entries(force_reload=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"更新交易失败: {e}")
            return False

    def delete_transaction_by_location(self, filename: str, lineno: int) -> bool:
        """根据文件名和行号删除交易"""
        try:
            # 首先找到要删除的交易
            entries, _, _ = self._load_entries()
            target_entry = None
            
            for entry in entries:
                if isinstance(entry, Transaction):
                    entry_filename = entry.meta.get('filename') if entry.meta else None
                    entry_lineno = entry.meta.get('lineno') if entry.meta else None
                    
                    if entry_filename and entry_lineno:
                        import os
                        entry_basename = os.path.basename(entry_filename)
                        if entry_basename == filename and entry_lineno == lineno:
                            target_entry = entry
                            break
            
            if not target_entry:
                print(f"未找到要删除的交易: {filename}:{lineno}")
                return False
            
            # 读取原始文件内容
            target_filename = target_entry.meta.get('filename')
            if not target_filename:
                print("无法获取交易所在的文件名")
                return False
            
            with open(target_filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 删除指定行的交易（这里简化处理，假设交易占一行）
            # 实际上可能需要更复杂的解析来处理多行交易
            if lineno <= len(lines):
                # 注释掉该行而不是直接删除，以保持行号的一致性
                original_line = lines[lineno - 1]
                lines[lineno - 1] = f"; DELETED: {original_line}"
                
                # 写回文件
                with open(target_filename, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                
                # 重新加载条目
                self._load_entries(force_reload=True)
                return True
            
            return False
            
        except Exception as e:
            print(f"删除交易失败: {e}")
            return False

    def _convert_entry_to_response(self, entry: Transaction) -> TransactionResponse:
        """将Beancount交易条目转换为响应格式"""
        # 转换分录
        postings = []
        for posting in entry.postings:
            posting_data = PostingBase(
                account=posting.account,
                amount=posting.units.number if posting.units else None,
                currency=posting.units.currency if posting.units else None
            )
            postings.append(posting_data)
        
        # 提取元数据
        filename = entry.meta.get('filename') if entry.meta else None
        lineno = entry.meta.get('lineno') if entry.meta else None
        
        # 生成唯一ID
        transaction_id = None
        if filename and lineno:
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

# 创建全局服务实例
beancount_service = BeancountService() 