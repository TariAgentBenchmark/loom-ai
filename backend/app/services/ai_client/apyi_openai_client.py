import asyncio
import logging
from io import BytesIO
from typing import Any, Dict, Optional

import httpx

from app.services.ai_client.base_client import BaseAIClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class ApyiOpenAIClient(BaseAIClient):
    """Apyi OpenAI兼容API客户端，支持图像编辑和GPT-4o"""

    def __init__(self):
        """初始化Apyi OpenAI客户端"""
        self.base_url = f"{settings.apiyi_base_url}/v1"
        self.api_key = settings.apiyi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_image_edit(
        self,
        image_bytes: bytes,
        mask_bytes: bytes,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url"
    ) -> Dict[str, Any]:
        """
        使用OpenAI兼容API编辑图像

        Args:
            image_bytes: 原始图像字节数据
            mask_bytes: 遮罩图像字节数据
            prompt: 编辑指令文本
            n: 生成的图像数量，默认为1，最大为10
            size: 输出图像尺寸，支持 256x256、512x512、1024x1024
            response_format: 返回格式，url（默认）或 b64_json

        Returns:
            API响应数据
        """
        endpoint = "/images/edits"

        # 准备multipart form数据
        files = {
            'image': ('image.png', BytesIO(image_bytes), 'image/png'),
            'mask': ('mask.png', BytesIO(mask_bytes), 'image/png')
        }

        data = {
            'prompt': prompt,
            'n': str(n),
            'size': size,
            'response_format': response_format
        }

        logger.info(f"Editing image with Apyi OpenAI: {prompt[:100]}...")
        logger.info(f"Parameters: n={n}, size={size}, response_format={response_format}")

        return await self._make_multipart_request("POST", endpoint, files, data)

    async def generate_image(
        self,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url"
    ) -> Dict[str, Any]:
        """
        使用OpenAI兼容API生成图像

        Args:
            prompt: 生成指令文本
            n: 生成的图像数量，默认为1，最大为10
            size: 输出图像尺寸，支持 256x256、512x512、1024x1024
            response_format: 返回格式，url（默认）或 b64_json

        Returns:
            API响应数据
        """
        endpoint = "/images/generations"

        data = {
            "prompt": prompt,
            "n": n,
            "size": size,
            "response_format": response_format
        }

        logger.info(f"Generating image with Apyi OpenAI: {prompt[:100]}...")
        logger.info(f"Parameters: n={n}, size={size}, response_format={response_format}")

        return await self._make_request("POST", endpoint, data)

    async def chat_completion(
        self,
        messages: list,
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        使用GPT-4o进行对话补全

        Args:
            messages: 对话消息列表
            model: 模型名称，默认为 gpt-4o
            max_tokens: 最大token数
            temperature: 温度参数
            stream: 是否使用流式响应

        Returns:
            API响应数据
        """
        endpoint = "/chat/completions"

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        if max_tokens:
            data["max_tokens"] = max_tokens

        logger.info(f"Chat completion with Apyi OpenAI: model={model}, messages={len(messages)}")

        return await self._make_request("POST", endpoint, data)

    async def _make_multipart_request(
        self,
        method: str,
        endpoint: str,
        files: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送multipart/form-data请求"""
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text
                if 500 <= status < 600 and attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + asyncio.uniform(0, 0.5)
                    logger.warning(
                        "Apyi OpenAI API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Apyi OpenAI API request failed: {status} - {body}")
                raise Exception(f"Apyi OpenAI服务请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + asyncio.uniform(0, 0.5)
                    logger.warning(
                        "Apyi OpenAI API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Apyi OpenAI API request error: {str(exc)}")
                raise Exception(f"Apyi OpenAI服务连接失败: {str(exc)}")

        raise Exception("Apyi OpenAI服务连接失败: 未知错误")

    @staticmethod
    def create_mask_for_rectangle(
        image_bytes: bytes,
        bbox: tuple,
        mask_format: str = "PNG"
    ) -> bytes:
        """
        为矩形区域创建遮罩

        Args:
            image_bytes: 原始图像字节数据
            bbox: 矩形区域 (x1, y1, x2, y2)
            mask_format: 遮罩格式，默认PNG

        Returns:
            遮罩图像字节数据
        """
        from PIL import Image, ImageDraw

        # 打开原始图像获取尺寸
        original = Image.open(BytesIO(image_bytes))
        width, height = original.size

        # 创建全黑遮罩（完全不透明）
        mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(mask)

        # 在指定区域绘制透明（要编辑的部分）
        draw.rectangle(bbox, fill=(0, 0, 0, 0))

        # 保存为字节
        buffer = BytesIO()
        mask.save(buffer, format=mask_format)
        return buffer.getvalue()

    @staticmethod
    def create_mask_for_circle(
        image_bytes: bytes,
        center: tuple,
        radius: int,
        mask_format: str = "PNG"
    ) -> bytes:
        """
        为圆形区域创建遮罩

        Args:
            image_bytes: 原始图像字节数据
            center: 圆心坐标 (x, y)
            radius: 半径
            mask_format: 遮罩格式，默认PNG

        Returns:
            遮罩图像字节数据
        """
        from PIL import Image, ImageDraw

        # 打开原始图像获取尺寸
        original = Image.open(BytesIO(image_bytes))
        width, height = original.size

        # 创建遮罩
        mask = Image.new('RGBA', (width, height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(mask)

        # 绘制圆形透明区域
        x, y = center
        draw.ellipse(
            [(x - radius, y - radius),
             (x + radius, y + radius)],
            fill=(0, 0, 0, 0)
        )

        # 保存为字节
        buffer = BytesIO()
        mask.save(buffer, format=mask_format)
        return buffer.getvalue()

    @staticmethod
    def create_mask_for_object_removal(
        image_bytes: bytes,
        bbox: tuple,
        mask_format: str = "PNG"
    ) -> bytes:
        """
        为对象移除创建遮罩

        Args:
            image_bytes: 原始图像字节数据
            bbox: 对象边界框 (x1, y1, x2, y2)
            mask_format: 遮罩格式，默认PNG

        Returns:
            遮罩图像字节数据
        """
        return ApyiOpenAIClient.create_mask_for_rectangle(image_bytes, bbox, mask_format)