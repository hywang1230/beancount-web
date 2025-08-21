import uuid
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.schemas import RecurringTransactionCreate, RecurringTransactionUpdate
from app.models.recurring import Recurring as RecurringModel
from app.services.beancount_service import beancount_service


class RecurringTransactionService:
    def _calculate_next_execution(self, transaction: RecurringModel) -> Optional[date]:
        # This is a placeholder for the actual calculation logic.
        # The full logic will be re-implemented based on the old service file.
        today = date.today()
        start_date = transaction.start_date
        
        if transaction.end_date and today > transaction.end_date:
            return None

        # Simplified logic for now
        # TODO: Implement full next execution date calculation
        if transaction.last_executed:
            next_date = transaction.last_executed + timedelta(days=30) # Assume monthly for now
        else:
            next_date = start_date

        return max(next_date, today)

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
        return query.all()

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
        for key, value in update_data.items():
            setattr(db_transaction, key, value)
            
        # Recalculate next execution date if relevant fields changed
        db_transaction.next_execution = self._calculate_next_execution(db_transaction)

        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    def delete_recurring_transaction(self, db: Session, transaction_id: int) -> bool:
        """删除周期记账"""
        db_transaction = self.get_recurring_transaction(db, transaction_id)
        if not db_transaction:
            return False
        
        db.delete(db_transaction)
        db.commit()
        return True

    def execute_pending_transactions(self, db: Session, execution_date: Optional[date] = None):
        """执行待处理的周期记账"""
        # This will be implemented later. It will involve:
        # 1. Querying for transactions where next_execution is today or in the past.
        # 2. Executing them using beancount_service.
        # 3. Logging the execution result (success/failure).
        # 4. Updating last_executed and calculating the new next_execution.
        pass

# This service will no longer be a singleton instance.
# It will be instantiated on-demand by the router with a DB session.
recurring_service = RecurringTransactionService() 