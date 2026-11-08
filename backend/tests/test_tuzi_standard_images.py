import asyncio
import base64
import json
from email import policy
from email.parser import BytesParser
from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.core.config import settings
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.tuzi_openai_client import (
    TUZI_GPT_IMAGE_2_MODEL, TUZI_GPT_IMAGE_2_VIP_MODEL, TuziOpenAIClient,
)


def image_bytes(mode="RGB", format="PNG"):
    buffer = BytesIO()
    Image.new(mode, (16, 32)).save(buffer, format=format)
    return buffer.getvalue()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "tuzi_api_key", "test-key")
    monkeypatch.setattr(settings, "tuzi_base_url", "https://api.tu-zi.com")

    async def run_without_redis(api_name, request):
        assert api_name == "tuzi_openai"
        return await request()

    monkeypatch.setattr(
        "app.services.ai_client.tuzi_openai_client.api_limiter.run",
        run_without_redis,
    )
    return TuziOpenAIClient()


def install_transport(monkeypatch, handler):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda **kwargs: original(transport=transport, **kwargs),
    )


async def multipart_parts(request):
    assert request.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    raw = (
        "Content-Type: " + request.headers["Content-Type"] + "\r\nMIME-Version: 1.0\r\n\r\n"
    ).encode() + await request.aread()
    message = BytesParser(policy=policy.default).parsebytes(raw)
    return {part.get_param("name", header="content-disposition"): part
            for part in message.iter_parts()}


@pytest.mark.asyncio
@pytest.mark.parametrize("mode,format", [("RGBA", "PNG"), ("CMYK", "JPEG"), ("RGB", "JPEG")])
async def test_standard_uses_real_png_multipart_not_chat_json(client, monkeypatch, mode, format):
    requests = []

    async def handler(request):
        requests.append(request)
        assert request.method == "POST"
        assert request.url.path == "/v1/images/edits"
        assert request.headers["Authorization"] == "Bearer test-key"
        parts = await multipart_parts(request)
        assert set(parts) == {"model", "prompt", "n", "response_format", "image"}
        assert parts["model"].get_content().strip() == TUZI_GPT_IMAGE_2_MODEL
        assert parts["prompt"].get_payload(decode=True).decode("utf-8") == "提取图案"
        assert parts["n"].get_content().strip() == "1"
        assert parts["response_format"].get_content().strip() == "b64_json"
        file = parts["image"]
        assert file.get_filename() == "image.png"
        assert file.get_content_type() == "image/png"
        with Image.open(BytesIO(file.get_payload(decode=True))) as image:
            assert image.format == "PNG"
            assert image.size == (16, 32)
            assert image.mode in {"RGB", "RGBA"}
            image.verify()
        return httpx.Response(200, json={"data": [{"b64_json": "test-result"}]})

    install_transport(monkeypatch, handler)
    response = await client.edit_image(
        image_bytes=image_bytes(mode, format), prompt="提取图案",
        mime_type="image/jpeg", model=TUZI_GPT_IMAGE_2_MODEL,
    )
    assert response == {"data": [{"b64_json": "test-result"}]}
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_standard_optional_quality_is_an_image_form_field(client, monkeypatch):
    async def handler(request):
        parts = await multipart_parts(request)
        assert parts["quality"].get_content().strip() == "low"
        return httpx.Response(200, json={"data": [{"url": "https://example.com/result.png"}]})

    install_transport(monkeypatch, handler)
    response = await client.edit_image(
        image_bytes=image_bytes(), prompt="edit", model=TUZI_GPT_IMAGE_2_MODEL,
        quality=" low ",
    )
    assert client.extract_image_url(response) == "https://example.com/result.png"


@pytest.mark.asyncio
async def test_vip_error_falls_back_to_images_edits_and_persists_base64(client, monkeypatch):
    paths = []
    encoded = base64.b64encode(image_bytes()).decode()
    saved = []

    async def handler(request):
        paths.append(request.url.path)
        if request.url.path == "/v1/chat/completions":
            body = json.loads(await request.aread())
            assert body["model"] == TUZI_GPT_IMAGE_2_VIP_MODEL
            assert body["stream"] is False
            return httpx.Response(400, json={"error": {"message": "Invalid request"}})
        assert request.url.path == "/v1/images/edits"
        parts = await multipart_parts(request)
        assert parts["model"].get_content().strip() == TUZI_GPT_IMAGE_2_MODEL
        return httpx.Response(200, json={"data": [{"b64_json": encoded}]})

    def save(value):
        saved.append(value)
        return "/files/results/persisted.png"

    install_transport(monkeypatch, handler)
    monkeypatch.setattr(client, "_save_base64_image", save)
    ai = AIClient.__new__(AIClient)
    ai.tuzi_openai_client = client
    errors = []
    result = await ai._extract_pattern_gpt_with_fallback(
        image_bytes(), label="gpt", branch_errors=errors,
    )
    assert result == "/files/results/persisted.png"
    assert paths == ["/v1/chat/completions", "/v1/images/edits"]
    assert saved == [encoded]
    assert errors[0]["model"] == TUZI_GPT_IMAGE_2_VIP_MODEL
    assert errors[0]["statusCode"] == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [400, 503])
async def test_image_post_preserves_error_without_blind_paid_resubmission(client, monkeypatch, status):
    calls = []

    async def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"message": "provider rejected request"}})

    install_transport(monkeypatch, handler)
    with pytest.raises(AIClientException) as caught:
        await client.edit_image(
            image_bytes=image_bytes(), prompt="edit", model=TUZI_GPT_IMAGE_2_MODEL,
        )
    assert len(calls) == 1
    assert caught.value.status_code == status
    assert "provider rejected request" in caught.value.response_body
    context = caught.value.request_data
    assert context["endpoint"] == "/images/edits"
    assert context["image"]["bytes"] > 0
    serialized = json.dumps(context)
    assert "test-key" not in serialized
    assert "Bearer" not in serialized
    assert "base64" not in serialized


@pytest.mark.asyncio
async def test_network_timeout_does_not_resubmit_paid_image_post(client, monkeypatch):
    calls = []

    async def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("upstream may still be generating", request=request)

    install_transport(monkeypatch, handler)
    with pytest.raises(AIClientException):
        await client.edit_image(
            image_bytes=image_bytes(), prompt="edit", model=TUZI_GPT_IMAGE_2_MODEL,
        )
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [b"<html>gateway</html>", b"[]"])
async def test_malformed_response_is_diagnostic_failure(client, monkeypatch, body):
    install_transport(monkeypatch, lambda request: httpx.Response(200, content=body))
    with pytest.raises(AIClientException, match="响应解析失败") as caught:
        await client.edit_image(
            image_bytes=image_bytes(), prompt="edit", model=TUZI_GPT_IMAGE_2_MODEL,
        )
    assert caught.value.status_code == 200


@pytest.mark.asyncio
async def test_cancellation_propagates_without_retry(client, monkeypatch):
    started = asyncio.Event()
    calls = []

    async def handler(request):
        calls.append(request)
        started.set()
        await asyncio.sleep(10)

    install_transport(monkeypatch, handler)
    task = asyncio.create_task(client.edit_image(
        image_bytes=image_bytes(), prompt="edit", model=TUZI_GPT_IMAGE_2_MODEL,
    ))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(calls) == 1
