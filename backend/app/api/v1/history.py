from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.core.database import get_db
from app.models.user import User
from app.models.task import Task
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse

router = APIRouter()


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
        query = db.query(Task).filter(Task.user_id == current_user.id)
        
        if type:
            query = query.filter(Task.type == type)
        if status:
            query = query.filter(Task.status == status)
        
        # 按时间倒序
        query = query.order_by(Task.created_at.desc())
        
        # 分页
        total = query.count()
        tasks = query.offset((page - 1) * limit).limit(limit).all()
        
        # 格式化任务数据
        formatted_tasks = []
        for task in tasks:
            formatted_task = {
                "taskId": task.task_id,
                "type": task.type,
                "typeName": task.type_name,
                "status": task.status,
                "originalImage": {
                    "url": task.original_image_url,
                    "filename": task.original_filename,
                    "size": task.original_file_size,
                    "dimensions": task.original_dimensions
                },
                "creditsUsed": task.credits_used,
                "processingTime": task.processing_time,
                "favorite": task.favorite,
                "tags": task.tags or [],
                "createdAt": task.created_at,
                "completedAt": task.completed_at
            }
            
            # 如果有结果图片，添加结果信息
            if task.result_image_url:
                formatted_task["resultImage"] = {
                    "url": task.result_image_url,
                    "filename": task.result_filename,
                    "size": task.result_file_size,
                    "dimensions": task.result_dimensions
                }
            
            formatted_tasks.append(formatted_task)
        
        # 计算统计信息
        total_tasks = db.query(Task).filter(Task.user_id == current_user.id).count()
        completed_tasks = db.query(Task).filter(
            Task.user_id == current_user.id,
            Task.status == "completed"
        ).count()
        failed_tasks = db.query(Task).filter(
            Task.user_id == current_user.id,
            Task.status == "failed"
        ).count()
        
        return SuccessResponse(
            data={
                "tasks": formatted_tasks,
                "statistics": {
                    "totalTasks": total_tasks,
                    "completedTasks": completed_tasks,
                    "failedTasks": failed_tasks,
                    "totalCreditsUsed": sum(task.credits_used for task in tasks if task.credits_used),
                    "avgProcessingTime": sum(task.processing_time for task in tasks if task.processing_time) // len([t for t in tasks if t.processing_time]) if tasks else 0
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
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == current_user.id
        ).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "type": task.type,
                "typeName": task.type_name,
                "status": task.status,
                "originalImage": {
                    "url": task.original_image_url,
                    "filename": task.original_filename,
                    "size": task.original_file_size,
                    "format": task.original_filename.split('.')[-1].lower(),
                    "dimensions": task.original_dimensions,
                    "uploadedAt": task.created_at
                },
                "resultImage": {
                    "url": task.result_image_url,
                    "filename": task.result_filename,
                    "size": task.result_file_size,
                    "format": task.result_filename.split('.')[-1].lower() if task.result_filename else None,
                    "dimensions": task.result_dimensions
                } if task.result_image_url else None,
                "options": task.options,
                "metadata": task.extra_metadata,
                "creditsUsed": task.credits_used,
                "processingTime": task.processing_time,
                "favorite": task.favorite,
                "tags": task.tags or [],
                "notes": task.notes,
                "downloadCount": task.download_count,
                "lastDownloaded": task.last_downloaded_at,
                "createdAt": task.created_at,
                "startedAt": task.started_at,
                "completedAt": task.completed_at
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
            
            file_url = task.original_image_url
            filename = task.original_filename
        elif file_type == "result":
            if not task.result_image_url:
                raise HTTPException(status_code=404, detail="结果文件不存在")
            
            file_url = task.result_image_url
            filename = task.result_filename
        else:
            raise HTTPException(status_code=400, detail="无效的文件类型")
        
        # 增加下载次数
        task.increment_download_count()
        db.commit()
        
        # 检查是否有多个文件（逗号分隔）
        file_urls = file_url.split(',')
        filenames = filename.split(',')
        
        from app.services.file_service import FileService
        file_service = FileService()
        
        if len(file_urls) > 1:
            # 多个文件，返回ZIP压缩包
            import zipfile
            import tempfile
            from datetime import datetime
            
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for i, (url, fname) in enumerate(zip(file_urls, filenames)):
                        url = url.strip()
                        fname = fname.strip()
                        file_path = file_service.get_file_path(url)
                        
                        if os.path.exists(file_path):
                            # 添加文件到ZIP，使用原始文件名
                            zip_file.write(file_path, fname)
                
                zip_filename = f"{task_id}_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                return FileResponse(
                    path=temp_file.name,
                    filename=zip_filename,
                    media_type="application/zip"
                )
        else:
            # 单个文件
            file_path = file_service.get_file_path(file_url)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type="application/octet-stream"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
