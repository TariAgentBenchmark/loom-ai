import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class DewatermarkClient(BaseAIClient):
    """Dewatermark.ai API客户端"""
    
    def __init__(self):
        super().__init__()
        self.dewatermark_api_key = settings.dewatermark_api_key
        self.dewatermark_url = "https://platform.dewatermark.ai/api/object_removal/v1/erase_watermark"
    
    async def remove_watermark(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI智能去水印（使用Dewatermark.ai API）"""
        try:
            # 将图片转换为base64
            image_base64 = self._image_to_base64(image_bytes, "JPEG")
            
            # 准备文件数据
            files = {}
            
            # 添加原始图片
            files["original_preview_image"] = ("original_preview_image.jpeg",
                                             BytesIO(base64.b64decode(image_base64)))
            
            # 添加mask_brush（如果提供）
            if options and "mask_brush" in options:
                mask_brush_path = options["mask_brush"]
                if os.path.exists(mask_brush_path):
                    files["mask_brush"] = ("mask_brush.png", open(mask_brush_path, "rb"))
            
            # 添加remove_text参数
            files["remove_text"] = (None, "true")
            
            # 准备请求头
            headers = {
                "X-API-KEY": self.dewatermark_api_key
            }
            
            logger.info("Sending request to Dewatermark.ai API")
            
            # 发送请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.dewatermark_url,
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                result = response.json()
            
            # 关闭打开的文件
            if "mask_brush" in files and hasattr(files["mask_brush"][1], 'close'):
                files["mask_brush"][1].close()
            
            # 检查响应
            if "edited_image" not in result:
                logger.error(f"Dewatermark.ai API unexpected response: {result}")
                raise Exception("Dewatermark.ai API响应格式错误")
            
            # 提取处理后的图片数据
            edited_image = result["edited_image"]
            if "image" in edited_image:
                # 保存处理后的图片并返回URL
                return self._save_base64_image(edited_image["image"])
            
            raise Exception("无法从Dewatermark.ai API响应中提取处理后的图片")
            
        except Exception as e:
            logger.error(f"Remove watermark failed: {str(e)}")
            raise Exception(f"智能去水印失败: {str(e)}")