import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from io import BytesIO
from random import uniform
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class LiblibUpscaleAPI:
    """Liblib AI无损放大API客户端"""
    
    def __init__(self, access_key: str, secret_key: str, base_url: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url or settings.liblib_api_url
    
    def _generate_signature(self, url_path: str, timestamp: str, nonce: str) -> str:
        """生成签名"""
        # 构造原文
        original_text = f"{url_path}&{timestamp}&{nonce}"
        
        # 使用hmacsha1加密
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            original_text.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # 生成URL安全的base64编码
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        return signature_b64
    
    def _get_common_params(self, url_path: str) -> Dict[str, str]:
        """获取通用参数"""
        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        signature = self._generate_signature(url_path, timestamp, nonce)
        
        return {
            "AccessKey": self.access_key,
            "Signature": signature,
            "Timestamp": timestamp,
            "SignatureNonce": nonce
        }
    
    async def generate_image(self, image_url: str, megapixels: float = 8.0) -> Dict:
        """
        生成高清放大图片
        
        Args:
            image_url: 输入图片的URL
            megapixels: 像素数量，范围0.01-16，默认8
            
        Returns:
            生成任务的响应数据
        """
        url_path = "/api/generate/comfyui/app"
        full_url = f"{self.base_url}{url_path}"
        
        # 构造请求参数
        payload = {
            "templateUuid": settings.liblib_template_uuid,
            "generateParams": {
                "34": {
                    "class_type": "ImageScaleToTotalPixels",
                    "inputs": {
                        "megapixels": megapixels
                    }
                },
                "233": {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": image_url
                    }
                },
                "workflowUuid": settings.liblib_workflow_uuid
            }
        }
        
        # 获取签名参数
        params = self._get_common_params(url_path)
        
        # 发送请求
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(full_url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def get_generate_status(self, generate_uuid: str) -> Dict:
        """
        查询生图任务状态
        
        Args:
            generate_uuid: 生成任务的UUID
            
        Returns:
            任务状态数据
        """
        url_path = "/api/generate/comfy/status"
        full_url = f"{self.base_url}{url_path}"
        
        # 构造请求体
        payload = {
            "generateUuid": generate_uuid
        }
        
        # 获取签名参数
        params = self._get_common_params(url_path)
        
        # 发送请求
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(full_url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def wait_for_completion(self, generate_uuid: str, poll_interval: int = 5, timeout: int = 300) -> Dict:
        """
        等待任务完成
        
        Args:
            generate_uuid: 生成任务的UUID
            poll_interval: 轮询间隔（秒）
            timeout: 超时时间（秒）
            
        Returns:
            最终的任务状态数据
        """
        start_time = time.time()
        
        while True:
            # 检查超时
            if time.time() - start_time > timeout:
                raise TimeoutError("任务执行超时")
            
            # 查询状态
            status_data = await self.get_generate_status(generate_uuid)
            
            # 检查状态码
            if status_data.get("code") != 0:
                raise Exception(f"API错误: {status_data.get('msg', '未知错误')}")
            
            data = status_data.get("data", {})
            generate_status = data.get("generateStatus")
            
            # 任务完成状态
            if generate_status in [5, 6]:  # 5:成功, 6:失败
                return status_data
            
            # 显示进度
            percent = data.get("percentCompleted", 0)
            logger.info(f"任务进度: {percent * 100:.1f}%")
            
            # 等待下一次轮询
            await asyncio.sleep(poll_interval)
    
    async def generate_and_wait(self, image_url: str, megapixels: float = 8.0) -> List[str]:
        """
        生成图片并等待完成，返回图片URL列表
        
        Args:
            image_url: 输入图片的URL
            megapixels: 像素数量
            
        Returns:
            生成的图片URL列表
        """
        # 1. 提交生成任务
        generate_response = await self.generate_image(image_url, megapixels)
        
        if generate_response.get("code") != 0:
            raise Exception(f"提交任务失败: {generate_response.get('msg', '未知错误')}")
        
        generate_uuid = generate_response["data"]["generateUuid"]
        logger.info(f"任务已提交，UUID: {generate_uuid}")
        
        # 2. 等待任务完成
        final_status = await self.wait_for_completion(generate_uuid)
        
        # 3. 提取图片URL
        data = final_status.get("data", {})
        images = data.get("images", [])
        
        # 只返回审核通过的图片
        approved_images = [
            img["imageUrl"] for img in images
            if img.get("auditStatus") == 3  # 3:审核通过
        ]
        
        return approved_images


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
        self.jimeng_region = "cn-north-1"
        self.jimeng_service = "cv"
        
        # Liblib API配置
        self.liblib_client = LiblibUpscaleAPI(
            access_key=settings.liblib_access_key,
            secret_key=settings.liblib_secret_key,
            base_url=settings.liblib_api_url
        )
    
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
    
    async def _make_jimeng_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送即梦API请求"""
        url = f"{self.jimeng_base_url}{endpoint}"
        
        if not self.jimeng_api_key or not self.jimeng_api_secret:
            raise Exception("即梦API密钥未配置")

        # 添加查询参数
        query_params = {
            "Action": data.get("Action", "CVSync2AsyncSubmitTask"),
            "Version": data.get("Version", "2022-08-31"),
        }

        canonical_querystring = "&".join(
            f"{key}={query_params[key]}" for key in sorted(query_params)
        )
        full_url = f"{url}?{canonical_querystring}" if canonical_querystring else url

        parsed_url = urlparse(full_url)
        canonical_uri = parsed_url.path or "/"
        host = parsed_url.netloc
        
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
        if "task_id" in data:
            request_data["task_id"] = data["task_id"]
        
        body_json = json.dumps(request_data, ensure_ascii=False, separators=(",", ":"))
        body_bytes = body_json.encode("utf-8")

        payload_hash = hashlib.sha256(body_bytes).hexdigest()
        content_type = "application/json"
        method_upper = method.upper()

        timestamp = datetime.datetime.utcnow()
        current_date = timestamp.strftime("%Y%m%dT%H%M%SZ")
        datestamp = timestamp.strftime("%Y%m%d")

        signed_headers = "content-type;host;x-content-sha256;x-date"
        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{host}\n"
            f"x-content-sha256:{payload_hash}\n"
            f"x-date:{current_date}\n"
        )

        canonical_request = (
            f"{method_upper}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{payload_hash}"
        )

        algorithm = "HMAC-SHA256"
        credential_scope = f"{datestamp}/{self.jimeng_region}/{self.jimeng_service}/request"
        string_to_sign = (
            f"{algorithm}\n"
            f"{current_date}\n"
            f"{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        k_date = _sign(self.jimeng_api_secret.encode("utf-8"), datestamp)
        k_region = _sign(k_date, self.jimeng_region)
        k_service = _sign(k_region, self.jimeng_service)
        signing_key = _sign(k_service, "request")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} "
            f"Credential={self.jimeng_api_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers = {
            "Content-Type": content_type,
            "Authorization": authorization_header,
            "X-Date": current_date,
            "X-Content-Sha256": payload_hash,
            "Host": host,
        }

        max_retries = 3
        backoff_base = 1.5

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.request(
                        method=method_upper,
                        url=full_url,
                        headers=headers,
                        content=body_bytes,
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

    async def process_image_gpt4o(self, image_bytes: bytes, prompt: str, mime_type: str = "image/jpeg", n: int = 1) -> Dict[str, Any]:
        """使用GPT-4o-image-vip处理图片"""
        url = f"{self.base_url}/v1/images/edits"
        
        # 准备multipart form数据
        files = {
            'image': ('image.png', BytesIO(image_bytes), mime_type)
        }
        
        data = {
            'model': 'gpt-4o-image-vip',
            'prompt': prompt,
            'n': str(n),
            'size': '1024x1024'
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"Processing image with GPT-4o (n={n}): {prompt[:100]}...")
        
        max_retries = 3
        backoff_base = 1.5
        
        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    return response.json()
            
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                body = exc.response.text
                if 500 <= status < 600 and attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "GPT-4o API request failed with %s (attempt %s/%s). Body: %s. Retrying in %.2fs",
                        status,
                        attempt,
                        max_retries,
                        body,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
                
                logger.error(f"GPT-4o API request failed: {status} - {body}")
                raise Exception(f"GPT-4o服务请求失败: {status}")
            
            except httpx.RequestError as exc:
                if attempt < max_retries:
                    wait_seconds = backoff_base * (2 ** (attempt - 1)) + uniform(0, 0.5)
                    logger.warning(
                        "GPT-4o API request error '%s' (attempt %s/%s). Retrying in %.2fs",
                        exc,
                        attempt,
                        max_retries,
                        wait_seconds,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
                
                logger.error(f"GPT-4o API request error: {str(exc)}")
                raise Exception(f"GPT-4o服务连接失败: {str(exc)}")
        
        raise Exception("GPT-4o服务连接失败: 未知错误")

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
        prompt = """将图案处理为四方连续的循环图案，适合大面积印花使用，图案可无缝拼接。"""
        
        result = await self.process_image_gemini(image_bytes, prompt, "image/png")
        return self._extract_image_url(result)

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
            "请仔细阅读用户的中文指令，根据指令对上传的图片进行精准修改。"
            "确保修改区域自然融入，避免出现明显的编辑痕迹或违背常识的结果。\n"
            f"用户指令：{instruction}"
        )

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
                "从提供的图片中严格提取图案，将图案设计的风格和内容元索还原为填充整个画面的平面印刷图像，"
                "准确识别并完整还原图案、纹理、颜色,等设计元素。1:1"
            )
        else:
            # 通用类型（默认）
            prompt = (
                "将图案设计的风格和内容元索还原为填充整个画面的平面印刷图像，"
                "准确识别并完整还原图案、纹理、颜色,等设计元素，干净底色，去掉布纹，"
                "缺失的花型要补齐出去，扩大花位，细节要细致还原保证细节一致。1:1"
            )

        # 精细效果类型使用GPT-4o模型，生成2张图片
        if pattern_type == "fine":
            result = await self.process_image_gpt4o(image_bytes, prompt, "image/png", n=2)
            image_urls = self._extract_image_urls(result)
            # 返回逗号分隔的URL字符串
            return ",".join(image_urls)
        else:
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
        """无损放大图片（使用Liblib AI API）
        
        注意：image_url必须是公开可访问的URL，不能是本地路径
        如果传入的是本地路径，需要先上传到OSS
        """
        try:
            # 检查是否是本地路径，如果是则需要上传到OSS
            if image_url.startswith("/files/"):
                logger.warning(f"Image URL is a local path: {image_url}, attempting to upload to OSS")
                
                # 导入OSS服务
                from app.services.oss_service import oss_service
                
                if not oss_service.is_configured():
                    raise Exception(
                        "图片URL必须是公开可访问的URL。"
                        "本地路径需要OSS配置才能使用。"
                        "请配置OSS或提供公开可访问的图片URL。"
                    )
                
                # 读取本地文件并上传到OSS
                import uuid
                # image_url 格式: /files/originals/temp_upscale_xxx.jpg
                # 需要转换为: ./uploads/originals/temp_upscale_xxx.jpg
                relative_path = image_url.replace('/files/', '')  # originals/temp_upscale_xxx.jpg
                local_path = os.path.join(settings.upload_path, relative_path)
                
                if not os.path.exists(local_path):
                    raise Exception(f"本地文件不存在: {local_path}")
                
                with open(local_path, "rb") as f:
                    image_bytes = f.read()
                
                # 上传到OSS
                temp_filename = f"temp_upscale_{uuid.uuid4().hex[:8]}.jpg"
                image_url = await oss_service.upload_image_for_jimeng(image_bytes, temp_filename)
                logger.info(f"Uploaded image to OSS: {image_url}")
            
            # 根据scale_factor确定megapixels参数
            # Liblib API使用megapixels参数来控制放大倍数
            # 默认8.0百万像素，可以根据需要调整
            megapixels = 8.0
            
            # 如果提供了自定义选项，使用自定义的megapixels值
            if options and "megapixels" in options:
                megapixels = options["megapixels"]
            else:
                # 根据scale_factor调整megapixels
                if scale_factor == 2:
                    megapixels = 4.0  # 2倍放大对应4百万像素
                elif scale_factor == 4:
                    megapixels = 16.0  # 4倍放大对应16百万像素
                # 其他情况保持默认8.0百万像素
            
            # 确保megapixels在有效范围内(0.01-16)
            megapixels = max(0.01, min(16.0, megapixels))
            
            logger.info(f"Sending Liblib AI upscale request with megapixels: {megapixels}")
            
            # 使用Liblib API进行图片放大
            result_images = await self.liblib_client.generate_and_wait(
                image_url=image_url,
                megapixels=megapixels
            )
            
            if not result_images:
                raise Exception("Liblib AI放大失败：未返回结果图片")
            
            # 下载并保存第一张结果图片
            result_url = result_images[0]
            logger.info(f"Liblib AI upscale completed successfully: {result_url}")
            
            # 下载图片
            result_bytes = await self._download_image_from_url(result_url)
            
            # 保存结果文件
            result_filename = f"upscaled_{uuid.uuid4().hex[:8]}.png"
            result_file_path = f"{settings.upload_path}/results/{result_filename}"
            
            os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
            with open(result_file_path, "wb") as f:
                f.write(result_bytes)
            
            # 返回文件URL格式
            logger.info(f"Result saved to: {result_file_path}")
            return f"/files/results/{result_filename}"
            
        except Exception as e:
            logger.error(f"Liblib AI upscale failed: {str(e)}")
            raise Exception(f"AI无损放大失败: {str(e)}")

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
            import uuid
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
                import os
                
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
            result = await self._make_jimeng_request("POST", "", data)
            
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
                
                status_result = await self.query_jimeng_task_status(task_id)
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
                            result_bytes = await self._download_image_from_url(result_url)
                            
                            # 保存结果文件
                            result_filename = f"embroidery_{uuid.uuid4().hex[:8]}.png"
                            result_file_path = f"{settings.upload_path}/results/{result_filename}"
                            
                            os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
                            with open(result_file_path, "wb") as f:
                                f.write(result_bytes)
                            
                            # 返回文件URL格式
                            logger.info(f"Result saved to: {result_file_path}")
                            return f"/files/results/{result_filename}"
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
                                
                                # 保存结果文件
                                result_filename = f"embroidery_{uuid.uuid4().hex[:8]}.png"
                                result_file_path = f"{settings.upload_path}/results/{result_filename}"
                                
                                # 确保目录存在
                                import os
                                os.makedirs(os.path.dirname(result_file_path), exist_ok=True)
                                with open(result_file_path, "wb") as f:
                                    f.write(result_bytes)
                                
                                # 返回文件URL格式
                                logger.info(f"Result saved to: {result_file_path}")
                                return f"/files/results/{result_filename}"
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
