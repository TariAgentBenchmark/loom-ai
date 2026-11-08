import base64
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.api_limiter import api_limiter
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)

TUZI_GPT_IMAGE_2_VIP_MODEL = "gpt-image-2-vip"
TUZI_GPT_IMAGE_2_MODEL = "gpt-image-2"


class TuziOpenAIClient(BaseAIClient):
    """Tuzi OpenAI-compatible image client for GPT Image 2 channels."""

    def __init__(self):
        super().__init__(api_name="tuzi_openai")
        self.base_url = f"{settings.tuzi_base_url.rstrip('/')}/v1"
        self.api_key = settings.tuzi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    async def edit_image(
        self,
        *,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        model: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("Tuzi gpt-image-2-vip API未配置")

        resolved_model = (
            model.strip()
            if isinstance(model, str) and model.strip()
            else TUZI_GPT_IMAGE_2_VIP_MODEL
        )
        if resolved_model == TUZI_GPT_IMAGE_2_MODEL:
            # Standard GPT Image 2 rejects Chat Completions. Upload a real file
            # through Images Edits; keep the VIP protocol unchanged pending diagnosis.
            normalized_png = base64.b64decode(
                self._image_to_base64(image_bytes, "PNG")
            )
            form = {
                "model": resolved_model,
                "prompt": prompt,
                "n": "1",
                "response_format": "b64_json",
            }
            if isinstance(quality, str) and quality.strip():
                form["quality"] = quality.strip()
            return await self._make_image_edit_request(normalized_png, form)

        image_format = "PNG" if mime_type == "image/png" else "JPEG"
        image_base64 = self._image_to_base64(image_bytes, image_format)

        data: Dict[str, Any] = {
            "model": resolved_model,
            # 接口文档要求必传 stream；固定 False 避免上游按 SSE 流式返回导致同步解析失败
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                            },
                        },
                    ],
                }
            ],
        }

        if isinstance(quality, str) and quality.strip():
            data["quality"] = quality.strip()

        logger.info("Editing image with Tuzi OpenAI model %s", resolved_model)
        return await self._make_request("POST", "/chat/completions", data)

    async def _make_image_edit_request(
        self, image_bytes: bytes, data: Dict[str, str],
    ) -> Dict[str, Any]:
        endpoint = "/images/edits"
        url = f"{self.base_url}{endpoint}"
        context = {
            **data,
            "endpoint": endpoint,
            "image": {"filename": "image.png", "mimeType": "image/png", "bytes": len(image_bytes)},
        }

        async def request() -> Dict[str, Any]:
            # A timed-out paid POST may still be processing upstream. Do not
            # blindly retry submission and risk generating/charging twice.
            try:
                async with httpx.AsyncClient(
                    timeout=getattr(self, "request_timeout", 300.0),
                ) as client:
                    response = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files={"image": ("image.png", image_bytes, "image/png")},
                        data=data,
                    )
                    response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise AIClientException(
                    message=f"Tuzi图片编辑请求失败: {exc.response.status_code}",
                    api_name=self.api_name,
                    status_code=exc.response.status_code,
                    response_body=exc.response.text[:2000],
                    request_data=context,
                ) from exc
            except httpx.RequestError as exc:
                raise AIClientException(
                    message=f"Tuzi图片编辑连接失败: {exc}",
                    api_name=self.api_name,
                    request_data=context,
                ) from exc

            try:
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError("图片接口返回的不是JSON对象")
                return result
            except ValueError as exc:
                raise AIClientException(
                    message=f"Tuzi图片编辑响应解析失败: {exc}",
                    api_name=self.api_name,
                    status_code=response.status_code,
                    response_body=response.text[:2000],
                    request_data=context,
                ) from exc

        logger.info("Editing image with Tuzi Images API model=%s", data["model"])
        return await api_limiter.run(self.api_name, request)

    def extract_image_url(self, api_response: Dict[str, Any]) -> str:
        return self._extract_image_url(api_response)
