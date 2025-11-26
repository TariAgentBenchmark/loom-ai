import asyncio
import json
import logging
from random import uniform
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.sign_meitu import Signer

logger = logging.getLogger(__name__)


def _summarize_result(result: Any) -> str:
    """Return a compact, readable representation of Meitu responses for logging."""
    try:
        return json.dumps(result, ensure_ascii=False)
    except Exception:
        return str(result)


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
        
        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                # 设定分阶段超时，避免连接长期挂起；并允许跟随重定向
                timeout = httpx.Timeout(connect=10.0, read=180.0, write=180.0, pool=30.0)
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.request(
                        method="POST",
                        url=url,
                        headers=self.meitu_headers,
                        json=data,
                        params={
                            "api_key": self.meitu_api_key,
                            "api_secret": self.meitu_api_secret,
                        },
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

    async def upscale_v2(
        self,
        image_url: str,
        scale_factor: int = 2,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """调用美图AI超清V2接口进行图片放大"""

        if not self.meitu_api_key or not self.meitu_api_secret:
            raise Exception("未配置美图AI密钥，请在后台配置后重试")

        if not image_url or not image_url.startswith("http"):
            raise Exception("美图AI超清V2需要可公开访问的图片URL，请检查存储配置")

        options = options or {}

        sr_num = options.get("sr_num")
        if not isinstance(sr_num, int):
            sr_num = 4 if scale_factor and scale_factor >= 4 else 2

        area_size = options.get("area_size")
        if sr_num == 2:
            area_size = int(area_size) if area_size else 1920
        elif area_size:
            area_size = int(area_size)

        params_payload = {"parameter": {"sr_num": sr_num}}
        if area_size:
            params_payload["parameter"]["area_size"] = area_size

        request_body = {
            "params": json.dumps(params_payload, separators=(",", ":")),
            "init_images": [
                {
                    "url": image_url,
                    "profile": {
                        "media_profiles": {
                            "media_data_type": "url"
                        }
                    }
                }
            ],
            "task": options.get("task", "/v1/Ultra_High_Definition_V2/478332"),
            "task_type": options.get("task_type", "formula"),
            "sync_timeout": int(options.get("sync_timeout", 30)),
            "rsp_media_type": options.get("rsp_media_type", "url"),
        }

        endpoint = "/api/v1/sdk/sync/push"
        base_url = self.meitu_base_url.rstrip("/")
        url = f"{base_url}{endpoint}"
        body_str = json.dumps(request_body, separators=(",", ":"))

        parsed_base = urlparse(self.meitu_base_url)
        host_header = parsed_base.netloc or "openapi.meitu.com"

        headers = {
            "Content-Type": "application/json",
            "Host": host_header,
            "X-Sdk-Content-Sha256": "UNSIGNED-PAYLOAD",
        }

        signer = Signer(self.meitu_api_key, self.meitu_api_secret)
        signer.sign(url, "POST", headers, body_str)

        timeout = httpx.Timeout(connect=10.0, read=180.0, write=180.0, pool=30.0)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.post(url, headers=headers, content=body_str)
                response.raise_for_status()
                result = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("Meitu AI超清V2请求失败: %s - %s", exc.response.status_code, exc.response.text)
            raise Exception(f"美图AI超清V2请求失败: {exc.response.status_code}")
        except httpx.RequestError as exc:
            logger.error("Meitu AI超清V2网络错误: %s", str(exc))
            raise Exception(f"美图AI超清V2网络错误: {str(exc)}")

        if result.get("code") != 0:
            summary = _summarize_result(result)
            logger.error("Meitu AI超清V2返回非零code: %s", summary)
            raise Exception(result.get("message") or f"美图AI超清V2返回错误码: {result.get('code')}；响应: {summary}")

        data = result.get("data") or {}
        status = data.get("status")
        summary = _summarize_result(result)

        if status == 10:
            urls = data.get("result", {}).get("urls") or []
            if not urls:
                raise Exception("美图AI超清V2未返回结果图片")
            return ",".join(urls)

        if status == 9:
            logger.error("Meitu AI超清V2处理超时: %s", summary)
            raise Exception(f"美图AI超清V2处理超时，请稍后重试；响应: {summary}")

        if status == 2:
            logger.error("Meitu AI超清V2处理失败: %s", summary)
            raise Exception(data.get("msg") or f"美图AI超清V2处理失败；响应: {summary}")

        logger.error("美图AI超清V2返回未知状态: %s", summary)
        raise Exception(f"美图AI超清V2处理未完成，状态码: {status}；响应: {summary}")
