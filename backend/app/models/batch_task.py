from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class BatchTaskStatus(PyEnum):
    QUEUED = "queued"  # 排队中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    PARTIAL = "partial"  # 部分完成


class BatchTask(Base):
    """批量任务模型"""
    __tablename__ = "batch_tasks"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(50), unique=True, index=True, nullable=False)  # 批量任务唯一标识
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务基本信息
    task_type = Column(String(50), nullable=False, index=True)  # 任务类型
    status = Column(String(20), default=BatchTaskStatus.QUEUED.value, index=True)
    
    # 批量任务统计
    total_images = Column(Integer, nullable=False, default=0)  # 总图片数
    completed_images = Column(Integer, nullable=False, default=0)  # 已完成图片数
    failed_images = Column(Integer, nullable=False, default=0)  # 失败图片数
    
    # 处理配置
    options = Column(JSON, nullable=True)  # 处理选项（所有图片共享）
    
    # 积分和时间
    total_credits_used = Column(Numeric(18, 2), nullable=False, default=0)  # 总消耗积分
    estimated_time = Column(Integer, nullable=True)  # 预计处理时间（秒）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="batch_tasks")
    tasks = relationship("Task", back_populates="batch_task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BatchTask(id={self.id}, batch_id={self.batch_id}, type={self.task_type}, status={self.status})>"

    @property
    def progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_images == 0:
            return 0.0
        return (self.completed_images + self.failed_images) / self.total_images * 100

    @property
    def is_completed(self) -> bool:
        """批量任务是否已完成"""
        return self.status in [BatchTaskStatus.COMPLETED.value, BatchTaskStatus.PARTIAL.value]

    @property
    def is_failed(self) -> bool:
        """批量任务是否失败"""
        return self.status == BatchTaskStatus.FAILED.value

    @property
    def is_processing(self) -> bool:
        """批量任务是否正在处理"""
        return self.status in [BatchTaskStatus.QUEUED.value, BatchTaskStatus.PROCESSING.value]

    def mark_as_started(self):
        """标记批量任务为开始处理"""
        self.status = BatchTaskStatus.PROCESSING.value
        self.started_at = func.now()

    def update_progress(self, completed: int, failed: int):
        """更新进度"""
        self.completed_images = completed
        self.failed_images = failed
        
        # 更新状态
        if completed + failed == self.total_images:
            if failed == self.total_images:
                self.status = BatchTaskStatus.FAILED.value
            elif failed > 0:
                self.status = BatchTaskStatus.PARTIAL.value
            else:
                self.status = BatchTaskStatus.COMPLETED.value
            self.completed_at = func.now()

    def mark_as_completed(self):
        """标记批量任务为完成"""
        self.status = BatchTaskStatus.COMPLETED.value
        self.completed_at = func.now()

    def mark_as_failed(self):
        """标记批量任务为失败"""
        self.status = BatchTaskStatus.FAILED.value
        self.completed_at = func.now()
