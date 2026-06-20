import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient

logger = logging.getLogger(__name__)

TUZI_GPT_IMAGE_2_VIP_MODEL = "gpt-image-2-vip"


class TuziOpenAIClient(BaseAIClient):
    """Tuzi OpenAI-compatible image client for gpt-image-2-vip."""

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
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("Tuzi gpt-image-2-vip API未配置")

        resolved_model = (
            model.strip()
            if isinstance(model, str) and model.strip()
            else TUZI_GPT_IMAGE_2_VIP_MODEL
        )
        image_format = "PNG" if mime_type == "image/png" else "JPEG"
        image_base64 = self._image_to_base64(image_bytes, image_format)

        data: Dict[str, Any] = {
            "model": resolved_model,
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

        logger.info("Editing image with Tuzi OpenAI model %s", resolved_model)
        return await self._make_request("POST", "/chat/completions", data)

    def extract_image_url(self, api_response: Dict[str, Any]) -> str:
        return self._extract_image_url(api_response)
