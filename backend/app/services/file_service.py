import os
import uuid
import aiofiles
import httpx
from typing import Dict, Any, Optional
from PIL import Image
from io import BytesIO
import logging
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """文件服务"""
    
    def __init__(self):
        self.upload_path = settings.upload_path
        self.max_file_size = settings.max_file_size
        self.allowed_extensions = settings.allowed_extensions_list
        
        # 确保上传目录存在
        os.makedirs(f"{self.upload_path}/originals", exist_ok=True)
        os.makedirs(f"{self.upload_path}/results", exist_ok=True)
        os.makedirs(f"{self.upload_path}/temp", exist_ok=True)

    def validate_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """验证文件"""
        # 检查文件大小
        if len(file_bytes) > self.max_file_size:
            raise Exception(f"文件大小超过限制 ({self.max_file_size / 1024 / 1024:.1f}MB)")
        
        # 检查文件扩展名
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in self.allowed_extensions:
            raise Exception(f"不支持的文件格式，支持格式: {', '.join(self.allowed_extensions)}")
        
        # 检查图片是否有效
        try:
            image = Image.open(BytesIO(file_bytes))
            width, height = image.size
            
            # 检查分辨率
            if width < 256 or height < 256:
                raise Exception("图片分辨率过低，最小支持256x256")
            
            if width > 8192 or height > 8192:
                raise Exception("图片分辨率过高，最大支持8192x8192")
            
            return {
                "valid": True,
                "width": width,
                "height": height,
                "format": image.format,
                "mode": image.mode,
                "size": len(file_bytes)
            }
            
        except Exception as e:
            if "图片分辨率" in str(e):
                raise e
            raise Exception("无效的图片文件")

    async def save_upload_file(self, file_bytes: bytes, filename: str, subfolder: str = "uploads") -> str:
        """保存上传的文件"""
        
        # 验证文件
        file_info = self.validate_file(file_bytes, filename)
        
        # 生成唯一文件名
        file_ext = filename.lower().split('.')[-1] if '.' in filename else 'png'
        unique_filename = f"{uuid.uuid4().hex[:16]}.{file_ext}"
        
        # 构建文件路径
        file_path = os.path.join(self.upload_path, subfolder, unique_filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 异步保存文件
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)
        
        # 返回访问URL
        return f"/files/{subfolder}/{unique_filename}"

    async def read_file(self, file_url: str) -> bytes:
        """读取文件"""
        if file_url.startswith("/files/"):
            # 本地文件
            file_path = file_url.replace("/files/", f"{self.upload_path}/")
            
            if not os.path.exists(file_path):
                raise Exception("文件不存在")
            
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
        
        elif file_url.startswith("http"):
            # 远程文件
            return await self.download_from_url(file_url)
        
        else:
            raise Exception("无效的文件URL")

    async def download_from_url(self, url: str) -> bytes:
        """从URL下载文件"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download from URL {url}: {str(e)}")
            raise Exception(f"下载文件失败: {str(e)}")

    async def delete_file(self, file_url: str) -> bool:
        """删除文件"""
        try:
            if file_url.startswith("/files/"):
                file_path = file_url.replace("/files/", f"{self.upload_path}/")
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_url}: {str(e)}")
            return False

    async def get_image_info(self, image_bytes: bytes) -> Dict[str, Any]:
        """获取图片信息"""
        try:
            image = Image.open(BytesIO(image_bytes))
            
            return {
                "width": image.size[0],
                "height": image.size[1],
                "format": image.format,
                "mode": image.mode,
                "size": len(image_bytes)
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            raise Exception("无法获取图片信息")

    async def create_thumbnail(self, image_bytes: bytes, size: tuple = (200, 200)) -> bytes:
        """创建缩略图"""
        try:
            image = Image.open(BytesIO(image_bytes))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 转换为字节
            buffer = BytesIO()
            format = "PNG" if image.mode == "RGBA" else "JPEG"
            image.save(buffer, format=format, quality=85)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {str(e)}")
            raise Exception("创建缩略图失败")

    def get_file_path(self, file_url: str) -> str:
        """获取文件的本地路径"""
        if file_url.startswith("/files/"):
            return file_url.replace("/files/", f"{self.upload_path}/")
        return file_url

    def get_file_url(self, file_path: str) -> str:
        """获取文件的访问URL"""
        if file_path.startswith(self.upload_path):
            return file_path.replace(self.upload_path, "/files")
        return file_path

    async def cleanup_old_files(self, days: int = 30):
        """清理旧文件"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            for root, dirs, files in os.walk(self.upload_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")

    def is_valid_image_format(self, filename: str) -> bool:
        """检查是否为有效的图片格式"""
        if '.' not in filename:
            return False
        
        ext = filename.lower().split('.')[-1]
        return ext in self.allowed_extensions
