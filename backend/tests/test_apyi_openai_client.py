import base64
from io import BytesIO

import pytest
from PIL import Image

from app.services.ai_client import base_client as base_client_module
from app.services.ai_client.apyi_openai_client import (
    ApyiOpenAIClient,
    GPT_IMAGE_2_ALL_MODEL,
)
from app.services.ai_client.image_utils import ImageProcessingUtils


def _build_png_bytes() -> bytes:
    image = Image.new("RGB", (2, 1), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_gpt_image_2_all_image_edit_uses_images_api_and_b64_json(monkeypatch):
    client = ApyiOpenAIClient()
    captured = {}

    async def fake_multipart(method, endpoint, files, data):
        captured.update(
            method=method,
            endpoint=endpoint,
            files=files,
            data=data,
        )
        return {"data": [{"b64_json": "encoded-result"}]}

    monkeypatch.setattr(client, "_make_multipart_request", fake_multipart)

    result = await client.generate_image(
        "提取牛仔纹理",
        n=3,
        size=None,
        model=GPT_IMAGE_2_ALL_MODEL,
        image_bytes=_build_png_bytes(),
    )

    assert result == {"data": [{"b64_json": "encoded-result"}]}
    assert captured["method"] == "POST"
    assert captured["endpoint"] == "/images/edits"
    assert captured["data"] == {
        "model": GPT_IMAGE_2_ALL_MODEL,
        "prompt": "提取牛仔纹理",
        "response_format": "b64_json",
    }
    filename, image_bytes, mime_type = captured["files"]["image"]
    assert filename == "image.png"
    assert mime_type == "image/png"
    with Image.open(BytesIO(image_bytes)) as image:
        assert image.format == "PNG"
        assert image.size == (2, 1)


@pytest.mark.asyncio
async def test_gpt_image_2_all_text_generation_uses_images_api_and_b64_json(monkeypatch):
    client = ApyiOpenAIClient()
    captured = {}

    async def fake_request(method, endpoint, data):
        captured.update(method=method, endpoint=endpoint, data=data)
        return {"data": [{"b64_json": "encoded-result"}]}

    monkeypatch.setattr(client, "_make_request", fake_request)

    await client.generate_image(
        "生成牛仔纹理",
        model=GPT_IMAGE_2_ALL_MODEL,
        response_format="b64_json",
    )

    assert captured == {
        "method": "POST",
        "endpoint": "/images/generations",
        "data": {
            "model": GPT_IMAGE_2_ALL_MODEL,
            "prompt": "生成牛仔纹理",
            "response_format": "b64_json",
        },
    }


@pytest.mark.asyncio
async def test_gpt_image_2_all_downloads_input_url_before_images_edit(monkeypatch):
    client = ApyiOpenAIClient()
    captured = {}
    source_bytes = _build_png_bytes()

    async def fake_download(url):
        captured["download_url"] = url
        return source_bytes

    async def fake_multipart(method, endpoint, files, data):
        captured["endpoint"] = endpoint
        captured["response_format"] = data["response_format"]
        return {"data": [{"b64_json": "encoded-result"}]}

    monkeypatch.setattr(client, "_download_image_from_url", fake_download)
    monkeypatch.setattr(client, "_make_multipart_request", fake_multipart)

    await client.generate_image(
        "编辑图片",
        model=GPT_IMAGE_2_ALL_MODEL,
        image_url="https://example.com/source.png",
    )

    assert captured == {
        "download_url": "https://example.com/source.png",
        "endpoint": "/images/edits",
        "response_format": "b64_json",
    }


@pytest.mark.parametrize("with_data_url_prefix", [False, True])
def test_b64_json_result_is_decoded_and_uploaded_directly_to_oss(
    monkeypatch,
    with_data_url_prefix,
):
    client = ApyiOpenAIClient()
    encoded = base64.b64encode(_build_png_bytes()).decode("ascii")
    if with_data_url_prefix:
        encoded = f"data:image/png;base64,{encoded}"
    captured = {}

    def fake_upload(image_bytes, filename, *, prefix, content_type):
        captured.update(
            image_bytes=image_bytes,
            filename=filename,
            prefix=prefix,
            content_type=content_type,
        )
        return "https://loomai.oss-cn-beijing.aliyuncs.com/results/result.png"

    monkeypatch.setattr(
        base_client_module.oss_service,
        "upload_file_sync",
        fake_upload,
    )

    result = client._extract_image_url({"data": [{"b64_json": encoded}]})

    assert result == "https://loomai.oss-cn-beijing.aliyuncs.com/results/result.png"
    assert captured["image_bytes"].startswith(b"\x89PNG\r\n\x1a\n")
    assert captured["filename"].startswith("ai_result_")
    assert captured["filename"].endswith(".png")
    assert captured["prefix"] == "results"
    assert captured["content_type"] == "image/png"


@pytest.mark.asyncio
async def test_denim_pattern_requests_b64_json_and_returns_persisted_url(monkeypatch):
    utils = ImageProcessingUtils()
    captured = {}

    async def fake_generate(prompt, **kwargs):
        captured["prompt"] = prompt
        captured["kwargs"] = kwargs
        return {"data": [{"b64_json": "encoded-result"}]}

    monkeypatch.setattr(utils.apyi_openai_client, "generate_image", fake_generate)
    monkeypatch.setattr(
        utils.apyi_openai_client,
        "_extract_image_urls",
        lambda result: [
            "https://loomai.oss-cn-beijing.aliyuncs.com/results/result.png"
        ],
    )

    result = await utils.extract_pattern(
        _build_png_bytes(),
        {"pattern_type": "denim", "num_images": 1, "aspect_ratio": "1:1"},
    )

    assert result == "https://loomai.oss-cn-beijing.aliyuncs.com/results/result.png"
    assert captured["kwargs"]["model"] == GPT_IMAGE_2_ALL_MODEL
    assert captured["kwargs"]["response_format"] == "b64_json"
    assert captured["kwargs"]["image_bytes"] == _build_png_bytes()
    assert captured["kwargs"]["size"] is None
