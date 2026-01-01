import logging
import os
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.utils.downloads import build_download_filename
from app.utils.result_filter import (
    filter_result_lists,
    filter_result_strings,
    split_and_clean_csv,
)
from app.utils.exceptions import UserFacingException

from app.core.database import get_db
from app.models.user import User
from app.services.processing_service import ProcessingService
from app.api.dependencies import get_current_user
from app.schemas.common import SuccessResponse
from app.services.credit_math import to_float
from app.models.task import TaskStatus

router = APIRouter()
processing_service = ProcessingService()
logger = logging.getLogger(__name__)


def _display_credits(task) -> float:
    """Return visible credits for a task, zeroing out failed ones."""
    if task.status == TaskStatus.FAILED.value:
        return 0.0
    return to_float(task.credits_used)


def _handle_processing_error(exc: Exception):
    """统一处理创建任务阶段的错误，补充积分不足提示。"""
    msg = str(exc)
    if isinstance(exc, UserFacingException):
        raise HTTPException(status_code=exc.status_code, detail=msg)
    if "积分不足" in msg:
        raise HTTPException(status_code=400, detail="积分不足，请充值后再试")
    raise HTTPException(status_code=400, detail="服务器火爆，重试一下。")


@router.post("/seamless")
async def seamless_pattern_conversion(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI四方连续转换"""
    try:
        # 记录上传文件大小
        file_size = 0
        # 读取图片数据
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
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
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="任务创建成功，正在处理中"
        )
        
    except Exception as e:
        _handle_processing_error(e)


@router.post("/prompt-edit")
async def prompt_edit_image(
    image: UploadFile = File(...),
    image2: UploadFile = File(None),
    instruction: str = Form(...),
    model: str = Form("new"),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI用嘴改图"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        secondary_bytes = await image2.read() if image2 else None
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        if image2:
            logger.info(
                "Uploaded secondary file size: %.2f MB, filename: %s",
                (len(secondary_bytes) if secondary_bytes else 0) / 1024 / 1024,
                image2.filename,
            )

        instruction_value = instruction.strip()
        if not instruction_value:
            raise ValueError("请填写修改指令")

        # 构建选项
        options = {
            "instruction": instruction_value,
            "model": (model or "new").strip().lower() or "new",
        }

        # 添加分辨率参数
        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="prompt_edit",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options,
            image_bytes_secondary=secondary_bytes,
            secondary_filename=image2.filename if image2 else None,
        )

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="指令改图任务创建成功"
        )

    except Exception as e:
        _handle_processing_error(e)


@router.post("/vectorize")
async def vectorize_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI矢量化(转SVG)"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
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
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="矢量化任务创建成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)

@router.post("/extract-pattern")
async def extract_pattern(
    image: UploadFile = File(...),
    pattern_type: str = Form("general_2"),
    quality: Optional[str] = Form("standard"),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    num_images: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI提取花型"""
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    start_time = time.time()
    request_id = f"extract_{int(start_time * 1000)}"
    
    try:
        logger.info(f"[{request_id}] Extract pattern request started - User: {current_user.id}, File: {image.filename}")
        
        # 记录上传文件大小
        image_bytes = await image.read()
        file_size = len(image_bytes)
        logger.info(f"[{request_id}] File uploaded - Size: {file_size / 1024 / 1024:.2f} MB, Type: {pattern_type}")
        
        # 构建选项
        options = {"pattern_type": pattern_type, "quality": quality}

        # 添加分辨率参数
        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        if num_images is not None:
            options["num_images"] = num_images

        logger.info(f"[{request_id}] Creating task with options: {options}")
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="extract_pattern",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options
        )
        
        elapsed = time.time() - start_time
        logger.info(f"[{request_id}] Task created successfully - TaskID: {task.task_id}, Time: {elapsed:.2f}s")
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="花型提取任务创建成功"
        )
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[{request_id}] Extract pattern failed - Time: {elapsed:.2f}s, Error: {str(e)}", exc_info=True)
        _handle_processing_error(e)


