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

logger = logging.getLogger(__name__)


class ProcessingService:
    """图片处理服务"""
    
    def __init__(self):
        self.credit_service = CreditService()
        self.file_service = FileService()
        
        # 各功能的基础算力消耗
        self.credit_costs = {
            TaskType.PROMPT_EDIT.value: 80,
            TaskType.SEAMLESS.value: 60,
            TaskType.VECTORIZE.value: 100,
            TaskType.EXTRACT_PATTERN.value: 100,
            TaskType.REMOVE_WATERMARK.value: 70,
            TaskType.DENOISE.value: 80,
            TaskType.EMBROIDERY.value: 120,  # 成本更高
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
        }

    def calculate_credits_needed(self, task_type: str, image_info: Dict[str, Any], user: User) -> int:
        """计算所需算力"""
        base_credits = self.credit_costs.get(task_type, 100)
        
        # 高分辨率附加费用
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        if max(width, height) > 2048:
            base_credits = int(base_credits * 1.5)
        
        # 大文件附加费用
        file_size = image_info.get('size', 0)
        if file_size > 10 * 1024 * 1024:  # 10MB
            base_credits += 20
        
        # 会员折扣
        if user.membership_type.value == "premium":
            base_credits = int(base_credits * 0.9)  # 9折
        elif user.membership_type.value == "enterprise":
            base_credits = int(base_credits * 0.8)  # 8折
        
        return max(base_credits, 10)  # 最少10算力

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
        original_url = await self.file_service.save_upload_file(
            image_bytes, original_filename, "originals", purpose="jimeng" if task_type == TaskType.EMBROIDERY.value else "general"
        )
        
        # 获取图片信息
        image_info = await self.file_service.get_image_info(image_bytes)
        
        # 计算所需算力
        credits_needed = self.calculate_credits_needed(task_type, image_info, user)
        
        # 检查算力是否足够
        if not user.can_afford(credits_needed):
            raise Exception("算力不足，请充值后再试")
        
        # 扣除算力
        user.deduct_credits(credits_needed)
        
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
        
        # 记录算力消耗
        await self.credit_service.record_transaction(
            db=db,
            user_id=user.id,
            amount=-credits_needed,
            source="processing",
            description=f"{task.type_name}处理",
            related_task_id=task.task_id
        )
        
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
            
            try:
                if task.type == TaskType.SEAMLESS.value:
                    result_url = await ai_client.seamless_pattern_conversion(image_bytes, task.options)
                elif task.type == TaskType.PROMPT_EDIT.value:
                    result_url = await ai_client.prompt_edit_image(image_bytes, task.options)
                elif task.type == TaskType.VECTORIZE.value:
                    result_url = await ai_client.vectorize_image(image_bytes, task.options)
                elif task.type == TaskType.EXTRACT_PATTERN.value:
                    result_url = await ai_client.extract_pattern(image_bytes, task.options)
                elif task.type == TaskType.REMOVE_WATERMARK.value:
                    result_url = await ai_client.remove_watermark(image_bytes, task.options)
                elif task.type == TaskType.DENOISE.value:
                    result_url = await ai_client.denoise_image(image_bytes, task.options)
                elif task.type == TaskType.EMBROIDERY.value:
                    result_url = await ai_client.enhance_embroidery(image_bytes, task.options)
                else:
                    raise Exception(f"不支持的任务类型: {task.type}")
                
                logger.info(
                    "Task %s generated result URL: %s", task_id, result_url
                )

                # 计算处理时间
                processing_time = int((datetime.utcnow() - start_time).total_seconds())
                
                # 获取结果文件信息
                # 根据任务类型确定文件格式
                if task.type == TaskType.VECTORIZE.value:
                    # 矢量化任务返回SVG格式
                    if result_url.startswith("/files/results/"):
                        # 本地文件，直接读取
                        result_bytes = await self.file_service.read_file(result_url)
                        result_filename = f"result_{task.task_id}.svg"
                    else:
                        # 远程URL，下载文件
                        result_bytes = await self.file_service.download_from_url(result_url)
                        result_filename = f"result_{task.task_id}.svg"
                else:
                    # 其他任务返回PNG格式
                    if result_url.startswith("/files/results/"):
                        # 本地文件，直接读取
                        result_bytes = await self.file_service.read_file(result_url)
                        result_filename = f"result_{task.task_id}.png"
                    else:
                        # 远程URL，下载文件
                        result_bytes = await self.file_service.download_from_url(result_url)
                        result_filename = f"result_{task.task_id}.png"
                
                # 保存结果文件
                final_result_url = await self.file_service.save_upload_file(
                    result_bytes, result_filename, "results"
                )
                
                # 标记任务完成
                task.mark_as_completed(
                    result_url=final_result_url,
                    result_filename=result_filename,
                    result_size=len(result_bytes),
                    processing_time=processing_time
                )
                
                # 更新用户处理次数
                user = db.query(User).filter(User.id == task.user_id).first()
                user.increment_processed_count()
                
                db.commit()
                logger.info(f"Task {task_id} completed successfully")
                
            except Exception as e:
                # 处理失败
                error_msg = str(e)
                task.mark_as_failed(error_msg, "P006")
                
                # 退还算力
                user = db.query(User).filter(User.id == task.user_id).first()
                user.add_credits(task.credits_used)
                
                # 记录退还算力
                await self.credit_service.record_transaction(
                    db=db,
                    user_id=user.id,
                    amount=task.credits_used,
                    source="refund",
                    description=f"{task.type_name}处理失败，退还算力",
                    related_task_id=task.task_id
                )
                
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
        """预估算力消耗"""
        base_credits = self.credit_costs.get(task_type, 100)
        additional_credits = 0
        
        # 高分辨率附加费用
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        if max(width, height) > 2048:
            additional_credits += int(base_credits * 0.5)
        
        # 大文件附加费用
        file_size = image_info.get('size', 0)
        if file_size > 10 * 1024 * 1024:
            additional_credits += 20
        
        total_credits = base_credits + additional_credits
        
        # 会员折扣
        discount = 0
        if user.membership_type.value == "premium":
            discount = 0.1  # 10%折扣
        elif user.membership_type.value == "enterprise":
            discount = 0.2  # 20%折扣
        
        final_credits = int(total_credits * (1 - discount))
        final_credits = max(final_credits, 10)  # 最少10算力
        
        return {
            "estimatedCredits": final_credits,
            "baseCredits": base_credits,
            "additionalCredits": additional_credits,
            "discount": discount,
            "finalCredits": final_credits,
            "canAfford": user.can_afford(final_credits),
            "currentBalance": user.credits
        }
