import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.dewatermark_client import DewatermarkClient
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
from app.services.ai_client.a8_vectorizer_client import A8VectorizerClient

logger = logging.getLogger(__name__)


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
        self.a8_vectorizer_client = A8VectorizerClient()
        self.dewatermark_client = DewatermarkClient()
        self.meitu_client = MeituClient()
        self.image_utils = ImageProcessingUtils()
        self.base_client_utils = BaseAIClient()
        self.gqch_client = GQCHClient()
        
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
        """调用GQCH实现无缝拼接/接循环"""
        filename = original_filename or "upload.png"
        return await self.gqch_client.seamless_loop(image_bytes, filename, options)

    async def prompt_edit_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """根据自然语言指令编辑图片"""
        return await self.image_utils.prompt_edit_image(image_bytes, options)

    async def extract_pattern(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI提取花型，并按需进行高清增强"""
        options = options or {}
        pattern_type = (options.get("pattern_type") or "general").strip().lower()

        raw_result = await self.image_utils.extract_pattern(image_bytes, options)
        if not raw_result:
            raise Exception("AI提取花型失败：未获得结果")

        # 精细模式直接返回原结果，多张图已在上游处理
        if pattern_type == "fine":
            return raw_result

        result_urls = [url.strip() for url in raw_result.split(",") if url.strip()]
        if not result_urls:
            raise Exception("AI提取花型失败：结果URL无效")

        enhanced_urls: List[str] = []
        for url in result_urls:
            try:
                # 通用 / 定位花：调用美图高清模型
                meitu_options = {
                    "engine": "meitu_v2",
                    "sr_num": 4,
                    "task": options.get("task", "/v1/Ultra_High_Definition_V2/478332"),
                    "task_type": options.get("task_type", "formula"),
                    "sync_timeout": options.get("sync_timeout", 30),
                    "rsp_media_type": options.get("rsp_media_type", "url"),
                }
                enhanced = await self.upscale_image(
                    url,
                    scale_factor=4,
                    options=meitu_options,
                )

                enhanced_urls.extend(
                    [item.strip() for item in enhanced.split(",") if item.strip()]
                )
            except Exception as exc:
                logger.warning(
                    "Pattern enhancement failed for %s with pattern_type=%s: %s. Falling back to raw result.",
                    url,
                    pattern_type,
                    str(exc),
                )
                enhanced_urls.append(url)

        return ",".join(enhanced_urls)

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
        """调用GQCH实现智能扩图"""
        filename = original_filename or "upload.png"
        return await self.gqch_client.expand_image(image_bytes, filename, options)

    # 矢量化相关方法
    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG) - 使用Vectorizer.ai API"""
        return await self.vectorizer_client.vectorize_image(image_bytes, options)

    async def vectorize_image_a8(
        self,
        image_bytes: bytes,
        fmt: str = 'eps',
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        AI矢量化 - 使用A8矢量转换API，支持EPS和SVG格式

        Args:
            image_bytes: 图片字节数据
            fmt: 输出格式 'eps' 或 'svg'
            options: 额外选项（目前主要用于兼容性）

        Returns:
            保存的矢量文件URL路径
        """
        return await self.a8_vectorizer_client.image_to_vector(image_bytes, fmt=fmt)

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
        return await self.a8_vectorizer_client.image_to_eps(image_bytes)

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
        return await self.a8_vectorizer_client.image_to_svg(image_bytes)

    # 去水印相关方法
    async def remove_watermark(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI智能去水印（使用Dewatermark.ai API）"""
        return await self.dewatermark_client.remove_watermark(image_bytes, options)

    # 无损放大相关方法
    async def upscale_image(
        self,
        image_url: str,
        scale_factor: int = 2,
        custom_width: Optional[int] = None,
        custom_height: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        image_bytes: Optional[bytes] = None,
    ) -> str:
        """无损放大图片，支持多种引擎"""
        options = options or {}
        engine = (options.get("engine") or "meitu_v2").strip().lower()

        # 准备可供第三方访问的图片URL
        public_url, _ = await self._prepare_image_for_external_api(
            image_url=image_url,
            image_bytes=image_bytes,
            purpose="upscale",
        )

        if engine == "meitu_v2":
            return await self._upscale_with_meitu_v2(
                public_url,
                scale_factor=scale_factor,
                options=options,
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

        return image_url, image_bytes

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
            raise Exception(f"AI无损放大失败: {str(exc)}")

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

    # 即梦特效相关方法
    async def convert_flat_to_3d(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI平面转3D"""
        try:
            image_url = await self._prepare_image_for_jimeng(image_bytes, "temp_flat3d")

            prompt = "将图片里的图案转换成3d立体效果，鲜艳颜色，精致细节。"

            data = {
                "Action": "CVSync2AsyncSubmitTask",
                "Version": "2022-08-31",
                "req_key": "jimeng_t2i_v40",
                "prompt": prompt,
                "image_urls": [image_url],
                "size": 2048 * 2048,
                "scale": 0.75,
                "force_single": True,
                "min_ratio": 1 / 3,
                "max_ratio": 3,
            }

            self._apply_jimeng_options(data, options)
            logger.info("Sending flat-to-3D request with image URL: %s", image_url)

            return await self._execute_jimeng_task(
                data,
                log_label="Flat to 3D conversion",
                result_prefix="flat3d",
            )

        except Exception as exc:
            logger.error("Convert flat to 3D failed: %s", str(exc))
            raise Exception(f"AI平面转3D失败: {str(exc)}")

    async def enhance_embroidery(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI毛线刺绣增强"""
        try:
            image_url = await self._prepare_image_for_jimeng(image_bytes, "temp_embroidery")

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
            
            data = {
                "Action": "CVSync2AsyncSubmitTask",
                "Version": "2022-08-31",
                "req_key": "jimeng_t2i_v40",
                "prompt": prompt,
                "image_urls": [image_url],
                "size": 2048 * 2048,  # 2K分辨率
                "scale": 0.7,  # 文本描述影响程度
                "force_single": True,  # 强制生成单图
                "min_ratio": 1/3,
                "max_ratio": 3
            }
            
            self._apply_jimeng_options(data, options)
            logger.info("Sending embroidery enhancement request with image URL: %s", image_url)

            return await self._execute_jimeng_task(
                data,
                log_label="Embroidery enhancement",
                result_prefix="embroidery",
            )

        except Exception as e:
            logger.error(f"Enhance embroidery failed: {str(e)}")
            raise Exception(f"毛线刺绣增强失败: {str(e)}")


# 创建全局AI客户端实例
ai_client = AIClient()