@router.post("/remove-watermark")
async def remove_watermark(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI智能去水印"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
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
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="去水印任务创建成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)


@router.post("/denoise")
async def denoise_image(
    image: UploadFile = File(...),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI布纹去噪"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
        # 构建选项
        options = {}

        # 添加分辨率参数
        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="denoise",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="去噪任务创建成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)


@router.post("/embroidery")
async def enhance_embroidery(
    image: UploadFile = File(...),
    scale: float = Form(0.7),
    size: int = Form(2048*2048),
    force_single: bool = Form(True),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI毛线刺绣增强"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
        # 构建选项
        options = {
            "scale": scale,
            "size": size,
            "force_single": force_single
        }

        # 添加分辨率参数
        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="embroidery",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="刺绣增强任务创建成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)


@router.post("/similar-image")
async def generate_similar_image(
    image: UploadFile = File(...),
    denoise: Optional[float] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI相似图（RunningHub工作流）"""
    try:
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            "Uploaded file size for similar-image: %.2f MB, filename: %s",
            file_size / 1024 / 1024,
            image.filename,
        )

        options = {}
        if denoise is not None:
            options["denoise"] = denoise

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="similar_image",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options,
        )

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at,
            },
            message="相似图任务创建成功",
        )
    except Exception as e:
        _handle_processing_error(e)


@router.post("/flat-to-3d")
async def convert_flat_to_3d(
    image: UploadFile = File(...),
    scale: float = Form(0.75),
    size: int = Form(2048 * 2048),
    force_single: bool = Form(True),
    aspect_ratio: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI平面转3D"""
    try:
        image_bytes = await image.read()

        options = {
            "scale": scale,
            "size": size,
            "force_single": force_single,
        }

        if aspect_ratio:
            options["aspect_ratio"] = aspect_ratio
        if width:
            options["width"] = width
        if height:
            options["height"] = height

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="flat_to_3d",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options
        )

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="平面转3D任务创建成功"
        )

    except Exception as e:
        _handle_processing_error(e)


@router.post("/upscale")
async def upscale_image(
    image: UploadFile = File(...),
    scale_factor: int = Form(2),
    custom_width: Optional[int] = Form(None),
    custom_height: Optional[int] = Form(None),
    engine: str = Form("meitu_v2"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI高清"""
    try:
        # 记录上传文件大小
        file_size = 0
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        
        # 构建选项
        engine_value = (engine or "meitu_v2").strip().lower()
        allowed_engines = {"meitu_v2", "runninghub_vr2"}
        if engine_value not in allowed_engines:
            engine_value = "meitu_v2"
        # 通用1（美图）仅支持 JPG/PNG，提前校验格式，避免回传格式不一致
        if engine_value == "meitu_v2":
            filename = image.filename or ""
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            allowed_ext = {"jpg", "jpeg", "png"}
            if ext not in allowed_ext:
                raise HTTPException(status_code=400, detail="AI高清通用1暂只支持JPG或PNG格式，请更换图片后重试")

        options = {
            "scale_factor": scale_factor,
            "engine": engine_value,
        }
        
        if custom_width:
            options["custom_width"] = custom_width
        if custom_height:
            options["custom_height"] = custom_height
        
        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="upscale",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options
        )
        
        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at
            },
            message="AI高清任务创建成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)


@router.post("/expand-image")
async def expand_image(
    image: UploadFile = File(...),
    expand_top: float = Form(0.0),
    expand_bottom: float = Form(0.0),
    expand_left: float = Form(0.0),
    expand_right: float = Form(0.0),
    prompt: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI扩图"""
    try:
        image_bytes = await image.read()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "Expand image upload size: %.2f MB, filename: %s",
            len(image_bytes) / 1024 / 1024,
            image.filename,
        )

        options = {
            "expand_top": expand_top,
            "expand_bottom": expand_bottom,
            "expand_left": expand_left,
            "expand_right": expand_right,
        }

        if prompt is not None:
            options["prompt"] = prompt

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="expand_image",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options,
        )

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at,
            },
            message="扩图任务创建成功",
        )

    except Exception as e:
        _handle_processing_error(e)


