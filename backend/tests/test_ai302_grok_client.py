import pytest

from app.core.config import settings
from app.services.ai_client.ai302_grok_client import AI302GrokClient
from app.utils.ai302_urls import rewrite_ai302_file_url


def test_rewrite_ai302_file_url_uses_domestic_file_host(monkeypatch):
    monkeypatch.setattr(settings, "ai302_file_base_url", "https://file.302ai.cn")

    rewritten = rewrite_ai302_file_url(
        "https://file.302.ai/gpt/imgs/20260522/result.jpg?x=1"
    )

    assert rewritten == "https://file.302ai.cn/gpt/imgs/20260522/result.jpg?x=1"


def test_rewrite_ai302_file_url_keeps_non_302_file_url(monkeypatch):
    monkeypatch.setattr(settings, "ai302_file_base_url", "https://file.302ai.cn")

    url = "https://example.com/gpt/imgs/result.jpg"

    assert rewrite_ai302_file_url(url) == url


@pytest.mark.parametrize(
    "response",
    [
        {
            "images": [
                {
                    "url": "https://file.302.ai/gpt/imgs/20260522/result.jpg",
                }
            ]
        },
        {
            "data": [
                {
                    "url": "https://file.302.ai/gpt/imgs/20260522/result.jpg",
                }
            ]
        },
        {
            "data": {
                "images": [
                    {
                        "url": "https://file.302.ai/gpt/imgs/20260522/result.jpg",
                    }
                ]
            }
        },
        {
            "image_url": "https://file.302.ai/gpt/imgs/20260522/result.jpg",
        },
        {
            "image_urls": ["https://file.302.ai/gpt/imgs/20260522/result.jpg"],
        },
        {
            "raw_response": (
                '{"data":[{"url":"https://file.302.ai/gpt/imgs/20260522/result.jpg"}]}'
            ),
        },
    ],
)
def test_ai302_grok_extract_image_url_rewrites_file_host(monkeypatch, response):
    monkeypatch.setattr(settings, "ai302_file_base_url", "https://file.302ai.cn")

    assert (
        AI302GrokClient.extract_image_url(response)
        == "https://file.302ai.cn/gpt/imgs/20260522/result.jpg"
    )


@pytest.mark.asyncio
async def test_ai302_grok_edit_image_polls_official_request_id_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "ai302_api_key", "test-key")
    monkeypatch.setattr(settings, "ai302_base_url", "https://api.302.ai")
    monkeypatch.setattr(settings, "ai302_file_base_url", "https://file.302ai.cn")
    monkeypatch.setattr(settings, "ai302_grok_poll_interval_seconds", 1)
    monkeypatch.setattr(settings, "ai302_grok_poll_timeout_seconds", 10)

    client = AI302GrokClient()
    calls = []
    responses = [
        {"request_id": "req-123", "status": "submitted"},
        {"request_id": "req-123", "status": "processing"},
        {"image_url": "https://file.302.ai/gpt/imgs/20260522/result.jpg"},
    ]

    async def fake_make_request(method, endpoint, data, headers=None, params=None):
        calls.append(
            {
                "method": method,
                "endpoint": endpoint,
                "data": data,
                "params": params,
            }
        )
        return responses.pop(0)

    async def fake_sleep(_seconds):
        return None

    monkeypatch.setattr(client, "_make_request", fake_make_request)
    monkeypatch.setattr(
        "app.services.ai_client.ai302_grok_client.asyncio.sleep",
        fake_sleep,
    )

    response = await client.edit_image(
        image_url="https://example.com/input.png",
        prompt="make a textile pattern",
        aspect_ratio="1:1",
    )

    assert response == {"image_url": "https://file.302.ai/gpt/imgs/20260522/result.jpg"}
    assert AI302GrokClient.extract_image_url(response) == (
        "https://file.302ai.cn/gpt/imgs/20260522/result.jpg"
    )
    assert calls == [
        {
            "method": "POST",
            "endpoint": "/302/submit/grok-imagine-image-edit",
            "data": {
                "image_url": "https://example.com/input.png",
                "prompt": "make a textile pattern",
                "output_format": "jpeg",
                "aspect_ratio": "1:1",
            },
            "params": None,
        },
        {
            "method": "GET",
            "endpoint": "/302/submit/grok-imagine-image",
            "data": None,
            "params": {"request_id": "req-123"},
        },
        {
            "method": "GET",
            "endpoint": "/302/submit/grok-imagine-image",
            "data": None,
            "params": {"request_id": "req-123"},
        },
    ]


@pytest.mark.asyncio
async def test_ai302_grok_edit_image_raises_on_async_failure(monkeypatch):
    monkeypatch.setattr(settings, "ai302_api_key", "test-key")
    monkeypatch.setattr(settings, "ai302_base_url", "https://api.302.ai")
    monkeypatch.setattr(settings, "ai302_grok_poll_interval_seconds", 1)
    monkeypatch.setattr(settings, "ai302_grok_poll_timeout_seconds", 10)

    client = AI302GrokClient()
    responses = [
        {"request_id": "req-123"},
        {"request_id": "req-123", "status": "failed", "error": "blocked"},
    ]

    async def fake_make_request(method, endpoint, data, headers=None, params=None):
        return responses.pop(0)

    monkeypatch.setattr(client, "_make_request", fake_make_request)

    with pytest.raises(ValueError, match="async task failed"):
        await client.edit_image(
            image_url="https://example.com/input.png",
            prompt="make a textile pattern",
        )
