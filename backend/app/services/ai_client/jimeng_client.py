import asyncio
import datetime
import hashlib
import hmac
import json
import logging
from random import uniform
from typing import Any, Dict
from urllib.parse import urlparse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class JimengClient:
    """即梦API客户端"""
    
    def __init__(self):
        self.jimeng_api_key = settings.jimeng_api_key
        self.jimeng_api_secret = settings.jimeng_api_secret
        self.jimeng_base_url = settings.jimeng_base_url
        self.jimeng_region = "cn-north-1"
        self.jimeng_service = "cv"
    
    async def _make_jimeng_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送即梦API请求"""
        url = f"{self.jimeng_base_url}{endpoint}"
        
        if not self.jimeng_api_key or not self.jimeng_api_secret:
            raise Exception("即梦API密钥未配置")

        # 添加查询参数
        query_params = {
            "Action": data.get("Action", "CVSync2AsyncSubmitTask"),
            "Version": data.get("Version", "2022-08-31"),
        }

        canonical_querystring = "&".join(
            f"{key}={query_params[key]}" for key in sorted(query_params)
        )
        full_url = f"{url}?{canonical_querystring}" if canonical_querystring else url

        parsed_url = urlparse(full_url)
        canonical_uri = parsed_url.path or "/"
        host = parsed_url.netloc
        
        # 准备请求数据
        request_data = {
            "req_key": data.get("req_key", "jimeng_t2i_v40"),
        }
        
        # 添加其他参数
        if "prompt" in data:
            request_data["prompt"] = data["prompt"]
        if "image_urls" in data:
            request_data["image_urls"] = data["image_urls"]
        if "size" in data:
            request_data["size"] = data["size"]
        if "width" in data:
            request_data["width"] = data["width"]
        if "height" in data:
            request_data["height"] = data["height"]
        if "scale" in data:
            request_data["scale"] = data["scale"]
        if "force_single" in data:
            request_data["force_single"] = data["force_single"]
        if "min_ratio" in data:
            request_data["min_ratio"] = data["min_ratio"]
        if "max_ratio" in data:
            request_data["max_ratio"] = data["max_ratio"]
        if "task_id" in data:
            request_data["task_id"] = data["task_id"]
        
        body_json = json.dumps(request_data, ensure_ascii=False, separators=(",", ":"))
        body_bytes = body_json.encode("utf-8")

        payload_hash = hashlib.sha256(body_bytes).hexdigest()
        content_type = "application/json"
        method_upper = method.upper()

        timestamp = datetime.datetime.utcnow()
        current_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
        datestamp = timestamp.strftime("%Y%m%d")

        signed_headers = "content-type;host;x-content-sha256;x-date"
        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{host}\n"
            f"x-content-sha256:{payload_hash}\n"
            f"x-date:{current_date}\n"
        )

        canonical_request = (
            f"{method_upper}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        algorithm = "HMAC-SHA256"
        credential_scope = f"{datestamp}/{self.jimeng_region}/{self.jimeng_service}/request"
        string_to_sign = (
            f"{algorithm}\n"
            f"{current_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = _sign(self.jimeng_api_secret.encode("utf-8"), datestamp)
        k_region = _sign(k_date, self.jimeng_region)
        k_service = _sign(k_region, self.jimeng_service)
        signing_key = _sign(k_service, "request")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} "
            f"Credential={self.jimeng_api_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers = {
            "Content-Type": content_type,
            "Authorization": authorization_header,
            "X-Date": current_date,
            "X-Content-Sha256": payload_hash,
            "Host": host,
        }

        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method_upper,
                        url=full_url,
                        headers=headers,
                        content=body_bytes,
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text
                if 500 <= status < 600 and attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Jimeng API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Jimeng API request failed: {status} - {body}")
                raise Exception(f"即梦API请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Jimeng API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Jimeng API request error: {str(exc)}")
                raise Exception(f"即梦API连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("即梦API连接失败: 未知错误")
    
    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询即梦异步任务状态"""
        data = {
            "Action": "CVSync2AsyncGetResult",
            "Version": "2022-08-31",
            "req_key": "jimeng_t2i_v40",
            "task_id": task_id
        }
        
        logger.info(f"Querying Jimeng task status: {task_id}")
        return await self._make_jimeng_request("POST", "", data)