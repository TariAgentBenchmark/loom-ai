import pytest

from app.services.ai_client.gqch_client import GQCHClient


@pytest.mark.asyncio
async def test_extract_pattern_submits_documented_gqch_endpoint(monkeypatch):
    client = GQCHClient()
    captured = {}

    async def fake_submit_task(endpoint, payload, image_bytes, original_filename):
        captured["endpoint"] = endpoint
        captured["payload"] = payload
        captured["image_bytes"] = image_bytes
        captured["original_filename"] = original_filename
        return "https://example.com/result.png"

    monkeypatch.setattr(client, "_submit_task", fake_submit_task)

    result = await client.extract_pattern(
        b"image-bytes",
        "source.png",
        {"aspect_ratio": "4:3", "model_version": "v2"},
    )

    assert result == "https://example.com/result.png"
    assert captured == {
        "endpoint": "/api/submit_extract_pattern_task",
        "payload": {
            "aspect_ratio": "4:3",
            "model_version": "v2",
            "include_text": None,
            "seamless_tile": None,
        },
        "image_bytes": b"image-bytes",
        "original_filename": "source.png",
    }
