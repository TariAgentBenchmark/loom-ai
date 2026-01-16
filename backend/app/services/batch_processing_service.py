import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.batch_task import BatchTask, BatchTaskStatus
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.services.credit_math import to_decimal, to_float
from app.services.file_service import FileService
from app.services.membership_service import MembershipService
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


class BatchProcessingService:
    """批量图片处理服务"""

    def __init__(self):
        self.processing_service = ProcessingService()
        self.file_service = FileService()
        self.membership_service = MembershipService()

    async def create_batch_task(
        self,
        db: Session,
        user: User,
        task_type: str,
        images_data: List[Tuple[bytes, str]],  # List of (image_bytes, filename)
        options: Dict[str, Any] = None,
        base_image: Optional[Tuple[bytes, str]] = None,  # (bytes, filename)
    ) -> BatchTask:
        """创建批量处理任务"""
        
        if not images_data:
            raise Exception("请至少上传一张图片")
        
        if len(images_data) > 10:  # 限制最大批量数
            raise Exception("单次最多处理10张图片")
        
        # 计算总积分需求
        service_key = self.processing_service._resolve_service_key(task_type)
        total_credits = to_decimal(0)
        
        for image_bytes, _ in images_data:
            image_info = await self.file_service.get_image_info(image_bytes)
            credits_needed = await self.membership_service.calculate_service_cost(
                db, service_key, options=options
            )
            if credits_needed is None:
                credits_needed = self.processing_service.default_service_costs.get(task_type)
                if credits_needed is None:
                    raise Exception("服务价格未配置，请联系管理员")
            total_credits += to_decimal(credits_needed)
        
        # 检查积分是否足够
        if not user.can_afford(total_credits):
            raise Exception(f"积分不足，需要 {to_float(total_credits)} 积分，当前余额 {to_float(user.credits)} 积分")
        
        # 创建批量任务记录
        batch_task = BatchTask(
            batch_id=f"batch_{task_type}_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            task_type=task_type,
            status=BatchTaskStatus.QUEUED.value,
            total_images=len(images_data),
            completed_images=0,
            failed_images=0,
            options=options or {},
            total_credits_used=total_credits,
            estimated_time=self.processing_service.estimated_times.get(task_type, 120) * len(images_data),
        )
        
        db.add(batch_task)
        db.commit()
        db.refresh(batch_task)
        
        # prompt_edit 基准图：保存一次，后续任务复用URL
        reference_image_url: Optional[str] = None
        if task_type == "prompt_edit" and base_image:
            base_bytes, base_filename = base_image
            reference_image_url = await self.file_service.save_upload_file(
                base_bytes,
                base_filename,
                "originals",
                purpose="general",
            )

        def _sanitize_options(raw: Dict[str, Any]) -> Dict[str, Any]:
            """移除不适合入库的值（如bytes），避免JSON序列化失败。"""
            sanitized = {}
            for key, value in (raw or {}).items():
                if isinstance(value, (bytes, bytearray)):
                    continue
                sanitized[key] = value
            return sanitized

        # 创建各个子任务
        for idx, (image_bytes, filename) in enumerate(images_data):
            try:
                # 保存原始图片
                original_url = await self.file_service.save_upload_file(
                    image_bytes,
                    filename,
                    "originals",
                    purpose="general",
                )
                
                # 获取图片信息
                image_info = await self.file_service.get_image_info(image_bytes)
                
                # 计算单个任务积分
                credits_needed = await self.membership_service.calculate_service_cost(
                    db, service_key, options=options
                )
                if credits_needed is None:
                    credits_needed = self.processing_service.default_service_costs.get(task_type)
                
                # 构建任务选项，包含基准图URL（如果有）
                task_options = dict(options or {})
                if reference_image_url and task_type == "prompt_edit":
                    task_options["secondary_image_url"] = reference_image_url
                task_options = _sanitize_options(task_options)
                
                # 创建子任务
                task = Task(
                    task_id=f"task_{task_type}_{uuid.uuid4().hex[:12]}",
                    user_id=user.id,
                    batch_id=batch_task.id,
                    type=task_type,
                    status=TaskStatus.QUEUED.value,
                    original_image_url=original_url,
                    original_filename=filename,
                    original_file_size=len(image_bytes),
                    original_dimensions={
                        "width": image_info["width"],
                        "height": image_info["height"],
                    },
                    options=task_options,
                    credits_used=credits_needed,
                    estimated_time=self.processing_service.estimated_times.get(task_type, 120),
                )
                
                db.add(task)
                
            except Exception as e:
                logger.error(f"Failed to create task for image {idx}: {str(e)}")
                # 如果创建子任务失败，标记批量任务失败
                batch_task.mark_as_failed()
                db.commit()
                raise Exception(f"创建第 {idx + 1} 个任务失败: {str(e)}")
        
        db.commit()
        
        # 异步开始处理批量任务
        asyncio.create_task(self._process_batch_async(batch_task.batch_id))
        
        logger.info(f"Created batch task {batch_task.batch_id} with {len(images_data)} images for user {user.id}")
        return batch_task

    async def _process_batch_async(self, batch_id: str):
        """异步处理批量任务"""
        try:
            from app.core.database import SessionLocal
            
            db = SessionLocal()
            
            batch_task = db.query(BatchTask).filter(BatchTask.batch_id == batch_id).first()
            if not batch_task:
                logger.error(f"Batch task {batch_id} not found")
                return
            
            # 标记批量任务开始
            batch_task.mark_as_started()
            db.commit()
            
            # 获取所有子任务
            tasks = db.query(Task).filter(Task.batch_id == batch_task.id).all()
            
            # 并发处理所有任务（限制并发数）
            semaphore = asyncio.Semaphore(3)  # 最多同时处理3个任务
            
            async def process_single_task(task: Task):
                async with semaphore:
                    try:
                        await self.processing_service._process_task_async(task.task_id)
                    except Exception as e:
                        logger.error(f"Failed to process task {task.task_id}: {str(e)}")
            
            # 启动所有任务处理
            await asyncio.gather(*[process_single_task(task) for task in tasks])
            
            # 更新批量任务状态
            db.refresh(batch_task)
            completed = db.query(Task).filter(
                Task.batch_id == batch_task.id,
                Task.status == TaskStatus.COMPLETED.value
            ).count()
            failed = db.query(Task).filter(
                Task.batch_id == batch_task.id,
                Task.status == TaskStatus.FAILED.value
            ).count()
            
            batch_task.update_progress(completed, failed)
            db.commit()
            
            logger.info(f"Batch task {batch_id} completed: {completed} succeeded, {failed} failed")
            
        except Exception as e:
            logger.error(f"Unexpected error processing batch task {batch_id}: {str(e)}")
        finally:
            db.close()

    async def get_batch_status(
        self, db: Session, batch_id: str, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取批量任务状态"""
        batch_task = (
            db.query(BatchTask)
            .filter(BatchTask.batch_id == batch_id, BatchTask.user_id == user_id)
            .first()
        )
        
        if not batch_task:
            return None
        
        # 获取所有子任务
        tasks = db.query(Task).filter(Task.batch_id == batch_task.id).all()
        
        task_statuses = []
        for task in tasks:
            # Generate signed URL for result if completed
            result_url = None
            if task.is_completed and task.result_image_url:
                try:
                    # Handle multiple result URLs (comma-separated)
                    result_urls = [url.strip() for url in task.result_image_url.split(",") if url.strip()]
                    if result_urls:
                        # For batch status, just return the first result URL with signature or original URL
                        result_url = await self.file_service.ensure_accessible_url(result_urls[0])
                except Exception as e:
                    logger.warning(f"Failed to generate accessible URL for task {task.task_id}: {str(e)}")
            
            task_status = {
                "taskId": task.task_id,
                "filename": task.original_filename,
                "status": task.status,
                "resultUrl": result_url,
                "errorMessage": task.error_message if task.is_failed else None,
            }
            task_statuses.append(task_status)
        
        return {
            "batchId": batch_task.batch_id,
            "status": batch_task.status,
            "totalImages": batch_task.total_images,
            "completedImages": batch_task.completed_images,
            "failedImages": batch_task.failed_images,
            "progress": batch_task.progress_percentage,
            "tasks": task_statuses,
            "createdAt": batch_task.created_at,
            "completedAt": batch_task.completed_at,
        }


    async def get_batch_download_urls(
        self, db: Session, batch_id: str, user_id: int
    ) -> Optional[List[Dict[str, str]]]:
        """获取批量任务结果的下载链接列表（前端打包）"""
        logger.info(f"Getting download URLs for batch {batch_id}, user {user_id}")
        
        batch_task = (
            db.query(BatchTask)
            .filter(BatchTask.batch_id == batch_id, BatchTask.user_id == user_id)
            .first()
        )
        
        if not batch_task:
            logger.warning(f"Batch task {batch_id} not found for user {user_id}")
            return None
        
        if not batch_task.is_completed:
            logger.warning(f"Batch task {batch_id} is not completed. Status: {batch_task.status}")
            raise Exception("批量任务尚未完成")
        
        # 获取所有已完成的子任务
        completed_tasks = (
            db.query(Task)
            .filter(
                Task.batch_id == batch_task.id,
                Task.status == TaskStatus.COMPLETED.value
            )
            .all()
        )
        
        logger.info(f"Found {len(completed_tasks)} completed tasks for batch {batch_id}")
        
        if not completed_tasks:
            raise Exception("没有已完成的任务")
        
        # 生成所有结果文件的签名URL
        result_files = []
        
        for task in completed_tasks:
            if task.result_image_url:
                try:
                    # 处理多个结果URL（逗号分隔）
                    result_urls = [url.strip() for url in task.result_image_url.split(",") if url.strip()]
                    
                    for url_idx, result_url in enumerate(result_urls):
                        # 生成签名URL或获取可访问URL
                        signed_url = await self.file_service.ensure_accessible_url(result_url)
                        
                        if not signed_url:
                            logger.warning(f"Failed to generate accessible URL for task {task.task_id}: URL is empty")
                            continue

                        # 生成文件名
                        original_name = task.original_filename.rsplit('.', 1)[0]
                        extension = result_url.split('.')[-1]
                        
                        if len(result_urls) > 1:
                            filename = f"{original_name}_{url_idx + 1}.{extension}"
                        else:
                            filename = f"{original_name}.{extension}"
                        
                        result_files.append({
                            "url": signed_url,
                            "filename": filename
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to generate accessible URL for task {task.task_id}: {str(e)}")
            else:
                logger.warning(f"Task {task.task_id} is completed but has no result_image_url")
        
        logger.info(f"Generated {len(result_files)} download URLs for batch {batch_id}")
        return result_files
