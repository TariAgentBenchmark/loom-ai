import asyncio
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

import httpx

from app.core.config import settings
from app.services.file_service import FileService
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


class VectorWebAPIClient:
    """基于 mm.kknc.site 的多服务器矢量转换API客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        poll_timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.vector_webapi_base_url).strip()
        self.api_key = api_key or settings.vector_webapi_key
        self.poll_timeout = poll_timeout or settings.vector_webapi_poll_timeout
        self.poll_interval = poll_interval or settings.vector_webapi_poll_interval
        self.file_service = FileService()

    @staticmethod
    def _normalize_format(vector_format: Optional[str]) -> str:
        fmt = (vector_format or ".svg").strip().lower()
        if not fmt.startswith("."):
            fmt = f".{fmt}"

        allowed = {".svg", ".eps", ".pdf", ".dxf", ".png"}
        return fmt if fmt in allowed else ".svg"

    @staticmethod
    def _extract_result_url(payload: dict) -> Optional[str]:
        msg = payload.get("msg")
        if isinstance(msg, str) and msg.startswith("http"):
            return msg.strip()
        return None

    async def _poll_result_url(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        timeout: int,
        interval: int,
    ) -> str:
        """轮询任务状态直到返回下载地址"""
        deadline = time.time() + timeout

        while True:
            if time.time() > deadline:
                raise AIClientException(
                    message="矢量化任务超时，请稍后重试",
                    api_name="VectorWebAPI",
                    request_data={"task_id": task_id},
                )

            response = await client.get(self.base_url, params={"bianhao": task_id})
            if response.status_code != 200:
                logger.warning(
                    "Vector API status request failed: %s - %s",
                    response.status_code,
                    response.text[:200],
                )
            else:
                data = response.json()
                if data.get("code") == 200:
                    result_url = self._extract_result_url(data)
                    if result_url:
                        return result_url
                elif data.get("code") in (400, 404):
                    raise AIClientException(
                        message=data.get("msg") or "矢量化任务不存在",
                        api_name="VectorWebAPI",
                        status_code=200,
                        response_body=data,
                        request_data={"task_id": task_id},
                    )

            await asyncio.sleep(interval)

    async def _download_and_save(self, url: str, vector_format: str) -> str:
        """下载矢量文件并保存到本地/OSS"""
        async with api_limiter.slot("vector_webapi"):
            async with httpx.AsyncClient(timeout=300.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.content

        ext = self._normalize_format(vector_format).lstrip(".")
        filename = f"vectorized_{uuid.uuid4().hex[:8]}.{ext}"

        saved_url = await self.file_service.save_upload_file(
            content,
            filename,
            subfolder="results",
        )
        logger.info("Vector file saved: %s", saved_url)
        return saved_url

    async def convert_image(
        self,
        image_bytes: bytes,
        vector_format: str = ".svg",
        filename: Optional[str] = None,
    ) -> str:
        """
        上传图片到矢量转换API并获取结果

        Args:
            image_bytes: 图片二进制数据
            vector_format: 输出格式(.svg/.eps/.pdf/.dxf/.png)
            filename: 原始文件名（用于日志与可选的 fileName 参数）

        Returns:
            已保存的矢量文件URL
        """
        if not self.api_key:
            raise Exception("未配置矢量化API密钥")

        fmt = self._normalize_format(vector_format)
        data = {
            "apiKey": self.api_key,
            "vectorFormat": fmt,
        }
        if filename:
            # 接口要求不带扩展名
            data["fileName"] = Path(filename).stem

        files = {
            "file": (filename or "upload.jpg", image_bytes, "image/jpeg"),
        }

        try:
            async with api_limiter.slot("vector_webapi"):
                client = httpx.AsyncClient(timeout=300.0)
                try:
                    logger.info("Uploading image to vector API, format=%s", fmt)
                    response = await client.post(
                        self.base_url,
                        data=data,
                        files=files,
                    )
                    response.raise_for_status()
                    payload = response.json()

                    if payload.get("code") != 200:
                        raise AIClientException(
                            message=payload.get("msg") or "矢量化服务异常",
                            api_name="VectorWebAPI",
                            status_code=200,
                            response_body=payload,
                            request_data=data,
                        )

                    # 如果直接返回了结果URL，直接下载保存
                    result_url = self._extract_result_url(payload)
                    if not result_url:
                        task_id = payload.get("bianhao")
                        if not task_id:
                            raise AIClientException(
                                message="矢量化任务创建失败，缺少任务编号",
                                api_name="VectorWebAPI",
                                status_code=200,
                                response_body=payload,
                                request_data=data,
                            )

                        logger.info("Vector task created: %s, start polling", task_id)
                        result_url = await self._poll_result_url(
                            client,
                            task_id,
                            timeout=self.poll_timeout,
                            interval=self.poll_interval,
                        )

                    return await self._download_and_save(result_url, fmt)
                finally:
                    await client.aclose()

        except httpx.HTTPStatusError as e:
            raise AIClientException(
                message=f"矢量化请求失败: {e.response.status_code}",
                api_name="VectorWebAPI",
                status_code=e.response.status_code,
                response_body=e.response.text,
                request_data=data,
            ) from e
        except httpx.RequestError as e:
            raise AIClientException(
                message=f"矢量化网络错误: {str(e)}",
                api_name="VectorWebAPI",
                request_data=data,
            ) from e
        except AIClientException:
            raise
        except Exception as exc:
            logger.error("Vector conversion failed: %s", str(exc))
            raise AIClientException(
                message=f"矢量化失败: {str(exc)}",
                api_name="VectorWebAPI",
            ) from exc
