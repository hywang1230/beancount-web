import json
import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import calendar

from app.core.config import settings
from app.models.schemas import (
    RecurringTransactionCreate, RecurringTransactionUpdate, 
    RecurringTransactionResponse, RecurrenceType,
    RecurringExecutionLog, RecurringExecutionResult,
    TransactionCreate
)
from app.services.beancount_service import beancount_service

def _parse_date(date_value) -> Optional[date]:
    """安全解析日期，支持字符串和date对象"""
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, str):
        return datetime.fromisoformat(date_value).date()
    return None

class RecurringTransactionService:
    def __init__(self):
        self.data_file = settings.data_dir / "recurring_transactions.json"
        self.log_file = settings.data_dir / "recurring_execution_logs.json"
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """确保数据文件存在"""
        if not self.data_file.exists():
            self.data_file.write_text("[]")
        if not self.log_file.exists():
            self.log_file.write_text("[]")
    
    def _load_recurring_transactions(self) -> List[Dict]:
        """加载周期记账数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_recurring_transactions(self, transactions: List[Dict]):
        """保存周期记账数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(transactions, f, ensure_ascii=False, indent=2, default=str)
    
    def _load_execution_logs(self) -> List[Dict]:
        """加载执行日志"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_execution_logs(self, logs: List[Dict]):
        """保存执行日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
    
    def create_recurring_transaction(self, transaction: RecurringTransactionCreate) -> RecurringTransactionResponse:
        """创建周期记账"""
        transactions = self._load_recurring_transactions()
        
        # 生成唯一ID
        transaction_id = str(uuid.uuid4())
        now = datetime.now()
        
        # 转换为字典
        transaction_dict = transaction.model_dump()
        transaction_dict.update({
            "id": transaction_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_executed": None,
            "next_execution": self._calculate_next_execution(transaction, None)
        })
        
        transactions.append(transaction_dict)
        self._save_recurring_transactions(transactions)
        
        return RecurringTransactionResponse(**transaction_dict)
    
    def get_recurring_transactions(self, active_only: bool = False) -> List[RecurringTransactionResponse]:
        """获取周期记账列表"""
        transactions = self._load_recurring_transactions()
        
        if active_only:
            transactions = [t for t in transactions if t.get("is_active", True)]
        
        # 更新下次执行时间
        for transaction in transactions:
            transaction["next_execution"] = self._calculate_next_execution_from_dict(transaction)
        
        return [RecurringTransactionResponse(**t) for t in transactions]
    
    def get_recurring_transaction(self, transaction_id: str) -> Optional[RecurringTransactionResponse]:
        """获取单个周期记账"""
        transactions = self._load_recurring_transactions()
        
        for transaction in transactions:
            if transaction["id"] == transaction_id:
                transaction["next_execution"] = self._calculate_next_execution_from_dict(transaction)
                return RecurringTransactionResponse(**transaction)
        
        return None
    
    def update_recurring_transaction(self, transaction_id: str, update_data: RecurringTransactionUpdate) -> Optional[RecurringTransactionResponse]:
        """更新周期记账"""
        transactions = self._load_recurring_transactions()
        
        for i, transaction in enumerate(transactions):
            if transaction["id"] == transaction_id:
                # 更新字段
                update_dict = update_data.model_dump(exclude_unset=True)
                transaction.update(update_dict)
                transaction["updated_at"] = datetime.now().isoformat()
                
                # 重新计算下次执行时间（考虑最后执行时间）
                transaction["next_execution"] = self._calculate_next_execution_from_dict(transaction)
                
                transactions[i] = transaction
                self._save_recurring_transactions(transactions)
                
                return RecurringTransactionResponse(**transaction)
        
        return None
    
    def delete_recurring_transaction(self, transaction_id: str) -> bool:
        """删除周期记账"""
        transactions = self._load_recurring_transactions()
        
        for i, transaction in enumerate(transactions):
            if transaction["id"] == transaction_id:
                del transactions[i]
                self._save_recurring_transactions(transactions)
                return True
        
        return False
    
    def execute_pending_transactions(self, execution_date: Optional[date] = None) -> RecurringExecutionResult:
        """执行待处理的周期记账"""
        if execution_date is None:
            execution_date = date.today()
        
        transactions = self._load_recurring_transactions()
        logs = self._load_execution_logs()
        
        executed_count = 0
        failed_count = 0
        details = []
        
        for transaction in transactions:
            if not transaction.get("is_active", True):
                continue
            
            if self._should_execute_on_date(transaction, execution_date):
                # 检查今天是否已经执行过
                if self._already_executed_today(transaction["id"], execution_date, logs):
                    continue
                
                try:
                    # 创建交易
                    success = self._execute_single_transaction(transaction, execution_date)
                    
                    if success:
                        executed_count += 1
                        # 更新最后执行时间
                        transaction["last_executed"] = execution_date.isoformat()
                        transaction["updated_at"] = datetime.now().isoformat()
                        
                        # 记录日志
                        log_entry = {
                            "id": str(uuid.uuid4()),
                            "recurring_transaction_id": transaction["id"],
                            "execution_date": execution_date.isoformat(),
                            "success": True,
                            "error_message": None,
                            "created_at": datetime.now().isoformat()
                        }
                        logs.append(log_entry)
                        
                        details.append({
                            "name": transaction["name"],
                            "success": True,
                            "message": "执行成功"
                        })
                    else:
                        failed_count += 1
                        details.append({
                            "name": transaction["name"],
                            "success": False,
                            "message": "创建交易失败"
                        })
                
                except Exception as e:
                    failed_count += 1
                    error_msg = str(e)
                    
                    # 记录错误日志
                    log_entry = {
                        "id": str(uuid.uuid4()),
                        "recurring_transaction_id": transaction["id"],
                        "execution_date": execution_date.isoformat(),
                        "success": False,
                        "error_message": error_msg,
                        "created_at": datetime.now().isoformat()
                    }
                    logs.append(log_entry)
                    
                    details.append({
                        "name": transaction["name"],
                        "success": False,
                        "message": f"执行失败: {error_msg}"
                    })
        
        # 保存更新后的数据
        self._save_recurring_transactions(transactions)
        self._save_execution_logs(logs)
        
        return RecurringExecutionResult(
            success=failed_count == 0,
            message=f"执行完成，成功 {executed_count} 个，失败 {failed_count} 个",
            executed_count=executed_count,
            failed_count=failed_count,
            details=details
        )
    
    def _execute_single_transaction(self, recurring_transaction: Dict, execution_date: date) -> bool:
        """执行单个周期记账"""
        try:
            # 构建交易数据
            transaction_data = {
                "date": execution_date.isoformat(),
                "flag": recurring_transaction.get("flag", "*"),
                "payee": recurring_transaction.get("payee"),
                "narration": recurring_transaction["narration"],
                "tags": recurring_transaction.get("tags", []),
                "links": recurring_transaction.get("links", []),
                "postings": recurring_transaction["postings"]
            }
            
            # 使用beancount服务创建交易
            return beancount_service.add_transaction(transaction_data)
        
        except Exception as e:
            print(f"执行周期记账失败: {e}")
            return False
    
    def _should_execute_on_date(self, transaction: Dict, target_date: date) -> bool:
        """判断是否应该在指定日期执行"""
        start_date = _parse_date(transaction["start_date"])
        end_date = _parse_date(transaction.get("end_date"))
        
        if not start_date:
            return False
        
        # 检查日期范围
        if target_date < start_date:
            return False
        if end_date and target_date > end_date:
            return False
        
        recurrence_type = transaction["recurrence_type"]
        
        if recurrence_type == RecurrenceType.DAILY:
            return True
        
        elif recurrence_type == RecurrenceType.WEEKDAYS:
            # 工作日（周一到周五）
            return target_date.weekday() < 5
        
        elif recurrence_type == RecurrenceType.WEEKLY:
            # 每周特定几天
            weekly_days = transaction.get("weekly_days", [])
            return target_date.weekday() in weekly_days
        
        elif recurrence_type == RecurrenceType.MONTHLY:
            # 每月特定几天
            monthly_days = transaction.get("monthly_days", [])
            return target_date.day in monthly_days
        
        return False
    
    def _already_executed_today(self, transaction_id: str, execution_date: date, logs: List[Dict]) -> bool:
        """检查今天是否已经执行过"""
        execution_date_str = execution_date.isoformat()
        
        for log in logs:
            if (log["recurring_transaction_id"] == transaction_id and 
                log["execution_date"] == execution_date_str and 
                log["success"]):
                return True
        
        return False
    
    def _calculate_next_execution(self, transaction: RecurringTransactionCreate, last_executed: Optional[date]) -> Optional[str]:
        """计算下次执行时间"""
        today = date.today()
        start_date = transaction.start_date
        end_date = transaction.end_date
        
        # 如果有结束日期且已过期，返回None
        if end_date and today > end_date:
            return None
        
        # 确定开始搜索的日期
        if last_executed:
            # 如果已经执行过，从最后执行日期的下一天开始搜索
            search_start = max(last_executed + timedelta(days=1), today)
        else:
            # 如果从未执行过，从今天或开始日期开始搜索
            search_start = max(today, start_date)
        
        # 最多查找365天
        for days_ahead in range(365):
            check_date = search_start + timedelta(days=days_ahead)
            
            if end_date and check_date > end_date:
                break
            
            if self._should_execute_on_date_obj(transaction, check_date):
                return check_date.isoformat()
        
        return None
    
    def _calculate_next_execution_from_dict(self, transaction: Dict) -> Optional[str]:
        """从字典计算下次执行时间"""
        last_executed = _parse_date(transaction.get("last_executed"))
        start_date = _parse_date(transaction["start_date"])
        end_date = _parse_date(transaction.get("end_date"))
        
        if not start_date:
            return None
        
        # 创建临时对象用于计算
        temp_transaction = RecurringTransactionCreate(
            name=transaction["name"],
            recurrence_type=RecurrenceType(transaction["recurrence_type"]),
            start_date=start_date,
            end_date=end_date,
            weekly_days=transaction.get("weekly_days"),
            monthly_days=transaction.get("monthly_days"),
            narration=transaction["narration"],
            postings=transaction["postings"]
        )
        
        return self._calculate_next_execution(temp_transaction, last_executed)
    
    def _should_execute_on_date_obj(self, transaction: RecurringTransactionCreate, target_date: date) -> bool:
        """判断是否应该在指定日期执行（基于对象）"""
        if recurrence_type := transaction.recurrence_type:
            if recurrence_type == RecurrenceType.DAILY:
                return True
            elif recurrence_type == RecurrenceType.WEEKDAYS:
                return target_date.weekday() < 5
            elif recurrence_type == RecurrenceType.WEEKLY:
                return target_date.weekday() in (transaction.weekly_days or [])
            elif recurrence_type == RecurrenceType.MONTHLY:
                return target_date.day in (transaction.monthly_days or [])
        
        return False
    
    def get_execution_logs(self, transaction_id: Optional[str] = None, days: int = 30) -> List[RecurringExecutionLog]:
        """获取执行日志"""
        logs = self._load_execution_logs()
        
        # 过滤指定天数内的日志
        cutoff_date = date.today() - timedelta(days=days)
        
        filtered_logs = []
        for log in logs:
            log_date = _parse_date(log["execution_date"])
            if log_date and log_date >= cutoff_date:
                if transaction_id is None or log["recurring_transaction_id"] == transaction_id:
                    filtered_logs.append(RecurringExecutionLog(**log))
        
        # 按日期降序排列
        filtered_logs.sort(key=lambda x: x.execution_date, reverse=True)
        
        return filtered_logs

# 创建全局服务实例
recurring_service = RecurringTransactionService() 