"""
定时任务工具
"""

from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from functools import wraps

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

# 延迟导入 RedisJobStore，避免在没有 redis 模块时报错
try:
    from apscheduler.jobstores.redis import RedisJobStore
    REDIS_AVAILABLE = True
except ImportError:
    RedisJobStore = None
    REDIS_AVAILABLE = False

from core.config import settings
from core.logger import logger
from tools.registry import register_method_tool


class SchedulerTool:
    """
    定时任务工具
    支持cron、间隔和一次性任务
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        self.backend = backend or settings.scheduler_backend
        self.redis_url = redis_url or settings.scheduler_redis_url
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._job_callbacks: Dict[str, Callable] = {}

    def _get_scheduler(self) -> AsyncIOScheduler:
        """获取调度器实例"""
        if self._scheduler is None:
            jobstores = {'default': MemoryJobStore()}
            executors = {'default': ThreadPoolExecutor(20)}

            if self.backend == 'redis' and self.redis_url:
                if not REDIS_AVAILABLE:
                    logger.warning("Redis backend requested but redis module not installed. Using memory backend instead.")
                    logger.warning("To use Redis backend, install redis: pip install redis")
                else:
                    jobstores['default'] = RedisJobStore(
                        jobs_key='agent:scheduler:jobs',
                        run_times_key='agent:scheduler:run_times',
                        url=self.redis_url
                    )

            self._scheduler = AsyncIOScheduler(
                jobstores=jobstores,
                executors=executors,
                timezone='Asia/Shanghai'
            )
            self._scheduler.start()
            logger.info(f"Scheduler started with {self.backend} backend")

        return self._scheduler

    @register_method_tool(
        name="scheduler_add_cron",
        description="添加cron定时任务",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "任务ID"},
                "cron_expr": {"type": "string", "description": "cron表达式（5段）", "example": "0 9 * * *"}
            },
            "required": ["job_id", "cron_expr"]
        },
        category="scheduler"
    )
    def add_cron_job(
        self,
        job_id: str,
        func: Callable,
        cron_expr: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        添加cron定时任务

        Args:
            job_id: 任务ID
            func: 任务函数
            cron_expr: cron表达式 (如 "0 9 * * *" 表示每天9点)
            **kwargs: 额外参数

        Returns:
            任务信息
        """
        scheduler = self._get_scheduler()

        # 解析cron表达式
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone='Asia/Shanghai'
        )

        job = scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **kwargs
        )

        self._job_callbacks[job_id] = func
        logger.info(f"Cron job '{job_id}' added: {cron_expr}")

        return {
            "job_id": job_id,
            "type": "cron",
            "expression": cron_expr,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        }

    @register_method_tool(
        name="scheduler_add_interval",
        description="添加间隔执行任务",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "任务ID"},
                "seconds": {"type": "integer", "description": "间隔秒数", "default": 0},
                "minutes": {"type": "integer", "description": "间隔分钟", "default": 0},
                "hours": {"type": "integer", "description": "间隔小时", "default": 0}
            },
            "required": ["job_id"]
        },
        category="scheduler"
    )
    def add_interval_job(
        self,
        job_id: str,
        func: Callable,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        添加间隔任务

        Args:
            job_id: 任务ID
            func: 任务函数
            seconds: 秒
            minutes: 分钟
            hours: 小时
            **kwargs: 额外参数

        Returns:
            任务信息
        """
        scheduler = self._get_scheduler()

        trigger = IntervalTrigger(
            seconds=seconds,
            minutes=minutes,
            hours=hours
        )

        job = scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            **kwargs
        )

        self._job_callbacks[job_id] = func
        interval_str = f"{hours}h {minutes}m {seconds}s".strip()
        logger.info(f"Interval job '{job_id}' added: {interval_str}")

        return {
            "job_id": job_id,
            "type": "interval",
            "interval": {"hours": hours, "minutes": minutes, "seconds": seconds},
            "next_run": str(job.next_run_time) if job.next_run_time else None
        }

    def add_one_time_job(
        self,
        job_id: str,
        func: Callable,
        run_date: datetime,
        **kwargs
    ) -> Dict[str, Any]:
        """
        添加一次性任务

        Args:
            job_id: 任务ID
            func: 任务函数
            run_date: 运行时间
            **kwargs: 额外参数

        Returns:
            任务信息
        """
        scheduler = self._get_scheduler()

        trigger = DateTrigger(run_date=run_date)

        job = scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            **kwargs
        )

        self._job_callbacks[job_id] = func
        logger.info(f"One-time job '{job_id}' added for {run_date}")

        return {
            "job_id": job_id,
            "type": "one_time",
            "run_date": str(run_date),
        }

    @register_method_tool(
        name="scheduler_remove_job",
        description="移除定时任务",
        parameters={
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "任务ID"}
            },
            "required": ["job_id"]
        },
        category="scheduler"
    )
    def remove_job(self, job_id: str) -> bool:
        """
        移除任务

        Args:
            job_id: 任务ID

        Returns:
            是否成功
        """
        scheduler = self._get_scheduler()

        try:
            scheduler.remove_job(job_id)
            if job_id in self._job_callbacks:
                del self._job_callbacks[job_id]
            logger.info(f"Job '{job_id}' removed")
            return True
        except Exception as e:
            logger.error(f"Failed to remove job '{job_id}': {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        scheduler = self._get_scheduler()
        try:
            scheduler.pause_job(job_id)
            logger.info(f"Job '{job_id}' paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job '{job_id}': {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        scheduler = self._get_scheduler()
        try:
            scheduler.resume_job(job_id)
            logger.info(f"Job '{job_id}' resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job '{job_id}': {e}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        scheduler = self._get_scheduler()
        job = scheduler.get_job(job_id)

        if job:
            return {
                "job_id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
        return None

    @register_method_tool(
        name="scheduler_list_jobs",
        description="列出所有定时任务",
        parameters={"type": "object", "properties": {}, "required": []},
        category="scheduler"
    )
    def list_jobs(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        scheduler = self._get_scheduler()
        jobs = scheduler.get_jobs()

        return [
            {
                "job_id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]

    def shutdown(self, wait: bool = True) -> None:
        """关闭调度器"""
        if self._scheduler:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown")
