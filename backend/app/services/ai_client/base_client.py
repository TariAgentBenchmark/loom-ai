import asyncio
import base64
import logging
import os
import uuid
from io import BytesIO
from random import uniform
from typing import Any, Dict, List, Optional

import httpx
from PIL import Image

from app.core.config import settings
from app.services.oss_service import oss_service
from app.services.api_limiter import api_limiter
from app.services.ai_client.exceptions import AIClientException

logger = logging.getLogger(__name__)


def _summarize_payload(payload: Any, max_length: int = 500) -> str:
    """Return a compact representation that avoids dumping huge blobs in logs."""
    try:
        if isinstance(payload, dict):
            parts = []
            for key, value in payload.items():
                parts.append(f"{key}={_summarize_value(value)}")
            text = ", ".join(parts)
        elif isinstance(payload, list):
            text = f"list(len={len(payload)}, sample={[_summarize_value(item) for item in payload[:3]]})"
        else:
            text = _summarize_value(payload)
    except Exception as exc:
        text = f"<unserializable payload: {exc}>"

    if len(text) > max_length:
        return f"{text[:max_length]}...<truncated>"
    return text


def _summarize_value(value: Any) -> str:
    if isinstance(value, dict):
        return f"dict(keys={list(value.keys())[:5]})"
    if isinstance(value, list):
        return f"list(len={len(value)})"
    if isinstance(value, bytes):
        return f"bytes(len={len(value)})"
    if isinstance(value, str):
        preview = value[:80]
        if len(value) > 80:
            preview = f"{preview}...<truncated>"
        return f"str(len={len(value)}, preview={preview!r})"
    return repr(value)


