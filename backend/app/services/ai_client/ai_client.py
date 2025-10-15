import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.dewatermark_client import DewatermarkClient
from app.services.ai_client.gemini_client import GeminiClient
from app.services.ai_client.gpt4o_client import GPT4oClient
from app.services.ai_client.image_utils import ImageProcessingUtils
from app.services.ai_client.jimeng_client import JimengClient
from app.services.ai_client.liblib_client import LiblibUpscaleAPI
from app.services.ai_client.meitu_client import MeituClient
from app.services.ai_client.vectorizer_client import VectorizerClient

logger = logging.getLogger(__name__)


class AIClient:
    """AI服务客户端 - 模块化版本"""
    
    def __init__(self):
        # 初始化各个服务客户端
        self.gpt4o_client = GPT4oClient()
        self.gemini_client = GeminiClient()
        self.jimeng_client = JimengClient()
        self.vectorizer_client = VectorizerClient()
        self.dewatermark_client = DewatermarkClient()
        self.meitu_client = MeituClient()
        self.image_utils = ImageProcessingUtils()
        self.base_client_utils = BaseAIClient()
        
        # Liblib API配置
        self.liblib_client = LiblibUpscaleAPI(
            access_key=settings.liblib_access_key,
            secret_key=settings.liblib_secret_key,
            base_url=settings.liblib_api_url
        )

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

    # 图片处理工具方法
    async def seamless_pattern_conversion(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI四方连续转换"""
        return await self.image_utils.seamless_pattern_conversion(image_bytes, options)

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
                if pattern_type == "creative_plus":
                    # 创造力+N：调用 Liblib 高清模型
                    enhanced = await self.upscale_image(
                        url,
                        scale_factor=4,
                        options={"engine": "creative_plus"},
                    )
                else:
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

    # 矢量化相关方法
    async def vectorize_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI矢量化(转SVG) - 使用Vectorizer.ai API"""
        return await self.vectorizer_client.vectorize_image(image_bytes, options)

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
        engine = (options.get("engine") or "creative_plus").strip().lower()

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

    # 毛线刺绣增强相关方法
    async def enhance_embroidery(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI毛线刺绣增强"""
        try:
            # 导入OSS服务
            from app.services.oss_service import oss_service
            
            # 生成临时文件名
            temp_filename = f"temp_embroidery_{uuid.uuid4().hex[:8]}.jpg"
            
            # 上传图片到OSS获取公开URL
            logger.info(f"OSS配置状态: {'已配置' if oss_service.is_configured() else '未配置'}")
            if oss_service.is_configured():
                logger.info("上传图片到OSS以供处理使用")
                image_url = await oss_service.upload_image_for_jimeng(image_bytes, temp_filename)
                logger.info(f"OSS上传完成，获得的URL: {image_url}")
            else:
                # 如果OSS未配置，保存到本地并使用相对路径（不推荐用于生产环境）
                logger.warning("OSS未配置，使用本地存储")
                
                temp_file_path = f"{settings.upload_path}/originals/{temp_filename}"
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                
                with open(temp_file_path, "wb") as f:
                    f.write(image_bytes)
                
                image_url = f"/files/originals/{temp_filename}"
                logger.warning(f"使用本地路径: {image_url}")
            
            # 构建请求参数
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
            
            # 如果提供了额外选项，添加到请求中
            if options:
                if "scale" in options:
                    data["scale"] = options["scale"]
                if "size" in options:
                    data["size"] = options["size"]
                if "width" in options and "height" in options:
                    data["width"] = options["width"]
                    data["height"] = options["height"]
                if "force_single" in options:
                    data["force_single"] = options["force_single"]
            
            logger.info(f"Sending embroidery enhancement request with image URL: {image_url}")
            result = await self.jimeng_client._make_jimeng_request("POST", "", data)
            
            # 检查响应是否包含错误
            if "code" in result and result["code"] != 10000:
                error_msg = result.get("message", "未知错误")
                logger.error(f"Embroidery enhancement API error: {result['code']} - {error_msg}")
                raise Exception(f"毛线刺绣增强处理失败: {error_msg}")
            
            # 提取任务ID
            if "data" not in result or "task_id" not in result["data"]:
                logger.error(f"Embroidery enhancement API unexpected response: {result}")
                raise Exception("毛线刺绣增强响应格式错误")
            
            task_id = result["data"]["task_id"]
            logger.info(f"Embroidery enhancement task created: {task_id}")
            
            # 轮询任务状态
            max_attempts = 40  # 最多轮询40次（增加到约2分钟）
            for attempt in range(max_attempts):
                # 动态调整等待时间：前20次等待3秒，后20次等待5秒
                wait_time = 3 if attempt < 20 else 5
                await asyncio.sleep(wait_time)
                
                status_result = await self.jimeng_client.query_task_status(task_id)
                if "code" in status_result and status_result["code"] != 10000:
                    error_msg = status_result.get("message", "未知错误")
                    logger.error(f"Embroidery enhancement status query error: {status_result['code']} - {error_msg}")
                    raise Exception(f"毛线刺绣增强状态查询失败: {error_msg}")
                
                if "data" in status_result:
                    status_data = status_result["data"]
                    current_status = status_data.get("status", "")
                    logger.info(f"Task {task_id} status: {current_status}")
                    logger.debug(f"Full status response: {status_result}")
                    
                    if current_status == "done":  # 任务成功
                        logger.info(f"Embroidery enhancement task {task_id} completed successfully")
                        
                        # 检查image_urls位置 - 可能在data中，也可能在根级别
                        image_urls = None
                        if "image_urls" in status_data and status_data["image_urls"]:
                            image_urls = status_data["image_urls"]
                        elif "image_urls" in status_result and status_result["image_urls"]:
                            image_urls = status_result["image_urls"]
                        
                        # 检查是否有二进制数据
                        binary_data = None
                        if "binary_data_base64" in status_data and status_data["binary_data_base64"]:
                            binary_data = status_data["binary_data_base64"]
                        elif "binary_data_base64" in status_result and status_result["binary_data_base64"]:
                            binary_data = status_result["binary_data_base64"]
                        
                        if image_urls and len(image_urls) > 0:
                            # 下载并保存结果图片
                            result_url = image_urls[0]
                            logger.info(f"Downloading result from: {result_url}")
                            result_bytes = await self.gemini_client._download_image_from_url(result_url)
                            saved_url = self.base_client_utils._save_image_bytes(result_bytes, prefix="embroidery")
                            logger.info("Result saved to: %s", saved_url)
                            return saved_url
                        elif binary_data:
                            # 处理base64编码的图片数据
                            logger.info("Processing base64 encoded image data")
                            try:
                                import base64
                                # 处理binary_data可能是列表的情况
                                if isinstance(binary_data, list):
                                    if binary_data and len(binary_data) > 0:
                                        binary_data = binary_data[0]
                                    else:
                                        logger.error("Binary data list is empty")
                                        raise Exception("二进制数据列表为空")
                                
                                # 确保binary_data是字符串
                                if not isinstance(binary_data, str):
                                    logger.error(f"Binary data is not a string: {type(binary_data)}")
                                    raise Exception(f"二进制数据格式错误: {type(binary_data)}")
                                
                                result_bytes = base64.b64decode(binary_data)
                                saved_url = self.base_client_utils._save_image_bytes(result_bytes, prefix="embroidery")
                                logger.info("Result saved to: %s", saved_url)
                                return saved_url
                            except Exception as e:
                                logger.error(f"Failed to process base64 image data: {str(e)}")
                                raise Exception(f"处理base64图片数据失败: {str(e)}")
                        else:
                            # 任务状态为done但没有结果，可能需要等待更长时间
                            if attempt < max_attempts - 1:  # 不是最后一次尝试
                                logger.warning(f"Task done but no results yet, retrying... (attempt {attempt + 1}/{max_attempts})")
                                continue
                            else:
                                logger.error("Task completed but no image URLs or binary data found in response")
                                logger.error(f"Status data: {status_data}")
                                logger.error(f"Full response: {status_result}")
                                raise Exception("任务完成但未找到结果图片")
                    
                    elif current_status in ["failed", "expired", "not_found"]:
                        error_msg = status_data.get("message", "任务执行失败")
                        raise Exception(f"毛线刺绣任务失败: {error_msg}")
                    
                    logger.info(f"Embroidery enhancement task {task_id} status: {current_status}")
            
            raise Exception(f"毛线刺绣任务超时: {task_id}")
            
        except Exception as e:
            logger.error(f"Enhance embroidery failed: {str(e)}")
            raise Exception(f"毛线刺绣增强失败: {str(e)}")


# 创建全局AI客户端实例
ai_client = AIClient()
