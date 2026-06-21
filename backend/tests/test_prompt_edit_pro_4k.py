import pytest

from app.services.ai_client.image_utils import (
    DENOISE_PRO_4K_MODEL,
    DENOISE_PRO_4K_RESOLUTION,
    PROMPT_EDIT_PRO_4K_MODEL,
    ImageProcessingUtils,
)
from app.services.service_pricing import resolve_pricing_key


def test_prompt_edit_pro_4k_resolves_variant_pricing_key():
    assert resolve_pricing_key("prompt_edit", {"model": "pro_4k"}) == "prompt_edit_pro_4k"
    assert resolve_pricing_key("prompt_edit_pro_4k") == "prompt_edit_pro_4k"
    assert resolve_pricing_key("prompt_edit", {"model": "new"}) == "prompt_edit"


@pytest.mark.asyncio
async def test_prompt_edit_pro_4k_uses_pro_model_and_resolution(monkeypatch):
    utils = ImageProcessingUtils()
    captured = {}

    async def fake_generate_image_preview_multi(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "generate_image_preview_multi",
        fake_generate_image_preview_multi,
    )
    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/result.png",
    )

    result = await utils.prompt_edit_image(
        b"fake-image",
        {"instruction": "把衣服改成白色", "model": "pro_4k"},
    )

    assert result == "https://example.com/result.png"
    assert captured["kwargs"]["resolution"] == "4K"
    assert captured["kwargs"]["model_name"] == PROMPT_EDIT_PRO_4K_MODEL


@pytest.mark.asyncio
async def test_denoise_uses_apyi_pro_4k_model(monkeypatch):
    utils = ImageProcessingUtils()
    captured = {}

    async def fake_generate_image_preview(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return {"ok": True}

    async def fail_if_legacy_process_image_called(*_args, **_kwargs):
        raise AssertionError("denoise should use Apyi preview 4K, not legacy process_image")

    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "generate_image_preview",
        fake_generate_image_preview,
    )
    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "_extract_image_url",
        lambda _result: "https://example.com/denoise.png",
    )
    monkeypatch.setattr(
        utils.apyi_gemini_client,
        "process_image",
        fail_if_legacy_process_image_called,
    )

    result = await utils.denoise_image(
        b"fake-image",
        {"aspect_ratio": "1:1"},
    )

    assert result == "https://example.com/denoise.png"
    assert captured["args"][0] == b"fake-image"
    assert "香蕉Pro 4K" in captured["args"][1]
    assert captured["kwargs"]["aspect_ratio"] == "1:1"
    assert captured["kwargs"]["resolution"] == DENOISE_PRO_4K_RESOLUTION
    assert captured["kwargs"]["model_name"] == DENOISE_PRO_4K_MODEL
