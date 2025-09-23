"""
汇率服务
负责汇率查询和货币转换
"""
from beancount.core.data import Price
from decimal import Decimal
from datetime import date
from typing import Dict, List, Any, Optional
from app.services.ledger_options_service import LedgerOptionsService


class ExchangeService:
    """汇率服务"""
    
    def __init__(self, options_service: Optional[LedgerOptionsService] = None):
        self.options_service = options_service
    
    @staticmethod
    def get_latest_exchange_rates(entries: List[Any], date_filter: date, base_currency: str) -> Dict[str, Decimal]:
        """获取最新汇率信息（兼容旧版本）"""
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
    
    def get_effective_rate(self, date_: date, from_currency: str, to_currency: Optional[str] = None) -> Optional[Decimal]:
        """获取指定日期的有效汇率"""
        if self.options_service:
            return self.options_service.get_effective_rate(date_, from_currency, to_currency)
        return None
    
    def convert_amount(self, amount: Decimal, from_currency: str, 
                      to_currency: str, date_: date) -> Optional[Decimal]:
        """转换金额"""
        if from_currency == to_currency:
            return amount
        
        rate = self.get_effective_rate(date_, from_currency, to_currency)
        if rate is not None:
            return amount * rate
        return None
    
    @staticmethod
    def calculate_total_with_currency_conversion(accounts: List[Any], 
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
