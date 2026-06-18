import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class HaoeeGeminiClient(BaseAIClient):
    """Haoee MaaS Gemini 图像模型客户端。"""

    GEMINI_3_PRO_ROUTE_MODEL = "gemini-3-pro-image-preview"

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
        super().__init__(api_name="haoee_maas")
        self.base_url = (
            settings.haoee_maas_base_url or "https://maas.haoee.com"
        ).rstrip("/")
        self.api_key = settings.haoee_maas_api_key
        # 4K image generation can exceed the generic 300s client timeout.
        self.request_timeout = 650.0
        self.max_retries = 1
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _ensure_credentials(self) -> None:
        if not self.api_key:
            raise AIClientException(
                message="Haoee MaaS API密钥未配置，请在环境变量中设置HAOEE_MAAS_API_KEY",
                api_name="haoee_maas",
            )

    async def generate_image_preview(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """调用 Haoee MaaS Gemini preview 模型生成图片。"""
        self._ensure_credentials()

        resolved_model_name = (
            model_name.strip()
            if isinstance(model_name, str) and model_name.strip()
            else settings.haoee_maas_default_preview_model
            or "gemini-3-pro-image-preview-lite"
        )
        endpoint_model_name = self._resolve_endpoint_model(resolved_model_name)
        endpoint = f"/v1beta/models/{endpoint_model_name}:generateContent"
        image_base64 = self._image_to_base64(
            image_bytes,
            "PNG" if mime_type == "image/png" else "JPEG",
        )

        data: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
            },
        }

        image_config: Dict[str, Any] = {}
        if aspect_ratio:
            if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
                logger.warning(
                    "Haoee MaaS 不支持的宽高比: %s，使用默认设置",
                    aspect_ratio,
                )
            else:
                image_config["aspectRatio"] = aspect_ratio

        if resolution:
            normalized_resolution = resolution.upper()
            if normalized_resolution not in {"1K", "2K", "4K"}:
                logger.warning(
                    "Haoee MaaS 不支持的分辨率: %s，跳过自定义分辨率",
                    resolution,
                )
            else:
                image_config["imageSize"] = normalized_resolution

        if image_config:
            data["generationConfig"]["imageConfig"] = image_config

        logger.info(
            "Processing image with Haoee MaaS preview model %s: aspect_ratio=%s, resolution=%s",
            resolved_model_name,
            image_config.get("aspectRatio"),
            image_config.get("imageSize"),
        )
        return await self._make_request(
            "POST",
            endpoint,
            data,
            headers={"ModelName": resolved_model_name},
        )

    @classmethod
    def _resolve_endpoint_model(cls, model_name: str) -> str:
        """Haoee registers Gemini 3 Pro image variants under the base route."""
        if model_name.startswith(cls.GEMINI_3_PRO_ROUTE_MODEL):
            return cls.GEMINI_3_PRO_ROUTE_MODEL
        return model_name
