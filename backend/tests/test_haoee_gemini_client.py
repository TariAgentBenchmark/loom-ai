from io import BytesIO

import pytest
from PIL import Image

from app.services.ai_client.haoee_gemini_client import HaoeeGeminiClient


def _build_png_bytes() -> bytes:
    image = Image.new("RGB", (1, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_generate_image_preview_sends_haoee_image_size(monkeypatch):
    client = HaoeeGeminiClient()
    client.api_key = "test-key"
    captured = {}

    async def fake_make_request(method, endpoint, data, headers=None):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["headers"] = headers
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.generate_image_preview(
        image_bytes=_build_png_bytes(),
        prompt="test prompt",
        mime_type="image/png",
        aspect_ratio="1:1",
        resolution="4K",
        model_name="gemini-3-pro-image-preview",
    )

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert (
        captured["endpoint"]
        == "/v1beta/models/gemini-3-pro-image-preview:generateContent"
    )
    assert captured["headers"] == {"ModelName": "gemini-3-pro-image-preview"}
    assert captured["data"]["generationConfig"]["imageConfig"] == {
        "aspectRatio": "1:1",
        "imageSize": "4K",
    }


@pytest.mark.asyncio
async def test_generate_image_preview_routes_lite_model_through_base_endpoint(monkeypatch):
    client = HaoeeGeminiClient()
    client.api_key = "test-key"
    captured = {}

    async def fake_make_request(method, endpoint, data, headers=None):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        captured["headers"] = headers
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.generate_image_preview(
        image_bytes=_build_png_bytes(),
        prompt="test prompt",
        mime_type="image/png",
        resolution="2K",
        model_name="gemini-3-pro-image-preview-lite",
    )

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert (
        captured["endpoint"]
        == "/v1beta/models/gemini-3-pro-image-preview:generateContent"
    )
    assert captured["headers"] == {"ModelName": "gemini-3-pro-image-preview-lite"}
    assert captured["data"]["generationConfig"]["imageConfig"] == {
        "imageSize": "2K",
    }
