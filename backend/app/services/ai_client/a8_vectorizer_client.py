import asyncio
import logging
import time
import uuid
from typing import Optional, Dict, Any

import httpx
import urllib3

from app.services.file_service import FileService
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class A8VectorizerClient:
    """A8矢量转换API客户端"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or "https://a8.zifeiyuai.top:2345"
        self.base_url = self.base_url.rstrip('/')

    async def image_to_vector(
        self,
        image_bytes: bytes,
        fmt: str = 'eps',
        save_path: Optional[str] = None,
        timeout: int = 120,
        poll_interval: int = 2
    ) -> str:
        """
        上传图片 → 轮询 → 下载指定格式（eps/svg）

        Args:
            image_bytes: 图片字节数据
            fmt: 输出格式 'eps' 或 'svg'
            save_path: 保存路径（可选）
            timeout: 最大等待秒数
            poll_interval: 轮询间隔秒数

        Returns:
            保存的文件URL路径
        """
        fmt = (fmt or 'eps').lower()
        if fmt not in ('eps', 'svg'):
            fmt = 'eps'

        try:
            # 1) 上传图片并指定格式
            files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
            data = {'format': fmt}

            logger.info(f"Uploading image to A8 vectorizer API, format: {fmt}")

            async with api_limiter.slot("a8_vectorizer"):
                async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                    response = await client.post(
                        f"{self.base_url}/add_task",
                        files=files,
                        data=data
                    )

            if response.status_code != 200:
                raise AIClientException(
                    message="A8矢量化服务异常，联系管理员",
                    api_name="A8Vectorizer",
                    status_code=response.status_code,
                    response_body=response.text,
                    request_data={"format": fmt},
                )

            data = response.json()
            if data.get('code') != 0:
                raise AIClientException(
                    message=data.get('message') or "A8矢量化服务异常，联系管理员",
                    api_name="A8Vectorizer",
                    status_code=200,
                    response_body=data,
                    request_data={"format": fmt},
                )

            taskid = data.get('id') or data.get('taskid')
            if not taskid:
                raise AIClientException(
                    message="A8矢量化任务创建失败",
                    api_name="A8Vectorizer",
                    status_code=200,
                    response_body=data,
                    request_data={"format": fmt},
                )

            logger.info(f"Task created successfully: {taskid}")

            # 2) 轮询任务状态
            t0 = time.time()
            while True:
                async with api_limiter.slot("a8_vectorizer"):
                    async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                        response = await client.get(
                            f"{self.base_url}/try_get",
                            params={'taskid': taskid}
                        )

                if response.status_code != 200:
                    raise AIClientException(
                        message="A8矢量化查询状态失败",
                        api_name="A8Vectorizer",
                        status_code=response.status_code,
                        response_body=response.text,
                        request_data={"taskid": taskid},
                    )

                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"Task {taskid} completed successfully")
                    break
                elif result.get('code') == -1:
                    raise AIClientException(
                        message=result.get('message') or "A8矢量化任务失败",
                        api_name="A8Vectorizer",
                        status_code=200,
                        response_body=result,
                        request_data={"taskid": taskid},
                    )

                if time.time() - t0 > timeout:
                    raise AIClientException(
                        message="A8矢量化任务超时，请稍后重试",
                        api_name="A8Vectorizer",
                        request_data={"taskid": taskid, "timeout": timeout},
                    )

                logger.info(f"Task {taskid} still processing, waiting {poll_interval}s...")
                await asyncio.sleep(poll_interval)

            # 3) 下载文件
            async with api_limiter.slot("a8_vectorizer"):
                async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                    response = await client.get(
                        f"{self.base_url}/get_image",
                        params={'taskid': taskid}
                    )

            if response.status_code != 200:
                raise AIClientException(
                    message="A8矢量化下载文件失败",
                    api_name="A8Vectorizer",
                    status_code=response.status_code,
                    response_body=response.text,
                    request_data={"taskid": taskid},
                )

            filename = f"vectorized_{uuid.uuid4().hex[:8]}.{fmt}"
            file_service = FileService()
            saved_url = await file_service.save_upload_file(
                response.content,
                filename,
                subfolder="results",
            )
            logger.info("Vector file saved to storage: %s", saved_url)
            return saved_url

        except AIClientException:
            raise
        except Exception as e:
            logger.error(f"Vectorize image failed: {str(e)}")
            raise AIClientException(
                message=f"A8矢量化失败: {str(e)}",
                api_name="A8Vectorizer",
            ) from e

    # 兼容旧方法：仍然可用
    async def image_to_eps(
        self,
        image_bytes: bytes,
        save_eps_path: Optional[str] = None,
        timeout: int = 120,
        poll_interval: int = 2
    ) -> str:
        """
        上传图片并转换为EPS格式

        Args:
            image_bytes: 图片字节数据
            save_eps_path: EPS文件保存路径（可选）
            timeout: 最大等待秒数
            poll_interval: 轮询间隔秒数

        Returns:
            保存的EPS文件URL路径
        """
        return await self.image_to_vector(
            image_bytes,
            fmt='eps',
            save_path=save_eps_path,
            timeout=timeout,
            poll_interval=poll_interval
        )

    async def image_to_svg(
        self,
        image_bytes: bytes,
        save_svg_path: Optional[str] = None,
        timeout: int = 120,
        poll_interval: int = 2
    ) -> str:
        """
        上传图片并转换为SVG格式

        Args:
            image_bytes: 图片字节数据
            save_svg_path: SVG文件保存路径（可选）
            timeout: 最大等待秒数
            poll_interval: 轮询间隔秒数

        Returns:
            保存的SVG文件URL路径
        """
        return await self.image_to_vector(
            image_bytes,
            fmt='svg',
            save_path=save_svg_path,
            timeout=timeout,
            poll_interval=poll_interval
        )
