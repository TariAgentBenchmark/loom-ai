import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis_client import get_redis_client
from app.models.task import Task, TaskStatus
from app.services.processing_service import ProcessingService
from app.services.task_log_service import TaskLogService

logger = logging.getLogger(__name__)


class TaskWatchdogService:
    """Watchdog to recover stuck tasks by retrying or failing them."""

    def __init__(self):
        self.processing_service = ProcessingService()
        self.task_log_service = TaskLogService()
        self._lock_key = "task_watchdog_lock"

    async def _acquire_lock(self, ttl_seconds: int) -> bool:
        if not settings.redis_url:
            return True
        try:
            client = get_redis_client()
            token = f"{os.getpid()}-{datetime.utcnow().isoformat()}"
            acquired = await client.set(self._lock_key, token, nx=True, ex=ttl_seconds)
            return bool(acquired)
        except Exception as exc:
            logger.warning("Task watchdog lock failed (continue anyway): %s", exc)
            return True

    def _get_retry_count(self, task: Task) -> int:
        meta = task.extra_metadata or {}
        try:
            return int(meta.get("watchdog_retries", 0))
        except Exception:
            return 0

    def _set_retry_metadata(self, task: Task, retries: int, reason: str) -> None:
        meta = dict(task.extra_metadata or {})
        meta["watchdog_retries"] = retries
        meta["watchdog_last_retry_at"] = datetime.utcnow().isoformat()
        meta["watchdog_reason"] = reason
        task.extra_metadata = meta

    def _append_give_up_metadata(self, task: Task, reason: str) -> None:
        meta = dict(task.extra_metadata or {})
        meta["watchdog_give_up_at"] = datetime.utcnow().isoformat()
        meta["watchdog_reason"] = reason
        task.extra_metadata = meta

    def _log_watchdog_event(
        self,
        db: Session,
        task: Task,
        *,
        event: str,
        message: str,
        level: str = "warning",
        details: Optional[dict] = None,
    ) -> None:
        self.task_log_service.record(
            db,
            task,
            event=event,
            message=message,
            level=level,
            details=details,
        )

    def _query_stuck_processing(self, db: Session, cutoff: datetime, limit: int) -> List[Task]:
        return (
            db.query(Task)
            .filter(Task.status == TaskStatus.PROCESSING.value)
            .filter(
                or_(
                    Task.started_at < cutoff,
                    and_(Task.started_at.is_(None), Task.created_at < cutoff),
                )
            )
            .order_by(Task.started_at.asc().nullsfirst(), Task.created_at.asc())
            .limit(limit)
            .all()
        )

    def _query_stuck_queued(self, db: Session, cutoff: datetime, limit: int) -> List[Task]:
        return (
            db.query(Task)
            .filter(Task.status == TaskStatus.QUEUED.value, Task.created_at < cutoff)
            .order_by(Task.created_at.asc())
            .limit(limit)
            .all()
        )

    async def recover_stuck_tasks(self) -> None:
        if not settings.task_watchdog_enabled:
            return

        acquired = await self._acquire_lock(settings.task_watchdog_lock_seconds)
        if not acquired:
            return

        now = datetime.utcnow()
        processing_cutoff = now - timedelta(
            seconds=settings.task_watchdog_processing_timeout_seconds
        )
        queued_cutoff = now - timedelta(
            seconds=settings.task_watchdog_queued_timeout_seconds
        )
        batch_limit = settings.task_watchdog_batch_size

        db = SessionLocal()
        try:
            processing_tasks = self._query_stuck_processing(db, processing_cutoff, batch_limit)
            queued_tasks = self._query_stuck_queued(db, queued_cutoff, batch_limit)
            candidates = processing_tasks + queued_tasks

            if not candidates:
                return

            logger.warning(
                "Task watchdog detected %s stuck tasks (processing=%s queued=%s)",
                len(candidates),
                len(processing_tasks),
                len(queued_tasks),
            )

            for task in candidates:
                retries = self._get_retry_count(task)
                reason = (
                    "processing_timeout"
                    if task.status == TaskStatus.PROCESSING.value
                    else "queued_timeout"
                )

                if retries >= settings.task_watchdog_max_retries:
                    task.mark_as_failed("任务超时，请重试", "WATCHDOG_TIMEOUT")
                    task.credits_used = 0
                    self._append_give_up_metadata(task, reason)
                    self._log_watchdog_event(
                        db,
                        task,
                        event="watchdog_give_up",
                        message="Task exceeded watchdog retry limit",
                        level="error",
                        details={"retries": retries, "reason": reason},
                    )
                    db.commit()
                    continue

                self._set_retry_metadata(task, retries + 1, reason)
                task.status = TaskStatus.QUEUED.value
                task.started_at = None
                db.commit()

                self._log_watchdog_event(
                    db,
                    task,
                    event="watchdog_retry",
                    message="Watchdog scheduled task retry",
                    details={"retries": retries + 1, "reason": reason},
                )
                db.commit()

                asyncio.create_task(self.processing_service._process_task_async(task.task_id))

        except asyncio.CancelledError:
            db.close()
            raise
        except Exception as exc:
            logger.warning("Task watchdog failed: %s", exc, exc_info=True)
        finally:
            db.close()


async def task_watchdog_worker() -> None:
    """Background loop to detect and recover stuck tasks."""
    service = TaskWatchdogService()
    interval = max(30, settings.task_watchdog_interval_seconds)
    while True:
        try:
            await service.recover_stuck_tasks()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover
            logger.warning("Task watchdog loop error: %s", exc, exc_info=True)
        await asyncio.sleep(interval)

