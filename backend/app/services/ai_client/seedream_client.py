import asyncio
import hashlib
import logging
import re
import time
from fractions import Fraction
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx
from PIL import Image, ImageOps

from app.core.config import settings
from app.services.ai_client.base_client import BaseAIClient
from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.seedream_recovery import (
    SeedreamPendingError,
    seedream_recovery,
)
from app.services.api_limiter import api_limiter

logger = logging.getLogger(__name__)
ASPECT_RATIOS = ("1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9")
SEEDREAM_PATTERN_PROMPT = "帮我把图案完全展开并彻底铺平提取出来，这是一个纯二维平面图案，强烈要求去除并禁止 出现所有褶皱、折痕、皱纹、拉伸、扭曲、卷曲、起伏、凹凸不平。 要求整个画面必须是绝对平整、绝对笔直、绝对展开的平面状态， 不存在任何折起来的区域或被遮挡的区域。图案倾斜的时候自动摆正上下左右齐平、校正透视、 对齐结构、统一比例，所有图形元素保持完整、连续、不要有裁切、 不被遮挡，所有文字、数字、标志必须完整清晰呈现。这是印刷图案本身，不是衣服、不是布料 、不是服装照片，不包含任何衣服轮廓、服装形态或穿着状态。 背景为干净、统一、平整的底色，增强图案细节但不增加任何立体感或材质感。生成 4K 超高分辨率 ，锐利对焦，超高清，高度详细，复杂细节，杰作级质量， 最高品质。图像表现为印刷级品质的无缝平铺图案，平滑、干净、边缘清晰锐利，无颗粒感、无噪点 无模糊。使用虚幻引擎5渲染，画面也必须保持完全二维、 无深度、无体积、无光照起伏。特写镜头、近景视角，高清印刷图。色彩纠正，整体色彩色调、饱和度、 亮度和对比度与原图完全一致, 整体颜色要和原图一模一样。 禁止生成纯色，禁止图案以外内容，禁止生成衣服形状，禁止生成衣服模特，禁止生成褶皱。"
MAX_RESULT_BYTES = 100 * 1024 * 1024


