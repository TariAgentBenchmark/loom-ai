import asyncio
import base64
import json
import logging
from io import BytesIO
from random import uniform
from typing import Any, Dict, List, Optional

import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """AI服务客户端"""
    
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

    async def generate_image_gpt4o(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """使用GPT-4o生成图片"""
        endpoint = "/v1/images/generations"
        data = {
            "model": "gpt-4o-image-vip",
            "prompt": prompt,
            "n": 1,
            "size": size
        }
        
        logger.info(f"Generating image with GPT-4o: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)

    async def process_image_gemini(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """使用Gemini-2.5-flash-image处理图片"""
        endpoint = "/v1beta/models/gemini-2.5-flash-image:generateContent"
        
        # 转换图片为base64
        image_base64 = self._image_to_base64(image_bytes, 
                                           "PNG" if mime_type == "image/png" else "JPEG")
        
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
            ]
        }
        
        logger.info(f"Processing image with Gemini: {prompt[:100]}...")
        return await self._make_request("POST", endpoint, data)

    async def seamless_pattern_conversion(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI四方连续转换"""
        prompt = """
        将这张图片转换为可以四方连续拼接的图案。要求：
        1. 确保图案边缘可以无缝连接
        2. 保持原有图案的主要特征和风格
        3. 去除背景元素
        4. 确保完美的循环拼接效果
        5. 输出为PNG格式，保持透明背景
        
        请生成一个可以四方连续拼接的图案版本。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG)"""
        prompt = """
        将这张图片转换为矢量风格的图案：
        1. 输出风格：矢量风格，线条清晰简洁
        2. 输出比例：1:1
        3. 保持图片的主要特征和识别度
        4. 线条要清晰，颜色要准确
        5. 适合用于产品设计和印刷
        
        请生成高质量的矢量风格图案。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def extract_pattern(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI提取花型"""
        prompt = (
            "把衣服图案展开，分析图案，提炼图案，图案细节图案密度一致，去掉皱褶，无阴影。"
            "增强细节，生成8K分辨率、超高清、高细节、照片级写实的印刷级品质2D平面图案。"
            "确保生成的是一个完整的、无缺失的图案。务必确保图像中只包含图案本身，排除图案以外内容，排除生成衣服形状。"
            "只输出最终整理好的完整图案平铺图，不要输出其他内容。"
        )

        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def remove_watermark(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI智能去水印"""
        prompt = """
        去除这张图片中的水印：
        1. 水印类型：自动识别并去除所有类型的水印
        2. 保留图片的原有细节和质量
        3. 确保去除水印后图片看起来自然
        4. 不要留下水印的痕迹或空白区域
        5. 保持图片的整体美观
        
        请彻底去除水印并修复图片。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/jpeg")
        return self._extract_image_url(result)

    async def denoise_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI布纹去噪"""
        prompt = """
        去除这张图片中的布纹纹理：
        1. 重点处理：fabric类型的问题
        2. 处理模式：标准去噪处理
        3. 保持图片的主要内容和结构
        4. 提升图片的清晰度和质量
        5. 确保处理后的图片自然美观
        
        请生成清晰、高质量的图片。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

    async def enhance_embroidery(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI毛线刺绣增强"""
        prompt = """
        将这张图片转换为毛线刺绣效果：
        1. 针线类型：中等针脚，平衡的刺绣效果
        2. 针脚密度：适中的针脚密度
        3. 增强纹理细节，展现真实的毛线质感
        4. 保持原图的主体形状和轮廓
        5. 营造真实的手工刺绣效果
        6. 色彩要自然，符合毛线刺绣的特点
        
        请生成逼真的毛线刺绣效果图。
        """
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

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

    def _process_gemini_response(self, content: Dict[str, Any]) -> str:
        """处理Gemini响应内容"""
        logger.info(content)
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

                # 处理内联数据
                if "inline_data" in part:
                    inline = part["inline_data"]
                    if not isinstance(inline, dict):
                        continue
                    data = inline.get("data")
                    if not data:
                        continue
                    return self._save_base64_image(data)

                # 处理文件URI
                if "file_uri" in part:
                    file_uri = part["file_uri"]
                    if isinstance(file_uri, str):
                        logger.info("Gemini response contains file uri: %s", file_uri)
                        return file_uri

            raise Exception("Gemini响应缺少可用的图片数据")

        except Exception as exc:
            logger.error(f"Gemini response parsing failed: {str(exc)}")
            raise Exception(f"Gemini响应解析失败: {str(exc)}")

    def _save_base64_image(self, base64_data: str) -> str:
        """保存base64图片并返回URL"""
        try:
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 生成文件名
            import uuid
            filename = f"ai_result_{uuid.uuid4().hex[:8]}.png"
            file_path = f"{settings.upload_path}/results/{filename}"
            
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 保存文件
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            # 返回访问URL
            return f"/files/results/{filename}"
            
        except Exception as e:
            logger.error(f"Failed to save base64 image: {str(e)}")
            raise Exception(f"保存图片失败: {str(e)}")


# 创建全局AI客户端实例
ai_client = AIClient()
