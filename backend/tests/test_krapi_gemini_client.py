from io import BytesIO

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
async def test_generate_image_requires_api_key():
    client = KrapiGeminiClient()
    client.api_key = ""

    with pytest.raises(AIClientException, match="KRAPI_API_KEY"):
        await client.generate_image_from_text("draw a cat")
