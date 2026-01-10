import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.gemini_client import GeminiClient
from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient
from app.services.ai_client.apyi_openai_client import ApyiOpenAIClient
from app.services.ai_client.gpt4o_client import GPT4oClient
from app.services.ai_client.image_utils import ImageProcessingUtils
from app.services.ai_client.gqch_client import GQCHClient
from app.services.ai_client.jimeng_client import JimengClient
from app.services.ai_client.liblib_client import LiblibUpscaleAPI
from app.services.ai_client.meitu_client import MeituClient
from app.services.ai_client.vectorizer_client import VectorizerClient
from app.services.ai_client.vector_webapi_client import VectorWebAPIClient
from app.services.ai_client.a8_vectorizer_client import A8VectorizerClient
from app.services.ai_client.runninghub_client import RunningHubClient
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

# Frontend surfaces combined/general/denim; aliases keep legacy pattern_type values compatible.
_PATTERN_TYPE_ALIASES = {
    "general": "general_1",
    "general1": "general_1",
    "general_1": "general_1",
    "general_model": "general_1",
    "general2": "general_2",
    "general_2": "general_2",
    "combined": "combined",
    "composite": "combined",
}

_COMBINED_VARIANTS = ("general_2", "combined_detail")


class AIClient:
    """AI服务客户端 - 模块化版本"""
    
    def __init__(self):
        # 初始化各个服务客户端
        self.gpt4o_client = GPT4oClient()
        self.gemini_client = GeminiClient()
        self.apyi_gemini_client = ApyiGeminiClient()
        self.apyi_openai_client = ApyiOpenAIClient()
        self.jimeng_client = JimengClient()
        self.vectorizer_client = VectorizerClient()
        self.vector_webapi_client = VectorWebAPIClient()
        self.a8_vectorizer_client = A8VectorizerClient()
        self.meitu_client = MeituClient()
        self.image_utils = ImageProcessingUtils()
        self.base_client_utils = BaseAIClient()
        self.gqch_client = GQCHClient()
        self.runninghub_client = RunningHubClient()
        self.file_service = FileService()
        
        # Liblib API配置
        self.liblib_client = LiblibUpscaleAPI(
            access_key=settings.liblib_access_key,
            secret_key=settings.liblib_secret_key,
            base_url=settings.liblib_api_url
        )

    async def _make_jimeng_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """向即梦API发送请求（兼容旧接口）"""
        return await self.jimeng_client._make_jimeng_request(method, endpoint, data)

    async def query_jimeng_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询即梦任务状态（兼容旧接口）"""
        return await self.jimeng_client.query_task_status(task_id)

    async def _download_image_from_url(self, url: str) -> bytes:
        """下载图片（兼容旧接口）"""
        return await self.base_client_utils._download_image_from_url(url)

    # GPT-4o相关方法
    async def generate_image_gpt4o(self, prompt: str, size: str = "1024x1024") -> Dict[str, Any]:
        """使用GPT-4o生成图片"""
        return await self.gpt4o_client.generate_image(prompt, size)

    async def process_image_gpt4o(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg", n: int = 1) -> Dict[str, Any]:
        """使用GPT-4o-image-vip处理图片"""
        return await self.gpt4o_client.process_image(image_bytes, prompt, mime_type, n)

    # Gemini相关方法
    async def process_image_gemini(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg") -> Dict[str, Any]:
        """使用Gemini-2.5-flash-image处理图片"""
        return await self.gemini_client.process_image(image_bytes, prompt, mime_type)

    async def process_image_apyi_gemini(
        self,
        image_bytes: bytes,
        prompt: str,
        mime_type: str = "image/jpeg",
        aspect_ratio: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        使用Apyi平台的Gemini-2.5-flash-image处理图片，支持自定义分辨率和宽高比

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
        return await self.apyi_gemini_client.process_image(
            image_bytes, prompt, mime_type, aspect_ratio, width, height
        )

    # Apyi OpenAI相关方法
    async def create_image_edit_apyi(
        self,
        image_bytes: bytes,
        mask_bytes: bytes,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        response_format: str = "url"
    ) -> Dict[str, Any]:
        """
        使用Apyi平台的OpenAI兼容API编辑图像

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
        return await self.apyi_openai_client.create_image_edit(
            image_bytes, mask_bytes, prompt, n, size, response_format
        )

    async def generate_image_apyi(
        self,
        prompt: str,
        n: int = 1,
        size: Optional[str] = "1024x1024",
        response_format: Optional[str] = None,
        model: str = "gpt-image-1",
    ) -> Dict[str, Any]:
        """
        使用Apyi平台的OpenAI兼容API生成图像

        Args:
            prompt: 生成指令文本
            n: 生成的图像数量，默认为1，最大为10
            size: 输出图像尺寸，支持 256x256、512x512、1024x1024，None 表示使用服务默认值
            response_format: 返回格式，可选值如 url 或 b64_json，None 表示使用服务默认值
            model: 使用的图像模型，默认 gpt-image-1

        Returns:
            API响应数据
        """
        return await self.apyi_openai_client.generate_image(
            prompt,
            n=n,
            size=size,
            response_format=response_format,
            model=model,
        )

    async def chat_completion_apyi(
        self,
        messages: list,
        model: str = "gpt-4o",
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        使用Apyi平台的GPT-4o进行对话补全

        Args:
            messages: 对话消息列表
            model: 模型名称，默认为 gpt-4o
            max_tokens: 最大token数
            temperature: 温度参数
            stream: 是否使用流式响应

        Returns:
            API响应数据
        """
        return await self.apyi_openai_client.chat_completion(
            messages, model, max_tokens, temperature, stream
        )

    # 遮罩创建工具方法
    def create_mask_for_rectangle_apyi(
        self,
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
        return ApyiOpenAIClient.create_mask_for_rectangle(image_bytes, bbox, mask_format)

    def create_mask_for_circle_apyi(
        self,
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
        return ApyiOpenAIClient.create_mask_for_circle(image_bytes, center, radius, mask_format)

    def create_mask_for_object_removal_apyi(
        self,
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
        return ApyiOpenAIClient.create_mask_for_object_removal(image_bytes, bbox, mask_format)

    # 图片处理工具方法
    async def seamless_pattern_conversion(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI四方连续转换"""
        return await self.image_utils.seamless_pattern_conversion(image_bytes, options)

    async def seamless_loop(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
        original_filename: Optional[str] = None,
    ) -> str:
        """调用RunningHub实现无缝拼接/接循环"""
        # 获取拼接方向参数，前端传的是0/1/2，需要映射到RunningHub的1/2/3
        # 0 -> 1 (四周拼接)
        # 1 -> 2 (上下拼接)
        # 2 -> 3 (左右拼接)
        frontend_direction = options.get("direction", 0) if options else 0
        runninghub_direction = frontend_direction + 1

        rh_options = dict(options or {})
        rh_options["original_filename"] = original_filename or "seamless_loop.png"

        result_urls = await self.runninghub_client.run_seamless_loop_workflow(
            image_bytes=image_bytes,
            workflow_id=settings.runninghub_workflow_id_seamless_loop,
            image_node_id=settings.runninghub_seamless_loop_image_node_id,
            image_field_name=settings.runninghub_seamless_loop_image_field_name,
            direction_node_id=settings.runninghub_seamless_loop_direction_node_id,
            direction_field_name=settings.runninghub_seamless_loop_direction_field_name,
            direction_value=runninghub_direction,
            options=rh_options,
        )

        cleaned_urls = [url.strip() for url in result_urls if url and url.strip()]
        if not cleaned_urls:
            raise Exception("RunningHub接循环未返回结果图片")

        return ",".join(cleaned_urls)

    async def prompt_edit_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """根据自然语言指令编辑图片"""
        return await self.image_utils.prompt_edit_image(image_bytes, options)

    def _normalize_pattern_type(self, raw_value: Optional[str]) -> str:
        normalized = (raw_value or "general").strip().lower().replace("-", "_")
        alias = _PATTERN_TYPE_ALIASES.get(normalized)
        if alias:
            return alias
        if normalized.startswith("general") and normalized[-1].isdigit():
            return f"general_{normalized[-1]}"
        return normalized or "general_1"

    @staticmethod
    def _split_urls(raw_result: str) -> List[str]:
        return [url.strip() for url in raw_result.split(",") if url and url.strip()]

    async def _extract_pattern_combined(
        self,
        image_bytes: bytes,
        options: Dict[str, Any],
    ) -> str:
        async def _run_variant(pt: str) -> Optional[str]:
            try:
                merged_options = dict(options or {})
                merged_options["pattern_type"] = pt
                result = await self.image_utils.extract_pattern(image_bytes, merged_options)
                if not result:
                    return None
                return result.split(",")[0].strip()
            except Exception as exc:
                logger.warning("Combined pattern variant %s failed: %s", pt, str(exc))
                return None

        async def _run_runninghub(workflow_id: str) -> Optional[str]:
            try:
                result_urls = await self.runninghub_client.run_workflow_with_custom_nodes(
                    image_bytes=image_bytes,
                    workflow_id=workflow_id,
                    node_ids=settings.runninghub_extract_combined_node_id,
                    field_name=settings.runninghub_extract_combined_field_name,
                    options=options,
                )
                if not result_urls:
                    return None
                return result_urls[0].strip()
            except Exception as exc:
                logger.warning(
                    "Combined pattern RunningHub workflow %s failed: %s",
                    workflow_id,
                    str(exc),
                )
                return None

        def _coerce_positive_int(value: Any) -> Optional[int]:
            try:
                value_int = int(value)
            except (TypeError, ValueError):
                return None
            return value_int if value_int > 0 else None

        def _build_gpt4o_size() -> str:
            width_value = _coerce_positive_int(options.get("width"))
            height_value = _coerce_positive_int(options.get("height"))
            if width_value and height_value:
                return f"{width_value}x{height_value}"

            size_option = options.get("size")
            if isinstance(size_option, str) and "x" in size_option:
                return size_option

            aspect_ratio = options.get("aspect_ratio")
            if isinstance(aspect_ratio, str):
                ratio_map = {
                    "1:1": "1024x1024",
                    "2:3": "1024x1536",
                    "3:2": "1536x1024",
                }
                mapped = ratio_map.get(aspect_ratio.strip())
                if mapped:
                    return mapped

            return "1024x1024"

        async def _run_gemini3_extract() -> Optional[str]:
            """使用 Gemini-3-pro-image-preview 提取花型"""
            try:
                prompt = (
                    "整性 (Outpainting & Integrity - 核心加强)\n\n"
                    "拒绝残缺： 确保画面边缘和扩展区域的所有花朵/几何图形都是结构完整的。严禁出现只有一半、被切断或破碎的花型。\n\n"
                    "腰头区域：去褶皱还原 (保持不变)\n\n"
                    "数字解压： 识别腰部的高密度是物理挤压造成的。必须将挤在一起的图案"拉开"、"摊平"，恢复其原本的自然间距和大小，与主体图案保持一致。\n\n"
                    "裤装/裙装隐形合并逻辑 (保持不变)\n\n"
                    "裤装缝合： 彻底忽略裤腿缝隙，将双腿图案合并为连续宽幅平面。\n\n"
                    "顺势排列： 图案走势顺应版型（裤装垂直），但不画出任何物理轮廓线。\n\n"
                    "画质：超高清印花级\n\n"
                    "刀锋锐利： 8K+分辨率，边缘锐利，无模糊，保留手绘/数码原稿的细腻笔触。\n\n"
                    "排除列表 (加强版)： 排除：图案拥挤，花型被切断，边缘残缺，腰部假性密集，裤子/裙子轮廓，缝隙，阴影，模糊"
                )
                aspect_ratio = options.get("aspect_ratio")
                result = await self.image_utils.apyi_gemini_client.generate_image_preview(
                    image_bytes,
                    prompt,
                    "image/png",
                    aspect_ratio=aspect_ratio,
                    resolution="4K",
                )
                url = self.image_utils.apyi_gemini_client._extract_image_url(result)
                return url.strip() if isinstance(url, str) and url.strip() else None
            except Exception as exc:
                logger.warning("Combined pattern Gemini-3 failed: %s", str(exc))
                return None

        variant_tasks = [
            asyncio.create_task(_run_variant(pt)) for pt in _COMBINED_VARIANTS
        ]
        gemini3_task = asyncio.create_task(_run_gemini3_extract())
        runninghub_tasks = [
            asyncio.create_task(
                _run_runninghub(settings.runninghub_workflow_id_extract_combined_4)
            ),
        ]

        variant_urls: List[str] = []
        for task in variant_tasks + [gemini3_task] + runninghub_tasks:
            url = await task
            if url:
                variant_urls.append(url)

        if not variant_urls:
            raise Exception("AI提取花型失败：综合模型未获得结果")

        logger.info("Combined pattern produced %s urls", len(variant_urls))
        return ",".join(variant_urls[:4])

    async def _extract_pattern_general_1(
        self,
        image_bytes: bytes,
        options: Dict[str, Any],
    ) -> str:
        ordered_results: List[str] = []
        max_general1_results = 4
        runninghub_workflows = [
            {
                "workflow_id": settings.runninghub_workflow_id_extract_general1_1,
                "node_ids": settings.runninghub_extract_general1_node_id_1,
                "field_name": settings.runninghub_extract_general1_field_name_1,
                "label": "提取花型-通用1-工作流1",
            },
            {
                "workflow_id": settings.runninghub_workflow_id_extract_general1_2,
                "node_ids": settings.runninghub_extract_general1_node_id_2,
                "field_name": settings.runninghub_extract_general1_field_name_2,
                "label": "提取花型-通用1-工作流2",
            },
            {
                "workflow_id": settings.runninghub_workflow_id_extract_general1_3,
                "node_ids": settings.runninghub_extract_general1_node_id_3,
                "field_name": settings.runninghub_extract_general1_field_name_3,
                "label": "提取花型-通用1-工作流3",
            },
            {
                "workflow_id": settings.runninghub_workflow_id_extract_general1_4,
                "node_ids": settings.runninghub_extract_general1_node_id_4,
                "field_name": settings.runninghub_extract_general1_field_name_4,
                "label": "提取花型-通用1-工作流4",
            },
        ]

        runninghub_tasks: List[Tuple[Dict[str, Any], asyncio.Task]] = []
        for workflow in runninghub_workflows:
            workflow_id = (workflow.get("workflow_id") or "").strip()
            if not workflow_id:
                logger.debug(
                    "Skipping RunningHub workflow %s: workflow_id not configured",
                    workflow["label"],
                )
                continue

            logger.info(
                "Submitting RunningHub workflow %s (%s) with nodes=%s",
                workflow["label"],
                workflow_id,
                workflow.get("node_ids"),
            )

            task = asyncio.create_task(
                self.runninghub_client.run_workflow_with_custom_nodes(
                    image_bytes=image_bytes,
                    workflow_id=workflow_id,
                    node_ids=workflow.get("node_ids"),
                    field_name=workflow.get("field_name"),
                    options=options,
                )
            )
            runninghub_tasks.append((workflow, task))

        for workflow, task in runninghub_tasks:
            try:
                rh_results = await task
                logger.info(
                    "RunningHub workflow %s returned %s urls",
                    workflow["label"],
                    len(rh_results),
                )
                for rh_url in rh_results:
                    cleaned = rh_url.strip()
                    if cleaned:
                        ordered_results.append(cleaned)
                        if len(ordered_results) >= max_general1_results:
                            break
            except Exception as exc:
                logger.warning(
                    "RunningHub workflow %s failed: %s",
                    workflow["label"],
                    str(exc),
                )
            finally:
                if len(ordered_results) >= max_general1_results:
                    break

        if not ordered_results:
            raise Exception("AI提取花型失败：通用1未获得结果")

        logger.info(
            "Final general-1 pattern output prepared (RunningHub only): %s urls",
            len(ordered_results),
        )

        return ",".join(ordered_results)

    async def _enhance_pattern_urls(
        self,
        urls: List[str],
        pattern_type: str,
        options: Dict[str, Any],
    ) -> List[str]:
        async def _enhance_url(url: str) -> List[str]:
            try:
                meitu_options = {
                    "engine": "meitu_v2",
                    "sr_num": 4,
                    "task": options.get("task", "/v1/Ultra_High_Definition_V2/478332"),
                    "task_type": options.get("task_type", "formula"),
                    "sync_timeout": options.get("sync_timeout", 120),
                    "rsp_media_type": options.get("rsp_media_type", "url"),
                }
                enhanced = await self.upscale_image(
                    url,
                    scale_factor=4,
                    options=meitu_options,
                )
                return [item.strip() for item in enhanced.split(",") if item.strip()]
            except Exception as exc:
                logger.warning(
                    "Pattern enhancement failed for %s with pattern_type=%s: %s. Falling back to raw result.",
                    url,
                    pattern_type,
                    str(exc),
                )
                return [url]

        logger.debug(
            "Extract pattern (%s) received %s raw URLs for enhancement",
            pattern_type,
            len(urls),
        )

        enhancement_tasks = [
            asyncio.create_task(_enhance_url(url))
            for url in urls
        ]
        enhanced_urls: List[str] = []
        for task in enhancement_tasks:
            enhanced_urls.extend(await task)
        logger.info(
            "Enhanced %s URLs for pattern_type=%s (input=%s)",
            len(enhanced_urls),
            pattern_type,
            len(urls),
        )
        return enhanced_urls

    async def _extract_pattern_with_image_utils(
        self,
        image_bytes: bytes,
        pattern_type: str,
        options: Dict[str, Any],
    ) -> str:
        raw_result = await self.image_utils.extract_pattern(image_bytes, options)
        if not raw_result:
            raise Exception("AI提取花型失败：未获得结果")

        if pattern_type == "fine":
            return raw_result

        result_urls = self._split_urls(raw_result)
        if not result_urls:
            raise Exception("AI提取花型失败：结果URL无效")

        if pattern_type == "general_2":
            logger.info(
                "Pattern type %s returns base result without secondary enhancement. urls=%s",
                pattern_type,
                len(result_urls),
            )
            return result_urls[0]

        if pattern_type == "denim":
            logger.info(
                "Pattern type %s returns base result without secondary enhancement. urls=%s",
                pattern_type,
                len(result_urls),
            )
            return ",".join(result_urls)

        enhanced_urls = await self._enhance_pattern_urls(
            result_urls,
            pattern_type,
            options,
        )
        final_result_pool = enhanced_urls or result_urls
        if not final_result_pool:
            raise Exception("AI提取花型失败：通用模式未获得结果")
        return ",".join(final_result_pool)

    async def extract_pattern(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI提取花型，并按需进行高清增强"""
        options = dict(options or {})
        raw_pattern_type = options.get("pattern_type")
        pattern_type = self._normalize_pattern_type(raw_pattern_type)
        options["pattern_type"] = pattern_type

        if raw_pattern_type and raw_pattern_type != pattern_type:
            logger.debug(
                "Normalized extract_pattern type %s -> %s",
                raw_pattern_type,
                pattern_type,
            )

        if pattern_type == "combined":
            return await self._extract_pattern_combined(image_bytes, options)

        if pattern_type == "positioning":
            return await self.runninghub_client.run_positioning_workflow(
                image_bytes,
                options,
            )

        if pattern_type == "general_1":
            return await self._extract_pattern_general_1(image_bytes, options)

        return await self._extract_pattern_with_image_utils(
            image_bytes,
            pattern_type,
            options,
        )

    async def denoise_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI布纹去噪"""
        return await self.image_utils.denoise_image(image_bytes, options)

    async def expand_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
        original_filename: Optional[str] = None,
    ) -> str:
        """调用RunningHub实现智能扩图"""
        # 获取扩展边距参数
        expand_top = float(options.get("expand_top", 0)) if options else 0
        expand_bottom = float(options.get("expand_bottom", 0)) if options else 0
        expand_left = float(options.get("expand_left", 0)) if options else 0
        expand_right = float(options.get("expand_right", 0)) if options else 0

        rh_options = dict(options or {})
        rh_options["original_filename"] = original_filename or "expand_image.png"

        result_urls = await self.runninghub_client.run_expand_image_workflow(
            image_bytes=image_bytes,
            workflow_id=settings.runninghub_workflow_id_expand_image,
            image_node_id=settings.runninghub_expand_image_node_id,
            image_field_name=settings.runninghub_expand_image_field_name,
            expand_top=expand_top,
            expand_bottom=expand_bottom,
            expand_left=expand_left,
            expand_right=expand_right,
            top_node_id=settings.runninghub_expand_top_node_id,
            bottom_node_id=settings.runninghub_expand_bottom_node_id,
            left_node_id=settings.runninghub_expand_left_node_id,
            right_node_id=settings.runninghub_expand_right_node_id,
            margin_field_name=settings.runninghub_expand_margin_field_name,
            options=rh_options,
        )

        cleaned_urls = [url.strip() for url in result_urls if url and url.strip()]
        if not cleaned_urls:
            raise Exception("RunningHub扩图未返回结果图片")

        return ",".join(cleaned_urls)

    # 矢量化相关方法
    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG) - 使用Vectorizer.ai API"""
        return await self.vectorizer_client.vectorize_image(image_bytes, options)

    async def vectorize_image_webapi(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI矢量化 - 使用 mm.kknc.site 提供的矢量转换API

        Args:
            image_bytes: 图片字节数据
            options: 可选配置，包括 vectorFormat/format、original_filename

        Returns:
            保存的矢量文件URL路径
        """
        opts = options or {}
        vector_format = (
            opts.get("vectorFormat")
            or opts.get("vectorformat")
            or opts.get("format")
            or ".svg"
        )
        original_filename = opts.get("original_filename")

        original_filename = opts.get("original_filename")

        # 优先尝试使用A8矢量化API
        try:
            # A8 API需要的格式参数是 'eps' 或 'svg'，去掉点号
            a8_fmt = vector_format.lstrip('.').lower()
            if a8_fmt not in ('eps', 'svg'):
                # 如果格式不支持，默认使用svg，或者根据需求决定是否跳过A8
                # 这里假设A8只支持eps和svg，如果请求其他格式，可能需要直接走WebAPI或者强制转为svg
                if a8_fmt == 'pdf': # WebAPI支持pdf，A8不支持，直接走WebAPI
                     logger.info(f"Format {vector_format} not supported by A8, skipping to WebAPI")
                     raise ValueError("Format not supported by A8")
                a8_fmt = 'svg' # 默认兜底

            logger.info(f"Attempting vectorization with A8 API, format: {a8_fmt}")
            return await self.a8_vectorizer_client.image_to_vector(
                image_bytes,
                fmt=a8_fmt,
                save_path=None, # 让client自己生成路径
                timeout=120
            )
        except Exception as e:
            logger.warning(f"A8 vectorization failed, falling back to WebAPI: {str(e)}")
            # 失败后降级调用 WebAPI
            return await self.vector_webapi_client.convert_image(
                image_bytes,
                vector_format=vector_format,
                filename=original_filename,
            )

    async def vectorize_image_a8(
        self,
        image_bytes: bytes,
        fmt: str = 'eps',
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI矢量化 - 兼容旧A8调用方式，内部转发至新的矢量转换API

        Args:
            image_bytes: 图片字节数据
            fmt: 输出格式 'eps' 或 'svg'
            options: 额外选项（目前主要用于兼容性）

        Returns:
            保存的矢量文件URL路径
        """
        merged_options: Dict[str, Any] = dict(options or {})
        merged_options.setdefault("vectorFormat", fmt)
        return await self.vectorize_image_webapi(image_bytes, merged_options)

    async def vectorize_image_a8_eps(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI矢量化为EPS格式 - 使用A8矢量转换API

        Args:
            image_bytes: 图片字节数据
            options: 额外选项（目前主要用于兼容性）

        Returns:
            保存的EPS文件URL路径
        """
        merged_options: Dict[str, Any] = dict(options or {})
        merged_options.setdefault("vectorFormat", ".eps")
        return await self.vectorize_image_webapi(image_bytes, merged_options)

    async def vectorize_image_a8_svg(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI矢量化为SVG格式 - 使用A8矢量转换API

        Args:
            image_bytes: 图片字节数据
            options: 额外选项（目前主要用于兼容性）

        Returns:
            保存的SVG文件URL路径
        """
        merged_options: Dict[str, Any] = dict(options or {})
        merged_options.setdefault("vectorFormat", ".svg")
        return await self.vectorize_image_webapi(image_bytes, merged_options)

    # 去水印相关方法
    async def remove_watermark(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI智能去水印（RunningHub一致性去水印工作流）"""
        try:
            workflow_id = (settings.runninghub_workflow_id_consistent_dewatermark or "").strip()
            node_ids = settings.runninghub_consistent_dewatermark_node_id
            field_name = (settings.runninghub_consistent_dewatermark_field_name or "").strip()

            if not workflow_id:
                raise Exception("未配置RunningHub一致性去水印workflowId")
            if not node_ids:
                raise Exception("未配置RunningHub一致性去水印nodeId")
            if not field_name:
                raise Exception("未配置RunningHub一致性去水印fieldName")

            rh_options = dict(options or {})
            if not rh_options.get("original_filename"):
                rh_options["original_filename"] = "remove_watermark.png"

            result_urls = await self.runninghub_client.run_workflow_with_custom_nodes(
                image_bytes=image_bytes,
                workflow_id=workflow_id,
                node_ids=node_ids,
                field_name=field_name,
                options=rh_options,
            )

            cleaned_urls = [url.strip() for url in result_urls if url and url.strip()]
            if not cleaned_urls:
                raise Exception("RunningHub一致性去水印未返回结果图片")

            return ",".join(cleaned_urls)
        except Exception as exc:
            logger.error("RunningHub一致性去水印失败: %s", str(exc))
            raise Exception(f"智能去水印失败: {str(exc)}")

    async def generate_similar_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI相似图（RunningHub相似图工作流）"""
        try:
            workflow_id = (settings.runninghub_workflow_id_similar_image or "").strip()
            node_ids = settings.runninghub_consistent_similar_image_node_id
            field_name = (settings.runninghub_consistent_similar_image_field_name or "").strip()

            if not workflow_id:
                raise Exception("未配置RunningHub相似图workflowId")
            if not node_ids:
                raise Exception("未配置RunningHub相似图nodeId")
            if not field_name:
                raise Exception("未配置RunningHub相似图fieldName")

            rh_options = dict(options or {})
            if not rh_options.get("original_filename"):
                rh_options["original_filename"] = "similar_image.png"

            result_urls = await self.runninghub_client.run_workflow_with_custom_nodes(
                image_bytes=image_bytes,
                workflow_id=workflow_id,
                node_ids=node_ids,
                field_name=field_name,
                options=rh_options,
            )

            cleaned_urls = [url.strip() for url in result_urls if url and url.strip()]
            if not cleaned_urls:
                raise Exception("RunningHub相似图未返回结果图片")

            return ",".join(cleaned_urls)
        except Exception as exc:
            logger.error("RunningHub相似图失败: %s", str(exc))
            raise Exception(f"相似图生成失败: {str(exc)}")

    # AI高清放大相关方法
    async def upscale_image(
        self,
        image_url: str,
        scale_factor: int = 2,
        custom_width: Optional[int] = None,
        custom_height: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """AI高清放大图片，支持多种引擎"""
        options = options or {}
        engine = (options.get("engine") or "meitu_v2").strip().lower()

        # 准备可供第三方访问的图片URL
        public_url, prepared_bytes = await self._prepare_image_for_external_api(
            image_url=image_url,
            image_bytes=image_bytes,
            purpose="upscale",
        )
        resolved_bytes = image_bytes or prepared_bytes

        if engine == "meitu_v2":
            return await self._upscale_with_meitu_v2(
                public_url,
                scale_factor=scale_factor,
                options=options,
            )

        if engine == "runninghub_vr2":
            return await self._upscale_with_runninghub_vr2(
                public_url,
                options=options,
                image_bytes=resolved_bytes,
            )

        # 默认使用Liblib引擎（创造力+N）
        return await self._upscale_with_liblib(
            public_url,
            scale_factor=scale_factor,
            custom_width=custom_width,
            custom_height=custom_height,
            options=options,
        )

    async def _prepare_image_for_external_api(
        self,
        image_url: str,
        image_bytes: Optional[bytes],
        purpose: str = "general",
    ) -> Tuple[str, Optional[bytes]]:
        """确保图片可以被第三方API访问，必要时上传至OSS"""
        is_oss = image_url.startswith("http") and self.file_service.is_oss_url(image_url)
        logger.info(
            "Preparing image for external API: url=%s is_oss=%s oss_configured=%s bucket=%s endpoint=%s domain=%s",
            image_url,
            is_oss,
            self.file_service.oss_service.is_configured(),
            getattr(self.file_service.oss_service, "bucket_name", None),
            getattr(self.file_service.oss_service, "endpoint", None),
            getattr(self.file_service.oss_service, "bucket_domain", None),
        )

        if image_url.startswith("/files/"):
            logger.warning("Image URL is a local path: %s", image_url)

            from app.services.oss_service import oss_service

            if not image_bytes:
                relative_path = image_url.replace("/files/", "")
                local_path = os.path.join(settings.upload_path, relative_path)
                if not os.path.exists(local_path):
                    raise Exception(f"本地文件不存在: {local_path}")
                with open(local_path, "rb") as file_obj:
                    image_bytes = file_obj.read()

            if not oss_service.is_configured():
                raise Exception(
                    "图片URL必须是公开可访问的URL。本地路径需要配置OSS才能使用。"
                )

            temp_filename = f"{purpose}_{uuid.uuid4().hex[:8]}.jpg"
            public_url = await oss_service.upload_image_for_jimeng(image_bytes, temp_filename)
            logger.info("Uploaded image to OSS for %s: %s", purpose, public_url)
            return public_url, image_bytes

        if image_url.startswith("http") and is_oss:
            try:
                presigned_url = await self.file_service.generate_presigned_url_for_full_url(
                    image_url,
                    expiration=settings.oss_expiration_time,
                )
                if presigned_url:
                    logger.info(
                        "Generated presigned OSS URL for external API: origin=%s presigned=%s",
                        image_url,
                        presigned_url,
                    )
                    return presigned_url, image_bytes
            except Exception as exc:
                logger.warning("Failed to generate presigned OSS URL for %s: %s", image_url, exc)

        return image_url, image_bytes

    async def _ensure_image_bytes(
        self,
        image_url: str,
        image_bytes: Optional[bytes],
    ) -> bytes:
        """确保能够获取图片字节数据"""
        if image_bytes:
            return image_bytes
        if not image_url:
            raise Exception("无法获取待处理图片")
        return await self._download_image_from_url(image_url)

    async def _prepare_image_for_jimeng(self, image_bytes: bytes, temp_prefix: str) -> str:
        """上传图片到OSS供即梦API使用，必要时回退到本地存储"""
        from app.services.oss_service import oss_service

        temp_filename = f"{temp_prefix}_{uuid.uuid4().hex[:8]}.jpg"
        logger.info("OSS配置状态: %s", "已配置" if oss_service.is_configured() else "未配置")

        if oss_service.is_configured():
            logger.info("上传图片到OSS以供即梦API使用")
            image_url = await oss_service.upload_image_for_jimeng(image_bytes, temp_filename)
            logger.info("OSS上传完成，获得的URL: %s", image_url)
            return image_url

        logger.warning("OSS未配置，使用本地存储")
        temp_file_path = f"{settings.upload_path}/originals/{temp_filename}"
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        with open(temp_file_path, "wb") as file_obj:
            file_obj.write(image_bytes)

        image_url = f"/files/originals/{temp_filename}"
        logger.warning("使用本地路径: %s", image_url)
        return image_url

    def _apply_jimeng_options(self, data: Dict[str, Any], options: Optional[Dict[str, Any]]) -> None:
        """将可选参数应用到即梦任务数据中"""
        if not options:
            return

        if "scale" in options:
            data["scale"] = options["scale"]
        if "size" in options:
            data["size"] = options["size"]

        if "width" in options and "height" in options:
            data["width"] = options["width"]
            data["height"] = options["height"]
        elif "aspect_ratio" in options:
            aspect_ratio = options["aspect_ratio"]
            ratio_map = {
                "21:9": (2048, 877),
                "16:9": (1920, 1080),
                "4:3": (1600, 1200),
                "3:2": (1800, 1200),
                "1:1": (2048, 2048),
                "9:16": (1080, 1920),
                "3:4": (1200, 1600),
                "2:3": (1200, 1800),
                "5:4": (1600, 1280),
                "4:5": (1280, 1600),
            }
            if aspect_ratio in ratio_map:
                width, height = ratio_map[aspect_ratio]
                data["width"] = width
                data["height"] = height

        if "force_single" in options:
            data["force_single"] = options["force_single"]

    async def _execute_jimeng_task(
        self,
        data: Dict[str, Any],
        *,
        log_label: str,
        result_prefix: str,
    ) -> str:
        """提交即梦任务并轮询结果"""
        try:
            result = await self.jimeng_client._make_jimeng_request("POST", "", data)
            if "code" in result and result["code"] != 10000:
                error_msg = result.get("message", "未知错误")
                logger.error("%s API error: %s - %s", log_label, result.get("code"), error_msg)
                raise Exception(f"{log_label}处理失败: {error_msg}")

            if "data" not in result or "task_id" not in result["data"]:
                logger.error("%s API unexpected response: %s", log_label, result)
                raise Exception(f"{log_label}响应格式错误")

            task_id = result["data"]["task_id"]
            logger.info("%s task created: %s", log_label, task_id)

            max_attempts = 40
            for attempt in range(max_attempts):
                wait_time = 3 if attempt < 20 else 5
                await asyncio.sleep(wait_time)

                status_result = await self.jimeng_client.query_task_status(task_id)
                if "code" in status_result and status_result["code"] != 10000:
                    error_msg = status_result.get("message", "未知错误")
                    logger.error("%s status query error: %s - %s", log_label, status_result.get("code"), error_msg)
                    raise Exception(f"{log_label}状态查询失败: {error_msg}")

                status_data = status_result.get("data", {})
                current_status = status_data.get("status", "")
                logger.info("%s task %s status: %s", log_label, task_id, current_status)
                logger.debug("%s full status response: %s", log_label, status_result)

                if current_status == "done":
                    image_urls = status_data.get("image_urls") or status_result.get("image_urls")
                    binary_data = status_data.get("binary_data_base64") or status_result.get("binary_data_base64")

                    if image_urls:
                        result_url = image_urls[0]
                        logger.info("Downloading %s result from: %s", log_label, result_url)
                        result_bytes = await self.gemini_client._download_image_from_url(result_url)
                        saved_url = self.base_client_utils._save_image_bytes(result_bytes, prefix=result_prefix)
                        logger.info("%s result saved to: %s", log_label, saved_url)
                        return saved_url

                    if binary_data:
                        logger.info("%s processing base64 encoded image data", log_label)
                        try:
                            import base64
                            if isinstance(binary_data, list):
                                if not binary_data:
                                    raise Exception("二进制数据列表为空")
                                binary_data = binary_data[0]

                            if not isinstance(binary_data, str):
                                raise Exception(f"二进制数据格式错误: {type(binary_data)}")

                            result_bytes = base64.b64decode(binary_data)
                            saved_url = self.base_client_utils._save_image_bytes(result_bytes, prefix=result_prefix)
                            logger.info("%s result saved to: %s", log_label, saved_url)
                            return saved_url
                        except Exception as exc:
                            logger.error("%s failed to process base64 image data: %s", log_label, str(exc))
                            raise Exception(f"{log_label}处理base64图片数据失败: {str(exc)}")

                    if attempt < max_attempts - 1:
                        logger.warning(
                            "%s task done but no results yet, retrying... (attempt %s/%s)",
                            log_label,
                            attempt + 1,
                            max_attempts,
                        )
                        continue

                    logger.error(
                        "%s task completed but no results found. status_data=%s, status_result=%s",
                        log_label,
                        status_data,
                        status_result,
                    )
                    raise Exception(f"{log_label}任务完成但未找到结果图片")

                if current_status in ["failed", "expired", "not_found"]:
                    error_msg = status_data.get("message", "任务执行失败")
                    raise Exception(f"{log_label}任务失败: {error_msg}")

            raise Exception(f"{log_label}任务超时: {task_id}")

        except Exception as exc:
            logger.error("%s failed: %s", log_label, str(exc))
            raise

    async def _upscale_with_liblib(
        self,
        image_url: str,
        scale_factor: int,
        custom_width: Optional[int],
        custom_height: Optional[int],
        options: Dict[str, Any],
    ) -> str:
        try:
            # 根据scale_factor确定megapixels参数
            megapixels = 8.0

            if "megapixels" in options:
                megapixels = options["megapixels"]
            else:
                if scale_factor == 2:
                    megapixels = 4.0
                elif scale_factor == 4:
                    megapixels = 16.0

            megapixels = max(0.01, min(16.0, float(megapixels)))
            logger.info("Sending Liblib AI upscale request with megapixels: %s", megapixels)

            result_images = await self.liblib_client.generate_and_wait(
                image_url=image_url,
                megapixels=megapixels,
            )

            if not result_images:
                raise Exception("Liblib AI放大失败：未返回结果图片")

            result_url = result_images[0]
            logger.info("Liblib AI upscale completed successfully: %s", result_url)

            result_bytes = await self.gemini_client._download_image_from_url(result_url)
            saved_url = self.base_client_utils._save_image_bytes(result_bytes, prefix="upscaled")
            logger.info("Result saved to: %s", saved_url)
            return saved_url

        except Exception as exc:
            logger.error("Liblib AI upscale failed: %s", str(exc))
            raise Exception(f"AI高清放大失败: {str(exc)}")

    async def _upscale_with_meitu_v2(
        self,
        image_url: str,
        scale_factor: int,
        options: Dict[str, Any],
    ) -> str:
        try:
            return await self.meitu_client.upscale_v2(
                image_url=image_url,
                scale_factor=scale_factor,
                options=options,
            )
        except Exception as exc:
            logger.error("Meitu AI 超清V2失败: %s", str(exc))
            raise Exception(f"美图AI超清失败: {str(exc)}")

    async def _upscale_with_runninghub_vr2(
        self,
        image_url: str,
        options: Dict[str, Any],
        image_bytes: Optional[bytes],
    ) -> str:
        try:
            resolved_bytes = await self._ensure_image_bytes(image_url, image_bytes)
            rh_options = dict(options or {})
            if not rh_options.get("original_filename"):
                rh_options["original_filename"] = "upscale_vr2.png"

            result_urls = await self.runninghub_client.run_workflow_with_custom_nodes(
                image_bytes=resolved_bytes,
                workflow_id=settings.runninghub_workflow_id_vr2,
                node_ids=settings.runninghub_vr2_node_id,
                field_name=settings.runninghub_vr2_field_name,
                options=rh_options,
            )

            cleaned_urls = [url.strip() for url in result_urls if url and url.strip()]
            if not cleaned_urls:
                raise Exception("RunningHub VR2未返回结果图片")

            return ",".join(cleaned_urls)
        except Exception as exc:
            logger.error("RunningHub VR2 upscale failed: %s", str(exc))
            raise Exception(f"AI高清放大失败: {str(exc)}")

    # 即梦特效相关方法
    async def convert_flat_to_3d(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI平面转3D（使用 Apyi Gemini 3 Pro Image Preview）"""
        try:
            prompt = "将图片里的图案转换成3D立体效果，鲜艳颜色，精致细节，具有深度感和光影表现。"
            resolution = (options or {}).get("resolution", "2K")
            aspect_ratio = (options or {}).get("aspect_ratio")

            result = await self.apyi_gemini_client.generate_image_preview(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type="image/png",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
            )

            image_url = self.base_client_utils._extract_image_url(result)
            if not image_url:
                raise Exception("AI平面转3D失败：未生成结果图片")

            return image_url

        except Exception as exc:
            logger.error("Convert flat to 3D failed: %s", str(exc))
            raise Exception(f"AI平面转3D失败: {str(exc)}")

    async def enhance_embroidery(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI毛线刺绣增强（使用 Apyi Gemini 3 Pro Image Preview）"""
        try:
            prompt = """
            将这张图片转换为毛线刺绣效果：
            1. 针线类型：中等针脚，平衡的刺绣效果
            2. 针脚密度：适中的针脚密度
            3. 增强纹理细节，展现真实的毛线质感
            4. 保持原图的主体形状和轮廓
            5. 营造真实的手工刺绣效果
            6. 色彩要自然，符合毛线刺绣的特点
            
            请生成逼真的毛线刺绣效果图。
            """.strip()
            
            resolution = (options or {}).get("resolution", "2K")
            aspect_ratio = (options or {}).get("aspect_ratio")

            result = await self.apyi_gemini_client.generate_image_preview(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type="image/png",
                aspect_ratio=aspect_ratio,
                resolution=resolution,
            )

            image_url = self.base_client_utils._extract_image_url(result)
            if not image_url:
                raise Exception("毛线刺绣增强失败：未生成结果图片")

            return image_url

        except Exception as e:
            logger.error(f"Enhance embroidery failed: {str(e)}")
            raise Exception(f"毛线刺绣增强失败: {str(e)}")


# 创建全局AI客户端实例
ai_client = AIClient()
