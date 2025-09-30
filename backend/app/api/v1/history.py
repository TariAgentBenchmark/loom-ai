from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

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
