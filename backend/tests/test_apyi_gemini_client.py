from io import BytesIO

import pytest
from PIL import Image

from app.services.ai_client.apyi_gemini_client import ApyiGeminiClient
from app.services.ai_client.image_utils import ImageProcessingUtils


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


@pytest.mark.asyncio
async def test_process_image_uses_apyi_banana1_endpoint(monkeypatch):
    client = ApyiGeminiClient()
    captured = {}

    async def fake_make_request(method, endpoint, data):
        captured.update(method=method, endpoint=endpoint, data=data)
        return {"ok": True}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.process_image(
        image_bytes=_build_png_bytes(),
        prompt="old combined detail prompt",
        mime_type="image/png",
        aspect_ratio="1:1",
    )

    assert result == {"ok": True}
    assert captured["method"] == "POST"
    assert captured["endpoint"] == (
        "/v1beta/models/gemini-2.5-flash-image:generateContent"
    )
    assert captured["data"]["contents"][0]["parts"][0] == {
        "text": "old combined detail prompt"
    }
    assert captured["data"]["generationConfig"] == {
        "responseModalities": ["IMAGE"],
        "imageConfig": {"aspectRatio": "1:1"},
    }


@pytest.mark.asyncio
async def test_combined_detail_uses_previous_prompt_with_apyi_banana1(monkeypatch):
    utils = ImageProcessingUtils()
    captured = {}

    async def fake_process_image(image_bytes, prompt, mime_type, **kwargs):
        captured.update(
            image_bytes=image_bytes,
            prompt=prompt,
            mime_type=mime_type,
            kwargs=kwargs,
        )
        return {"ok": True}

    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "process_image",
        fake_process_image,
    )
    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/banana1.png",
    )

    result = await utils.extract_pattern(
        _build_png_bytes(),
        {"pattern_type": "combined_detail", "aspect_ratio": "1:1"},
    )

    assert result == "https://example.com/banana1.png"
    assert captured == {
        "image_bytes": _build_png_bytes(),
        "prompt": (
            "把衣服图案展开，分析图案，提炼图案，图案细节图案密度一致，去掉皱褶，干净底色，无阴影。"
            "线条清晰，增强细节，生成8K分辨率、干净底色，超高清、高细节、照片级写实的印刷级品质2d平面图案。"
            "以你的能力极限生成一张超高清8K分辨率、锐利对焦, 高度详细, 复杂的细节、杰作，最高品质，使用虚幻引擎5渲染。"
            "确保生成的的是一个完整的、无缺失的图案。务必确保图像中只包含图案本身，排除图案以外内容。排除生成衣服形状。"
        ),
        "mime_type": "image/png",
        "kwargs": {
            "aspect_ratio": "1:1",
            "width": None,
            "height": None,
        },
    }
