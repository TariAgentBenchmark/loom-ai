import asyncio
import time
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.services.ai_client.ai_client import AIClient


def _build_client() -> AIClient:
    client = AIClient.__new__(AIClient)
    client.image_utils = SimpleNamespace(
        extract_pattern=None,
        apyi_gemini_client=SimpleNamespace(
            generate_image_preview=None,
            _extract_image_url=lambda _result: None,
        ),
    )
    client.runninghub_client = SimpleNamespace(run_workflow_with_custom_nodes=None)
    client.ai302_grok_client = SimpleNamespace(edit_image=None, extract_image_url=None)
    return client


@pytest.mark.asyncio
async def test_extract_pattern_combined_returns_early_when_enough_results(monkeypatch):
    client = _build_client()
    cancelled = {"grok": False, "runninghub": False}

    async def fake_extract_pattern(_image_bytes, options):
        pattern_type = options["pattern_type"]
        if pattern_type == "general_2":
            await asyncio.sleep(0.01)
            return "https://example.com/general.png"
        if pattern_type == "combined_detail":
            await asyncio.sleep(0.02)
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {pattern_type}")

    async def slow_edit_image(**_kwargs):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled["grok"] = True
            raise

    async def slow_runninghub(**_kwargs):
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled["runninghub"] = True
            raise

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 180)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 2)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.ai302_grok_client, "edit_image", slow_edit_image)
    monkeypatch.setattr(client.ai302_grok_client, "extract_image_url", lambda _result: None)

    result = await client._extract_pattern_combined(
        b"fake-image",
        {"original_image_url": "https://example.com/source.png", "aspect_ratio": "1:1"},
    )

    assert result == "https://example.com/general.png,https://example.com/detail.png"
    assert cancelled == {"grok": True, "runninghub": True}


@pytest.mark.asyncio
async def test_extract_pattern_combined_allows_timeouts_when_other_branches_succeed(monkeypatch):
    client = _build_client()

    async def fake_extract_pattern(_image_bytes, options):
        pattern_type = options["pattern_type"]
        if pattern_type == "general_2":
            return "https://example.com/general.png"
        if pattern_type == "combined_detail":
            await asyncio.sleep(1)
            return "https://example.com/detail.png"
        raise AssertionError(f"unexpected pattern type: {pattern_type}")

    async def fast_edit_image(**_kwargs):
        return {"data": [{"url": "https://example.com/grok.png"}]}

    async def slow_runninghub(**_kwargs):
        await asyncio.sleep(1)
        return ["https://example.com/runninghub.png"]

    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.05)
    monkeypatch.setattr(settings, "extract_pattern_combined_early_return_success_count", 4)
    monkeypatch.setattr(client.image_utils, "extract_pattern", fake_extract_pattern)
    monkeypatch.setattr(
        client.runninghub_client,
        "run_workflow_with_custom_nodes",
        slow_runninghub,
    )
    monkeypatch.setattr(client.ai302_grok_client, "edit_image", fast_edit_image)
    monkeypatch.setattr(
        client.ai302_grok_client,
        "extract_image_url",
        lambda result: result["data"][0]["url"],
    )

    started = time.monotonic()
    result = await client._extract_pattern_combined(
        b"fake-image",
        {"original_image_url": "https://example.com/source.png", "aspect_ratio": "1:1"},
    )
    elapsed = time.monotonic() - started

    assert result == "https://example.com/general.png,https://example.com/grok.png"
    assert elapsed < 0.3
