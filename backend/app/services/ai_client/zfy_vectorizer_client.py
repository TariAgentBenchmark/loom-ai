import asyncio
import logging
import time
import uuid
from typing import Optional

import httpx
import urllib3

from app.core.config import settings
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException
from app.services.file_service import FileService

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class ZfyVectorizerClient:
    """矢量化 API 客户端，兼容 zifeiyu /add_task 示例协议。"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        poll_timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.vector_zfy_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.vector_zfy_api_key
        self.poll_timeout = poll_timeout or settings.vector_zfy_poll_timeout
        self.poll_interval = poll_interval or settings.vector_zfy_poll_interval
        self.file_service = FileService()

    @staticmethod
    def _normalize_format(fmt: Optional[str]) -> str:
        normalized = (fmt or "eps").strip().lower().lstrip(".")
        return normalized if normalized in {"eps", "svg"} else "eps"

    @staticmethod
    def _detect_result_format(
        content: bytes,
        requested_fmt: str,
        headers: httpx.Headers,
    ) -> str:
        content_type = headers.get("content-type", "").lower()
        disposition = headers.get("content-disposition", "").lower()
        head = content[:256].lstrip().lower()

        if "postscript" in content_type or ".eps" in disposition:
            return "eps"
        if "svg" in content_type or ".svg" in disposition:
            return "svg"
        if head.startswith(b"%!ps"):
            return "eps"
        if head.startswith(b"<?xml") or head.startswith(b"<svg"):
            return "svg"

        return requested_fmt

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            raise AIClientException(
                message="未配置新矢量化API密钥",
                api_name="ZfyVectorizer",
            )
        return {"zfyai-api-key": self.api_key}

    async def image_to_vector(
        self,
        image_bytes: bytes,
        fmt: str = "eps",
        filename: Optional[str] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> str:
        fmt = self._normalize_format(fmt)
        wait_timeout = timeout or self.poll_timeout
        wait_interval = poll_interval or self.poll_interval
        request_headers = self.headers
        upload_filename = filename or "image.jpg"

        try:
            files = {"file": (upload_filename, image_bytes, "image/jpeg")}
            data = {"format": fmt}

            logger.info("Uploading image to ZFY vectorizer API, format=%s", fmt)
            async with api_limiter.slot("zfy_vectorizer"):
                async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                    response = await client.post(
                        f"{self.base_url}/add_task",
                        headers=request_headers,
                        files=files,
                        data=data,
                    )

            if response.status_code != 200:
                raise AIClientException(
                    message="新矢量化服务异常，联系管理员",
                    api_name="ZfyVectorizer",
                    status_code=response.status_code,
                    response_body=response.text,
                    request_data={"format": fmt},
                )

            payload = response.json()
            if payload.get("code") != 0:
                raise AIClientException(
                    message=payload.get("message") or "新矢量化服务异常，联系管理员",
                    api_name="ZfyVectorizer",
                    status_code=200,
                    response_body=payload,
                    request_data={"format": fmt},
                )

            task_id = payload.get("id") or payload.get("taskid")
            if not task_id:
                raise AIClientException(
                    message="新矢量化任务创建失败",
                    api_name="ZfyVectorizer",
                    status_code=200,
                    response_body=payload,
                    request_data={"format": fmt},
                )

            logger.info("ZFY vector task created: %s", task_id)

            start_time = time.time()
            while True:
                async with api_limiter.slot("zfy_vectorizer"):
                    async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                        response = await client.get(
                            f"{self.base_url}/try_get",
                            headers=request_headers,
                            params={"taskid": task_id},
                        )

                if response.status_code != 200:
                    raise AIClientException(
                        message="新矢量化查询状态失败",
                        api_name="ZfyVectorizer",
                        status_code=response.status_code,
                        response_body=response.text,
                        request_data={"taskid": task_id},
                    )

                result = response.json()
                if result.get("code") == 0:
                    logger.info("ZFY vector task completed: %s", task_id)
                    break
                if result.get("code") == -1:
                    raise AIClientException(
                        message=result.get("message") or "新矢量化任务失败",
                        api_name="ZfyVectorizer",
                        status_code=200,
                        response_body=result,
                        request_data={"taskid": task_id},
                    )

                if time.time() - start_time > wait_timeout:
                    raise AIClientException(
                        message="新矢量化任务超时，请稍后重试",
                        api_name="ZfyVectorizer",
                        request_data={"taskid": task_id, "timeout": wait_timeout},
                    )

                await asyncio.sleep(wait_interval)

            async with api_limiter.slot("zfy_vectorizer"):
                async with httpx.AsyncClient(timeout=300.0, verify=False) as client:
                    response = await client.get(
                        f"{self.base_url}/get_image",
                        headers=request_headers,
                        params={"taskid": task_id},
                    )

            if response.status_code != 200:
                raise AIClientException(
                    message="新矢量化下载文件失败",
                    api_name="ZfyVectorizer",
                    status_code=response.status_code,
                    response_body=response.text,
                    request_data={"taskid": task_id},
                )

            result_fmt = self._detect_result_format(
                response.content,
                requested_fmt=fmt,
                headers=response.headers,
            )
            result_filename = f"vectorized_{uuid.uuid4().hex[:8]}.{result_fmt}"
            saved_url = await self.file_service.save_upload_file(
                response.content,
                result_filename,
                subfolder="results",
                validate_dimensions=False,
                validate_file_size=False,
            )
            logger.info("ZFY vector file saved: %s", saved_url)
            return saved_url

        except AIClientException:
            raise
        except Exception as exc:
            logger.error("ZFY vectorize image failed: %s", exc)
            raise AIClientException(
                message=f"新矢量化失败: {str(exc)}",
                api_name="ZfyVectorizer",
            ) from exc

    async def image_to_eps(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> str:
        return await self.image_to_vector(
            image_bytes,
            fmt="eps",
            filename=filename,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    async def image_to_svg(
        self,
        image_bytes: bytes,
        filename: Optional[str] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> str:
        return await self.image_to_vector(
            image_bytes,
            fmt="svg",
            filename=filename,
            timeout=timeout,
            poll_interval=poll_interval,
        )
