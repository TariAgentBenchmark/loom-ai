import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.task import Task
from app.services.file_service import FileService

logger = logging.getLogger(__name__)


async def purge_expired_oss_objects(
    db: Session,
    file_service: FileService,
    retention_days: Optional[int] = None,
) -> int:
    """删除超过保留期的OSS文件，返回成功删除的数量。"""
    if not file_service.oss_service.is_configured():
        logger.debug("OSS未配置，跳过OSS清理任务")
        return 0

    cutoff = datetime.utcnow() - timedelta(days=retention_days or settings.oss_storage_retention_days)
    expired_records = (
        db.query(Task.original_image_url, Task.result_image_url)
        .filter(Task.created_at < cutoff)
        .all()
    )

    deleted = 0
    for original_url, result_url in expired_records:
        for url in (original_url, result_url):
            if not url or not file_service.is_oss_url(url):
                continue
            try:
                if await file_service.delete_file(url):
                    deleted += 1
            except Exception as exc:  # pragma: no cover - 防御性日志
                logger.warning("删除过期OSS文件失败: url=%s err=%s", url, exc)
    return deleted


async def storage_cleanup_worker(interval_hours: int = 24):
    """后台循环任务：定期清理过期OSS文件及本地遗留文件。"""
    file_service = FileService()
    while True:
        db = SessionLocal()
        try:
            oss_deleted = await purge_expired_oss_objects(db, file_service)
            # 同步清理本地uploads目录，复用同一保留期
            await file_service.cleanup_old_files(days=settings.oss_storage_retention_days)
            logger.info(
                "存储清理完成: oss_deleted=%s, retention_days=%s",
                oss_deleted,
                settings.oss_storage_retention_days,
            )
        except asyncio.CancelledError:
            db.close()
            raise
        except Exception as exc:  # pragma: no cover - 防御性日志
            logger.warning("存储清理任务失败: %s", exc, exc_info=True)
        finally:
            db.close()

        await asyncio.sleep(interval_hours * 3600)
