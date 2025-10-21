import logging
import os
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ai_client.gemini_client import GeminiClient
from app.services.ai_client.gpt4o_client import GPT4oClient
from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient

logger = logging.getLogger(__name__)


class ImageProcessingUtils:
    """图片处理工具类"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.gpt4o_client = GPT4oClient()
        self.apyi_gemini_client = ApyiGeminiClient()
    
    async def seamless_pattern_conversion(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI四方连续转换"""
        prompt = """基于这张图片，生成一个新的四方连续循环图案，适合大面积印花使用，图案可无缝拼接。请生成高质量的图片。"""

        result = await self.apyi_gemini_client.process_image(image_bytes, prompt, "image/png")
        return self.apyi_gemini_client._extract_image_url(result)

    async def prompt_edit_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """根据自然语言指令编辑图片"""
        options = options or {}
        instruction = (options.get("instruction") or "").strip()
        if not instruction:
            raise Exception("请提供修改指令")

        model_choice = (options.get("model") or "new").strip().lower()
        if model_choice not in {"new", "original"}:
            model_choice = "new"

        if model_choice == "original":
            prefix = (
                "你是一名专业的服装与电商图片修图师，偏好保守的风格调整，"
                "执行时保持原图细节与主体结构稳定，不引入额外装饰。"
            )
        else:
            prefix = (
                "你是一名专业的图像编辑AI助手，使用最新的模型快速响应用户需求，"
                "在保证人物和主体自然的前提下，可以适度进行创造性调整。"
            )

        prompt = (
            f"{prefix}\n"
            "请仔细阅读用户的中文指令，根据指令对上传的图片进行精准修改并生成新的图片。"
            "确保修改区域自然融入，避免出现明显的编辑痕迹或违背常识的结果。\n"
            f"用户指令：{instruction}"
        )

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        result = await self.apyi_gemini_client.process_image(
            image_bytes,
            prompt,
            "image/png",
            aspect_ratio=aspect_ratio,
            width=width,
            height=height
        )
        return self.apyi_gemini_client._extract_image_url(result)

    async def extract_pattern(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI提取花型
        
        注意：当pattern_type为"fine"时，返回的字符串是逗号分隔的多个URL
        """
        options = options or {}
        pattern_type = options.get("pattern_type", "general")
        
        # 根据不同的花型类型使用不同的提示词
        if pattern_type == "positioning":
            # 定位花类型
            prompt = (
                "衣服的图案展开平铺。将图案设计的风格和内容元索还原为填充整个画面的平面印刷图像，"
                "将图案所有设计元素和形状：比例、位置、形态完全匹配。去掉皱褶，干净底色，增强细节，"
                "以你的能力极限生成一张超高清8K分辨率、锐利对焦, 超高清、高度详细, 复杂的细节、"
                "杰作，最高品质，照片级写实的印刷级品质无缝图案。"
                "特写镜头, 放大视角，平滑，矢量风格，无颗粒感，无模糊。1:1"
            )
        elif pattern_type == "fine":
            # 精细效果类型
            prompt = (
                "从提供的图片中严格提取图案，生成新的平面印刷图像，将图案设计的风格和内容元索还原为填充整个画面的平面印刷图像，"
                "准确识别并完整还原图案、纹理、颜色,等设计元素。请生成高质量的图片。1:1"
            )
        else:
            # 通用类型（默认）
            prompt = (
                "从提供的图片中严格提取图案并生成高质量的图片，准确识别并完整还原图案、纹理、等设计元素，确保没有任何遗漏或扭曲。去除褶皱。亮丽的颜色别丢掉了。还原为填充整个画面的平面印刷图像。花位不要铺太大了。"
            )

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        # 精细效果类型使用GPT-4o模型，生成2张图片
        if pattern_type == "fine":
            result = await self.gpt4o_client.process_image(image_bytes, prompt, "image/png", n=2)
            image_urls = self.gpt4o_client._extract_image_urls(result)
            # 返回逗号分隔的URL字符串
            return ",".join(image_urls)
        else:
            result = await self.apyi_gemini_client.process_image(
                image_bytes,
                prompt,
                "image/png",
                aspect_ratio=aspect_ratio,
                width=width,
                height=height
            )
            return self.apyi_gemini_client._extract_image_url(result)

    async def denoise_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI布纹去噪"""
        options = options or {}
        prompt = "Generate a new image by removing the fabric texture from this image, make the surface smooth while preserving the original color tone and overall appearance as much as possible."

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        result = await self.apyi_gemini_client.process_image(
            image_bytes,
            prompt,
            "image/png",
            aspect_ratio=aspect_ratio,
            width=width,
            height=height
        )
        return self.apyi_gemini_client._extract_image_url(result)
