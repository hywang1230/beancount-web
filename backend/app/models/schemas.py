from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

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
    narration: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

class FileInfo(BaseModel):
    name: str
    path: str
    size: int
    modified: datetime
    is_main: bool = False

class FileListResponse(BaseModel):
    files: List[FileInfo]
    main_file: Optional[str] = None 