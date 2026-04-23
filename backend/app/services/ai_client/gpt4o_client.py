import logging
from typing import Any, Dict

from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.apyi_openai_client import GPT_IMAGE_2_ALL_MODEL

logger = logging.getLogger(__name__)


class GPT4oClient(BaseAIClient):
    """Legacy image client wrapper, now routed to Apyi gpt-image-2-all."""
    
    def __init__(self):
        super().__init__(api_name="gpt4o")
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """使用 gpt-image-2-all 生成图片。"""
        endpoint = "/v1/chat/completions"
        data = {
            "model": GPT_IMAGE_2_ALL_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"生成图片尺寸/构图参考：{size}。{prompt}"},
                    ],
                }
            ],
        }
        
        logger.info("Generating image with %s: %s...", GPT_IMAGE_2_ALL_MODEL, prompt[:100])
        return await self._make_request("POST", endpoint, data)

    async def process_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        n: int = 1,
        size: str = "1024x1024",
    ) -> Dict[str, Any]:
        """使用 gpt-image-2-all 处理图片。"""
        endpoint = "/v1/chat/completions"
        image_base64 = self._image_to_base64(
            image_bytes,
            "PNG" if mime_type == "image/png" else "JPEG",
        )
        data = {
            "model": GPT_IMAGE_2_ALL_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"生成图片尺寸/构图参考：{size}。{prompt}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
        }
        logger.info(
            "Processing image with %s (requested_n=%s): %s...",
            GPT_IMAGE_2_ALL_MODEL,
            n,
            prompt[:100],
        )
        return await self._make_request("POST", endpoint, data)
