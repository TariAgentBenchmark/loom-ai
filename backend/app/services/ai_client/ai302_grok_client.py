import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.utils.ai302_urls import rewrite_ai302_file_url

logger = logging.getLogger(__name__)


class AI302GrokClient(BaseAIClient):
    """302.AI xAI Grok image edit client."""

    _ASYNC_RESULT_ENDPOINT = "/302/submit/grok-imagine-image"
    _PENDING_STATUSES = {
        "pending",
        "processing",
        "running",
        "queued",
        "submitted",
        "starting",
    }
    _COMPLETED_STATUSES = {
        "completed",
        "complete",
        "succeeded",
        "success",
        "done",
        "finished",
    }
    _FAILED_STATUSES = {
        "failed",
        "failure",
        "error",
        "cancelled",
        "canceled",
        "rejected",
    }
    _REQUEST_ID_KEYS = (
        "request_id",
        "requestId",
        "requestID",
        "id",
        "task_id",
        "taskId",
    )
    _IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

    def __init__(self):
        super().__init__(api_name="ai302_grok")
        self.base_url = settings.ai302_base_url.rstrip("/")
        self.api_key = settings.ai302_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _is_public_http_url(image_url: Optional[str]) -> bool:
        if not image_url or not isinstance(image_url, str):
            return False

        parsed = urlparse(image_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False

        host = (parsed.hostname or "").lower()
        if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
            return False
        if host.endswith(".local"):
            return False
        return True

    @classmethod
    def _normalize_image_url(
        cls,
        value: Any,
        *,
        require_image_like: bool = False,
    ) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None

        url = value.strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None

        if require_image_like and not parsed.path.lower().endswith(cls._IMAGE_EXTENSIONS):
            return None

        return rewrite_ai302_file_url(url) or url

    @classmethod
    def _find_image_url(
        cls,
        value: Any,
        *,
        in_image_context: bool = False,
    ) -> Optional[str]:
        """Extract image URLs from documented and observed 302.AI response shapes."""
        if isinstance(value, str):
            return cls._normalize_image_url(value, require_image_like=not in_image_context)

        if isinstance(value, list):
            for item in value:
                url = cls._find_image_url(item, in_image_context=in_image_context)
                if url:
                    return url
            return None

        if not isinstance(value, dict):
            return None

        # Official async V2 fetch schema uses image_url / image_urls.
        for key in ("image_url", "imageUrl", "output_url", "outputUrl"):
            url = cls._normalize_image_url(value.get(key), require_image_like=False)
            if url:
                return url

        for key in ("image_urls", "imageUrls", "output_urls", "outputUrls"):
            urls = value.get(key)
            if isinstance(urls, list):
                for item in urls:
                    url = cls._normalize_image_url(item, require_image_like=False)
                    if url:
                        return url

        # Official Grok sync schema uses images: [{url: ...}]. OpenAI-like schemas use data.
        for key in ("images", "data"):
            url = cls._find_image_url(value.get(key), in_image_context=True)
            if url:
                return url

        # Some wrappers put the final payload under result/output/response.
        for key in ("result", "results", "output", "outputs", "response"):
            url = cls._find_image_url(value.get(key), in_image_context=in_image_context)
            if url:
                return url

        # Some async APIs store the provider payload as a JSON string.
        raw_response = value.get("raw_response")
        if isinstance(raw_response, str) and raw_response.strip():
            try:
                parsed = json.loads(raw_response)
            except json.JSONDecodeError:
                parsed = None
            if parsed is not None:
                url = cls._find_image_url(parsed, in_image_context=in_image_context)
                if url:
                    return url

        # Only accept a generic url field if it is in an image/data context or looks image-like.
        url = cls._normalize_image_url(
            value.get("url"),
            require_image_like=not in_image_context,
        )
        if url:
            return url

        return None

    @classmethod
    def _extract_request_id(cls, value: Any) -> Optional[str]:
        """Find the request_id needed by the official Grok result endpoint."""
        if isinstance(value, list):
            for item in value:
                request_id = cls._extract_request_id(item)
                if request_id:
                    return request_id
            return None

        if not isinstance(value, dict):
            return None

        for key in cls._REQUEST_ID_KEYS:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()

        for key in ("data", "result", "response", "output"):
            request_id = cls._extract_request_id(value.get(key))
            if request_id:
                return request_id

        return None

    @staticmethod
    def _extract_status(api_response: Dict[str, Any]) -> str:
        status = api_response.get("status")
        if isinstance(status, str):
            return status.strip().lower()
        data = api_response.get("data")
        if isinstance(data, dict) and isinstance(data.get("status"), str):
            return data["status"].strip().lower()
        return ""

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    async def edit_image(
        self,
        *,
        image_url: str,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        output_format: str = "jpeg",
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("302.AI Grok API未配置")
        if not self._is_public_http_url(image_url):
            raise ValueError("302.AI Grok 需要公网可访问的 image_url")

        data: Dict[str, Any] = {
            "image_url": image_url,
            "prompt": prompt,
            "output_format": output_format,
        }
        if aspect_ratio:
            data["aspect_ratio"] = aspect_ratio

        logger.info(
            "Editing image with 302.AI Grok: aspect_ratio=%s, image_url=%s",
            aspect_ratio,
            image_url,
        )
        response = await self._make_request(
            "POST",
            "/302/submit/grok-imagine-image-edit",
            data,
        )

        if self._find_image_url(response):
            return response

        request_id = self._extract_request_id(response)
        if not request_id:
            return response

        logger.info(
            "302.AI Grok returned async request_id=%s; polling official result endpoint",
            request_id,
        )
        return await self._poll_image_result(request_id)

    async def _poll_image_result(self, request_id: str) -> Dict[str, Any]:
        """Poll 302.AI's documented Grok result endpoint until an image is available."""
        timeout_seconds = max(1.0, float(settings.ai302_grok_poll_timeout_seconds))
        interval_seconds = max(0.5, float(settings.ai302_grok_poll_interval_seconds))
        deadline = time.monotonic() + timeout_seconds
        attempt = 0

        while True:
            attempt += 1
            last_response = await self._make_request(
                "GET",
                self._ASYNC_RESULT_ENDPOINT,
                None,
                params={"request_id": request_id},
            )

            if self._find_image_url(last_response):
                logger.info(
                    "302.AI Grok async request_id=%s completed after %s polls",
                    request_id,
                    attempt,
                )
                return last_response

            status = self._extract_status(last_response)
            if status in self._FAILED_STATUSES:
                raise ValueError(
                    f"302.AI Grok async task failed: request_id={request_id}, status={status}"
                )
            if status in self._COMPLETED_STATUSES:
                raise ValueError(
                    "302.AI Grok async task completed without image url: "
                    f"request_id={request_id}, status={status}"
                )

            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(
                    f"302.AI Grok async task timed out after {timeout_seconds:.0f}s: "
                    f"request_id={request_id}, status={status or 'unknown'}"
                )

            if status and status not in self._PENDING_STATUSES:
                logger.info(
                    "302.AI Grok async request_id=%s returned status=%s without image; "
                    "polling again",
                    request_id,
                    status,
                )

            await asyncio.sleep(min(interval_seconds, max(0.0, deadline - now)))

    @classmethod
    def extract_image_url(cls, api_response: Dict[str, Any]) -> str:
        url = cls._find_image_url(api_response)
        if url:
            return url

        raise ValueError("302.AI Grok response missing image url")
