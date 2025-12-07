import asyncio
import logging
import mimetypes
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.api_limiter import api_limiter


logger = logging.getLogger(__name__)


class GQCHClient:
    """GQCH 图像处理平台客户端"""

    def __init__(self) -> None:
        self.base_url = (settings.gqch_api_base_url or "https://gqch.haoee.com").rstrip("/")
        self.api_key = settings.gqch_api_key or ""

    def _ensure_credentials(self) -> None:
        if not self.api_key:
            raise Exception("GQCH API密钥未配置，请在环境变量中设置GQCH_API_KEY")

    async def _request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        files: Optional[Dict[str, Any]] = None,
        timeout: float = 300.0,
    ) -> Dict[str, Any]:
        self._ensure_credentials()

        url = f"{self.base_url}{endpoint}"
        payload = {key: value for key, value in data.items() if value is not None}

        async def _do_request():
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, data=payload, files=files)
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                logger.error("GQCH API request timed out: %s", exc)
                raise Exception("GQCH 接口请求超时，请稍后再试")
            except httpx.HTTPStatusError as exc:
                body = exc.response.text
                logger.error("GQCH API returned HTTP %s: %s", exc.response.status_code, body)
                raise Exception("GQCH 接口请求失败，请联系管理员或稍后再试")
            except httpx.RequestError as exc:
                logger.error("GQCH API request error: %s", exc)
                raise Exception("无法连接到 GQCH 接口，请检查网络或配置")
            except Exception as exc:  # noqa: BLE001
                logger.error("Unexpected error when calling GQCH API: %s", exc)
                raise

        result = await api_limiter.run("gqch", _do_request)

        err_code = result.get("err_code")
        if err_code != 0:
            message = result.get("err_msg") or "GQCH 接口返回错误"
            logger.error("GQCH API responded with err_code=%s, message=%s", err_code, message)
            raise Exception(message)

        return result

    async def expand_image(
        self,
        image_bytes: bytes,
        original_filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """提交扩图任务并返回处理后的结果URL"""
        payload: Dict[str, Any] = {
            "expand_top": self._to_optional_str(options, "expand_top"),
            "expand_bottom": self._to_optional_str(options, "expand_bottom"),
            "expand_left": self._to_optional_str(options, "expand_left"),
            "expand_right": self._to_optional_str(options, "expand_right"),
            "prompt": self._trimmed_or_none(options, "prompt"),
        }

        return await self._submit_task(
            endpoint="/api/submit_expand_image_task",
            payload=payload,
            image_bytes=image_bytes,
            original_filename=original_filename,
        )

    async def seamless_loop(
        self,
        image_bytes: bytes,
        original_filename: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """提交无缝拼图任务并返回处理后的结果URL"""
        payload: Dict[str, Any] = {
            "fit": self._to_optional_str(options, "fit"),
            "direction": self._to_optional_str(options, "direction"),
            "expand_top": self._to_optional_str(options, "expand_top"),
            "expand_bottom": self._to_optional_str(options, "expand_bottom"),
            "expand_left": self._to_optional_str(options, "expand_left"),
            "expand_right": self._to_optional_str(options, "expand_right"),
        }

        return await self._submit_task(
            endpoint="/api/submit_seamless_task",
            payload=payload,
            image_bytes=image_bytes,
            original_filename=original_filename,
        )

    async def _submit_task(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        image_bytes: bytes,
        original_filename: str,
    ) -> str:
        self._ensure_credentials()

        upload_name = original_filename or "upload.png"
        content_type = mimetypes.guess_type(upload_name)[0] or "application/octet-stream"

        form_data = {"user_key": self.api_key}
        form_data.update({k: v for k, v in payload.items() if v not in (None, "")})

        files = {
            "input_image": (upload_name, image_bytes, content_type),
        }

        logger.info("Submitting GQCH task to %s", endpoint)
        submit_response = await self._request(endpoint, form_data, files)

        task_id = submit_response.get("task_id")
        if not task_id:
            raise Exception("GQCH 接口未返回任务ID")

        status_payload = await self._poll_task_status(task_id)
        return self._extract_result_urls(status_payload)

    async def _poll_task_status(self, task_id: str) -> Dict[str, Any]:
        logger.info("Polling GQCH task status: %s", task_id)

        data = {
            "user_key": self.api_key,
            "task_id": task_id,
        }

        max_attempts = 80  # ~4分钟
        for attempt in range(max_attempts):
            if attempt > 0:
                await asyncio.sleep(3)

            status_response = await self._request("/api/check_task_status", data, files=None, timeout=120.0)
            status_value = str(status_response.get("status", "")).lower()

            if status_value in {"completed", "success", "done"}:
                logger.info("GQCH task %s completed", task_id)
                return status_response

            if status_value in {"failed", "error", "expired"}:
                message = status_response.get("err_msg") or "GQCH 任务处理失败"
                raise Exception(message)

        raise Exception("GQCH 任务处理超时，请稍后在历史记录中查看")

    def _extract_result_urls(self, payload: Dict[str, Any]) -> str:
        candidates: List[str] = []

        primary_url = payload.get("images_url")
        if isinstance(primary_url, str) and primary_url.strip():
            candidates.append(primary_url.strip())

        multi_urls = payload.get("images_urls")
        if isinstance(multi_urls, (list, tuple)):
            for item in multi_urls:
                if isinstance(item, str) and item.strip():
                    candidates.append(item.strip())

        for extra_key in ("images_url_1m", "grid_url", "vector_url"):
            extra_url = payload.get(extra_key)
            if isinstance(extra_url, str) and extra_url.strip():
                candidates.append(extra_url.strip())

        if not candidates:
            raise Exception("GQCH 任务未返回可用的结果链接")

        # 去重，保持顺序
        unique_urls: List[str] = []
        seen = set()
        for url in candidates:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return ",".join(unique_urls)

    @staticmethod
    def _to_optional_str(options: Optional[Dict[str, Any]], key: str) -> Optional[str]:
        if not options:
            return None
        value = options.get(key)
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed if trimmed else None
        return str(value)

    @staticmethod
    def _trimmed_or_none(options: Optional[Dict[str, Any]], key: str) -> Optional[str]:
        if not options:
            return None
        raw = options.get(key)
        if not isinstance(raw, str):
            return None
        trimmed = raw.strip()
        return trimmed or None

