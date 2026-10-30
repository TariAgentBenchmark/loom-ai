import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.tuzi_openai_client import (
    TUZI_GPT_IMAGE_2_MODEL,
    TUZI_GPT_IMAGE_2_VIP_MODEL,
    TuziOpenAIClient,
)

RESULT = {"data": [{"url": "https://example.com/backup.png"}]}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 1)
    client = AIClient.__new__(AIClient)
    client.tuzi_openai_client = TuziOpenAIClient()
    client.tuzi_openai_client.edit_image = AsyncMock()
    return client


async def run_branch(client, errors):
    return await client._extract_pattern_gpt_with_fallback(
        b"image", label="gpt_branch", branch_errors=errors,
    )


def called_models(client):
    return [
        call.kwargs["model"]
        for call in client.tuzi_openai_client.edit_image.await_args_list
    ]


@pytest.mark.asyncio
async def test_vip_success_does_not_call_or_charge_backup(client):
    client.tuzi_openai_client.edit_image.return_value = RESULT
    errors = []

    assert await run_branch(client, errors) == RESULT["data"][0]["url"]
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL]
    assert errors == []


@pytest.mark.asyncio
async def test_backup_runs_after_vip_http_error(client):
    client.tuzi_openai_client.edit_image.side_effect = [
        AIClientException("Invalid request", api_name="tuzi_openai", status_code=400),
        RESULT,
    ]
    errors = []

    assert await run_branch(client, errors) == RESULT["data"][0]["url"]
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL, TUZI_GPT_IMAGE_2_MODEL]
    assert errors[0]["model"] == TUZI_GPT_IMAGE_2_VIP_MODEL
    assert errors[0]["statusCode"] == 400


@pytest.mark.asyncio
async def test_backup_runs_after_unparseable_vip_response(client):
    response = {"choices": [{"message": {"content": "No image available"}}]}
    client.tuzi_openai_client.edit_image.side_effect = [response, RESULT]
    errors = []

    assert await run_branch(client, errors) == RESULT["data"][0]["url"]
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL, TUZI_GPT_IMAGE_2_MODEL]
    assert errors[0]["responseBody"] == response


@pytest.mark.asyncio
async def test_empty_image_url_also_uses_backup(client):
    client.tuzi_openai_client.edit_image.side_effect = [
        {"data": [{"url": " "}]}, RESULT,
    ]
    assert await run_branch(client, []) == RESULT["data"][0]["url"]
    assert len(called_models(client)) == 2


@pytest.mark.asyncio
async def test_vip_timeout_is_cancelled_before_backup(client, monkeypatch):
    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.05)
    cancelled = asyncio.Event()

    async def edit_image(**kwargs):
        if kwargs["model"] == TUZI_GPT_IMAGE_2_VIP_MODEL:
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.set()
        assert cancelled.is_set()
        return RESULT

    client.tuzi_openai_client.edit_image.side_effect = edit_image
    errors = []
    assert await run_branch(client, errors) == RESULT["data"][0]["url"]
    assert cancelled.is_set()
    assert errors[0]["exceptionType"] == "TimeoutError"
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL, TUZI_GPT_IMAGE_2_MODEL]


@pytest.mark.asyncio
async def test_both_channels_failing_preserves_diagnostics(client):
    client.tuzi_openai_client.edit_image.side_effect = RuntimeError("upstream unavailable")
    errors = []

    assert await run_branch(client, errors) is None
    assert [e["model"] for e in errors] == [
        TUZI_GPT_IMAGE_2_VIP_MODEL, TUZI_GPT_IMAGE_2_MODEL,
    ]
    assert [e["attempt"] for e in errors] == [1, 2]
    assert [e["fallback"] for e in errors] == [False, True]


@pytest.mark.asyncio
async def test_two_hung_channels_are_bounded_by_one_branch_budget(client, monkeypatch):
    monkeypatch.setattr(settings, "extract_pattern_combined_branch_timeout_seconds", 0.05)

    async def hang(**kwargs):
        await asyncio.sleep(10)

    client.tuzi_openai_client.edit_image.side_effect = hang
    errors = []
    assert await asyncio.wait_for(run_branch(client, errors), timeout=0.5) is None
    assert len(errors) == 2
    assert all(e["exceptionType"] == "TimeoutError" for e in errors)


@pytest.mark.asyncio
async def test_task_cancellation_does_not_start_backup(client):
    started = asyncio.Event()

    async def hang(**kwargs):
        started.set()
        await asyncio.sleep(10)

    client.tuzi_openai_client.edit_image.side_effect = hang
    task = asyncio.create_task(run_branch(client, []))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL]


@pytest.mark.asyncio
@pytest.mark.parametrize("pattern_type", ["combined", "combined_t2"])
async def test_both_combined_modes_keep_backup_image_when_other_branches_fail(client, pattern_type):
    failure = RuntimeError("other provider unavailable")
    gemini = SimpleNamespace(generate_image_preview=AsyncMock(side_effect=failure))
    client._gemini_preview_client_for_provider = lambda _provider: gemini
    client.image_utils = SimpleNamespace(
        _build_pattern_prompt=lambda _pt: "pattern prompt",
        extract_pattern=AsyncMock(side_effect=failure),
    )
    client.runninghub_client = SimpleNamespace(
        run_workflow_with_custom_nodes=AsyncMock(side_effect=failure),
    )
    client.tuzi_openai_client.edit_image.side_effect = [RuntimeError("VIP failed"), RESULT]
    options = {"num_images": 2}

    if pattern_type == "combined":
        result = await client._extract_pattern_combined(b"image", options)
    else:
        result = await client._extract_pattern_combined_t2(b"image", options)

    assert result == RESULT["data"][0]["url"]
    assert called_models(client) == [TUZI_GPT_IMAGE_2_VIP_MODEL, TUZI_GPT_IMAGE_2_MODEL]
