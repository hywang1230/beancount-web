"""
重构后的 Beancount 服务
作为统一的服务接口，协调各个专门的服务模块
"""
from typing import List, Dict, Optional
from datetime import date
from pathlib import Path

from app.core.config import settings
from app.models.schemas import (
    TransactionResponse, BalanceResponse, IncomeStatement, 
    TransactionFilter
)
from .ledger_loader import LedgerLoader
from .ledger_query import LedgerQuery
from .report_generator import ReportGenerator
from .exchange_service import ExchangeService
from .transaction_validator import TransactionValidator
from .transaction_repository import TransactionRepository
from .account_manager import AccountManager


class BeancountService:
    """
    重构后的 Beancount 服务
    作为统一入口，协调各个专门的服务模块
    """
    
    def __init__(self):
        self.data_dir = settings.data_dir
        self.main_file = self.data_dir / settings.default_beancount_file
        
        # 初始化各个服务模块
        self.loader = LedgerLoader()
        self.query = LedgerQuery(self.loader)
        self.report_generator = ReportGenerator(self.loader)
        self.exchange_service = ExchangeService()
        self.validator = TransactionValidator(str(self.main_file))
        self.transaction_repo = TransactionRepository(str(self.main_file), self.loader)
        self.account_manager = AccountManager(str(self.main_file), self.loader)
    
    # =============================================================================
    # 文件加载和配置相关方法 - 委托给 LedgerLoader
    # =============================================================================
    
    def get_account_configuration(self) -> dict:
        """获取账户配置信息，用于调试和验证"""
        return self.loader.get_account_configuration()
    
    def get_conversion_account_info(self) -> dict:
        """获取转换账户的说明信息"""
        return self.loader.get_conversion_account_info()
    
    # =============================================================================
    # 交易查询相关方法 - 委托给 LedgerQuery
    # =============================================================================
    
    def get_transactions(self, filter_params: Optional[TransactionFilter] = None) -> List[TransactionResponse]:
        """获取交易列表"""
        return self.query.get_transactions(filter_params)
    
    def get_transaction_by_location(self, filename: str, lineno: int) -> Optional[TransactionResponse]:
        """根据文件名和行号获取特定交易"""
        return self.query.get_transaction_by_location(filename, lineno)
    
    def get_all_accounts(self) -> List[str]:
        """获取所有账户列表（包括所有类型的账户）"""
        return self.query.get_all_accounts()
    
    def get_archived_accounts(self) -> List[str]:
        """获取已归档的账户列表"""
        return self.query.get_archived_accounts()
    
    def get_active_accounts(self) -> List[str]:
        """获取活跃账户列表（排除已归档的账户）"""
        return self.query.get_active_accounts()
    
    def get_all_payees(self) -> List[str]:
        """获取所有收付方列表"""
        return self.query.get_all_payees()
    
    # =============================================================================
    # 报表生成相关方法 - 委托给 ReportGenerator
    # =============================================================================
    
    def get_balance_sheet(self, date_filter: Optional[date] = None) -> BalanceResponse:
        """获取资产负债表"""
        return self.report_generator.get_balance_sheet(date_filter)
    
    def get_income_statement(self, start_date: date, end_date: date) -> IncomeStatement:
        """获取损益表"""
        return self.report_generator.get_income_statement(start_date, end_date)
    
    # =============================================================================
    # 交易验证相关方法 - 委托给 TransactionValidator
    # =============================================================================
    
    def validate_transaction(self, transaction_data: Dict) -> Dict:
        """校验交易数据但不保存到文件"""
        return self.validator.validate_transaction(transaction_data)
    
    # =============================================================================
    # 交易CRUD相关方法 - 委托给 TransactionRepository
    # =============================================================================
    
    def add_transaction(self, transaction_data: Dict) -> bool:
        """添加新交易到账本文件"""
        return self.transaction_repo.add_transaction(transaction_data)
    
    def update_transaction_by_location(self, filename: str, lineno: int, transaction_data: Dict) -> bool:
        """根据文件名和行号更新交易"""
        return self.transaction_repo.update_transaction_by_location(filename, lineno, transaction_data)
    
    def delete_transaction_by_location(self, filename: str, lineno: int) -> bool:
        """根据文件名和行号删除交易"""
        return self.transaction_repo.delete_transaction_by_location(filename, lineno)
    
    # =============================================================================
    # 账户管理相关方法 - 委托给 AccountManager
    # =============================================================================
    
    def create_account(self, account_name: str, open_date: date, 
                      currencies: Optional[List[str]] = None, 
                      booking_method: Optional[str] = None) -> bool:
        """创建账户（添加open指令）"""
        return self.account_manager.create_account(account_name, open_date, currencies, booking_method)
    
    def close_account(self, account_name: str, close_date: date) -> bool:
        """归档账户（添加close指令）"""
        return self.account_manager.close_account(account_name, close_date)
    
    def restore_account(self, account_name: str) -> bool:
        """恢复账户（删除close指令）"""
        return self.account_manager.restore_account(account_name)


# 创建全局服务实例
beancount_service = BeancountService()
