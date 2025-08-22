import uuid
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.schemas import RecurringTransactionCreate, RecurringTransactionUpdate
from app.models.recurring import Recurring as RecurringModel, RecurringExecutionLog
from app.services.beancount_service import beancount_service
from app.core.config import settings

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RecurringTransactionService:
    def _calculate_next_execution(self, transaction: RecurringModel) -> Optional[date]:
        """计算下次执行日期"""
        today = date.today()
        
        # 如果有结束日期且已过期，返回None
        if transaction.end_date and today > transaction.end_date:
            return None
        
        # 获取基准日期（上次执行日期或开始日期）
        base_date = transaction.last_executed if transaction.last_executed else transaction.start_date
        
        # 根据周期类型计算下次执行日期
        if transaction.recurrence_type == "daily":
            next_date = base_date + timedelta(days=1)
            
        elif transaction.recurrence_type == "weekly":
            # 每周特定几天
            if not transaction.weekly_days:
                # 如果没有指定周几，默认为每周的同一天
                next_date = base_date + timedelta(weeks=1)
            else:
                # 找到下一个指定的周几
                next_date = self._find_next_weekday(base_date, transaction.weekly_days)
                
        elif transaction.recurrence_type == "weekdays":
            # 工作日（周一到周五）
            next_date = self._find_next_weekday(base_date, [0, 1, 2, 3, 4])  # 0=周一, 4=周五
            
        elif transaction.recurrence_type == "monthly":
            # 每月特定几天
            if not transaction.monthly_days:
                # 如果没有指定日期，默认为每月的同一天
                if base_date.month == 12:
                    next_date = base_date.replace(year=base_date.year + 1, month=1)
                else:
                    next_date = base_date.replace(month=base_date.month + 1)
            else:
                # 找到下一个指定的月日
                next_date = self._find_next_monthly_date(base_date, transaction.monthly_days)
        else:
            logger.warning(f"未知的周期类型: {transaction.recurrence_type}")
            return None
        
        # 确保下次执行日期不早于今天
        if next_date <= today:
            # 如果计算出的日期是今天或之前，需要再计算下一个周期
            if transaction.recurrence_type == "daily":
                while next_date <= today:
                    next_date += timedelta(days=1)
            elif transaction.recurrence_type == "weekly":
                if transaction.weekly_days:
                    next_date = self._find_next_weekday(today, transaction.weekly_days)
                else:
                    while next_date <= today:
                        next_date += timedelta(weeks=1)
            elif transaction.recurrence_type == "weekdays":
                next_date = self._find_next_weekday(today, [0, 1, 2, 3, 4])
            elif transaction.recurrence_type == "monthly":
                if transaction.monthly_days:
                    next_date = self._find_next_monthly_date(today, transaction.monthly_days)
                else:
                    while next_date <= today:
                        if next_date.month == 12:
                            next_date = next_date.replace(year=next_date.year + 1, month=1)
                        else:
                            next_date = next_date.replace(month=next_date.month + 1)
        
        # 检查是否超过结束日期
        if transaction.end_date and next_date > transaction.end_date:
            return None
            
        return next_date
    
    def _find_next_weekday(self, base_date: date, weekdays: List[int]) -> date:
        """找到下一个指定的周几"""
        current_weekday = base_date.weekday()  # 0=周一, 6=周日
        
        # 在当前周内查找下一个指定的周几
        for day_offset in range(1, 8):
            target_date = base_date + timedelta(days=day_offset)
            if target_date.weekday() in weekdays:
                return target_date
        
        # 如果在当前周内没找到，查找下一周
        for day_offset in range(8, 15):
            target_date = base_date + timedelta(days=day_offset)
            if target_date.weekday() in weekdays:
                return target_date
                
        # 默认返回下周的第一个指定日期
        return base_date + timedelta(days=7)
    
    def _find_next_monthly_date(self, base_date: date, monthly_days: List[int]) -> date:
        """找到下一个指定的月日"""
        import calendar
        
        # 在当前月内查找下一个指定日期
        for day in sorted(monthly_days):
            if day > base_date.day:
                try:
                    return base_date.replace(day=day)
                except ValueError:
                    # 如果当前月没有这一天（比如2月30日），跳过
                    continue
        
        # 在当前月没找到，查找下一个月
        next_month = base_date.month + 1
        next_year = base_date.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        # 找到下个月的第一个有效日期
        for day in sorted(monthly_days):
            try:
                # 检查下个月是否有这一天
                max_day = calendar.monthrange(next_year, next_month)[1]
                if day <= max_day:
                    return date(next_year, next_month, day)
            except ValueError:
                continue
        
        # 如果都找不到，返回下个月的第一天
        return date(next_year, next_month, 1)
    
    def _convert_to_beancount_transaction(self, transaction: RecurringModel, execution_date: date) -> dict:
        """将周期记账转换为beancount交易格式"""
        try:
            # 构建交易数据
            transaction_data = {
                'date': execution_date.strftime('%Y-%m-%d'),
                'flag': transaction.flag or '*',
                'payee': transaction.payee,
                'narration': transaction.narration,
                'postings': []
            }
            
            # 添加标签和链接信息到描述中
            if transaction.tags:
                tags_str = ' '.join(f"#{tag}" for tag in transaction.tags)
                transaction_data['narration'] += f" {tags_str}"
            
            if transaction.links:
                links_str = ' '.join(f"^{link}" for link in transaction.links)
                transaction_data['narration'] += f" {links_str}"
            
            # 处理分录
            if transaction.postings:
                for posting in transaction.postings:
                    posting_data = {
                        'account': posting['account']
                    }
                    
                    # 如果有金额和货币，添加到分录中
                    if posting.get('amount') is not None and posting.get('currency'):
                        posting_data['amount'] = posting['amount']
                        posting_data['currency'] = posting['currency']
                    
                    transaction_data['postings'].append(posting_data)
            
            logger.debug(f"转换周期记账为beancount格式: {transaction_data}")
            return transaction_data
            
        except Exception as e:
            logger.error(f"转换周期记账格式失败: {str(e)}")
            raise Exception(f"转换交易格式失败: {str(e)}")

    def create_recurring_transaction(self, db: Session, transaction_in: RecurringTransactionCreate) -> RecurringModel:
        """创建周期记账"""
        
        transaction_data = transaction_in.model_dump()
        
        db_transaction = RecurringModel(**transaction_data)
        
        # Calculate initial next_execution date
        db_transaction.next_execution = self._calculate_next_execution(db_transaction)

        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    def get_recurring_transactions(self, db: Session, active_only: bool = False) -> List[RecurringModel]:
        """获取周期记账列表"""
        query = db.query(RecurringModel)
        if active_only:
            query = query.filter(RecurringModel.is_active == True)
        
        # 添加SQL日志
        sql_query = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        logger.debug(f"获取周期记账列表SQL: {sql_query}")
        
        results = query.all()
        logger.info(f"获取到 {len(results)} 个周期记账")
        
        for r in results:
            logger.debug(f"周期记账: ID={r.id}, name={r.name}, is_active={r.is_active}, next_execution={r.next_execution}")
        
        return results

    def get_recurring_transaction(self, db: Session, transaction_id: int) -> Optional[RecurringModel]:
        """获取单个周期记账"""
        return db.query(RecurringModel).filter(RecurringModel.id == transaction_id).first()

    def update_recurring_transaction(
        self, db: Session, transaction_id: int, transaction_in: RecurringTransactionUpdate
    ) -> Optional[RecurringModel]:
        """更新周期记账"""
        db_transaction = self.get_recurring_transaction(db, transaction_id)
        if not db_transaction:
            return None

        update_data = transaction_in.model_dump(exclude_unset=True)
        
        # 检查是否更新了影响执行时间计算的字段
        execution_affecting_fields = {
            'recurrence_type', 'start_date', 'end_date', 
            'weekly_days', 'monthly_days', 'is_active'
        }
        should_recalculate = any(field in update_data for field in execution_affecting_fields)
        
        for key, value in update_data.items():
            setattr(db_transaction, key, value)
            
        # 只有在相关字段改变时才重新计算下次执行时间
        if should_recalculate:
            logger.info(f"重新计算周期记账 {db_transaction.name} 的下次执行时间，因为相关字段发生变化")
            db_transaction.next_execution = self._calculate_next_execution(db_transaction)
        else:
            logger.debug(f"周期记账 {db_transaction.name} 更新未影响执行时间计算字段，保持原有的 next_execution")

        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    def delete_recurring_transaction(self, db: Session, transaction_id: int) -> bool:
        """删除周期记账"""
        db_transaction = self.get_recurring_transaction(db, transaction_id)
        if not db_transaction:
            return False
        
        try:
            # 先删除相关的执行日志
            execution_logs = db.query(RecurringExecutionLog).filter(
                RecurringExecutionLog.recurring_transaction_id == transaction_id
            ).all()
            
            logger.info(f"删除周期记账 {db_transaction.name} 及其 {len(execution_logs)} 条执行日志")
            
            for log in execution_logs:
                db.delete(log)
            
            # 再删除周期记账本身
            db.delete(db_transaction)
            db.commit()
            
            logger.info(f"成功删除周期记账 {db_transaction.name}")
            return True
            
        except Exception as e:
            logger.error(f"删除周期记账失败: {str(e)}")
            db.rollback()
            raise

    def execute_pending_transactions(self, db: Session, execution_date: Optional[date] = None):
        """执行待处理的周期记账"""
        if execution_date is None:
            execution_date = date.today()
        
        logger.info(f"开始执行周期记账，执行日期: {execution_date}")
        
        # 1. 查询需要执行的周期记账
        query = db.query(RecurringModel).filter(
            RecurringModel.is_active == True,
            RecurringModel.next_execution <= execution_date
        )
        
        # 添加SQL日志
        sql_query = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        logger.debug(f"执行SQL查询: {sql_query}")
        
        pending_transactions = query.all()
        logger.info(f"找到 {len(pending_transactions)} 个待执行的周期记账")
        
        executed_count = 0
        failed_count = 0
        details = []
        
        for transaction in pending_transactions:
            logger.info(f"执行周期记账: {transaction.name} (ID: {transaction.id})")
            execution_log = None
            
            try:
                # 2. 使用beancount_service创建交易
                transaction_data = self._convert_to_beancount_transaction(transaction, execution_date)
                success = beancount_service.add_transaction(transaction_data)
                
                if not success:
                    raise Exception("写入账本文件失败")
                
                # 生成交易ID用于记录
                created_transaction_id = f"recurring_{transaction.id}_{execution_date}"
                
                # 3. 更新执行记录
                transaction.last_executed = execution_date
                transaction.next_execution = self._calculate_next_execution(transaction)
                
                # 4. 创建执行日志（成功）
                execution_log = RecurringExecutionLog(
                    recurring_transaction_id=transaction.id,
                    execution_date=execution_date,
                    success=True,
                    created_transaction_id=created_transaction_id
                )
                db.add(execution_log)
                
                executed_count += 1
                details.append({
                    "name": transaction.name,
                    "success": True,
                    "message": "执行成功"
                })
                logger.info(f"周期记账 {transaction.name} 执行成功，下次执行: {transaction.next_execution}")
                
            except Exception as e:
                failed_count += 1
                error_msg = f"执行失败: {str(e)}"
                
                # 4. 创建执行日志（失败）
                execution_log = RecurringExecutionLog(
                    recurring_transaction_id=transaction.id,
                    execution_date=execution_date,
                    success=False,
                    error_message=error_msg
                )
                db.add(execution_log)
                
                details.append({
                    "name": transaction.name,
                    "success": False,
                    "message": error_msg
                })
                logger.error(f"周期记账 {transaction.name} 执行失败: {str(e)}")
        
        # 提交数据库更改
        try:
            db.commit()
            logger.info("数据库提交成功")
        except Exception as e:
            db.rollback()
            logger.error(f"数据库提交失败: {str(e)}")
            raise
        
        result = {
            "success": failed_count == 0,
            "message": f"执行完成，成功 {executed_count} 个，失败 {failed_count} 个",
            "executed_count": executed_count,
            "failed_count": failed_count,
            "details": details
        }
        
        logger.info(f"周期记账执行完成: {result}")
        return result
    
    def get_execution_logs(self, db: Session, transaction_id: Optional[int] = None, days: int = 30) -> List[RecurringExecutionLog]:
        """获取执行日志"""
        from datetime import datetime, timedelta
        
        # 计算查询的起始日期
        start_date = datetime.now() - timedelta(days=days)
        
        query = db.query(RecurringExecutionLog).filter(
            RecurringExecutionLog.created_at >= start_date
        )
        
        if transaction_id:
            query = query.filter(RecurringExecutionLog.recurring_transaction_id == transaction_id)
        
        # 按创建时间降序排列
        query = query.order_by(RecurringExecutionLog.created_at.desc())
        
        # 添加SQL日志
        sql_query = str(query.statement.compile(compile_kwargs={"literal_binds": True}))
        logger.debug(f"获取执行日志SQL: {sql_query}")
        
        results = query.all()
        logger.info(f"获取到 {len(results)} 条执行日志")
        
        return results

# This service will no longer be a singleton instance.
# It will be instantiated on-demand by the router with a DB session.
recurring_service = RecurringTransactionService() 