from pydantic import BaseModel
from typing import Any, Optional, List, Dict
from datetime import datetime


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool
    message: str
    timestamp: datetime = datetime.utcnow()


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    success: bool = True
    data: Any


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error: Dict[str, Any]


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int
    limit: int
    total: int
    total_pages: int


class PaginationResponse(BaseModel):
    """分页响应模型"""
    pagination: PaginationMeta


class FileInfo(BaseModel):
    """文件信息模型"""
    url: str
    filename: str
    size: int
    format: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None


class ImageDimensions(BaseModel):
    """图片尺寸模型"""
    width: int
    height: int


class ProcessingOptions(BaseModel):
    """处理选项基类"""
    pass


class TaskMetadata(BaseModel):
    """任务元数据"""
    algorithm: Optional[str] = None
    processing_steps: Optional[List[Dict[str, Any]]] = None
    quality_score: Optional[float] = None
