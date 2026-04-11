import logging
import asyncio
from typing import Optional
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.credit_math import to_float
from app.utils.downloads import build_download_filename
from app.utils.result_filter import (
    filter_result_lists,
    filter_result_strings,
    split_and_clean_csv,
)

router = APIRouter()
logger = logging.getLogger(__name__)


try:
    BEIJING_TZ = ZoneInfo("Asia/Shanghai")
except ZoneInfoNotFoundError:
    BEIJING_TZ = timezone(timedelta(hours=8))


def _to_beijing_isoformat(dt):
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(BEIJING_TZ).isoformat()


async def _resolve_image_urls(file_service, file_url: Optional[str], semaphore: asyncio.Semaphore):
    if not file_url:
        return None, None, None

    clean_url = file_url.strip()

    async def _limited(callable_):
        async with semaphore:
            return await callable_

    preview_url, thumbnail_url, accessible_url = await asyncio.gather(
        _limited(file_service.ensure_preview_url(clean_url)),
        _limited(file_service.ensure_thumbnail_url(clean_url)),
        _limited(file_service.ensure_accessible_url(clean_url)),
    )

    resolved_accessible = accessible_url or clean_url
    resolved_preview = preview_url or resolved_accessible
    resolved_thumbnail = thumbnail_url or resolved_preview
    return resolved_accessible, resolved_preview, resolved_thumbnail


