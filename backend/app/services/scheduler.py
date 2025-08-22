import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.services.recurring_service import recurring_service
from app.core.config import settings
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class RecurringTransactionScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 每天中午12点执行周期记账
        self.scheduler.add_job(
            func=self._execute_daily_recurring_transactions,
            trigger=CronTrigger(hour=12, minute=0),  # 每天12:00
            id="daily_recurring_transactions",
            name="每日周期记账执行",
            replace_existing=True
        )
        
        logger.info("定时任务已设置：每天中午12点执行周期记账")
    
    async def _execute_daily_recurring_transactions(self):
        """执行每日周期记账任务"""
        try:
            logger.info("开始执行每日周期记账任务")
            # 需要数据库会话来执行周期记账
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                result = recurring_service.execute_pending_transactions(db)
                
                if result and hasattr(result, 'success'):
                    if result.success:
                        logger.info(f"周期记账执行成功：{result.message}")
                        if hasattr(result, 'executed_count') and result.executed_count > 0:
                            logger.info(f"成功执行 {result.executed_count} 个周期记账")
                            # 如果有周期记账被执行，安排延迟同步
                            self.schedule_delayed_sync(db, delay_seconds=settings.recurring_sync_delay_seconds)
                    else:
                        logger.warning(f"周期记账执行有错误：{result.message}")
                        if hasattr(result, 'failed_count') and result.failed_count > 0:
                            logger.warning(f"失败 {result.failed_count} 个周期记账")
                            if hasattr(result, 'details'):
                                for detail in result.details:
                                    if not detail["success"]:
                                        logger.warning(f"- {detail['name']}: {detail['message']}")
                else:
                    logger.info("没有待执行的周期记账")
            finally:
                db.close()
        
        except Exception as e:
            logger.error(f"执行每日周期记账任务时发生错误: {e}")
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("周期记账调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("周期记账调度器已关闭")
    
    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
    
    async def manual_execute(self, db: Session = None):
        """手动执行一次周期记账"""
        if db:
            # 如果有数据库会话，直接执行
            try:
                logger.info("手动执行周期记账任务")
                result = recurring_service.execute_pending_transactions(db)
                
                if result and hasattr(result, 'success'):
                    if result.success and hasattr(result, 'executed_count') and result.executed_count > 0:
                        logger.info(f"手动执行周期记账成功：{result.executed_count} 个交易")
                        # 安排延迟同步
                        self.schedule_delayed_sync(db, delay_seconds=settings.sync_delay_seconds)
                        return result
                
                return result
            except Exception as e:
                logger.error(f"手动执行周期记账失败: {e}")
                raise
        else:
            # 否则使用原有方法
            await self._execute_daily_recurring_transactions()
    
    def schedule_delayed_sync(self, db: Session, delay_seconds: int = None):
        """安排延迟同步任务
        
        Args:
            db: 数据库会话
            delay_seconds: 延迟秒数，如果不指定则使用配置的默认值
        """
        if delay_seconds is None:
            delay_seconds = settings.sync_delay_seconds
        try:
            # 如果已存在延迟同步任务，先取消
            existing_job = self.scheduler.get_job("delayed_auto_sync")
            if existing_job:
                self.scheduler.remove_job("delayed_auto_sync")
                logger.info("已取消之前的延迟同步任务")
            
            # 安排新的延迟同步任务
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            self.scheduler.add_job(
                func=self._execute_delayed_sync,
                trigger=DateTrigger(run_date=run_time),
                id="delayed_auto_sync",
                name="延迟自动同步",
                args=[db],
                replace_existing=True
            )
            
            logger.info(f"已安排延迟同步任务，将在 {delay_seconds} 秒后执行")
            
        except Exception as e:
            logger.error(f"安排延迟同步任务失败: {e}")
    
    async def _execute_delayed_sync(self, db: Session):
        """执行延迟同步任务"""
        try:
            logger.info("开始执行延迟自动同步")
            
            # 导入GitHubSyncService避免循环导入
            from app.services.github_sync_service import GitHubSyncService
            
            sync_service = GitHubSyncService(db=db)
            config = await sync_service.get_config()
            
            if config and config.auto_sync:
                try:
                    logger.info("延迟自动同步触发")
                    await sync_service._auto_sync()
                    logger.info("延迟自动同步执行成功")
                except Exception as e:
                    logger.error(f"延迟自动同步执行失败: {e}")
            else:
                logger.info("自动同步未启用，跳过延迟同步")
                
        except Exception as e:
            logger.error(f"执行延迟同步任务时发生错误: {e}")
    
    def cancel_delayed_sync(self):
        """取消延迟同步任务"""
        try:
            existing_job = self.scheduler.get_job("delayed_auto_sync")
            if existing_job:
                self.scheduler.remove_job("delayed_auto_sync")
                logger.info("已取消延迟同步任务")
                return True
            return False
        except Exception as e:
            logger.error(f"取消延迟同步任务失败: {e}")
            return False

# 创建全局调度器实例
scheduler = RecurringTransactionScheduler() 