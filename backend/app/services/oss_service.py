import os
import uuid
import logging
from typing import Optional, Dict, Any
import oss2
from oss2.exceptions import OssError
from datetime import datetime, timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSSService:
    """阿里云OSS服务"""
    
    def __init__(self):
        """初始化OSS服务"""
        self.access_key_id = settings.oss_access_key_id
        self.access_key_secret = settings.oss_access_key_secret
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket_name
        self.bucket_domain = settings.oss_bucket_domain
        self.expiration_time = settings.oss_expiration_time
        
        # 检查配置
        if not all([self.access_key_id, self.access_key_secret, self.endpoint, self.bucket_name]):
            logger.warning("OSS配置不完整，OSS功能将不可用")
            logger.warning(f"配置状态: access_key_id={'已配置' if self.access_key_id else '未配置'}, "
                          f"access_key_secret={'已配置' if self.access_key_secret else '未配置'}, "
                          f"endpoint={'已配置' if self.endpoint else '未配置'}, "
                          f"bucket_name={'已配置' if self.bucket_name else '未配置'}")
            self.auth = None
            self.bucket = None
        else:
            # 创建认证对象
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            # 创建Bucket对象
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
            logger.info(f"OSS服务初始化成功，Bucket: {self.bucket_name}, Endpoint: {self.endpoint}")
    
    def is_configured(self) -> bool:
        """检查OSS是否已正确配置"""
        return self.auth is not None and self.bucket is not None
    
    def _generate_object_key(self, filename: str, prefix: str = "uploads") -> str:
        """生成OSS对象键"""
        # 获取文件扩展名
        file_ext = filename.lower().split('.')[-1] if '.' in filename else 'jpg'
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex[:16]}.{file_ext}"
        # 添加日期前缀以便管理
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        return f"{prefix}/{date_prefix}/{unique_filename}"
    
    async def upload_file(
        self, 
        file_bytes: bytes, 
        filename: str, 
        prefix: str = "uploads",
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传文件到OSS
        
        Args:
            file_bytes: 文件字节数据
            filename: 原始文件名
            prefix: OSS对象前缀
            content_type: 文件MIME类型
            
        Returns:
            包含文件URL和信息的字典
        """
        if not self.is_configured():
            raise Exception("OSS服务未正确配置")
        
        try:
            # 生成对象键
            object_key = self._generate_object_key(filename, prefix)
            
            # 设置Content-Type
            if not content_type:
                # 根据文件扩展名推断Content-Type
                ext = filename.lower().split('.')[-1] if '.' in filename else ''
                content_type_map = {
                    'jpg': 'image/jpeg',
                    'jpeg': 'image/jpeg',
                    'png': 'image/png',
                    'gif': 'image/gif',
                    'bmp': 'image/bmp',
                    'webp': 'image/webp',
                    'svg': 'image/svg+xml'
                }
                content_type = content_type_map.get(ext, 'application/octet-stream')
            
            # 上传文件
            result = self.bucket.put_object(
                object_key, 
                file_bytes,
                headers={'Content-Type': content_type}
            )
            
            if result.status != 200:
                raise Exception(f"OSS上传失败，状态码: {result.status}")
            
            # 生成访问URL
            if self.bucket_domain:
                # 使用自定义域名
                file_url = f"https://{self.bucket_domain}/{object_key}"
            else:
                # 使用默认域名
                file_url = f"https://{self.bucket_name}.{self.endpoint.replace('https://', '')}/{object_key}"
            
            logger.info(f"文件上传到OSS成功: {object_key}")
            logger.info(f"生成的OSS URL: {file_url}")
            
            return {
                "url": file_url,
                "object_key": object_key,
                "size": len(file_bytes),
                "content_type": content_type,
                "bucket": self.bucket_name
            }
            
        except OssError as e:
            logger.error(f"OSS上传失败: {e.status} - {e.message}")
            raise Exception(f"OSS上传失败: {e.message}")
        except Exception as e:
            logger.error(f"上传文件到OSS时发生错误: {str(e)}")
            raise Exception(f"上传文件失败: {str(e)}")
    
    async def upload_image_for_jimeng(self, image_bytes: bytes, filename: str) -> str:
        """
        上传图片到OSS
        
        Args:
            image_bytes: 图片字节数据
            filename: 原始文件名
            
        Returns:
            图片的访问URL（优先使用预签名URL）
        """
        result = await self.upload_file(
            image_bytes,
            filename,
            prefix="jimeng",
            content_type="image/jpeg"
        )
        
        # 生成预签名URL，确保即梦API可以访问
        try:
            presigned_url = await self.generate_presigned_url(result["object_key"], expiration=3600)
            logger.info(f"生成预签名URL: {presigned_url}")
            return presigned_url
        except Exception as e:
            logger.warning(f"生成预签名URL失败，使用原始URL: {str(e)}")
            return result["url"]
    
    async def generate_presigned_url(self, object_key: str, expiration: Optional[int] = None) -> str:
        """
        生成预签名URL
        
        Args:
            object_key: OSS对象键
            expiration: 过期时间（秒），默认使用配置的过期时间
            
        Returns:
            预签名URL
        """
        if not self.is_configured():
            raise Exception("OSS服务未正确配置")
        
        try:
            expiration_time = expiration or self.expiration_time
            url = self.bucket.sign_url('GET', object_key, expiration_time)
            return url
        except OssError as e:
            logger.error(f"生成预签名URL失败: {e.status} - {e.message}")
            raise Exception(f"生成预签名URL失败: {e.message}")
    
    async def delete_file(self, object_key: str) -> bool:
        """
        删除OSS文件
        
        Args:
            object_key: OSS对象键
            
        Returns:
            是否删除成功
        """
        if not self.is_configured():
            logger.warning("OSS服务未正确配置，无法删除文件")
            return False
        
        try:
            result = self.bucket.delete_object(object_key)
            if result.status == 204:
                logger.info(f"文件删除成功: {object_key}")
                return True
            else:
                logger.warning(f"文件删除失败，状态码: {result.status}")
                return False
        except OssError as e:
            logger.error(f"删除OSS文件失败: {e.status} - {e.message}")
            return False
    
    async def check_file_exists(self, object_key: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_key: OSS对象键
            
        Returns:
            文件是否存在
        """
        if not self.is_configured():
            return False
        
        try:
            return self.bucket.object_exists(object_key)
        except OssError as e:
            logger.error(f"检查文件存在性失败: {e.status} - {e.message}")
            return False
    
    async def get_file_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            object_key: OSS对象键
            
        Returns:
            文件信息字典，如果文件不存在则返回None
        """
        if not self.is_configured():
            return None
        
        try:
            meta = self.bucket.get_object_meta(object_key)
            return {
                "object_key": object_key,
                "size": int(meta.headers.get('Content-Length', 0)),
                "content_type": meta.headers.get('Content-Type', ''),
                "last_modified": meta.headers.get('Last-Modified', '')
            }
        except OssError as e:
            if e.status == 404:
                return None
            logger.error(f"获取文件信息失败: {e.status} - {e.message}")
            return None


# 创建全局OSS服务实例
oss_service = OSSService()