class BaseAIClient:
    """基础AI客户端，提供通用功能"""
    
    def __init__(self, api_name: str = "apyi_gemini"):
        self.base_url = settings.apiyi_base_url
        self.api_key = settings.apiyi_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.api_name = api_name
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求"""
        url = f"{self.base_url}{endpoint}"

        max_retries = 3
        backoff_base = 1.5

        async def _do_request():
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

                    logger.error(
                        "AI API request failed permanently: method=%s url=%s status=%s body=%s payload=%s",
                        method,
                        url,
                        status,
                        _summarize_payload(body),
                        _summarize_payload(data),
                    )
                    raise AIClientException(
                        message=f"AI服务请求失败: {status}",
                        api_name=self.api_name,
                        status_code=status,
                        response_body=body,
                        request_data=data,
                    )

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

                    logger.error(
                        "AI API request error without retry: method=%s url=%s error=%s payload=%s",
                        method,
                        url,
                        str(exc),
                        _summarize_payload(data),
                    )
                    raise AIClientException(
                        message=f"AI服务连接失败: {str(exc)}",
                        api_name=self.api_name,
                        request_data=data,
                    )

            # 理论上不会到达这里，保留兜底处理
            raise AIClientException(
                message="AI服务连接失败: 未知错误",
                api_name=self.api_name,
                request_data=data,
            )

        if self.api_name:
            return await api_limiter.run(self.api_name, _do_request)
        return await _do_request()

    def _image_to_base64(self, image_bytes: bytes, format: str = "JPEG") -> str:
        """将图片字节转换为base64编码"""
        try:
            # 使用PIL处理图片
            image = Image.open(BytesIO(image_bytes))
            target_format = format.upper()

            # 统一模式，防止“cannot write mode CMYK as PNG/JPEG”等错误
            if target_format == "JPEG":
                if image.mode == "RGBA":
                    # JPEG 不支持 alpha，使用白底合成
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode != "RGB":
                    image = image.convert("RGB")
            else:  # PNG 或其他支持透明度的格式
                if image.mode == "CMYK":
                    image = image.convert("RGB")
                elif image.mode not in ("RGB", "RGBA", "LA", "L"):
                    # 对其他特殊模式（如 P、YCbCr 等）做一次通用转换
                    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

            # 转换为字节
            buffer = BytesIO()
            save_kwargs = {"format": target_format}
            if target_format == "JPEG":
                save_kwargs["quality"] = 95
            image.save(buffer, **save_kwargs)
            image_bytes = buffer.getvalue()
            
            # 编码为base64
            return base64.b64encode(image_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Image to base64 conversion failed: {str(e)}")
            raise Exception(f"图片格式转换失败: {str(e)}")

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
            # 检查chat/completion响应格式（gpt-4o-image模型）
            if "choices" in api_response and isinstance(api_response["choices"], list):
                choice = api_response["choices"][0] if api_response["choices"] else None
                if choice and "message" in choice:
                    message = choice["message"]
                    content = message.get("content", "")

                    # 检查是否包含政策违规错误
                    if "违反了OpenAI的相关服务政策" in content or "政策" in content:
                        logger.error("OpenAI policy violation detected: %s", content)
                        raise Exception("暂时还不支持大牌花型哦")

                    # 首先尝试从markdown格式中提取图像URL
                    import re
                    markdown_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
                    matches = re.findall(markdown_pattern, content)
                    if matches:
                        return matches[0]

                    # 按行分割内容，查找第一个有效的URL
                    lines = content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        # 检查是否是HTTP URL且是图片格式
                        if line.startswith("http") and any(ext in line.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                            return line
                        # 检查是否是独立的URL（没有markdown格式）
                        elif line.startswith("http") and ("image" in line.lower() or "img" in line.lower() or "图片" in line):
                            return line

                    # 如果还是没有，在整个文本中搜索第一个URL模式
                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.jpg|\.jpeg|\.png|\.webp)'
                    text_matches = re.findall(url_pattern, content, re.IGNORECASE)
                    if text_matches:
                        return text_matches[0]

            # GPT-4o / OpenAI兼容响应格式
            if "data" in api_response and isinstance(api_response["data"], list):
                first_item = api_response["data"][0] if api_response["data"] else None
                if isinstance(first_item, dict):
                    url = first_item.get("url")
                    if isinstance(url, str):
                        return url

                    # 处理base64格式的响应
                    for key in ("b64_json", "b64_bytes", "base64", "image_base64"):
                        base64_value = first_item.get(key)
                        if isinstance(base64_value, str):
                            return self._save_base64_image(base64_value)

            # Gemini响应格式 (需要根据实际响应调整)
            if "candidates" in api_response:
                candidate = api_response["candidates"][0]

                # 检查是否是IMAGE_RECITATION错误
                finish_reason = candidate.get("finishReason")
                safety_note = self._format_safety_feedback(
                    candidate.get("safetyRatings"),
                    api_response.get("promptFeedback", {}).get("safetyRatings")
                )
                if finish_reason == "IMAGE_RECITATION":
                    logger.error(
                        "Gemini API returned IMAGE_RECITATION error - model interpreted request as image description instead of generation. "
                        "This usually happens when the prompt is ambiguous. "
                        "Please make sure your prompt explicitly asks to generate a new image."
                    )
                    raise Exception(
                        "AI模型将请求误解为图片描述而非生成，未扣除积分，您可以重新尝试。"
                    )

                if finish_reason == "NO_IMAGE":
                    logger.error(
                        "Gemini API returned NO_IMAGE finish reason; prompt may not explicitly request image generation. candidate=%s",
                        candidate
                    )
                    message = (
                        "AI 生成图片异常，请在指令中明确要求\"生成新的高清图像/无缝图案\"，并描述风格、颜色和构图。"
                    )
                    if safety_note:
                        message += f"（安全提示：{safety_note}）"
                    raise Exception(message)

                if "content" in candidate:
                    # 处理Gemini的响应格式
                    return self._process_gemini_response(candidate["content"])

            # 如果是base64格式，需要保存为文件并返回URL
            if "image" in api_response:
                return self._save_base64_image(api_response["image"])

            logger.error(
                "无法从AI响应中提取图片 - 完整响应内容: %s",
                api_response
            )
            raise Exception("无法从AI响应中提取图片")

        except Exception as e:
            # 如果是我们自定义的政策违规错误，直接抛出
            if str(e) == "暂时还不支持大牌花型哦":
                raise

            logger.error(
                "Failed to extract image URL from response: error=%s response=%s full_response=%s",
                str(e),
                _summarize_payload(api_response),
                api_response
            )
            raise Exception(f"处理AI响应失败: {str(e)}")

    def _extract_image_urls(self, api_response: Dict[str, Any]) -> List[str]:
        """从API响应中提取多张图片URL"""
        try:
            # 检查chat/completion响应格式（gpt-4o-image模型）
            if "choices" in api_response and isinstance(api_response["choices"], list):
                choice = api_response["choices"][0] if api_response["choices"] else None
                if choice and "message" in choice:
                    message = choice["message"]
                    content = message.get("content", "")

                    # 检查是否包含政策违规错误
                    if "违反了OpenAI的相关服务政策" in content or "政策" in content:
                        logger.error("OpenAI policy violation detected: %s", content)
                        raise Exception("暂时还不支持大牌花型哦")

                    urls = []

                    import re

                    # 尝试从markdown格式中提取图像URL
                    markdown_pattern = r'!\[.*?\]\((https?://[^\)]+)\)'
                    markdown_matches = re.findall(markdown_pattern, content)
                    urls.extend(markdown_matches)

                    # 按行分割内容，查找独立的URL（即使有markdown格式也要检查）
                    lines = content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        # 跳过markdown格式的行（避免重复）
                        if line.startswith('![') and '](' in line:
                            continue
                        # 检查是否是HTTP URL且是图片格式
                        if line.startswith("http") and any(ext in line.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                            urls.append(line)
                        # 检查是否是独立的URL（没有markdown格式）
                        elif line.startswith("http") and ("image" in line.lower() or "img" in line.lower() or "图片" in line):
                            urls.append(line)

                    # 如果还是没有，尝试在整个文本中搜索URL模式
                    if not urls:
                        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+(?:\.jpg|\.jpeg|\.png|\.webp)'
                        text_matches = re.findall(url_pattern, content, re.IGNORECASE)
                        urls.extend(text_matches)

                    # 去重并返回
                    if urls:
                        # 去重，保持顺序
                        seen = set()
                        unique_urls = []
                        for url in urls:
                            if url not in seen:
                                seen.add(url)
                                unique_urls.append(url)
                        return unique_urls

            # GPT-4o响应格式 - 返回多张图片
            if "data" in api_response and isinstance(api_response["data"], list):
                urls: List[str] = []
                for item in api_response["data"]:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url")
                    if isinstance(url, str):
                        urls.append(url)
                        continue
                    # 处理base64图像
                    for key in ("b64_json", "b64_bytes", "base64", "image_base64"):
                        base64_value = item.get(key)
                        if isinstance(base64_value, str):
                            urls.append(self._save_base64_image(base64_value))
                            break
                if urls:
                    return urls

            # Gemini响应格式 - 目前只支持单张
            if "candidates" in api_response:
                candidate = api_response["candidates"][0]

                # 检查是否是IMAGE_RECITATION错误
                if candidate.get("finishReason") == "IMAGE_RECITATION":
                    logger.error(
                        "Gemini API returned IMAGE_RECITATION error - model interpreted request as image description instead of generation. "
                        "This usually happens when the prompt is ambiguous. "
                        "Please make sure your prompt explicitly asks to generate a new image."
                    )
                    raise Exception(
                        "AI模型将请求误解为图片描述而非生成。"
                        "请确保提示词明确要求生成新图片，例如使用'生成图片'、'创建图片'等明确指令。"
                    )

                if "content" in candidate:
                    return [self._process_gemini_response(candidate["content"])]

            # 如果是base64格式
            if "image" in api_response:
                return [self._save_base64_image(api_response["image"])]

            logger.error(
                "无法从AI响应中提取图片 - 完整响应内容: %s",
                api_response
            )
            raise Exception("无法从AI响应中提取图片")

        except Exception as e:
            # 如果是我们自定义的政策违规错误，直接抛出
            if str(e) == "暂时还不支持大牌花型哦":
                raise

            logger.error(
                "Failed to extract image URLs from response: error=%s response=%s full_response=%s",
                str(e),
                _summarize_payload(api_response),
                api_response
            )
            raise Exception(f"处理AI响应失败: {str(e)}")

    def _process_gemini_response(self, content: Dict[str, Any]) -> str:
        """处理Gemini响应内容"""
        logger.debug(content)
        try:
            if isinstance(content, dict):
                raw_parts = content.get("parts")
                parts: List[Dict[str, Any]] = raw_parts if isinstance(raw_parts, list) else []
            else:
                parts = []

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

            logger.error(
                "AI响应缺少可用的图片数据 - 完整响应内容: %s",
                content
            )
            raise Exception("AI响应缺少可用的图片数据")

        except Exception as exc:
            logger.error(
                "Gemini response parsing failed: error=%s content=%s full_response=%s",
                str(exc),
                _summarize_payload(content),
                content
            )
            raise Exception(f"AI响应解析失败: {str(exc)}")

    def _format_safety_feedback(
        self,
        *safety_sources: Optional[Any]
    ) -> Optional[str]:
        """提取安全拦截信息"""
        categories: List[str] = []
        for source in safety_sources:
            if not isinstance(source, list):
                continue
            for rating in source:
                if not isinstance(rating, dict):
                    continue
                category = rating.get("category") or rating.get("harmCategory") or "未知";
                probability = rating.get("probability") or rating.get("rating")
                blocked = rating.get("blocked")
                details = []
                if probability:
                    details.append(str(probability))
                if blocked:
                    details.append("已拦截")
                label = f"{category}({', '.join(details)})" if details else category
                categories.append(label)
        if categories:
            return "；".join(categories)
        return None

    def _save_base64_image(self, base64_data: str) -> str:
        """保存base64图片并返回URL"""
        try:
            if base64_data.startswith("data:"):
                base64_data = base64_data.split(",", 1)[-1]

            image_bytes = base64.b64decode(base64_data)
            return self._save_image_bytes(image_bytes, prefix="ai_result")

        except Exception as e:
            logger.error(f"Failed to save base64 image: {str(e)}")
            raise Exception(f"保存图片失败: {str(e)}")

    def _save_image_bytes(self, image_bytes: bytes, prefix: str = "ai_result") -> str:
        """保存图片字节为PNG并返回URL"""
        try:
            image = Image.open(BytesIO(image_bytes))

            if image.mode not in ("RGB", "RGBA", "LA"):
                image = image.convert("RGB")
            elif image.mode == "LA":
                image = image.convert("RGBA")

            filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
            # 优先上传到OSS（如果已配置）
            oss_url = oss_service.upload_file_sync(
                png_bytes,
                filename,
                prefix="results",
                content_type="image/png",
            )
            if oss_url:
                return oss_url

            # 回退到本地存储
            file_path = f"{settings.upload_path}/results/{filename}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image.save(file_path, format="PNG")
            return f"/files/results/{filename}"
        except Exception as exc:
            logger.error("Failed to persist image bytes: %s", str(exc))
            raise Exception(f"保存图片失败: {str(exc)}")