class SeedreamClient(BaseAIClient):
    """Authenticated async task API. Never retry a paid submission automatically."""

    def __init__(self):
        super().__init__(api_name="seedream")
        self.base_url = settings.seedream_base_url.rstrip("/")
        key_file = Path(settings.seedream_api_key_file)
        self.api_key = settings.seedream_api_key.strip() or (
            key_file.read_text().strip() if key_file.is_file() else ""
        )
        self.headers = {"X-API-Key": self.api_key}
        origin = urlsplit(self.base_url)
        if (
            origin.scheme != "https"
            or not origin.netloc
            or origin.username
            or origin.query
            or origin.fragment
        ):
            raise ValueError("Seedream必须使用有效的HTTPS服务地址")

    def _error(self, message: str, operation: str, status=None) -> AIClientException:
        # No headers, prompt, raw image, or provider response is put into logs.
        message = (
            str(message).replace(self.api_key, "<redacted>")
            if self.api_key
            else str(message)
        )
        return AIClientException(
            message=f"Seedream: {message[:400]}",
            api_name=self.api_name,
            status_code=status,
            request_data={"operation": operation},
        )

    def _result_url(self, item) -> str:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("url"), str)
            or not item["url"].strip()
        ):
            raise self._error("结果地址无效", "download")
        raw_url = item["url"].strip()
        if len(raw_url) > 4096 or self.api_key in raw_url:
            raise self._error("结果地址包含不安全信息", "download")
        url = urljoin(self.base_url + "/", raw_url)
        origin, target = urlsplit(self.base_url), urlsplit(url)
        if (target.scheme, target.netloc) != (
            origin.scheme,
            origin.netloc,
        ) or target.username:
            raise self._error("拒绝跨域结果地址，避免泄露密钥", "download")
        return url

    @staticmethod
    def prepare_images(images: list[bytes], ratio: str):
        normalized = []
        dimensions = None
        for raw in images:
            with Image.open(BytesIO(raw)) as source:
                image = ImageOps.exif_transpose(source)
                if dimensions is None:
                    dimensions = image.size
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                buffer = BytesIO()
                image.save(buffer, format="PNG")
                normalized.append(buffer.getvalue())
        ratio = str(ratio or "auto").strip().lower()
        if ratio not in ("auto", *ASPECT_RATIOS):
            raise ValueError("当前模型pro不支持此图片比例")
        if ratio == "auto" and dimensions:
            width, height = dimensions

            def mismatch(option):
                x, y = map(int, option.split(":"))
                a, b = width * y, height * x
                return Fraction(max(a, b), min(a, b))

            ratio = min(ASPECT_RATIOS, key=mismatch)
        return normalized, ratio

    async def _json(self, client, method, path, **kwargs):
        async def request():
            response = await client.request(method, self.base_url + path, **kwargs)
            if response.is_redirect or response.is_error:
                message = "接口请求失败"
                try:
                    rejected = response.json()
                    if isinstance(rejected, dict):
                        message = rejected.get("message") or message
                except ValueError:
                    pass
                raise self._error(message, path, response.status_code)
            try:
                data = response.json()
            except ValueError as exc:
                raise self._error("接口未返回JSON", path, response.status_code) from exc
            if not isinstance(data, dict):
                raise self._error("接口响应格式无效", path, response.status_code)
            return data

        return await api_limiter.run(self.api_name, request)

    async def generate(
        self,
        images: list[bytes],
        prompt: str,
        ratio: str = "auto",
        slot: str = "prompt_edit",
    ) -> list[str]:
        if not self.api_key:
            raise self._error("API密钥未配置", "configuration")
        if not prompt.strip() or not images:
            raise ValueError("请提供图片和修改指令")
        recovery = seedream_recovery.get()
        record = dict(recovery.records.get(slot) or {}) if recovery else {}
        fingerprint = hashlib.sha256(
            prompt.encode()
            + b"\0"
            + str(ratio).encode()
            + b"".join(hashlib.sha256(image).digest() for image in images)
        ).hexdigest()
        if record and (
            record.get("baseUrl") != self.base_url or record.get("input") != fingerprint
        ):
            raise self._error(
                "已提交任务的输入或服务地址发生变化，请人工核对", "recovery"
            )
        if record.get("savedResults"):
            return list(record["savedResults"])
        if record and not record.get("taskid"):
            raise SeedreamPendingError(
                "Seedream提交状态未确认，需人工核对，未重复提交",
                api_name=self.api_name,
            )

        def checkpoint():
            if recovery:
                recovery.checkpoint(slot, record)

        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=120,
            follow_redirects=False,
        ) as client:
            if not record.get("taskid"):
                files, resolved_ratio = await asyncio.to_thread(
                    self.prepare_images, images, ratio
                )
                record = {
                    "baseUrl": self.base_url,
                    "input": fingerprint,
                    "state": "submitting",
                }
                checkpoint()
                try:
                    data = await self._json(
                        client,
                        "POST",
                        "/add_task",
                        data={"prompt": prompt, "ratio": resolved_ratio},
                        files=[
                            ("file", (f"reference_{i}.png", raw, "image/png"))
                            for i, raw in enumerate(files)
                        ],
                    )
                except (httpx.RequestError, TimeoutError, AIClientException) as exc:
                    if (
                        isinstance(exc, AIClientException)
                        and exc.status_code is not None
                        and 300 <= exc.status_code < 500
                    ):
                        raise
                    record["state"] = "submission_unknown"
                    checkpoint()
                    raise SeedreamPendingError(
                        "Seedream提交未确认，未自动重发，请核对上游任务",
                        api_name=self.api_name,
                    ) from exc
                if data.get("code") != 0:
                    raise self._error(data.get("message") or "提交失败", "submit")
                taskid = data.get("taskid")
                if not isinstance(taskid, str) or not re.fullmatch(
                    r"[A-Za-z0-9_-]{1,160}", taskid
                ):
                    raise SeedreamPendingError(
                        "Seedream返回无效任务号，未自动重发，请人工核对",
                        api_name=self.api_name,
                    )
                record.update(taskid=taskid, state="submitted")
                checkpoint()
                logger.info("Seedream accepted task=%s slot=%s", taskid, slot)

            if not record.get("results"):
                deadline = time.monotonic() + max(
                    0.01, settings.seedream_poll_timeout_seconds
                )
                while time.monotonic() < deadline:
                    try:
                        data = await self._json(
                            client,
                            "GET",
                            "/try_get",
                            params={"taskid": record["taskid"]},
                            timeout=30,
                        )
                    except (httpx.RequestError, TimeoutError):
                        await asyncio.sleep(settings.seedream_poll_interval_seconds)
                        continue
                    except AIClientException as exc:
                        if exc.status_code in {408, 429} or (
                            exc.status_code and exc.status_code >= 500
                        ):
                            await asyncio.sleep(settings.seedream_poll_interval_seconds)
                            continue
                        raise
                    if data.get("code") == -1:
                        raise self._error(data.get("message") or "任务失败", "poll")
                    if data.get("code") == 0:
                        results = data.get("results")
                        if not isinstance(results, list) or not results:
                            raise self._error("完成但未返回图片", "poll")
                        # One result per charged application task/combined branch.
                        record.update(
                            results=[{"url": self._result_url(results[0])}],
                            state="completed",
                        )
                        checkpoint()
                        break
                    await asyncio.sleep(settings.seedream_poll_interval_seconds)
                else:
                    raise SeedreamPendingError(
                        "Seedream仍在排队或生成，保留任务号继续查询",
                        api_name=self.api_name,
                        request_data={"taskid": record["taskid"]},
                    )

            refs = []
            for item in record["results"]:
                url = self._result_url(item)

                async def download(result_url=url):
                    content = bytearray()
                    async with client.stream("GET", result_url) as response:
                        if response.is_redirect or response.is_error:
                            raise self._error(
                                "图片下载失败", "download", response.status_code
                            )
                        async for block in response.aiter_bytes():
                            if len(content) + len(block) > MAX_RESULT_BYTES:
                                raise self._error("返回图片超过100MB限制", "download")
                            content.extend(block)
                    with Image.open(BytesIO(content)) as image:
                        if image.format not in {"PNG", "JPEG", "WEBP"}:
                            raise self._error("返回了不支持的图片格式", "download")
                        image.verify()
                    return await asyncio.to_thread(
                        self._save_image_bytes, bytes(content), "seedream"
                    )

                # Keep the completed descriptor if download/storage fails; recovery
                # can retry the read without creating a new paid task.
                try:
                    refs.append(await api_limiter.run(self.api_name, download))
                except Exception as exc:
                    raise SeedreamPendingError(
                        "Seedream已出图，等待恢复下载或保存",
                        api_name=self.api_name,
                        request_data={
                            "taskid": record["taskid"],
                            "reason": type(exc).__name__,
                        },
                    ) from exc
            record["savedResults"] = refs
            checkpoint()
            return refs
