import logging
from typing import Any, Dict

from app.services.ai_client.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseAIClient):
    """Gemini API客户端"""
    
    async def process_image(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """使用Gemini-2.5-flash-image处理图片"""
        endpoint = "/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        # 转换图片为base64
        image_base64 = self._image_to_base64(image_bytes, 
                                           "PNG" if mime_type == "image/png" else "JPEG")
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        logger.info(f"Processing image with Gemini: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)