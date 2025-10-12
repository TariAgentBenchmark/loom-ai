import asyncio
import base64
import logging
import os
import uuid
from io import BytesIO
from random import uniform
from typing import Any, Dict, List, Optional

import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseAIClient:
    """基础AI客户端，提供通用功能"""
    
    def __init__(self):
        self.base_url = settings.tuzi_base_url
        self.api_key = settings.tuzi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text
                if 500 <= status < 600 and attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "AI API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"AI API request failed: {status} - {body}")
                raise Exception(f"AI服务请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "AI API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"AI API request error: {str(exc)}")
                raise Exception(f"AI服务连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("AI服务连接失败: 未知错误")

    def _image_to_base64(self, image_bytes: bytes, format: str = "JPEG") -> str:
        """将图片字节转换为base64编码"""
        try:
            # 使用PIL处理图片
            image = Image.open(BytesIO(image_bytes))
            
            # 如果是RGBA模式且要转换为JPEG，需要转换为RGB
            if image.mode == "RGBA" and format.upper() == "JPEG":
                # 创建白色背景
                background = Image.new("RGB", image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                image = background
            
            # 转换为字节
            buffer = BytesIO()
            image.save(buffer, format=format, quality=95)
            image_bytes = buffer.getvalue()
            
            # 编码为base64
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Image to base64 conversion failed: {str(e)}")
            raise Exception(f"图片格式转换失败: {str(e)}")

    async def _download_image_from_url(self, url: str) -> bytes:
        """从URL下载图片"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.content
        except Exception as e:
            logger.error(f"Failed to download image from URL {url}: {str(e)}")
            raise Exception(f"下载图片失败: {str(e)}")

    def _extract_image_url(self, api_response: Dict[str, Any]) -> str:
        """从API响应中提取图片URL"""
        try:
            # GPT-4o响应格式
            if "data" in api_response and isinstance(api_response["data"], list):
                return api_response["data"][0]["url"]
            
            # Gemini响应格式 (需要根据实际响应调整)
            if "candidates" in api_response:
                # 这里需要根据Gemini的实际响应格式调整
                # 假设响应中包含生成的图片URL或base64数据
                candidate = api_response["candidates"][0]
                if "content" in candidate:
                    # 处理Gemini的响应格式
                    return self._process_gemini_response(candidate["content"])
            
            # 如果是base64格式，需要保存为文件并返回URL
            if "image" in api_response:
                return self._save_base64_image(api_response["image"])
                
            raise Exception("无法从AI响应中提取图片")
            
        except Exception as e:
            logger.error(f"Failed to extract image URL: {str(e)}")
            raise Exception(f"处理AI响应失败: {str(e)}")

    def _extract_image_urls(self, api_response: Dict[str, Any]) -> List[str]:
        """从API响应中提取多张图片URL"""
        try:
            # GPT-4o响应格式 - 返回多张图片
            if "data" in api_response and isinstance(api_response["data"], list):
                return [item["url"] for item in api_response["data"]]
            
            # Gemini响应格式 - 目前只支持单张
            if "candidates" in api_response:
                candidate = api_response["candidates"][0]
                if "content" in candidate:
                    return [self._process_gemini_response(candidate["content"])]
            
            # 如果是base64格式
            if "image" in api_response:
                return [self._save_base64_image(api_response["image"])]
                
            raise Exception("无法从AI响应中提取图片")
            
        except Exception as e:
            logger.error(f"Failed to extract image URLs: {str(e)}")
            raise Exception(f"处理AI响应失败: {str(e)}")

    def _process_gemini_response(self, content: Dict[str, Any]) -> str:
        """处理Gemini响应内容"""
        logger.debug(content)
        try:
            parts: List[Dict[str, Any]] = content.get("parts", []) if isinstance(content, dict) else []

            for part in parts:
                if not isinstance(part, dict):
                    continue

                # 处理文本中的图片链接
                if "text" in part:
                    text = part["text"]
                    if isinstance(text, str):
                        # 查找markdown格式的图片链接 ![image](url)
                        import re
                        image_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
                        matches = re.findall(image_pattern, text)
                        if matches:
                            image_url = matches[0]
                            logger.info("Found image URL in Gemini text response: %s", image_url)
                            return image_url

                # 处理内联数据 - 支持两种格式: inline_data 和 inlineData
                inline_data = part.get("inline_data") or part.get("inlineData")
                if inline_data:
                    if not isinstance(inline_data, dict):
                        continue
                    # 支持两种格式: data 和 base64 编码的数据
                    data = inline_data.get("data")
                    if not data:
                        continue
                    logger.info("Found inline image data in Gemini response")
                    return self._save_base64_image(data)

                # 处理fileData结构 - Gemini图片通常以文件形式返回
                file_data = part.get("fileData") or part.get("file_data")
                if isinstance(file_data, dict):
                    file_uri = file_data.get("fileUri") or file_data.get("file_uri")
                    if isinstance(file_uri, str) and file_uri:
                        logger.info("Gemini response contains file data uri: %s", file_uri)
                        return file_uri
                    # 某些情况下文件数据可能内联返回
                    inline_data = file_data.get("inlineData") or file_data.get("inline_data")
                    if isinstance(inline_data, dict):
                        data = inline_data.get("data")
                        if data:
                            logger.info("Gemini response contains file data inline image")
                            return self._save_base64_image(data)

                # 处理文件URI
                if "file_uri" in part or "fileUri" in part:
                    file_uri = part.get("file_uri") or part.get("fileUri")
                    if isinstance(file_uri, str):
                        logger.info("Gemini response contains file uri: %s", file_uri)
                        return file_uri

            raise Exception("AI响应缺少可用的图片数据")

        except Exception as exc:
            logger.error(f"Gemini response parsing failed: {str(exc)}")
            raise Exception(f"AI响应解析失败: {str(exc)}")

    def _save_base64_image(self, base64_data: str) -> str:
        """保存base64图片并返回URL"""
        try:
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 生成文件名
            filename = f"ai_result_{uuid.uuid4().hex[:8]}.png"
            file_path = f"{settings.upload_path}/results/{filename}"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            # 返回访问URL
            return f"/files/results/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save base64 image: {str(e)}")
            raise Exception(f"保存图片失败: {str(e)}")