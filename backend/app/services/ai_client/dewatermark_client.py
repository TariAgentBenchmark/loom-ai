import base64
import logging
import os
from io import BytesIO
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class DewatermarkClient(BaseAIClient):
    """Dewatermark.ai API客户端"""
    
    def __init__(self):
        super().__init__(api_name="dewatermark")
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
            try:
                async with api_limiter.slot("dewatermark"):
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.post(
                            self.dewatermark_url,
                            headers=headers,
                            files=files
                        )
                        response.raise_for_status()
                        result = response.json()
            except httpx.HTTPStatusError as e:
                raise AIClientException(
                    message=f"Dewatermark请求失败: {e.response.status_code}",
                    api_name="Dewatermark",
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                    request_data={"has_mask_brush": "mask_brush" in files},
                ) from e
            except httpx.RequestError as e:
                raise AIClientException(
                    message=f"Dewatermark网络错误: {str(e)}",
                    api_name="Dewatermark",
                    request_data={"has_mask_brush": "mask_brush" in files},
                ) from e
            finally:
                # 关闭打开的文件
                if "mask_brush" in files and hasattr(files["mask_brush"][1], 'close'):
                    files["mask_brush"][1].close()

            # 检查响应
            if "edited_image" not in result:
                logger.error(f"Dewatermark.ai API unexpected response: {result}")
                raise AIClientException(
                    message="Dewatermark.ai API响应格式错误",
                    api_name="Dewatermark",
                    status_code=200,
                    response_body=result,
                )

            # 提取处理后的图片数据
            edited_image = result["edited_image"]
            if "image" in edited_image:
                # 保存处理后的图片并返回URL
                return self._save_base64_image(edited_image["image"])

            raise AIClientException(
                message="无法从Dewatermark.ai API响应中提取处理后的图片",
                api_name="Dewatermark",
                status_code=200,
                response_body=result,
            )

        except AIClientException:
            raise
        except Exception as e:
            logger.error(f"Remove watermark failed: {str(e)}")
            raise AIClientException(
                message=f"智能去水印失败: {str(e)}",
                api_name="Dewatermark",
            ) from e
