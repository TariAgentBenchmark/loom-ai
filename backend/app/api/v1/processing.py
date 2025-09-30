from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.services.processing_service import ProcessingService
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse

router = APIRouter()
processing_service = ProcessingService()


@router.post("/seamless")
async def seamless_pattern_conversion(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI四方连续转换"""
    try:
        # 读取图片数据
        image_bytes = await image.read()
        
        # 创建处理任务
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="seamless",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="任务创建成功，正在处理中"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vectorize")
async def vectorize_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI矢量化(转SVG)"""
    try:
        image_bytes = await image.read()
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="vectorize",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="矢量化任务创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/extract-pattern")
async def extract_pattern(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI提取花型"""
    try:
        image_bytes = await image.read()
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="extract_pattern",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="花型提取任务创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/remove-watermark")
async def remove_watermark(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI智能去水印"""
    try:
        image_bytes = await image.read()
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="remove_watermark",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="去水印任务创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/denoise")
async def denoise_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI布纹去噪"""
    try:
        image_bytes = await image.read()
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="denoise",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="去噪任务创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/embroidery")
async def enhance_embroidery(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI毛线刺绣增强"""
    try:
        image_bytes = await image.read()
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="embroidery",
            image_bytes=image_bytes,
            original_filename=image.filename,
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at
            },
            message="刺绣增强任务创建成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询任务状态"""
    try:
        task = await processing_service.get_task_status(db, task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 计算进度
        progress = 0
        if task.status == "queued":
            progress = 10
        elif task.status == "processing":
            progress = 50
        elif task.status == "completed":
            progress = 100
        elif task.status == "failed":
            progress = 0
        
        response_data = {
            "taskId": task.task_id,
            "status": task.status,
            "progress": progress,
            "estimatedTime": task.estimated_time if task.status in ["queued", "processing"] else 0,
            "createdAt": task.created_at,
            "completedAt": task.completed_at
        }
        
        # 如果任务完成，包含结果信息
        if task.is_completed and task.result_image_url:
            response_data["result"] = {
                "originalImage": task.original_image_url,
                "processedImage": task.result_image_url,
                "fileSize": task.result_file_size,
                "dimensions": task.result_dimensions
            }
        
        # 如果任务失败，包含错误信息
        if task.is_failed:
            response_data["error"] = {
                "message": task.error_message,
                "code": task.error_code
            }
        
        return SuccessResponse(
            data=response_data,
            message="获取任务状态成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{task_id}/download")
async def download_result(
    task_id: str,
    format: Optional[str] = "png",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载处理结果"""
    try:
        task = await processing_service.get_task_status(db, task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        if not task.is_completed:
            raise HTTPException(status_code=400, detail="任务尚未完成")
        
        if not task.result_image_url:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        # 增加下载次数
        task.increment_download_count()
        db.commit()
        
        # 返回文件下载响应
        from app.services.file_service import FileService
        
        file_service = FileService()
        file_path = file_service.get_file_path(task.result_image_url)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=task.result_filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_tasks(
    type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    try:
        result = await processing_service.get_user_tasks(
            db=db,
            user_id=current_user.id,
            task_type=type,
            status=status,
            page=page,
            limit=limit
        )
        
        # 格式化任务数据
        formatted_tasks = []
        for task in result["tasks"]:
            formatted_task = {
                "taskId": task.task_id,
                "type": task.type,
                "typeName": task.type_name,
                "status": task.status,
                "creditsUsed": task.credits_used,
                "createdAt": task.created_at,
                "completedAt": task.completed_at
            }
            formatted_tasks.append(formatted_task)
        
        return SuccessResponse(
            data={
                "tasks": formatted_tasks,
                "pagination": result["pagination"]
            },
            message="获取任务列表成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务"""
    try:
        success = await processing_service.delete_task(db, task_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return SuccessResponse(
            data=None,
            message="任务删除成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/estimate")
async def estimate_credits(
    task_type: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预估算力消耗"""
    try:
        # 读取图片并获取信息
        image_bytes = await image.read()
        from app.services.file_service import FileService
        file_service = FileService()
        image_info = await file_service.get_image_info(image_bytes)
        
        # 预估算力
        estimation = await processing_service.estimate_credits(
            task_type=task_type,
            image_info=image_info,
            user=current_user,
        )
        
        return SuccessResponse(
            data=estimation,
            message="预估算力消耗成功"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-download")
async def batch_download(
    task_ids: list[str],
    format: str = "zip",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量下载"""
    try:
        # 验证任务归属
        tasks = []
        for task_id in task_ids:
            task = await processing_service.get_task_status(db, task_id, current_user.id)
            if task and task.is_completed and task.result_image_url:
                tasks.append(task)
        
        if not tasks:
            raise HTTPException(status_code=400, detail="没有可下载的任务")
        
        # 创建压缩包
        import zipfile
        import tempfile
        from fastapi.responses import FileResponse
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                for task in tasks:
                    try:
                        file_path = file_service.get_file_path(task.result_image_url)
                        if os.path.exists(file_path):
                            zip_file.write(file_path, task.result_filename)
                    except Exception as e:
                        continue  # 跳过有问题的文件
            
            return FileResponse(
                path=temp_file.name,
                filename=f"loom_ai_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                media_type="application/zip"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
