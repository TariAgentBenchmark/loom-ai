import logging
import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ai_client.gemini_client import GeminiClient
from app.services.ai_client.gpt4o_client import GPT4oClient
from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient
from app.services.ai_client.apyi_openai_client import ApyiOpenAIClient

logger = logging.getLogger(__name__)


class ImageProcessingUtils:
    """图片处理工具类"""
    
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.gpt4o_client = GPT4oClient()
        self.apyi_gemini_client = ApyiGeminiClient()
        self.apyi_openai_client = ApyiOpenAIClient()

    async def _process_image_with_retry(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/png",
        aspect_ratio: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        max_retries: int = 3,
    ) -> str:
        """
        调用Gemini生成图片，带重试。三次均无法解析出图片URL才抛出异常。
        """
        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                result = await self.apyi_gemini_client.process_image(
                    image_bytes,
                    prompt,
                    mime_type,
                    aspect_ratio=aspect_ratio,
                    width=width,
                    height=height,
                )
                url = self.apyi_gemini_client._extract_image_url(result)
                if url:
                    return url
                last_error = Exception("Gemini返回缺少图片URL")
                logger.warning(
                    "Gemini response missing image url (attempt %s/%s): %s",
                    attempt,
                    max_retries,
                    result,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini call failed (attempt %s/%s): %s",
                    attempt,
                    max_retries,
                    str(exc),
                )
            await asyncio.sleep(0.2)

        raise Exception(f"Gemini调用失败: {last_error}")
    
    async def seamless_pattern_conversion(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI四方连续转换"""
        prompt = """生成图片：基于这张图片，生成一个新的四方连续循环图案，适合大面积印花使用，图案可无缝拼接。请生成高质量的图片。"""

        return await self._process_image_with_retry(
            image_bytes,
            prompt,
            "image/png",
        )

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
            "生成图片：\n"
            f"{prefix}\n"
            "请仔细阅读用户的中文指令，根据指令对上传的图片进行精准修改并生成新的图片。"
            "确保修改区域自然融入，避免出现明显的编辑痕迹或违背常识的结果。\n"
            f"用户指令：{instruction}"
        )

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        secondary_image_bytes = options.get("secondary_image_bytes")
        image_list: List[bytes] = [image_bytes]
        if isinstance(secondary_image_bytes, (bytes, bytearray)):
            image_list.append(bytes(secondary_image_bytes))

        last_error: Optional[Exception] = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                result = await self.apyi_gemini_client.generate_image_preview_multi(
                    image_list,
                    prompt,
                    "image/png",
                    aspect_ratio=aspect_ratio,
                    width=width,
                    height=height,
                )
                url = self.apyi_gemini_client._extract_image_url(result)
                if url:
                    return url
                last_error = Exception("Gemini返回缺少图片URL")
                logger.warning(
                    "Gemini 3 preview response missing image url (attempt %s/%s): %s",
                    attempt,
                    max_retries,
                    result,
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini 3 preview call failed (attempt %s/%s): %s",
                    attempt,
                    max_retries,
                    str(exc),
                )
            await asyncio.sleep(0.3)

        raise Exception(f"Gemini调用失败: {last_error}")

    async def extract_pattern(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI提取花型
        
        注意：当pattern_type为"fine"（烫画/胸前花）时，返回的字符串是逗号分隔的多个URL
        """
        options = options or {}
        pattern_type_raw = (options.get("pattern_type") or "general").strip().lower()
        normalized_pattern_type = pattern_type_raw.replace("-", "_")
        if normalized_pattern_type == "general":
            pattern_type = "general_2"
        elif normalized_pattern_type.startswith("general") and normalized_pattern_type[-1].isdigit():
            pattern_type = f"general_{normalized_pattern_type[-1]}"
        else:
            pattern_type = normalized_pattern_type
        quality_mode = (options.get("quality") or "standard").strip().lower()
        
        # 根据不同的花型类型使用不同的提示词
        if pattern_type == "positioning":
            # 线条/矢量类型
            prompt = (
                "将衣服上的印花图案提取出来，我要求提取出来的图案跟衣服上的图案一模一样，细节一模一样，"
                "平整图案，拉平褶皱，不能改变图案，我要求把褶皱的地方展开，补全褶皱缺失的图案，"
                "我要求图案不能少，图案要完整，不能缺失，要求把图案补充完整，"
                "我要求位置不能变，不要改变印花图案的排布，按照原有的图案排布输出，底色不变，颜色不变 "
                "要求图案清晰 要求补齐图案，要一模一样 要求卡位置 把图片补全 不要少内容 ，"
                "图案对比度拉高，图案优化清晰，图案排版一样，提取出来的图案要与衣服上的图案一致，"
                "图案要补全。图案要协调，噪点要磨平，图案上下左右都要扩展出去"
            )
        elif pattern_type == "fine":
            # 烫画/胸前花类型
            prompt = (
                "生成图片："
                "从提供的图片中严格提取图案，将图案设计的风格和内容元索还原为填充整个画面的平面印刷图像，准确识别并完整还原图案、纹理、颜色,等设计元素。2 1：1"
            )
        elif pattern_type == "denim":
            # 牛仔风格专用类型
            prompt = (
                "从整条牛仔裤中提取完整的牛仔面料质感，包括裤腿、腰带、口袋、接缝和褶皱细节，还有花型。"
                "保持纹理结构和比例准确，没有遗漏区域或失真。在画布上无缝地展平和平铺整个牛仔纹理。"
                "输出具有逼真织物纹理、照明和编织细节的高分辨率数字纺织品印花，适用于纺织品或图案设计。"
            )
        else:
            # 通用类型（默认）
            prompt = (
                "核心任务： 全幅宽定位印花画稿生成 (密度控制 + 智能扩展) 角色设定： 您是顶级印花设计专家。您的目标是生成一张**\"准备上机打印\"**的、构图完美的数码印花源文件。\n"
                "\n"
                "核心指令 (必须严格执行)：\n"
                "\n"
                "定位花布局与密度控制 (Engineered Layout & Density - 核心加强)\n"
                "\n"
                "定位逻辑： 严格遵循\"定位印花\"的设计原则。花型的位置是经过精心设计的，而非随机平铺。保持原图特有的花位布局（如：花朵在特定位置的聚散）。\n"
                "\n"
                "呼吸感与留白 (Neg平面。\n"
                "\n"
                "顺势排列： 图案走势顺应版型（裤装垂直），但不画出任何物理轮廓线。\n"
                "\n"
                "画质：超高清印花级\n"
                "\n"
                "刀锋锐利： 8K+分辨率，边缘锐利，无模糊，保留手绘/数码原稿的细腻笔触。\n"
                "\n"
                "排除列表 (加强版)： 排除：图案拥挤，花型被切断，边缘残缺，腰部假性密集，裤子/裙子轮廓，缝隙，阴影，模糊"
            )

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        def _coerce_positive_int(value: Any) -> Optional[int]:
            try:
                value_int = int(value)
            except (TypeError, ValueError):
                return None
            return value_int if value_int > 0 else None

        def _build_size() -> str:
            """Return OpenAI size string when width/height valid."""
            width_value = _coerce_positive_int(width)
            height_value = _coerce_positive_int(height)

            if width_value and height_value:
                return f"{width_value}x{height_value}"

            size_option = options.get("size")
            if isinstance(size_option, str) and "x" in size_option:
                return size_option

            return "1024x1024"

        # 烫画/胸前花类型使用Apyi OpenAI模型，生成2张图片
        if pattern_type == "fine":
            size = _build_size()
            model_option = options.get("model")
            model = model_option.strip() if isinstance(model_option, str) and model_option.strip() else "gpt-4o-image"

            result = await self.apyi_openai_client.generate_image(
                prompt,
                n=2,
                size=size,
                model=model,
                image_bytes=image_bytes,  # 传递输入图像数据
            )
            image_urls = self.apyi_openai_client._extract_image_urls(result)
            # 返回逗号分隔的URL字符串
            return ",".join(image_urls)
        elif pattern_type == "denim":
            result = await self.gpt4o_client.process_image(
                image_bytes,
                prompt,
                "image/png",
                n=1,
            )
            return self.gpt4o_client._extract_image_url(result)
        else:
            # general_2 和 positioning 模式都使用 gemini-3-pro-image-preview
            if pattern_type in ["general_2", "positioning"]:
                # general_2 使用 4K，positioning 使用 2K
                resolution = "4K" if pattern_type == "general_2" else "2K"
                result = await self.apyi_gemini_client.generate_image_preview(
                    image_bytes,
                    prompt,
                    "image/png",
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                )
            else:
                # 其他模式使用 gemini-2.5-flash-image
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
        prompt = (
            "生成图片："
            "Generate a new image by removing the fabric texture from this image, make the surface smooth while preserving the original color tone and overall appearance as much as possible."
        )

        # 提取分辨率参数
        aspect_ratio = options.get("aspect_ratio")
        width = options.get("width")
        height = options.get("height")

        return await self._process_image_with_retry(
            image_bytes,
            prompt,
            "image/png",
            aspect_ratio=aspect_ratio,
            width=width,
            height=height
        )
