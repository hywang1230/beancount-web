from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

class TransactionBase(BaseModel):
    date: date
    flag: str = "*"
    payee: Optional[str] = None
    narration: str
    tags: Optional[List[str]] = Field(default_factory=list)
    links: Optional[List[str]] = Field(default_factory=list)

class PostingBase(BaseModel):
    account: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    price: Optional[Dict[str, Any]] = None
    # 原始金额和货币信息（用于汇率转换显示）
    original_amount: Optional[Decimal] = None
    original_currency: Optional[str] = None

class TransactionCreate(TransactionBase):
    postings: List[PostingBase]

class TransactionResponse(TransactionBase):
    postings: List[PostingBase]
    # 添加唯一标识字段
    filename: Optional[str] = None
    lineno: Optional[int] = None
    transaction_id: Optional[str] = None  # 由filename+lineno组成的唯一标识
    
    model_config = {"from_attributes": True}

class AccountInfo(BaseModel):
    name: str
    balance: Decimal
    currency: str
    account_type: str
    # 添加原币金额和币种信息，用于多币种显示
    original_balance: Optional[Decimal] = None
    original_currency: Optional[str] = None

class BalanceResponse(BaseModel):
    accounts: List[AccountInfo]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    net_worth: Decimal  # 净资产 = 总资产 - 总负债
    currency: str

class IncomeStatement(BaseModel):
    income_accounts: List[AccountInfo]
    expense_accounts: List[AccountInfo]
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
    currency: str

class TransactionFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account: Optional[str] = None
    payee: Optional[str] = None
    narration: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None  # 交易类型：income, expense, transfer

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: datetime
    is_main: bool = False

class FileTreeNode(BaseModel):
    """文件树节点"""
    name: str
    path: str
    size: int
    type: str = "file"  # file or directory
    is_main: bool = False
    includes: List['FileTreeNode'] = Field(default_factory=list)
    modified: Optional[float] = None
    error: Optional[str] = None

# 允许前向引用
FileTreeNode.model_rebuild()

class FileListResponse(BaseModel):
    files: List[FileInfo]
    main_file: Optional[str] = None

class FileTreeResponse(BaseModel):
    """文件树响应"""
    tree: FileTreeNode
    total_files: int
    main_file: str

class RecurrenceType(str, Enum):
    """周期类型枚举"""
    DAILY = "daily"  # 每日
    WEEKLY = "weekly"  # 每周特定几天
    WEEKDAYS = "weekdays"  # 工作日
    MONTHLY = "monthly"  # 每月特定几天

class RecurringTransactionBase(BaseModel):
    name: str
    recurrence_type: str
    start_date: date
    end_date: Optional[date] = None
    weekly_days: Optional[List[int]] = None
    monthly_days: Optional[List[int]] = None
    flag: Optional[str] = "*"
    payee: Optional[str] = None
    narration: str
    tags: Optional[List[str]] = []
    links: Optional[List[str]] = []
    postings: List[Any] # Adjust 'Any' to a more specific Posting schema if available
    is_active: Optional[bool] = True


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(BaseModel):
    name: Optional[str] = None
    recurrence_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    weekly_days: Optional[List[int]] = None
    monthly_days: Optional[List[int]] = None
    flag: Optional[str] = None
    payee: Optional[str] = None
    narration: Optional[str] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None
    postings: Optional[List[Any]] = None
    is_active: Optional[bool] = None


class RecurringTransactionResponse(RecurringTransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_executed: Optional[date] = None
    next_execution: Optional[date] = None

    class Config:
        orm_mode = True

class RecurringExecutionLog(BaseModel):
    """周期记账执行日志"""
    id: str
    recurring_transaction_id: str
    execution_date: date
    success: bool
    error_message: Optional[str] = None
    created_transaction_id: Optional[str] = None
    created_at: datetime

class RecurringExecutionResult(BaseModel):
    """周期记账执行结果"""
    success: bool
    message: str
    executed_count: int
    failed_count: int
    details: List[Dict[str, Any]]

class AccountCreate(BaseModel):
    """创建账户请求"""
    name: str = Field(..., description="账户名称，需要符合beancount规范")
    open_date: date = Field(..., description="账户开启日期")
    currencies: Optional[List[str]] = Field(None, description="约束货币列表")
    booking_method: Optional[str] = Field(None, description="记账方法")

class AccountClose(BaseModel):
    """归档账户请求"""
    name: str = Field(..., description="账户名称")
    close_date: date = Field(..., description="账户关闭日期")

class AccountRestore(BaseModel):
    """恢复账户请求"""
    name: str = Field(..., description="账户名称")

class AccountActionResponse(BaseModel):
    """账户操作响应"""
    success: bool
    message: str
    account_name: str

# 新增：主币种和价格管理相关的 Schema
class OperatingCurrencyResponse(BaseModel):
    """主币种响应"""
    operating_currency: str

class OperatingCurrencyUpdate(BaseModel):
    """主币种更新请求"""
    operating_currency: str = Field(..., description="主币种代码，如 CNY, USD 等")

class PriceEntry(BaseModel):
    """价格条目"""
    entry_date: date = Field(..., description="价格日期", alias="date")
    from_currency: str = Field(..., description="源货币")
    to_currency: str = Field(..., description="目标货币")
    rate: Decimal = Field(..., description="汇率")
    
    model_config = {"populate_by_name": True}

class PriceCreate(BaseModel):
    """创建价格请求"""
    entry_date: date = Field(..., description="价格日期", alias="date")
    from_currency: str = Field(..., description="源货币")
    to_currency: Optional[str] = Field(None, description="目标货币，默认为主币种")
    rate: Decimal = Field(..., description="汇率")
    
    model_config = {"populate_by_name": True}

class PriceResponse(BaseModel):
    """价格响应"""
    prices: List[PriceEntry]
    total: int
    page: int
    page_size: int

class PriceFilter(BaseModel):
    """价格筛选参数"""
    from_currency: Optional[str] = None
    to_currency: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    price_date: Optional[date] = None 