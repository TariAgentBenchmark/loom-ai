import logging
from io import BytesIO
from random import uniform
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GPT4oClient:
    """GPT-4o API客户端"""
    
    def __init__(self):
        self.base_url = settings.tuzi_base_url
        self.api_key = settings.tuzi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data
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
                raise Exception(f"GPT-4o服务请求失败: {status}")

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
                raise Exception(f"GPT-4o服务连接失败: {str(exc)}")

        raise Exception("GPT-4o服务连接失败: 未知错误")
    
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

    async def process_image(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg", n: int = 1) -> Dict[str, Any]:
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
            'size': '1024x1024'
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"Processing image with GPT-4o (n={n}): {prompt[:100]}...")
        
        max_retries = 3
        backoff_base = 1.5
        
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
                raise Exception(f"GPT-4o服务请求失败: {status}")
            
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
                raise Exception(f"GPT-4o服务连接失败: {str(exc)}")
        
        raise Exception("GPT-4o服务连接失败: 未知错误")