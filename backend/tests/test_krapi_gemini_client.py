from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.krapi_gemini_client import (
    KRAPI_BANANA_PRO_MODEL,
    KrapiGeminiClient,
)


def _build_png_bytes() -> bytes:
    image = Image.new("RGB", (1, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_krapi_client_defaults_to_banana_pro_model():
    client = KrapiGeminiClient()

    assert client.base_url == "https://ai.krapi.cn"
    assert client.default_image_model == KRAPI_BANANA_PRO_MODEL
    assert client.request_timeout == 650.0
    assert client.max_retries == 1


@pytest.mark.asyncio
async def test_generate_image_preview_uses_newapi_gemini_payload(monkeypatch):
    client = KrapiGeminiClient()
    client.api_key = "test-key"
    captured = {}

    async def fake_make_request(method, endpoint, data):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.generate_image_preview(
        image_bytes=_build_png_bytes(),
        prompt="test prompt",
        mime_type="image/png",
        aspect_ratio="1:1",
        resolution="4K",
    )

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/v1beta/models/T%E9%A6%99%E8%95%89pro:generateContent"
    assert captured["data"]["generationConfig"] == {
        "responseModalities": ["IMAGE"],
        "imageConfig": {
            "aspectRatio": "1:1",
            "imageSize": "4K",
        },
    }
    parts = captured["data"]["contents"][0]["parts"]
    assert parts[0] == {"text": "test prompt"}
    assert parts[1]["inlineData"]["mimeType"] == "image/png"
    assert parts[1]["inlineData"]["data"]


@pytest.mark.asyncio
async def test_generate_image_from_text_accepts_model_override(monkeypatch):
    client = KrapiGeminiClient()
    client.api_key = "test-key"
    captured = {}

    async def fake_make_request(method, endpoint, data):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.generate_image_from_text(
        "draw a cat",
        model_name="T香蕉2",
        resolution="2K",
    )

    assert result == {"ok": True}
    assert captured["endpoint"] == "/v1beta/models/T%E9%A6%99%E8%95%892:generateContent"
    assert captured["data"]["contents"] == [{"parts": [{"text": "draw a cat"}]}]
    assert captured["data"]["generationConfig"] == {
        "responseModalities": ["IMAGE"],
        "imageConfig": {"imageSize": "2K"},
    }


@pytest.mark.asyncio
async def test_generate_image_preview_polls_async_image_task(monkeypatch):
    client = KrapiGeminiClient()
    client.api_key = "test-key"
    client.task_poll_interval_seconds = 0
    image_url = "https://example.com/result.jpg"
    final_result = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": image_url}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }
    task_ids = []

    async def fake_make_request(method, endpoint, data):
        return {
            "id": "task_test",
            "task_id": "task_test",
            "object": "image.task",
            "status": "queued",
            "model": "T香蕉pro",
        }

    async def fake_get_image_task(task_id):
        task_ids.append(task_id)
        return {
            "id": task_id,
            "task_id": task_id,
            "object": "image.task",
            "status": "succeeded",
            "result": final_result,
        }

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    monkeypatch.setattr(client, "_get_image_task", fake_get_image_task)

    result = await client.generate_image_preview(
        image_bytes=_build_png_bytes(),
        prompt="test prompt",
        mime_type="image/png",
    )

    assert result == final_result
    assert task_ids == ["task_test"]
    assert client._extract_image_url(result) == image_url


@pytest.mark.asyncio
async def test_generate_image_preview_uses_top_level_task_url_when_result_is_redacted(monkeypatch):
    client = KrapiGeminiClient()
    client.api_key = "test-key"
    client.task_poll_interval_seconds = 0
    image_url = "https://example.com/redacted-result.jpg"

    async def fake_make_request(method, endpoint, data):
        return {
            "id": "task_test",
            "task_id": "task_test",
            "object": "image.task",
            "status": "queued",
            "model": "T香蕉2",
        }

    async def fake_get_image_task(task_id):
        return {
            "id": task_id,
            "task_id": task_id,
            "object": "image.task",
            "status": "succeeded",
            "model": "T香蕉2",
            "result": {
                "contains_result_urls": True,
                "large_result_redacted": True,
                "result_omitted": True,
                "omitted_reason": "result exceeded image task storage limit",
            },
            "url": image_url,
            "urls": [image_url],
        }

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    monkeypatch.setattr(client, "_get_image_task", fake_get_image_task)

    result = await client.generate_image_preview(
        image_bytes=_build_png_bytes(),
        prompt="test prompt",
        mime_type="image/png",
        model_name="T香蕉2",
    )

    assert result == {"data": [{"url": image_url}]}
    assert client._extract_image_url(result) == image_url


@pytest.mark.asyncio
async def test_get_image_task_retries_connection_errors(monkeypatch):
    client = KrapiGeminiClient()
    client.api_key = "test-key"
    client.task_poll_request_retries = 2
    client.task_poll_request_retry_backoff_seconds = 0
    calls = {"count": 0}

    class FakeAsyncClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url, headers):
            calls["count"] += 1
            request = httpx.Request("GET", url)
            if calls["count"] == 1:
                raise httpx.ReadTimeout("read timed out", request=request)
            return httpx.Response(
                200,
                json={"task_id": "task_test", "status": "succeeded"},
                request=request,
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    result = await client._get_image_task("task_test")

    assert result == {"task_id": "task_test", "status": "succeeded"}
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_generate_image_requires_api_key():
    client = KrapiGeminiClient()
    client.api_key = ""

    with pytest.raises(AIClientException, match="KRAPI_API_KEY"):
        await client.generate_image_from_text("draw a cat")
