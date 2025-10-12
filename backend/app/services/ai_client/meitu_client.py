import asyncio
import logging
from random import uniform
from typing import Any, Dict

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MeituClient:
    """美图API客户端"""
    
    def __init__(self):
        self.meitu_base_url = settings.meitu_base_url
        self.meitu_api_key = settings.meitu_api_key
        self.meitu_api_secret = settings.meitu_api_secret
        self.meitu_headers = {
            "Content-Type": "application/json"
        }
    
    async def _make_meitu_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送美图API请求"""
        url = f"{self.meitu_base_url}{endpoint}"
        url_with_params = f"{url}?api_key={self.meitu_api_key}&api_secret={self.meitu_api_secret}"
        
        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method="POST",
                        url=url_with_params,
                        headers=self.meitu_headers,
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
                        "Meitu API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu API request failed: {status} - {body}")
                raise Exception(f"美图API请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Meitu API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu API request error: {str(exc)}")
                raise Exception(f"美图API连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("美图API连接失败: 未知错误")