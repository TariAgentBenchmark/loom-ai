import asyncio
import base64
import json
import logging
import os
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
        
        # 美图API配置
        self.meitu_base_url = settings.meitu_base_url
        self.meitu_api_key = settings.meitu_api_key
        self.meitu_api_secret = settings.meitu_api_secret
        self.meitu_headers = {
            "Content-Type": "application/json"
        }
        
        # Dewatermark.ai API配置
        self.dewatermark_api_key = settings.dewatermark_api_key
        self.dewatermark_url = "https://platform.dewatermark.ai/api/object_removal/v1/erase_watermark"
        
        # Vectorizer.ai API配置
        self.vectorizer_api_key = settings.vectorizer_api_key
        self.vectorizer_api_secret = settings.vectorizer_api_secret
        self.vectorizer_url = "https://vectorizer.ai/api/v1/vectorize"
        
        # 即梦API配置
        self.jimeng_api_key = settings.jimeng_api_key
        self.jimeng_api_secret = settings.jimeng_api_secret
        self.jimeng_base_url = settings.jimeng_base_url
    
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
    
    async def _make_meitu_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送美图API请求"""
        url = f"{self.meitu_base_url}{endpoint}"
        url_with_params = f"{url}?api_key={self.meitu_api_key}&api_secret={self.meitu_api_secret}"
        
        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method="POST",
                        url=url_with_params,
                        headers=self.meitu_headers,
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
                        "Meitu API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu API request failed: {status} - {body}")
                raise Exception(f"美图API请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Meitu API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu API request error: {str(exc)}")
                raise Exception(f"美图API连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("美图API连接失败: 未知错误")
    
    async def _make_meitu_async_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送美图异步API请求"""
        url = f"{self.meitu_base_url}{endpoint}"
        url_with_params = f"{url}?api_key={self.meitu_api_key}&api_secret={self.meitu_api_secret}"
        
        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method="POST",
                        url=url_with_params,
                        headers=self.meitu_headers,
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
                        "Meitu async API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu async API request failed: {status} - {body}")
                raise Exception(f"美图异步API请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Meitu async API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Meitu async API request error: {str(exc)}")
                raise Exception(f"美图异步API连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("美图异步API连接失败: 未知错误")
    
    async def _make_jimeng_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送即梦API请求"""
        url = f"{self.jimeng_base_url}{endpoint}"
        
        # 添加查询参数
        query_params = {
            "Action": data.get("Action", "CVSync2AsyncSubmitTask"),
            "Version": data.get("Version", "2022-08-31")
        }
        
        # 构建完整URL
        import urllib.parse
        query_string = urllib.parse.urlencode(query_params)
        full_url = f"{url}?{query_string}"
        
        # 准备请求数据
        request_data = {
            "req_key": data.get("req_key", "jimeng_t2i_v40"),
        }
        
        # 添加其他参数
        if "prompt" in data:
            request_data["prompt"] = data["prompt"]
        if "image_urls" in data:
            request_data["image_urls"] = data["image_urls"]
        if "size" in data:
            request_data["size"] = data["size"]
        if "width" in data:
            request_data["width"] = data["width"]
        if "height" in data:
            request_data["height"] = data["height"]
        if "scale" in data:
            request_data["scale"] = data["scale"]
        if "force_single" in data:
            request_data["force_single"] = data["force_single"]
        if "min_ratio" in data:
            request_data["min_ratio"] = data["min_ratio"]
        if "max_ratio" in data:
            request_data["max_ratio"] = data["max_ratio"]
        
        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method,
                        url=full_url,
                        json=request_data
                    )
                    response.raise_for_status()
                    return response.json()

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text
                if 500 <= status < 600 and attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Jimeng API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Jimeng API request failed: {status} - {body}")
                raise Exception(f"即梦API请求失败: {status}")

            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "Jimeng API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

                logger.error(f"Jimeng API request error: {str(exc)}")
                raise Exception(f"即梦API连接失败: {str(exc)}")

        # 理论上不会到达这里，保留兜底处理
        raise Exception("即梦API连接失败: 未知错误")
    
    async def query_jimeng_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询即梦异步任务状态"""
        data = {
            "Action": "CVSync2AsyncGetResult",
            "Version": "2022-08-31",
            "req_key": "jimeng_t2i_v40",
            "task_id": task_id
        }
        
        logger.info(f"Querying Jimeng task status: {task_id}")
        return await self._make_jimeng_request("POST", "", data)
    
    async def query_meitu_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询美图异步任务状态"""
        endpoint = "/api/v1/sdk/sync/status"
        data = {
            "task_id": task_id
        }
        
        logger.info(f"Querying Meitu task status: {task_id}")
        return await self._make_meitu_async_request(endpoint, data)

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
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.vectorizer_url,
                    files=files,
                    data=data,
                    auth=auth
                )
                response.raise_for_status()
                
                # 保存结果为SVG文件
                import uuid
                filename = f"vectorized_{uuid.uuid4().hex[:8]}.svg"
                file_path = f"{settings.upload_path}/results/{filename}"
                
                # 确保目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # 保存文件
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                # 返回文件URL格式，让处理服务可以访问
                return f"/files/results/{filename}"
            
        except Exception as e:
            logger.error(f"Vectorize image failed: {str(e)}")
            raise Exception(f"矢量化失败: {str(e)}")

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
        """AI智能去水印（使用Dewatermark.ai API）"""
        try:
            # 将图片转换为base64
            image_base64 = self._image_to_base64(image_bytes, "JPEG")
            
            # 准备文件数据
            files = {}
            
            # 添加原始图片
            files["original_preview_image"] = ("original_preview_image.jpeg",
                                             BytesIO(base64.b64decode(image_base64)))
            
            # 添加mask_brush（如果提供）
            if options and "mask_brush" in options:
                mask_brush_path = options["mask_brush"]
                if os.path.exists(mask_brush_path):
                    files["mask_brush"] = ("mask_brush.png", open(mask_brush_path, "rb"))
            
            # 添加remove_text参数
            files["remove_text"] = (None, "true")
            
            # 准备请求头
            headers = {
                "X-API-KEY": self.dewatermark_api_key
            }
            
            logger.info("Sending request to Dewatermark.ai API")
            
            # 发送请求
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    self.dewatermark_url,
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                result = response.json()
            
            # 关闭打开的文件
            if "mask_brush" in files and hasattr(files["mask_brush"][1], 'close'):
                files["mask_brush"][1].close()
            
            # 检查响应
            if "edited_image" not in result:
                logger.error(f"Dewatermark.ai API unexpected response: {result}")
                raise Exception("Dewatermark.ai API响应格式错误")
            
            # 提取处理后的图片数据
            edited_image = result["edited_image"]
            if "image" in edited_image:
                # 保存处理后的图片并返回URL
                return self._save_base64_image(edited_image["image"])
            
            raise Exception("无法从Dewatermark.ai API响应中提取处理后的图片")
            
        except Exception as e:
            logger.error(f"Remove watermark failed: {str(e)}")
            raise Exception(f"智能去水印失败: {str(e)}")

    async def denoise_image(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI布纹去噪"""
        prompt = "Remove the fabric texture from this image, make the surface smooth while preserving the original color tone and overall appearance as much as possible."
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)
    
    async def upscale_image(
        self,
        image_url: str,
        scale_factor: int = 2,
        custom_width: Optional[int] = None,
        custom_height: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """无损放大图片（使用美图API）"""
        try:
            # 构建参数
            if custom_width and custom_height:
                # 自定义尺寸放大
                params = {
                    "sr_mode": 2,  # 自定义尺寸放大
                    "ir_mode": 4,
                    "rsp_media_type": "url",
                    "save_photo_format": 1,
                    "max_width": 8000,
                    "max_height": 8000,
                    "sr_size_w": custom_width,
                    "sr_size_h": custom_height
                }
            else:
                # 固定倍数放大
                params = {
                    "sr_mode": 1,  # 2、4、8倍放大
                    "ir_mode": 4,
                    "rsp_media_type": "url",
                    "save_photo_format": 1,
                    "max_width": 8000,
                    "max_height": 8000,
                    "sr_num": scale_factor
                }
            
            # 构建请求数据
            data = {
                "params": json.dumps({"parameter": params}),
                "init_images": [{
                    "url": image_url
                }],
                "task": "v1/mtimagesr_async",
                "task_type": "mtlab"
            }
            
            # 如果提供了自定义任务ID，添加到请求中
            if options and "task_id" in options:
                data["task_id"] = options["task_id"]
            
            # 如果提供了同步超时时间，添加到请求中
            if options and "sync_timeout" in options:
                data["sync_timeout"] = options["sync_timeout"]
            
            logger.info(f"Sending upscale request to Meitu API with scale factor: {scale_factor}")
            result = await self._make_meitu_async_request("/api/v1/sdk/sync/push", data)
            
            # 检查响应是否包含错误
            if "error_code" in result:
                error_code = result["error_code"]
                error_msg = result.get("error_msg", "未知错误")
                logger.error(f"Meitu upscale API error: {error_code} - {error_msg}")
                raise Exception(f"美图无损放大API处理失败: {error_msg}")
            
            # 检查任务状态
            if "data" in result:
                task_data = result["data"]
                status = task_data.get("status", -1)
                
                if status == 10:  # 任务成功
                    if "result" in task_data and "urls" in task_data["result"]:
                        urls = task_data["result"]["urls"]
                        if urls and len(urls) > 0:
                            return urls[0]
                
                elif status == 9:  # 需要查询结果
                    if "result" in task_data and "id" in task_data["result"]:
                        task_id = task_data["result"]["id"]
                        logger.info(f"Task {task_id} requires status polling")
                        
                        # 轮询任务状态
                        max_attempts = 30  # 最多轮询30次
                        for attempt in range(max_attempts):
                            await asyncio.sleep(2)  # 等待2秒
                            
                            status_result = await self.query_meitu_task_status(task_id)
                            if "data" in status_result:
                                status_data = status_result["data"]
                                current_status = status_data.get("status", -1)
                                
                                if current_status == 10:  # 任务成功
                                    if "result" in status_data and "urls" in status_data["result"]:
                                        urls = status_data["result"]["urls"]
                                        if urls and len(urls) > 0:
                                            return urls[0]
                                
                                elif current_status == 2:  # 任务失败
                                    error_msg = status_data.get("msg", "任务执行失败")
                                    raise Exception(f"无损放大任务失败: {error_msg}")
                                
                                logger.info(f"Task {task_id} status: {current_status}, progress: {status_data.get('progress', 0)}")
                        
                        raise Exception(f"无损放大任务超时: {task_id}")
                
                elif status == 2:  # 任务失败
                    error_msg = task_data.get("msg", "任务执行失败")
                    raise Exception(f"无损放大任务失败: {error_msg}")
            
            raise Exception("无法从美图无损放大API响应中提取结果")
            
        except Exception as e:
            logger.error(f"Upscale image failed: {str(e)}")
            raise Exception(f"无损放大失败: {str(e)}")

    async def enhance_embroidery(
        self,
        image_bytes: bytes,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """AI毛线刺绣增强（使用即梦API）"""
        try:
            # 将图片转换为base64并保存为临时文件
            import uuid
            import os
            
            # 生成临时文件名
            temp_filename = f"temp_embroidery_{uuid.uuid4().hex[:8]}.jpg"
            temp_file_path = f"{settings.upload_path}/originals/{temp_filename}"
            
            # 确保目录存在
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
            
            # 保存临时文件
            with open(temp_file_path, "wb") as f:
                f.write(image_bytes)
            
            # 构建图片URL（这里需要根据实际的文件服务配置调整）
            image_url = f"/files/originals/{temp_filename}"
            
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
            
            logger.info("Sending embroidery enhancement request to Jimeng API")
            result = await self._make_jimeng_request("POST", "", data)
            
            # 检查响应是否包含错误
            if "code" in result and result["code"] != 10000:
                error_msg = result.get("message", "未知错误")
                logger.error(f"Jimeng embroidery API error: {result['code']} - {error_msg}")
                raise Exception(f"即梦毛线刺绣API处理失败: {error_msg}")
            
            # 提取任务ID
            if "data" not in result or "task_id" not in result["data"]:
                logger.error(f"Jimeng embroidery API unexpected response: {result}")
                raise Exception("即梦毛线刺绣API响应格式错误")
            
            task_id = result["data"]["task_id"]
            logger.info(f"Jimeng embroidery task created: {task_id}")
            
            # 轮询任务状态
            max_attempts = 30  # 最多轮询30次
            for attempt in range(max_attempts):
                await asyncio.sleep(3)  # 等待3秒
                
                status_result = await self.query_jimeng_task_status(task_id)
                if "code" in status_result and status_result["code"] != 10000:
                    error_msg = status_result.get("message", "未知错误")
                    logger.error(f"Jimeng embroidery status query error: {status_result['code']} - {error_msg}")
                    raise Exception(f"即梦毛线刺绣状态查询失败: {error_msg}")
                
                if "data" in status_result:
                    status_data = status_result["data"]
                    current_status = status_data.get("status", "")
                    
                    if current_status == "done":  # 任务成功
                        if "image_urls" in status_data and status_data["image_urls"]:
                            image_urls = status_data["image_urls"]
                            if image_urls and len(image_urls) > 0:
                                # 下载并保存结果图片
                                result_url = image_urls[0]
                                result_bytes = await self._download_image_from_url(result_url)
                                
                                # 保存结果文件
                                result_filename = f"embroidery_{uuid.uuid4().hex[:8]}.png"
                                result_file_path = f"{settings.upload_path}/results/{result_filename}"
                                
                                os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
                                with open(result_file_path, "wb") as f:
                                    f.write(result_bytes)
                                
                                # 返回文件URL格式
                                return f"/files/results/{result_filename}"
                    
                    elif current_status in ["failed", "expired", "not_found"]:
                        error_msg = status_data.get("message", "任务执行失败")
                        raise Exception(f"毛线刺绣任务失败: {error_msg}")
                    
                    logger.info(f"Jimeng embroidery task {task_id} status: {current_status}")
            
            raise Exception(f"毛线刺绣任务超时: {task_id}")
            
        except Exception as e:
            logger.error(f"Enhance embroidery failed: {str(e)}")
            raise Exception(f"毛线刺绣增强失败: {str(e)}")
    
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
