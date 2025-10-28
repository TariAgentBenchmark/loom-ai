import asyncio
import logging
import time
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class A8VectorizerClient:
    """A8矢量化服务客户端"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        default_timeout: int = 120,
        default_poll_interval: int = 2,
    ) -> None:
        self.base_url = (base_url or settings.a8_vectorizer_base_url).rstrip("/")
        self.default_timeout = default_timeout
        self.default_poll_interval = default_poll_interval

    async def convert_to_eps(
        self,
        image_bytes: bytes,
        filename: str = "image.png",
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
    ) -> bytes:
        """上传图片并下载转换后的EPS文件内容"""
        timeout = timeout or self.default_timeout
        poll_interval = poll_interval or self.default_poll_interval

        if not self.base_url:
            raise Exception("服务异常，联系管理员")

        try:
            async with httpx.AsyncClient(verify=False, timeout=timeout) as client:
                files = {"file": (filename, image_bytes)}
                upload_resp = await client.post(f"{self.base_url}/add_task", files=files)
                upload_resp.raise_for_status()
                upload_data = upload_resp.json()

                if upload_data.get("code") != 0:
                    logger.error("A8 vectorizer upload failed: %s", upload_data)
                    raise Exception("服务异常，联系管理员")

                task_id = upload_data.get("id") or upload_data.get("taskid")
                if not task_id:
                    logger.error("A8 vectorizer response missing task id: %s", upload_data)
                    raise Exception("服务异常，联系管理员")

                start_time = time.monotonic()

                while True:
                    status_resp = await client.get(
                        f"{self.base_url}/try_get", params={"taskid": task_id}
                    )
                    status_resp.raise_for_status()
                    status_data = status_resp.json()

                    code = status_data.get("code")
                    if code == 0:
                        break
                    if code == -1:
                        logger.error(
                            "A8 vectorizer reported failure for task %s: %s",
                            task_id,
                            status_data,
                        )
                        raise Exception("服务异常，联系管理员")

                    if time.monotonic() - start_time > timeout:
                        logger.error(
                            "A8 vectorizer polling timed out for task %s after %s seconds",
                            task_id,
                            timeout,
                        )
                        raise Exception("服务异常，联系管理员")

                    await asyncio.sleep(poll_interval)

                download_resp = await client.get(
                    f"{self.base_url}/get_image", params={"taskid": task_id}
                )
                download_resp.raise_for_status()
                return download_resp.content

        except httpx.HTTPError as exc:
            logger.error("HTTP request to A8 vectorizer failed: %s", str(exc))
            raise Exception("服务异常，联系管理员") from exc

        except Exception:
            raise
