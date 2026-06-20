from io import BytesIO

import pytest
from PIL import Image

from app.core.config import settings
from app.services.ai_client.tuzi_openai_client import (
    TUZI_GPT_IMAGE_2_VIP_MODEL,
    TuziOpenAIClient,
)


def _build_png_bytes() -> bytes:
    image = Image.new("RGB", (1, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_tuzi_openai_edit_image_uses_gpt_image_2_vip_chat_payload(monkeypatch):
    monkeypatch.setattr(settings, "tuzi_api_key", "test-key")
    monkeypatch.setattr(settings, "tuzi_base_url", "https://api.tu-zi.com")
    client = TuziOpenAIClient()
    captured = {}

    async def fake_make_request(method, endpoint, data):
        captured["method"] = method
        captured["endpoint"] = endpoint
        captured["data"] = data
        return {"data": [{"url": "https://example.com/result.png"}]}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    result = await client.edit_image(
        image_bytes=_build_png_bytes(),
        prompt="提取图案，输出4K",
    )

    assert result == {"data": [{"url": "https://example.com/result.png"}]}
    assert client.base_url == "https://api.tu-zi.com/v1"
    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/chat/completions"
    assert captured["data"]["model"] == TUZI_GPT_IMAGE_2_VIP_MODEL
    content = captured["data"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "提取图案，输出4K"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_tuzi_openai_extract_image_url_from_chat_response():
    client = TuziOpenAIClient()

    assert (
        client.extract_image_url(
            {
                "choices": [
                    {
                        "message": {
                            "content": "![result](https://example.com/result.png)"
                        }
                    }
                ]
            }
        )
        == "https://example.com/result.png"
    )
