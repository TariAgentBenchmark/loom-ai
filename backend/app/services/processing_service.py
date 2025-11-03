import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.task import Task, TaskType, TaskStatus
from app.models.user import User
from app.services.ai_client import ai_client
from app.services.credit_service import CreditService
from app.services.file_service import FileService
from app.services.membership_service import MembershipService
from app.services.credit_math import to_decimal, to_float

logger = logging.getLogger(__name__)


class ProcessingService:
    """图片处理服务"""
    
    def __init__(self):
        self.credit_service = CreditService()
        self.file_service = FileService()
        self.membership_service = MembershipService()
        
        self.service_key_map = {
            TaskType.PROMPT_EDIT.value: "prompt_edit",
            TaskType.SEAMLESS.value: "seamless",
            TaskType.VECTORIZE.value: "style",
            TaskType.EXTRACT_PATTERN.value: "extract_pattern",
            TaskType.REMOVE_WATERMARK.value: "watermark_removal",
            TaskType.DENOISE.value: "noise_removal",
            TaskType.EMBROIDERY.value: "embroidery",
            TaskType.FLAT_TO_3D.value: "flat_to_3d",
            TaskType.UPSCALE.value: "upscale",
            TaskType.EXPAND.value: "expand_image",
            TaskType.SEAMLESS_LOOP.value: "seamless_loop",
        }
        
        # 预计处理时间（秒）
        self.estimated_times = {
            TaskType.PROMPT_EDIT.value: 150,
            TaskType.SEAMLESS.value: 120,
            TaskType.VECTORIZE.value: 180,
            TaskType.EXTRACT_PATTERN.value: 200,
            TaskType.REMOVE_WATERMARK.value: 90,
            TaskType.DENOISE.value: 120,
            TaskType.EMBROIDERY.value: 200,  # 处理时间更长
            TaskType.FLAT_TO_3D.value: 210,
            TaskType.UPSCALE.value: 180,  # 无损放大
            TaskType.EXPAND.value: 180,
            TaskType.SEAMLESS_LOOP.value: 210,
        }
        
        # 服务成本兜底配置，避免未初始化价格时阻塞功能
        self.default_service_costs = {
            TaskType.FLAT_TO_3D.value: to_decimal(1.5),
        }

    def _resolve_service_key(self, task_type: str) -> str:
        service_key = self.service_key_map.get(task_type)
        if not service_key:
            raise Exception(f"未配置的服务类型: {task_type}")
        return service_key

    async def create_task(
        self,
        db: Session,
        user: User,
        task_type: str,
        image_bytes: bytes,
        original_filename: str,
        options: Dict[str, Any] = None
    ) -> Task:
        """创建处理任务"""
        
        # 保存原始图片
        jimeng_purposes = {TaskType.EMBROIDERY.value, TaskType.FLAT_TO_3D.value}
        original_url = await self.file_service.save_upload_file(
            image_bytes,
            original_filename,
            "originals",
            purpose="jimeng" if task_type in jimeng_purposes else "general"
        )
        
        # 获取图片信息
        image_info = await self.file_service.get_image_info(image_bytes)
        
        # 计算所需积分
        service_key = self._resolve_service_key(task_type)
        credits_needed = await self.membership_service.calculate_service_cost(db, service_key)
        if credits_needed is None:
            credits_needed = self.default_service_costs.get(task_type)
            if credits_needed is None:
                raise Exception("服务价格未配置，请联系管理员")

        # 检查积分是否足够
        if not user.can_afford(credits_needed):
            raise Exception("积分不足，请充值后再试")
        
        # 创建任务记录
        task = Task(
            task_id=f"task_{task_type}_{uuid.uuid4().hex[:12]}",
            user_id=user.id,
            type=task_type,
            status=TaskStatus.QUEUED.value,
            original_image_url=original_url,
            original_filename=original_filename,
            original_file_size=len(image_bytes),
            original_dimensions={"width": image_info["width"], "height": image_info["height"]},
            options=options or {},
            credits_used=credits_needed,
            estimated_time=self.estimated_times.get(task_type, 120)
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # 异步开始处理任务
        asyncio.create_task(self._process_task_async(task.task_id))
        
        logger.info(f"Created task {task.task_id} for user {user.id}")
        return task

    async def _process_task_async(self, task_id: str):
        """异步处理任务"""
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            # 标记任务开始
            task.mark_as_started()
            db.commit()
            
            # 读取原始图片
            image_bytes = await self.file_service.read_file(task.original_image_url)
            
            # 根据任务类型调用相应的AI处理方法
            start_time = datetime.utcnow()
            task_options = task.options or {}

            try:
                if task.type == TaskType.SEAMLESS.value:
                    result_url = await ai_client.seamless_pattern_conversion(image_bytes, task_options)
                elif task.type == TaskType.PROMPT_EDIT.value:
                    result_url = await ai_client.prompt_edit_image(image_bytes, task_options)
                elif task.type == TaskType.VECTORIZE.value:
                    result_url = await ai_client.vectorize_image_a8_svg(image_bytes, task_options)
                elif task.type == TaskType.EXTRACT_PATTERN.value:
                    result_url = await ai_client.extract_pattern(image_bytes, task_options)
                elif task.type == TaskType.REMOVE_WATERMARK.value:
                    result_url = await ai_client.remove_watermark(image_bytes, task_options)
                elif task.type == TaskType.DENOISE.value:
                    result_url = await ai_client.denoise_image(image_bytes, task_options)
                elif task.type == TaskType.EMBROIDERY.value:
                    result_url = await ai_client.enhance_embroidery(image_bytes, task_options)
                elif task.type == TaskType.FLAT_TO_3D.value:
                    result_url = await ai_client.convert_flat_to_3d(image_bytes, task_options)
                elif task.type == TaskType.UPSCALE.value:
                    # For upscale, we need to first save the image and get its URL
                    temp_filename = f"temp_upscale_{task.task_id}.jpg"
                    # save_upload_file 返回的是完整的URL路径（如 /files/originals/xxx.jpg）
                    image_url = await self.file_service.save_upload_file(
                        image_bytes, temp_filename, "originals", purpose="upscale"
                    )
                    # image_url 现在已经是正确的格式了，直接使用
                    result_url = await ai_client.upscale_image(
                        image_url,
                        task_options.get("scale_factor", 2),
                        task_options.get("custom_width"),
                        task_options.get("custom_height"),
                        task_options,
                        image_bytes=image_bytes
                    )
                elif task.type == TaskType.EXPAND.value:
                    result_url = await ai_client.expand_image(
                        image_bytes,
                        task_options,
                        task.original_filename,
                    )
                elif task.type == TaskType.SEAMLESS_LOOP.value:
                    result_url = await ai_client.seamless_loop(
                        image_bytes,
                        task_options,
                        task.original_filename,
                    )
                else:
                    raise Exception(f"不支持的任务类型: {task.type}")
                
                logger.info(
                    "Task %s generated result URL: %s", task_id, result_url
                )

                # 计算处理时间
                processing_time = int((datetime.utcnow() - start_time).total_seconds())
                
                # 检查是否是多张图片（精细效果类型）
                result_urls = result_url.split(",") if "," in result_url else [result_url]
                
                # 处理所有结果图片
                final_result_urls = []
                result_filenames = []
                total_size = 0
                
                for idx, single_result_url in enumerate(result_urls):
                    # 获取结果文件信息
                    # 根据任务类型确定文件格式
                    if task.type == TaskType.VECTORIZE.value:
                        # 矢量化任务返回SVG格式
                        if single_result_url.startswith("/files/results/"):
                            # 本地文件，直接使用，不需要重新保存
                            final_url = single_result_url
                            # 从URL中提取文件名
                            filename = single_result_url.split("/")[-1]
                            # 读取文件内容以获取文件大小
                            result_bytes = await self.file_service.read_file(single_result_url)
                        else:
                            # 远程URL，下载文件
                            result_bytes = await self.file_service.download_from_url(single_result_url)
                            filename = f"result_{task.task_id}_{idx}.svg"
                            # 保存结果文件
                            final_url = await self.file_service.save_upload_file(
                                result_bytes, filename, "results"
                            )
                    else:
                        # 其他任务返回PNG格式
                        if single_result_url.startswith("/files/results/"):
                            # 本地文件，直接使用，不需要重新保存
                            final_url = single_result_url
                            # 从URL中提取文件名
                            filename = single_result_url.split("/")[-1]
                            # 读取文件内容以获取文件大小
                            result_bytes = await self.file_service.read_file(single_result_url)
                        else:
                            # 远程URL，下载文件
                            result_bytes = await self.file_service.download_from_url(single_result_url)
                            filename = f"result_{task.task_id}_{idx}.png"
                            # 保存结果文件
                            final_url = await self.file_service.save_upload_file(
                                result_bytes, filename, "results"
                            )
                    
                    final_result_urls.append(final_url)
                    result_filenames.append(filename)
                    total_size += len(result_bytes)
                
                # 合并结果URL和文件名
                final_result_url = ",".join(final_result_urls)
                result_filename = ",".join(result_filenames)
                
                # 标记任务完成
                task.mark_as_completed(
                    result_url=final_result_url,
                    result_filename=result_filename,
                    result_size=total_size,
                    processing_time=processing_time
                )

                # 扣除积分并更新处理次数
                user = db.query(User).filter(User.id == task.user_id).first()
                if not user:
                    raise Exception(f"找不到用户 {task.user_id}")

                if not user.deduct_credits(task.credits_used):
                    task.mark_as_failed("积分不足，请充值后再试", "P007")
                    task.credits_used = to_decimal(0)
                    db.commit()
                    logger.warning("Task %s failed during settlement due to insufficient credits", task_id)
                    return

                user.increment_processed_count()
                
                db.commit()

                if task.credits_used:
                    await self.credit_service.record_transaction(
                        db=db,
                        user_id=user.id,
                        amount=-task.credits_used,
                        source="processing",
                        description=f"{task.type_name}处理",
                        related_task_id=task.task_id
                    )

                logger.info(f"Task {task_id} completed successfully")
                
            except Exception as e:
                # 处理失败
                error_msg = str(e)
                task.mark_as_failed("服务器火爆，重试一下。", "P006")
                task.credits_used = to_decimal(0)

                db.commit()
                logger.error(f"Task {task_id} failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Unexpected error processing task {task_id}: {str(e)}")
        finally:
            db.close()

    async def get_task_status(self, db: Session, task_id: str, user_id: int) -> Optional[Task]:
        """获取任务状态"""
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == user_id
        ).first()
        return task

    async def get_user_tasks(
        self,
        db: Session,
        user_id: int,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取用户任务列表"""
        query = db.query(Task).filter(Task.user_id == user_id)
        
        if task_type:
            query = query.filter(Task.type == task_type)
        if status:
            query = query.filter(Task.status == status)
        
        # 分页
        total = query.count()
        tasks = query.offset((page - 1) * limit).limit(limit).all()
        
        return {
            "tasks": tasks,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }

    async def delete_task(self, db: Session, task_id: str, user_id: int) -> bool:
        """删除任务"""
        task = db.query(Task).filter(
            Task.task_id == task_id,
            Task.user_id == user_id
        ).first()
        
        if not task:
            return False
        
        # 删除相关文件
        try:
            if task.original_image_url:
                await self.file_service.delete_file(task.original_image_url)
            if task.result_image_url:
                await self.file_service.delete_file(task.result_image_url)
        except Exception as e:
            logger.warning(f"Failed to delete files for task {task_id}: {str(e)}")
        
        # 删除任务记录
        db.delete(task)
        db.commit()
        
        logger.info(f"Deleted task {task_id}")
        return True

    async def estimate_credits(
        self,
        task_type: str,
        image_info: Dict[str, Any],
        user: User,
    ) -> Dict[str, Any]:
        """预估积分消耗"""
        service_key = self._resolve_service_key(task_type)
        unit_price = await self.membership_service.get_service_price(db, service_key)
        if unit_price is None:
            raise Exception("服务价格未配置，请联系管理员")

        final_credits = unit_price
        return {
            "unitPrice": to_float(unit_price),
            "estimatedCredits": to_float(final_credits),
            "finalCredits": to_float(final_credits),
            "quantity": 1,
            "canAfford": user.can_afford(final_credits),
            "currentBalance": to_float(user.credits)
        }
