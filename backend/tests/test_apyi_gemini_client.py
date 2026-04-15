from io import BytesIO

import pytest
from PIL import Image

from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient


def _build_png_bytes() -> bytes:
    image = Image.new("RGB", (1, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_generate_image_preview_uses_overridden_model_endpoint(monkeypatch):
    client = ApyiGeminiClient()
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
        model_name="gemini-3-pro-image-preview",
    )

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/v1beta/models/gemini-3-pro-image-preview:generateContent"
    assert captured["data"]["generationConfig"]["imageConfig"] == {
        "aspectRatio": "1:1",
        "image_size": "4K",
    }
