import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class AI302GrokClient(BaseAIClient):
    """302.AI xAI Grok image edit client."""

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
        return await self._make_request(
            "POST",
            "/302/submit/grok-imagine-image-edit",
            data,
        )

    @staticmethod
    def extract_image_url(api_response: Dict[str, Any]) -> str:
        images = api_response.get("images")
        if isinstance(images, list):
            for item in images:
                if not isinstance(item, dict):
                    continue
                url = item.get("url")
                if isinstance(url, str) and url.strip():
                    return url.strip()

        data = api_response.get("data")
        if isinstance(data, dict):
            nested_images = data.get("images")
            if isinstance(nested_images, list):
                for item in nested_images:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url")
                    if isinstance(url, str) and url.strip():
                        return url.strip()

        raise ValueError("302.AI Grok response missing image url")
