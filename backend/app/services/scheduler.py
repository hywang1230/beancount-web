import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.recurring_service import recurring_service

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
            result = recurring_service.execute_pending_transactions()
            
            if result.success:
                logger.info(f"周期记账执行成功：{result.message}")
                if result.executed_count > 0:
                    logger.info(f"成功执行 {result.executed_count} 个周期记账")
            else:
                logger.warning(f"周期记账执行有错误：{result.message}")
                if result.failed_count > 0:
                    logger.warning(f"失败 {result.failed_count} 个周期记账")
                    for detail in result.details:
                        if not detail["success"]:
                            logger.warning(f"- {detail['name']}: {detail['message']}")
        
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
    
    async def manual_execute(self):
        """手动执行一次周期记账"""
        await self._execute_daily_recurring_transactions()

# 创建全局调度器实例
scheduler = RecurringTransactionScheduler() 