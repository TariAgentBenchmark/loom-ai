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
    assert captured["data"]["stream"] is False
    assert "quality" not in captured["data"]
    content = captured["data"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "提取图案，输出4K"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_tuzi_openai_edit_image_passes_quality_when_provided(monkeypatch):
    monkeypatch.setattr(settings, "tuzi_api_key", "test-key")
    monkeypatch.setattr(settings, "tuzi_base_url", "https://api.tu-zi.com")
    client = TuziOpenAIClient()
    captured = {}

    async def fake_make_request(method, endpoint, data):
        captured["data"] = data
        return {"data": [{"url": "https://example.com/result.png"}]}

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    await client.edit_image(
        image_bytes=_build_png_bytes(),
        prompt="提取图案，输出4K",
        quality="2k",
    )

    assert captured["data"]["quality"] == "2k"


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


def test_tuzi_openai_extract_image_url_from_multimodal_content_part():
    client = TuziOpenAIClient()

    assert (
        client.extract_image_url(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "已生成"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": "https://example.com/part.png"
                                    },
                                },
                            ]
                        }
                    }
                ]
            }
        )
        == "https://example.com/part.png"
    )


def test_tuzi_openai_extract_image_url_saves_base64_content_part(monkeypatch):
    client = TuziOpenAIClient()
    saved = {}

    def fake_save(base64_data):
        saved["data"] = base64_data
        return "https://oss.example.com/results/saved.png"

    monkeypatch.setattr(client, "_save_base64_image", fake_save)

    data_url = "data:image/png;base64,iVBORw0KGgo="
    result = client.extract_image_url(
        {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                }
            ]
        }
    )

    assert result == "https://oss.example.com/results/saved.png"
    assert saved["data"] == data_url


def test_tuzi_openai_extract_image_url_saves_base64_markdown(monkeypatch):
    client = TuziOpenAIClient()
    monkeypatch.setattr(
        client,
        "_save_base64_image",
        lambda data: "https://oss.example.com/results/saved.png",
    )

    data_url = "data:image/png;base64,iVBORw0KGgo="
    result = client.extract_image_url(
        {
            "choices": [
                {"message": {"content": f"生成完成\n![result]({data_url})"}}
            ]
        }
    )

    assert result == "https://oss.example.com/results/saved.png"


def test_tuzi_openai_extract_image_url_saves_bare_base64_line(monkeypatch):
    client = TuziOpenAIClient()
    monkeypatch.setattr(
        client,
        "_save_base64_image",
        lambda data: "https://oss.example.com/results/saved.png",
    )

    data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="
    result = client.extract_image_url(
        {
            "choices": [
                {"message": {"content": f"这是生成的图片：\n{data_url}"}}
            ]
        }
    )

    assert result == "https://oss.example.com/results/saved.png"


def test_tuzi_openai_extract_image_url_prefers_http_over_base64_fallback():
    client = TuziOpenAIClient()

    # http URL 优先，不触发 base64 转存
    assert (
        client.extract_image_url(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "![result](https://example.com/direct.png)",
                                }
                            ]
                        }
                    }
                ]
            }
        )
        == "https://example.com/direct.png"
    )
