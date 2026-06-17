from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.ai_client.zfy_vectorizer_client import ZfyVectorizerClient


class VectorizerClient:
    """兼容旧 VectorizerClient 名称，内部使用 zifeiyu /add_task 协议。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        zfy_client: Optional[ZfyVectorizerClient] = None,
    ):
        self.zfy_client = zfy_client or ZfyVectorizerClient(
            base_url=base_url,
            api_key=api_key,
        )
        self.vectorizer_url = f"{self.zfy_client.base_url}/add_task"

    @staticmethod
    def _extract_format(options: Optional[Dict[str, Any]]) -> str:
        opts = options or {}
        vector_format = (
            opts.get("vectorFormat")
            or opts.get("vectorformat")
            or opts.get("format")
            or opts.get("fmt")
            or settings.vectorizer_default_format
            or ".eps"
        )
        return str(vector_format).lstrip(".").lower()

    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化 - 使用新版 /add_task、/try_get、/get_image 调用协议。"""
        opts = options or {}
        return await self.zfy_client.image_to_vector(
            image_bytes,
            fmt=self._extract_format(opts),
            filename=opts.get("original_filename") or opts.get("filename"),
        )