@router.get("/tasks")
async def get_history_tasks(
    type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取处理历史"""
    try:
        from app.services.file_service import FileService

        query = db.query(Task).filter(Task.user_id == current_user.id)

        cutoff = datetime.utcnow() - timedelta(days=settings.history_retention_days)
        query = query.filter(Task.created_at >= cutoff)
        
        if type:
            query = query.filter(Task.type == type)
        if status:
            query = query.filter(Task.status == status)
        
        # 按时间倒序
        query = query.order_by(Task.created_at.desc())
        
        # 分页
        total = query.count()
        tasks = query.offset((page - 1) * limit).limit(limit).all()

        file_service = FileService()
        semaphore = asyncio.Semaphore(12)

        async def _format_task(task: Task):
            credits_used_value = to_float(task.credits_used)
            if task.status == TaskStatus.FAILED.value:
                credits_used_value = 0.0

            (
                original_image_url,
                original_image_preview_url,
                original_image_thumbnail_url,
            ) = await _resolve_image_urls(file_service, task.original_image_url, semaphore)

            formatted_task = {
                "taskId": task.task_id,
                "type": task.type,
                "typeName": task.type_name,
                "status": task.status,
                "originalImage": {
                    "url": original_image_url,
                    "previewUrl": original_image_preview_url or original_image_url,
                    "thumbnailUrl": (
                        original_image_thumbnail_url
                        or original_image_preview_url
                        or original_image_url
                    ),
                    "filename": task.original_filename,
                    "size": task.original_file_size,
                    "dimensions": task.original_dimensions
                },
                "creditsUsed": credits_used_value,
                "processingTime": task.processing_time,
                "favorite": task.favorite,
                "tags": task.tags or [],
                "createdAt": _to_beijing_isoformat(task.created_at),
                "completedAt": _to_beijing_isoformat(task.completed_at)
            }
            
            # 如果有结果图片，添加结果信息
            if task.result_image_url:
                filtered_urls, filtered_filenames = filter_result_strings(
                    task.type,
                    task.result_image_url,
                    task.result_filename,
                )
                resolved_results = await asyncio.gather(
                    *(
                        _resolve_image_urls(file_service, url, semaphore)
                        for url in filtered_urls
                    )
                )
                signed_urls = [resolved[0] for resolved in resolved_results if resolved[0]]
                preview_urls = [resolved[1] for resolved in resolved_results if resolved[1]]
                thumbnail_urls = [resolved[2] for resolved in resolved_results if resolved[2]]

                formatted_task["resultImage"] = {
                    "url": ",".join(signed_urls) if signed_urls else task.result_image_url,
                    "previewUrl": ",".join(preview_urls)
                    if preview_urls
                    else task.result_image_url,
                    "thumbnailUrl": ",".join(thumbnail_urls)
                    if thumbnail_urls
                    else task.result_image_url,
                    "filename": ",".join(filtered_filenames) if filtered_filenames else task.result_filename,
                    "size": task.result_file_size,
                    "dimensions": task.result_dimensions
                }

            return formatted_task

        formatted_tasks = await asyncio.gather(*(_format_task(task) for task in tasks))
        
        # 计算统计信息
        stats_query = db.query(Task).filter(
            Task.user_id == current_user.id,
            Task.created_at >= cutoff
        )
        completed_query = stats_query.filter(Task.status == TaskStatus.COMPLETED.value)
        failed_query = stats_query.filter(Task.status == TaskStatus.FAILED.value)
        total_tasks = stats_query.count()
        completed_tasks = completed_query.count()
        failed_tasks = failed_query.count()
        
        processing_times = [task.processing_time for task in tasks if task.processing_time]
        total_credits_used = sum(
            (task.credits_used or 0)
            for task in tasks
            if task.status == TaskStatus.COMPLETED.value and task.credits_used
        )

        return SuccessResponse(
            data={
                "tasks": formatted_tasks,
                "retentionDays": settings.history_retention_days,
                "statistics": {
                    "totalTasks": total_tasks,
                    "completedTasks": completed_tasks,
                    "failedTasks": failed_tasks,
                    "totalCreditsUsed": to_float(total_credits_used),
                    "avgProcessingTime": int(sum(processing_times) / len(processing_times)) if processing_times else 0
                },
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit
                }
            },
            message="获取历史记录成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    """获取任务详情"""
    try:
        from app.services.file_service import FileService

        file_service = FileService()
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        result_image_payload = None
        if task.result_image_url:
            filtered_urls, filtered_filenames = filter_result_strings(
                task.type,
                task.result_image_url,
                task.result_filename,
            )
            signed_urls = []
            preview_urls = []
            thumbnail_urls = []
            for url in filtered_urls:
                clean_url = url.strip()
                preview_url = await file_service.ensure_preview_url(clean_url)
                thumbnail_url = await file_service.ensure_thumbnail_url(clean_url)
                accessible_url = await file_service.ensure_accessible_url(clean_url)
                signed_urls.append(accessible_url or clean_url)
                preview_urls.append(preview_url or accessible_url or clean_url)
                thumbnail_urls.append(
                    thumbnail_url or preview_url or accessible_url or clean_url
                )
            filename_value = (
                ",".join(filtered_filenames) if filtered_filenames else task.result_filename
            )
            first_filename = (
                filtered_filenames[0]
                if filtered_filenames and filtered_filenames[0]
                else task.result_filename
            )
            result_image_payload = {
                "url": ",".join(signed_urls) if signed_urls else task.result_image_url,
                "previewUrl": ",".join(preview_urls)
                if preview_urls
                else task.result_image_url,
                "thumbnailUrl": ",".join(thumbnail_urls)
                if thumbnail_urls
                else task.result_image_url,
                "filename": filename_value,
                "size": task.result_file_size,
                "format": first_filename.split(".")[-1].lower() if first_filename else None,
                "dimensions": task.result_dimensions
            }

        original_image_url = task.original_image_url
        original_image_preview_url = None
        original_image_thumbnail_url = None
        if original_image_url:
            original_image_preview_url = await file_service.ensure_preview_url(
                original_image_url
            )
            original_image_thumbnail_url = await file_service.ensure_thumbnail_url(
                original_image_url
            )
            original_image_url = await file_service.ensure_accessible_url(original_image_url)

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "type": task.type,
                "typeName": task.type_name,
                "status": task.status,
                "originalImage": {
                    "url": original_image_url,
                    "previewUrl": original_image_preview_url or original_image_url,
                    "thumbnailUrl": (
                        original_image_thumbnail_url
                        or original_image_preview_url
                        or original_image_url
                    ),
                    "filename": task.original_filename,
                    "size": task.original_file_size,
                    "format": task.original_filename.split('.')[-1].lower(),
                    "dimensions": task.original_dimensions,
                    "uploadedAt": _to_beijing_isoformat(task.created_at)
                },
                "resultImage": result_image_payload,
                "options": task.options,
                "metadata": task.extra_metadata,
                "creditsUsed": to_float(task.credits_used),
                "processingTime": task.processing_time,
                "favorite": task.favorite,
                "tags": task.tags or [],
                "notes": task.notes,
                "downloadCount": task.download_count,
                "lastDownloaded": _to_beijing_isoformat(task.last_downloaded_at),
                "createdAt": _to_beijing_isoformat(task.created_at),
                "startedAt": _to_beijing_isoformat(task.started_at),
                "completedAt": _to_beijing_isoformat(task.completed_at)
            },
            message="获取任务详情成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}/download")
async def download_task_file(
    task_id: str,
    file_type: str = "result",  # "result" for processed image, "original" for original image
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载任务文件（原图或处理后的图）"""
    try:
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if task.status != "completed":
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        # 根据file_type决定下载哪个文件
        if file_type == "original":
            if not task.original_image_url:
                raise HTTPException(status_code=404, detail="原图文件不存在")
            file_urls = [task.original_image_url]
            filenames = [task.original_filename]
        elif file_type == "result":
            if not task.result_image_url:
                raise HTTPException(status_code=404, detail="结果文件不存在")
            raw_urls = split_and_clean_csv(task.result_image_url)
            raw_filenames = split_and_clean_csv(task.result_filename)
            filtered_urls, filtered_filenames = filter_result_lists(
                task.type,
                raw_urls,
                raw_filenames,
            )
            if not filtered_urls:
                raise HTTPException(status_code=404, detail="结果文件不存在")
            file_urls = filtered_urls
            if filtered_filenames:
                filenames = filtered_filenames
            else:
                fallback_name = task.result_filename or "result.png"
                filenames = [fallback_name] * len(filtered_urls)
        else:
            raise HTTPException(status_code=400, detail="无效的文件类型")
        
        # 增加下载次数
        task.increment_download_count()
        db.commit()
        
        from app.services.file_service import FileService
        file_service = FileService()
        
        if len(file_urls) > 1:
            # 多个文件，返回ZIP压缩包（OSS文件会先下载到临时目录）
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for url, fname in zip(file_urls, filenames):
                        clean_url = url.strip()
                        clean_fname = fname.strip()

                        if clean_url.startswith("/files/"):
                            file_path = file_service.get_file_path(clean_url)
                            if os.path.exists(file_path):
                                zip_file.write(file_path, clean_fname or os.path.basename(file_path))
                        else:
                            # 远程文件直接以字节写入 ZIP，避免创建遗留临时文件
                            content = await file_service.read_file(clean_url)
                            zip_file.writestr(clean_fname or os.path.basename(clean_url), content)
                
                download_name = build_download_filename(None, "zip")
                return FileResponse(
                    path=temp_file.name,
                    filename=download_name,
                    media_type="application/zip"
                )
        else:
            # 单个文件：读取文件字节并流式返回（确保 Content-Disposition 正确传递文件名）
            from io import BytesIO

            single_url = file_urls[0]
            download_name = build_download_filename(filenames[0])
            if download_name == "tuyun":
                download_name = build_download_filename(single_url)

            if file_service.is_managed_oss_ref(single_url):
                try:
                    file_bytes = await file_service.read_file(single_url)
                except Exception:
                    raise HTTPException(status_code=404, detail="文件不存在")

                headers = {
                    "Content-Disposition": f'attachment; filename="{download_name}"'
                }
                return StreamingResponse(
                    BytesIO(file_bytes),
                    headers=headers,
                    media_type="application/octet-stream",
                )

            file_path = file_service.get_file_path(single_url)

            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="文件不存在")

            return FileResponse(
                path=file_path,
                filename=download_name,
                media_type="application/octet-stream"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
