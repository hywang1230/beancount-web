"""
Beancount账本文件加载器
负责文件加载、缓存和基础数据管理
"""
from beancount import loader
from beancount.parser import options
from pathlib import Path
from typing import Optional, Tuple, List, Any
import os

from app.core.config import settings
from app.core.exceptions import FileNotFoundError
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class LedgerLoader:
    """Beancount账本加载器"""
    
    def __init__(self):
        self.data_dir = settings.data_dir
        self.main_file = self.data_dir / settings.default_beancount_file
        self._entries = None
        self._errors = None
        self._options_map = None
        
    def load_entries(self, force_reload: bool = False) -> Tuple[List[Any], List[Any], dict]:
        """加载Beancount条目"""
        try:
            if self._entries is None or force_reload:
                if not self.main_file.exists():
                    raise FileNotFoundError(str(self.main_file))
                
                logger.info(f"Loading beancount file: {self.main_file}")
                self._entries, self._errors, self._options_map = loader.load_file(str(self.main_file))
                
                if self._errors:
                    logger.warning(f"Loaded with {len(self._errors)} errors")
                    for i, error in enumerate(self._errors[:3]):  # 只记录前3个错误
                        logger.warning(f"Error {i+1}: {error}")
                else:
                    logger.info(f"Successfully loaded {len(self._entries)} entries")
                        
            return self._entries, self._errors, self._options_map
        
        except Exception as e:
            logger.error(f"Failed to load beancount file: {e}")
            raise
    
    def get_default_accounts(self) -> dict:
        """获取Beancount默认配置的账户名称"""
        entries, errors, options_map = self.load_entries()
        
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
    
    def get_account_configuration(self) -> dict:
        """获取账户配置信息，用于调试和验证"""
        entries, errors, options_map = self.load_entries()
        default_accounts = self.get_default_accounts()
        
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
    
    def get_conversion_account_info(self) -> dict:
        """获取转换账户的说明信息"""
        entries, errors, options_map = self.load_entries()
        default_accounts = self.get_default_accounts()
        
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
