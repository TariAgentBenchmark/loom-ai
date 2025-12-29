import asyncio
import logging
from io import BytesIO
from random import uniform
from typing import Any, Dict

import httpx

from app.services.ai_client.base_client import BaseAIClient
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class GPT4oClient(BaseAIClient):
    """GPT-4o API客户端"""
    
    def __init__(self):
        super().__init__(api_name="gpt4o")
    
    async def generate_image(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """使用GPT-4o生成图片"""
        endpoint = "/v1/images/generations"
        data = {
            "model": "gpt-4o-image-vip",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        logger.info(f"Generating image with GPT-4o: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)

    async def process_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        n: int = 1,
        size: str = "1024x1024",
    ) -> Dict[str, Any]:
        """使用GPT-4o-image-vip处理图片"""
        url = f"{self.base_url}/v1/images/edits"
        
        # 准备multipart form数据
        files = {
            'image': ('image.png', BytesIO(image_bytes), mime_type)
        }
        
        data = {
            'model': 'gpt-4o-image-vip',
            'prompt': prompt,
            'n': str(n),
            'size': size,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"Processing image with GPT-4o (n={n}): {prompt[:100]}...")
        
        max_retries = 3
        backoff_base = 1.5

        async def _do_request():
            for attempt in range(1, max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.post(
                            url,
                            headers=headers,
                            files=files,
                            data=data
                        )
                        response.raise_for_status()
                        return response.json()
                
                except httpx.HTTPStatusError as exc:
                    status = exc.response.status_code
                    body = exc.response.text
                    if 500 <= status < 600 and attempt < max_retries:
                        wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                        logger.warning(
                            "GPT-4o API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                            status,
                            attempt,
                            max_retries,
                            body,
                            wait_seconds,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue
                    
                    logger.error(f"GPT-4o API request failed: {status} - {body}")
                    raise AIClientException(
                        message=f"GPT-4o服务请求失败: {status}",
                        api_name="GPT4o",
                        status_code=status,
                        response_body=body,
                        request_data=data,
                    )

                except httpx.RequestError as exc:
                    if attempt < max_retries:
                        wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                        logger.warning(
                            "GPT-4o API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                            exc,
                            attempt,
                            max_retries,
                            wait_seconds,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    logger.error(f"GPT-4o API request error: {str(exc)}")
                    raise AIClientException(
                        message=f"GPT-4o服务连接失败: {str(exc)}",
                        api_name="GPT4o",
                        request_data=data,
                    )

            raise AIClientException(
                message="GPT-4o服务连接失败: 未知错误",
                api_name="GPT4o",
                request_data=data,
            )

        return await api_limiter.run("gpt4o", _do_request)
