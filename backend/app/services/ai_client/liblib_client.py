import asyncio
import base64
import hashlib
import hmac
import logging
import time
import uuid
from typing import Dict, List

import httpx

from app.core.config import settings
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class LiblibUpscaleAPI:
    """Liblib AI高清放大API客户端"""
    
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
        try:
            async with api_limiter.slot("liblib"):
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(full_url, params=params, json=payload)
                    response.raise_for_status()
                    return response.json()
        except httpx.HTTPStatusError as e:
            raise AIClientException(
                message=f"Liblib生成图片请求失败: {e.response.status_code}",
                api_name="Liblib",
                status_code=e.response.status_code,
                response_body=e.response.text,
                request_data={"image_url": image_url, "megapixels": megapixels},
            ) from e
        except httpx.RequestError as e:
            raise AIClientException(
                message=f"Liblib生成图片网络错误: {str(e)}",
                api_name="Liblib",
                request_data={"image_url": image_url, "megapixels": megapixels},
            ) from e

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
        try:
            async with api_limiter.slot("liblib"):
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(full_url, params=params, json=payload)
                    response.raise_for_status()
                    return response.json()
        except httpx.HTTPStatusError as e:
            raise AIClientException(
                message=f"Liblib查询状态请求失败: {e.response.status_code}",
                api_name="Liblib",
                status_code=e.response.status_code,
                response_body=e.response.text,
                request_data={"generate_uuid": generate_uuid},
            ) from e
        except httpx.RequestError as e:
            raise AIClientException(
                message=f"Liblib查询状态网络错误: {str(e)}",
                api_name="Liblib",
                request_data={"generate_uuid": generate_uuid},
            ) from e

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
                raise AIClientException(
                    message=f"Liblib API错误: {status_data.get('msg', '未知错误')}",
                    api_name="Liblib",
                    status_code=200,
                    response_body=status_data,
                    request_data={"generate_uuid": generate_uuid},
                )
            
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
            raise AIClientException(
                message=f"Liblib提交任务失败: {generate_response.get('msg', '未知错误')}",
                api_name="Liblib",
                status_code=200,
                response_body=generate_response,
                request_data={"image_url": image_url, "megapixels": megapixels},
            )
        
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
