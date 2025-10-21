import logging
from typing import Any, Dict, Optional

from app.services.ai_client.base_client import BaseAIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class ApyiGeminiClient(BaseAIClient):
    """Apyi Gemini API客户端，支持自定义分辨率和宽高比"""

    # 支持的宽高比列表
    SUPPORTED_ASPECT_RATIOS = [
        "21:9", "16:9", "4:3", "3:2", "1:1",
        "9:16", "3:4", "2:3", "5:4", "4:5"
    ]

    def __init__(self):
        """初始化Apyi客户端"""
        self.base_url = settings.apiyi_base_url
        self.api_key = settings.apiyi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def process_image(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        aspect_ratio: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        使用Apyi平台的Gemini-2.5-flash-image处理图片

        Args:
            image_bytes: 图片字节数据
            prompt: 编辑指令文本
            mime_type: 图片MIME类型
            aspect_ratio: 宽高比 (如 "16:9", "1:1" 等)
            width: 自定义宽度 (像素)
            height: 自定义高度 (像素)

        Returns:
            API响应数据
        """
        endpoint = "/v1beta/models/gemini-2.5-flash-image:generateContent"

        # 转换图片为base64
        image_base64 = self._image_to_base64(image_bytes,
                                           "PNG" if mime_type == "image/png" else "JPEG")

        # 构建请求数据
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"]
            }
        }

        # 添加图片配置
        image_config = {}

        # 优先使用宽高比配置
        if aspect_ratio:
            if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
                logger.warning(f"不支持的宽高比: {aspect_ratio}，使用默认设置")
            else:
                image_config["aspectRatio"] = aspect_ratio
                logger.info(f"使用宽高比: {aspect_ratio}")

        # 如果指定了自定义尺寸，则覆盖宽高比设置
        if width and height:
            image_config["width"] = width
            image_config["height"] = height
            logger.info(f"使用自定义尺寸: {width}x{height}")

        # 如果有图片配置，添加到generationConfig中
        if image_config:
            data["generationConfig"]["imageConfig"] = image_config

        logger.info(f"Processing image with Apyi Gemini: {prompt[:100]}...")
        logger.info(f"Image config: {image_config}")

        return await self._make_request("POST", endpoint, data)

    def validate_aspect_ratio(self, aspect_ratio: str) -> bool:
        """验证宽高比是否支持"""
        return aspect_ratio in self.SUPPORTED_ASPECT_RATIOS

    def get_supported_aspect_ratios(self) -> list:
        """获取支持的宽高比列表"""
        return self.SUPPORTED_ASPECT_RATIOS.copy()
