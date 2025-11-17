from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class TaskType(PyEnum):
    PROMPT_EDIT = "prompt_edit"  # AI用嘴改图
    SEAMLESS = "seamless"  # AI四方连续转换
    VECTORIZE = "vectorize"  # AI矢量化(转SVG)
    EXTRACT_PATTERN = "extract_pattern"  # AI提取花型
    REMOVE_WATERMARK = "remove_watermark"  # AI智能去水印
    DENOISE = "denoise"  # AI布纹去噪
    EMBROIDERY = "embroidery"  # AI毛线刺绣增强
    FLAT_TO_3D = "flat_to_3d"  # AI平面转3D
    UPSCALE = "upscale"  # AI高清
    EXPAND = "expand_image"  # AI扩图
    SEAMLESS_LOOP = "seamless_loop"  # AI接循环


class TaskStatus(PyEnum):
    QUEUED = "queued"  # 排队中
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败


class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True, nullable=False)  # 任务唯一标识
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 任务基本信息
    type = Column(String(50), nullable=False, index=True)  # 任务类型
    status = Column(String(20), default=TaskStatus.QUEUED.value, index=True)
    
    # 文件信息
    original_image_url = Column(String(500), nullable=False)  # 原图URL
    original_filename = Column(String(255), nullable=False)
    original_file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    original_dimensions = Column(JSON, nullable=True)  # {"width": 1024, "height": 768}
    
    result_image_url = Column(String(500), nullable=True)  # 结果图URL
    result_filename = Column(String(255), nullable=True)
    result_file_size = Column(Integer, nullable=True)
    result_dimensions = Column(JSON, nullable=True)
    
    # 处理配置和结果
    options = Column(JSON, nullable=True)  # 处理选项
    extra_metadata = Column(JSON, nullable=True)  # 处理元数据（算法版本、步骤等）
    
    # 积分和时间
    credits_used = Column(Numeric(18, 2), nullable=False)  # 消耗的积分
    estimated_time = Column(Integer, nullable=True)  # 预计处理时间（秒）
    processing_time = Column(Integer, nullable=True)  # 实际处理时间（秒）
    
    # 用户相关
    favorite = Column(Boolean, default=False)  # 是否收藏
    tags = Column(JSON, nullable=True)  # 用户标签 ["花卉", "装饰"]
    notes = Column(Text, nullable=True)  # 用户备注
    download_count = Column(Integer, default=0)  # 下载次数
    last_downloaded_at = Column(DateTime, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_code = Column(String(20), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", back_populates="tasks")
    shares = relationship("TaskShare", back_populates="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, task_id={self.task_id}, type={self.type}, status={self.status})>"

    @property
    def type_name(self) -> str:
        """获取任务类型的中文名称"""
        type_names = {
            TaskType.PROMPT_EDIT.value: "AI用嘴改图",
            TaskType.SEAMLESS.value: "AI四方连续转换",
            TaskType.VECTORIZE.value: "AI矢量化(转SVG)",
            TaskType.EXTRACT_PATTERN.value: "AI提取花型",
            TaskType.REMOVE_WATERMARK.value: "AI智能去水印",
            TaskType.DENOISE.value: "AI布纹去噪",
            TaskType.EMBROIDERY.value: "AI毛线刺绣增强",
            TaskType.FLAT_TO_3D.value: "AI平面转3D",
            TaskType.UPSCALE.value: "AI高清",
            TaskType.EXPAND.value: "AI扩图",
            TaskType.SEAMLESS_LOOP.value: "AI接循环",
        }
        return type_names.get(self.type, self.type)

    @property
    def is_completed(self) -> bool:
        """任务是否已完成"""
        return self.status == TaskStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """任务是否失败"""
        return self.status == TaskStatus.FAILED.value

    @property
    def is_processing(self) -> bool:
        """任务是否正在处理"""
        return self.status in [TaskStatus.QUEUED.value, TaskStatus.PROCESSING.value]

    def mark_as_started(self):
        """标记任务为开始处理"""
        self.status = TaskStatus.PROCESSING.value
        self.started_at = func.now()

    def mark_as_completed(self, result_url: str, result_filename: str, result_size: int, processing_time: int):
        """标记任务为完成"""
        self.status = TaskStatus.COMPLETED.value
        self.result_image_url = result_url
        self.result_filename = result_filename
        self.result_file_size = result_size
        self.processing_time = processing_time
        self.completed_at = func.now()

    def mark_as_failed(self, error_message: str, error_code: str = None):
        """标记任务为失败"""
        self.status = TaskStatus.FAILED.value
        self.error_message = error_message
        self.error_code = error_code
        self.completed_at = func.now()

    def increment_download_count(self):
        """增加下载次数"""
        self.download_count += 1
        self.last_downloaded_at = func.now()


class TaskShare(Base):
    """任务分享模型"""
    __tablename__ = "task_shares"

    id = Column(Integer, primary_key=True, index=True)
    share_id = Column(String(50), unique=True, index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # 分享配置
    password = Column(String(255), nullable=True)  # 分享密码
    allow_download = Column(Boolean, default=True)
    expire_hours = Column(Integer, default=24)
    
    # 统计信息
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # 状态
    status = Column(String(20), default="active")  # active, expired
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    # 关联关系
    task = relationship("Task", back_populates="shares")

    @property
    def is_expired(self) -> bool:
        """分享是否已过期"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_active(self) -> bool:
        """分享是否有效"""
        return self.status == "active" and not self.is_expired