@router.post("/seamless-loop")
async def seamless_loop(
    image: UploadFile = File(...),
    fit: float = Form(0.7),
    direction: int = Form(0),
    expand_top: float = Form(0.0),
    expand_bottom: float = Form(0.0),
    expand_left: float = Form(0.0),
    expand_right: float = Form(0.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI接循环（无缝拼接）"""
    try:
        image_bytes = await image.read()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "Seamless loop upload size: %.2f MB, filename: %s",
            len(image_bytes) / 1024 / 1024,
            image.filename,
        )

        options = {
            "fit": fit,
            "direction": direction,
            "expand_top": expand_top,
            "expand_bottom": expand_bottom,
            "expand_left": expand_left,
            "expand_right": expand_right,
        }

        task = await processing_service.create_task(
            db=db,
            user=current_user,
            task_type="seamless_loop",
            image_bytes=image_bytes,
            original_filename=image.filename,
            options=options,
        )

        return SuccessResponse(
            data={
                "taskId": task.task_id,
                "status": task.status,
                "estimatedTime": task.estimated_time,
                "creditsUsed": _display_credits(task),
                "createdAt": task.created_at,
            },
            message="接循环任务创建成功",
        )

    except Exception as e:
        _handle_processing_error(e)


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
        from app.services.file_service import FileService

        file_service = FileService()
        
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
            filtered_urls, _ = filter_result_strings(
                task.type,
                task.result_image_url,
                task.result_filename,
            )
            signed_urls = []
            for url in filtered_urls:
                clean_url = url.strip()
                accessible_url = await file_service.ensure_accessible_url(clean_url)
                signed_urls.append(accessible_url or clean_url)

            processed_value = ",".join(signed_urls) if signed_urls else task.result_image_url
            original_image_url = task.original_image_url
            if original_image_url:
                original_image_url = await file_service.ensure_accessible_url(original_image_url)

            response_data["result"] = {
                "originalImage": original_image_url,
                "processedImage": processed_value,
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
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


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
        
        # 检查是否有多个文件（逗号分隔）
        file_urls = split_and_clean_csv(task.result_image_url)
        filenames = split_and_clean_csv(task.result_filename)
        filtered_urls, filtered_filenames = filter_result_lists(task.type, file_urls, filenames)

        if not filtered_urls:
            raise HTTPException(status_code=404, detail="结果文件不存在")
        
        from app.services.file_service import FileService
        file_service = FileService()
        
        if len(filtered_urls) > 1:
            # 多个文件，返回ZIP压缩包
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for index, url in enumerate(filtered_urls):
                        clean_url = url.strip()
                        fname = None
                        if filtered_filenames and index < len(filtered_filenames):
                            fname = filtered_filenames[index].strip()
                        if not fname:
                            fname = os.path.basename(clean_url) or f"result_{index}.png"
                        try:
                            file_bytes = await file_service.read_file(clean_url)
                            zip_file.writestr(fname, file_bytes)
                        except Exception as exc:
                            logger.warning("打包结果文件失败(%s): %s", clean_url, exc)
                
                download_name = build_download_filename(None, "zip")
                return FileResponse(
                    path=temp_file.name,
                    filename=download_name,
                    media_type="application/zip"
                )
        else:
            # 单个文件
            clean_url = filtered_urls[0].strip()
            filename_value = (filtered_filenames or [task.result_filename or "result.png"])[0]
            download_name = build_download_filename(filename_value)
            try:
                file_bytes = await file_service.read_file(clean_url)
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


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
                "creditsUsed": _display_credits(task),
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
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


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
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")


@router.post("/estimate")
async def estimate_credits(
    task_type: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预估积分消耗"""
    try:
        # 记录上传文件大小
        file_size = 0
        # 读取图片并获取信息
        image_bytes = await image.read()
        file_size = len(image_bytes)
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Estimate: Uploaded file size: {file_size / 1024 / 1024:.2f} MB, filename: {image.filename}")
        from app.services.file_service import FileService
        file_service = FileService()
        image_info = file_service.validate_file(image_bytes, image.filename or "")
        
        # 预估积分
        estimation = await processing_service.estimate_credits(
            task_type=task_type,
            image_info=image_info,
            user=current_user,
        )
        
        return SuccessResponse(
            data=estimation,
            message="预估积分消耗成功"
        )
        
    except Exception as e:
        _handle_processing_error(e)


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
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            with zipfile.ZipFile(temp_file.name, 'w') as zip_file:
                for task in tasks:
                    try:
                        urls = split_and_clean_csv(task.result_image_url)
                        filenames = split_and_clean_csv(task.result_filename)
                        filtered_urls, filtered_filenames = filter_result_lists(
                            task.type,
                            urls,
                            filenames,
                        )
                        if not filtered_urls:
                            continue
                        for index, url in enumerate(filtered_urls):
                            file_path = file_service.get_file_path(url)
                            if os.path.exists(file_path):
                                name = None
                                if filtered_filenames and index < len(filtered_filenames):
                                    name = filtered_filenames[index]
                                elif task.result_filename:
                                    name = task.result_filename
                                else:
                                    name = os.path.basename(file_path)
                                zip_file.write(file_path, name)
                    except Exception as e:
                        continue  # 跳过有问题的文件
            
            download_name = build_download_filename(None, "zip")
            return FileResponse(
                path=temp_file.name,
                filename=download_name,
                media_type="application/zip"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器火爆，重试一下。")
