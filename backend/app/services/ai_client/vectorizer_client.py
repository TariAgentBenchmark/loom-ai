import logging
import os
import uuid
from typing import Any, Dict, Optional

from app.core.config import settings
from app.services.ai_client.a8_vectorizer_client import A8VectorizerClient

logger = logging.getLogger(__name__)


class VectorizerClient:
    """矢量化服务客户端"""

    def __init__(self) -> None:
        self.a8_client = A8VectorizerClient()

    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG/EPS) - 使用A8矢量化服务"""
        try:
            options = options or {}

            source_filename = options.get("filename", "image.png")

            result = await self.a8_client.vectorize(
                image_bytes,
                filename=source_filename,
                timeout=options.get("timeout"),
                poll_interval=options.get("poll_interval"),
            )

            extension = result.extension or "svg"
            filename = f"vectorized_{uuid.uuid4().hex[:8]}.{extension}"
            file_path = os.path.join(settings.upload_path, "results", filename)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as output_file:
                output_file.write(result.content)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                logger.info(
                    "Vector file saved successfully: %s, size: %s bytes (type: %s)",
                    file_path,
                    file_size,
                    extension,
                )
            else:
                logger.error("Failed to save vector file: %s", file_path)

            return f"/files/results/{filename}"

        except Exception as e:
            logger.error("Vectorize image failed: %s", str(e))
            raise Exception(f"矢量化失败: {str(e)}")
