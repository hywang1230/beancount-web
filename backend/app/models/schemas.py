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
    tags: Optional[List[str]] = []
    links: Optional[List[str]] = []

class PostingBase(BaseModel):
    account: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    price: Optional[Dict[str, Any]] = None

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

class FileListResponse(BaseModel):
    files: List[FileInfo]
    main_file: Optional[str] = None

class RecurrenceType(str, Enum):
    """周期类型枚举"""
    DAILY = "daily"  # 每日
    WEEKLY = "weekly"  # 每周特定几天
    WEEKDAYS = "weekdays"  # 工作日
    MONTHLY = "monthly"  # 每月特定几天

class RecurringTransactionBase(BaseModel):
    """周期记账基础模型"""
    name: str = Field(..., description="周期记账名称")
    description: Optional[str] = Field(None, description="描述")
    recurrence_type: RecurrenceType = Field(..., description="周期类型")
    start_date: date = Field(..., description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期，为空表示无限期")
    
    # 周期配置
    weekly_days: Optional[List[int]] = Field(None, description="每周的第几天（0=周一，6=周日）")
    monthly_days: Optional[List[int]] = Field(None, description="每月的第几日（1-31）")
    
    # 交易模板
    flag: str = Field("*", description="交易标志")
    payee: Optional[str] = Field(None, description="收付方")
    narration: str = Field(..., description="摘要")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")
    links: Optional[List[str]] = Field(default_factory=list, description="链接")
    postings: List[PostingBase] = Field(..., description="记账分录")
    
    # 状态
    is_active: bool = Field(True, description="是否启用")

class RecurringTransactionCreate(RecurringTransactionBase):
    """创建周期记账请求"""
    pass

class RecurringTransactionUpdate(BaseModel):
    """更新周期记账请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    recurrence_type: Optional[RecurrenceType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    weekly_days: Optional[List[int]] = None
    monthly_days: Optional[List[int]] = None
    flag: Optional[str] = None
    payee: Optional[str] = None
    narration: Optional[str] = None
    tags: Optional[List[str]] = None
    links: Optional[List[str]] = None
    postings: Optional[List[PostingBase]] = None
    is_active: Optional[bool] = None

class RecurringTransactionResponse(RecurringTransactionBase):
    """周期记账响应"""
    id: str = Field(..., description="ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_executed: Optional[date] = Field(None, description="最后执行日期")
    next_execution: Optional[date] = Field(None, description="下次执行日期")
    
    model_config = {"from_attributes": True}

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