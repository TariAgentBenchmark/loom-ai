import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


KRAPI_BANANA_PRO_MODEL = "T香蕉pro"
KRAPI_BANANA_2_MODEL = "T香蕉2"


class KrapiGeminiClient(BaseAIClient):
    """Kr API / New API Gemini image client.

    The public Kr API model marketplace exposes Google image models such as
    ``T香蕉pro`` through the New API Gemini-compatible endpoint:
    ``/v1beta/models/{model}:generateContent``.
    """

    DEFAULT_IMAGE_MODEL = KRAPI_BANANA_PRO_MODEL
    SUPPORTED_ASPECT_RATIOS = [
        "21:9",
        "16:9",
        "4:3",
        "3:2",
        "1:1",
        "9:16",
        "3:4",
        "2:3",
        "5:4",
        "4:5",
        "1:4",
        "4:1",
        "1:8",
        "8:1",
    ]

    def __init__(self):
        super().__init__(api_name="krapi_gemini")
        self.base_url = (settings.krapi_base_url or "https://ai.krapi.cn").rstrip("/")
        self.api_key = settings.krapi_api_key
        self.default_image_model = (
            settings.krapi_default_image_model.strip()
            if isinstance(settings.krapi_default_image_model, str)
            and settings.krapi_default_image_model.strip()
            else self.DEFAULT_IMAGE_MODEL
        )
        # Image generation can be slow; keep this aligned with other Gemini image clients.
        self.request_timeout = 650.0
        self.max_retries = 1
        self.task_poll_interval_seconds = 2.0
        self.task_poll_timeout_seconds = self.request_timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ensure_credentials(self) -> None:
        if not self.api_key:
            raise AIClientException(
                message="Kr API密钥未配置，请在环境变量中设置KRAPI_API_KEY",
                api_name="krapi_gemini",
            )

    def _resolve_model_name(self, model_name: Optional[str] = None) -> str:
        return (
            model_name.strip()
            if isinstance(model_name, str) and model_name.strip()
            else self.default_image_model
        )

    def _build_endpoint(self, model_name: str) -> str:
        # Percent-encode non-ASCII model names such as "T香蕉pro" for URL safety.
        encoded_model = quote(model_name, safe="")
        return f"/v1beta/models/{encoded_model}:generateContent"

    def _build_generation_config(
        self,
        *,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        generation_config: Dict[str, Any] = {"responseModalities": ["IMAGE"]}
        image_config: Dict[str, Any] = {}

        if aspect_ratio:
            if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
                logger.warning("Kr API 不支持的宽高比: %s，使用默认设置", aspect_ratio)
            else:
                image_config["aspectRatio"] = aspect_ratio

        if resolution:
            normalized_resolution = resolution.upper()
            if normalized_resolution in {"1K", "2K", "4K"}:
                image_config["imageSize"] = normalized_resolution
            else:
                logger.warning("Kr API 不支持的分辨率: %s，跳过自定义分辨率", resolution)

        if image_config:
            generation_config["imageConfig"] = image_config
        return generation_config

    def _build_inline_image_part(self, image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
        image_base64 = self._image_to_base64(
            image_bytes,
            "PNG" if mime_type == "image/png" else "JPEG",
        )
        # New API Gemini docs use camelCase field names for inline media.
        return {
            "inlineData": {
                "mimeType": mime_type,
                "data": image_base64,
            }
        }

    def _is_image_task_response(self, response: Dict[str, Any]) -> bool:
        return (
            isinstance(response, dict)
            and response.get("object") == "image.task"
            and bool(response.get("task_id") or response.get("id"))
        )

    async def _get_image_task(self, task_id: str) -> Dict[str, Any]:
        """Fetch a Kr API async image task by public task id."""
        endpoint = f"/v1/images/tasks/{quote(task_id, safe='')}"
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise AIClientException(
                message=f"Kr API任务查询失败: {exc.response.status_code}",
                api_name="krapi_gemini",
                status_code=exc.response.status_code,
                response_body=exc.response.text,
                request_data={"task_id": task_id},
            ) from exc
        except httpx.RequestError as exc:
            raise AIClientException(
                message=f"Kr API任务查询连接失败: {str(exc)}",
                api_name="krapi_gemini",
                request_data={"task_id": task_id},
            ) from exc

    async def _poll_image_task(
        self,
        task_id: str,
        initial_response: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Poll Kr API async image task and return the final Gemini-like result."""
        deadline = time.monotonic() + self.task_poll_timeout_seconds
        response = initial_response or {}

        while True:
            status = str(response.get("status") or "").strip().lower()
            if status in {"succeeded", "success", "completed"}:
                result = response.get("result")
                if isinstance(result, dict):
                    return result
                raise AIClientException(
                    message="Kr API任务已完成但缺少图片结果",
                    api_name="krapi_gemini",
                    response_body=response,
                    request_data={"task_id": task_id},
                )

            if status in {"failed", "failure", "cancelled", "canceled", "error"}:
                error_detail = (
                    response.get("error")
                    or response.get("fail_reason")
                    or response.get("message")
                    or "未知错误"
                )
                raise AIClientException(
                    message=f"Kr API任务失败: {error_detail}",
                    api_name="krapi_gemini",
                    response_body=response,
                    request_data={"task_id": task_id},
                )

            if time.monotonic() >= deadline:
                raise AIClientException(
                    message="Kr API任务查询超时",
                    api_name="krapi_gemini",
                    response_body=response,
                    request_data={"task_id": task_id},
                )

            await asyncio.sleep(self.task_poll_interval_seconds)
            response = await self._get_image_task(task_id)

    async def _resolve_image_task_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Kr API may return an async image.task; resolve it before callers parse images."""
        if not self._is_image_task_response(response):
            return response

        task_id = str(response.get("task_id") or response.get("id") or "").strip()
        logger.info(
            "Polling Kr API image task %s (status=%s)",
            task_id,
            response.get("status"),
        )
        return await self._poll_image_task(task_id, initial_response=response)

    async def generate_image_from_text(
        self,
        prompt: str,
        *,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate an image from text with Kr API's Gemini-compatible endpoint."""
        self._ensure_credentials()
        resolved_model_name = self._resolve_model_name(model_name)
        data: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": self._build_generation_config(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
            ),
        }

        logger.info(
            "Generating image with Kr API model %s: aspect_ratio=%s resolution=%s",
            resolved_model_name,
            aspect_ratio,
            resolution,
        )
        response = await self._make_request(
            "POST",
            self._build_endpoint(resolved_model_name),
            data,
        )
        return await self._resolve_image_task_response(response)

    async def generate_image_preview(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate/edit an image using one input image and a prompt."""
        return await self.generate_image_preview_multi(
            [image_bytes],
            prompt,
            mime_type=mime_type,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            model_name=model_name,
        )

    async def generate_image_preview_multi(
        self,
        image_bytes_list: List[bytes],
        prompt: str,
        mime_type: str = "image/png",
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate/edit an image using one or more input images and a prompt."""
        self._ensure_credentials()
        if not image_bytes_list:
            raise ValueError("至少需要一张图片")

        resolved_model_name = self._resolve_model_name(model_name)
        parts: List[Dict[str, Any]] = [{"text": prompt}]
        parts.extend(
            self._build_inline_image_part(image_bytes, mime_type)
            for image_bytes in image_bytes_list
        )

        data: Dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": self._build_generation_config(
                aspect_ratio=aspect_ratio,
                resolution=resolution,
            ),
        }

        logger.info(
            "Generating image with Kr API model %s: images=%s aspect_ratio=%s resolution=%s",
            resolved_model_name,
            len(image_bytes_list),
            aspect_ratio,
            resolution,
        )
        response = await self._make_request(
            "POST",
            self._build_endpoint(resolved_model_name),
            data,
        )
        return await self._resolve_image_task_response(response)
