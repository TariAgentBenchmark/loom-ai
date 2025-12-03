import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.core.database import get_db
from app.models.user import User
from app.services.batch_processing_service import BatchProcessingService
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse

router = APIRouter()
batch_processing_service = BatchProcessingService()
logger = logging.getLogger(__name__)


@router.post("/batch/{task_type}")
async def create_batch_task(
    task_type: str,
    images: List[UploadFile] = File(...),
    instruction: Optional[str] = Form(None),
    pattern_type: Optional[str] = Form(None),
    quality: Optional[str] = Form(None),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    upscale_engine: Optional[str] = Form(None),
    scale_factor: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建批量处理任务"""
    try:
        # 验证任务类型
        valid_types = [
            "prompt_edit", "seamless", "vectorize", "extract_pattern",
            "remove_watermark", "denoise", "embroidery", "flat_to_3d",
            "upscale", "expand_image", "seamless_loop"
        ]
        
        if task_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"不支持的任务类型: {task_type}")
        
        # 读取所有图片
        images_data = []
        for image in images:
            image_bytes = await image.read()
            images_data.append((image_bytes, image.filename))
        
        logger.info(f"Batch upload: {len(images_data)} images, total size: {sum(len(b) for b, _ in images_data) / 1024 / 1024:.2f} MB")
        
        # 构建选项
        options = {}
        
        if task_type == "prompt_edit" and instruction:
            options["instruction"] = instruction.strip()
            if not options["instruction"]:
                raise HTTPException(status_code=400, detail="请填写修改指令")
        
        if task_type == "extract_pattern":
            options["pattern_type"] = pattern_type or "general_2"
            options["quality"] = quality or "standard"
        
        if task_type == "upscale":
            options["engine"] = upscale_engine or "meitu_v2"
            options["scale_factor"] = scale_factor or 2
        
        # 添加分辨率参数
        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        
        # 创建批量任务
        batch_task = await batch_processing_service.create_batch_task(
            db=db,
            user=current_user,
            task_type=task_type,
            images_data=images_data,
            options=options
        )
        
        return SuccessResponse(
            data={
                "batchId": batch_task.batch_id,
                "status": batch_task.status,
                "totalImages": batch_task.total_images,
                "estimatedTime": batch_task.estimated_time,
                "totalCreditsUsed": float(batch_task.total_credits_used),
                "createdAt": batch_task.created_at
            },
            message=f"批量任务创建成功，共 {batch_task.total_images} 张图片"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create batch task: {str(e)}", exc_info=True)
        error_msg = str(e)
        if "积分不足" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


@router.get("/batch/status/{batch_id}")
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取批量任务状态"""
    try:
        status = await batch_processing_service.get_batch_status(db, batch_id, current_user.id)
        
        if not status:
            raise HTTPException(status_code=404, detail="批量任务不存在")
        
        return SuccessResponse(
            data=status,
            message="获取批量任务状态成功"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get batch status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


@router.get("/batch/download/{batch_id}")
async def download_batch_results(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载批量任务结果"""
    try:
        zip_bytes = await batch_processing_service.download_batch_results(db, batch_id, current_user.id)
        
        if not zip_bytes:
            raise HTTPException(status_code=404, detail="批量任务不存在")
        
        # 返回ZIP文件
        return StreamingResponse(
            BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=batch_{batch_id}_results.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download batch results: {str(e)}", exc_info=True)
        error_msg = str(e)
        if "尚未完成" in error_msg or "没有已完成" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail="服务器火爆,重试一下。")
