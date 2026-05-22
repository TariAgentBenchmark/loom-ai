import pytest

from app.core.config import settings
from app.services.ai_client.ai302_grok_client import AI302GrokClient
from app.services.ai_client.ai302_urls import rewrite_ai302_file_url


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
    ],
)
def test_ai302_grok_extract_image_url_rewrites_file_host(monkeypatch, response):
    monkeypatch.setattr(settings, "ai302_file_base_url", "https://file.302ai.cn")

    assert (
        AI302GrokClient.extract_image_url(response)
        == "https://file.302ai.cn/gpt/imgs/20260522/result.jpg"
    )
