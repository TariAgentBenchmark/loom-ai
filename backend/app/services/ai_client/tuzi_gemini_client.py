import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class TuziGeminiClient(BaseAIClient):
    """Tuzi Gemini API客户端，仅用于保留旧站点的特定图片链路。"""

    DEFAULT_PREVIEW_MODEL = "gemini-3-pro-image-preview"
    SUPPORTED_ASPECT_RATIOS = [
        "21:9", "16:9", "4:3", "3:2", "1:1",
        "9:16", "3:4", "2:3", "5:4", "4:5",
        "1:4", "4:1", "1:8", "8:1",
    ]

    def __init__(self):
        super().__init__(api_name="")
        self.base_url = settings.tuzi_base_url
        self.api_key = settings.tuzi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_image_preview(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """使用 Tuzi 的 Gemini preview 模型生成图片。"""
        resolved_model_name = (
            model_name.strip()
            if isinstance(model_name, str) and model_name.strip()
            else self.DEFAULT_PREVIEW_MODEL
        )
        endpoint = f"/v1beta/models/{resolved_model_name}:generateContent"
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
                logger.warning("Tuzi 不支持的宽高比: %s，使用默认设置", aspect_ratio)
            else:
                image_config["aspectRatio"] = aspect_ratio

        if resolution:
            normalized_resolution = resolution.upper()
            if normalized_resolution not in {"1K", "2K", "4K"}:
                logger.warning("Tuzi 不支持的分辨率: %s，跳过自定义分辨率", resolution)
            else:
                image_config["imageSize"] = normalized_resolution

        if image_config:
            data["generationConfig"]["imageConfig"] = image_config

        logger.info(
            "Processing image with Tuzi preview model %s: aspect_ratio=%s, resolution=%s",
            resolved_model_name,
            image_config.get("aspectRatio"),
            image_config.get("imageSize"),
        )
        return await self._make_request("POST", endpoint, data)
