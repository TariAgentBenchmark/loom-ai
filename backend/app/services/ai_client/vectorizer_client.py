import logging
import uuid
from io import BytesIO
from typing import Any, Dict, Optional

import httpx
from app.core.config import settings
from app.services.file_service import FileService
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class VectorizerClient:
    """Vectorizer.ai API客户端"""

    def __init__(self):
        self.vectorizer_api_key = settings.vectorizer_api_key
        self.vectorizer_api_secret = settings.vectorizer_api_secret
        self.vectorizer_url = "https://vectorizer.ai/api/v1/vectorize"

    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG) - 使用Vectorizer.ai API"""
        try:
            # 准备文件数据
            files = {
                'image': ('image.jpeg', BytesIO(image_bytes))
            }

            # 准备认证信息
            auth = (self.vectorizer_api_key, self.vectorizer_api_secret)

            # 准备请求数据
            data = {}

            # 如果提供了额外选项，添加到请求中
            if options:
                # Vectorizer.ai支持的各种选项
                if 'mode' in options:
                    data['mode'] = options['mode']
                if 'colors' in options:
                    data['colors'] = options['colors']
                if 'filter_speckle' in options:
                    data['filter_speckle'] = options['filter_speckle']
                if 'corners_threshold' in options:
                    data['corners_threshold'] = options['corners_threshold']
                if 'iterations' in options:
                    data['iterations'] = options['iterations']
                if 'layering' in options:
                    data['layering'] = options['layering']
                if 'pathsimplify' in options:
                    data['pathsimplify'] = options['pathsimplify']

            logger.info("Sending request to Vectorizer.ai API")

            # 发送请求
            try:
                async with api_limiter.slot("vectorizer"):
                    async with httpx.AsyncClient(timeout=300.0) as client:
                        response = await client.post(
                            self.vectorizer_url,
                            files=files,
                            data=data,
                            auth=auth
                        )
                        response.raise_for_status()

                        # 保存结果为SVG文件，默认走OSS
                        filename = f"vectorized_{uuid.uuid4().hex[:8]}.svg"
                        file_service = FileService()
                        saved_url = await file_service.save_upload_file(
                            response.content,
                            filename,
                            subfolder="results",
                        )
                        logger.info("SVG file saved to storage: %s", saved_url)
                        return saved_url
            except httpx.HTTPStatusError as e:
                raise AIClientException(
                    message=f"Vectorizer请求失败: {e.response.status_code}",
                    api_name="Vectorizer",
                    status_code=e.response.status_code,
                    response_body=e.response.text,
                    request_data=options or {},
                ) from e
            except httpx.RequestError as e:
                raise AIClientException(
                    message=f"Vectorizer网络错误: {str(e)}",
                    api_name="Vectorizer",
                    request_data=options or {},
                ) from e

        except AIClientException:
            raise
        except Exception as e:
            logger.error(f"Vectorize image failed: {str(e)}")
            raise AIClientException(
                message=f"矢量化失败: {str(e)}",
                api_name="Vectorizer",
            ) from e
