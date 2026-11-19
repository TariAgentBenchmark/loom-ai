import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.core.config import settings
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.seedream_client import (
    SEEDREAM_PATTERN_PROMPT,
    SeedreamClient,
)
from app.services.ai_client.seedream_recovery import (
    SeedreamPendingError,
    SeedreamRecovery,
    SeedreamSubmissionUnknownError,
    seedream_recovery,
)


@pytest.fixture
def cached_combined(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "seedream_api_key", "offline-only")
    monkeypatch.setattr(settings, "seedream_api_key_file", str(tmp_path / "unused"))
    ai = AIClient.__new__(AIClient)
    ai.seedream_client = SeedreamClient()
    ai.seedream_client._json = AsyncMock(side_effect=AssertionError("No upstream I/O"))
    ai._extract_pattern_gpt_with_fallback = AsyncMock(
        side_effect=AssertionError("No regeneration")
    )
    ai._gemini_preview_client_for_provider = lambda provider: (_ for _ in ()).throw(
        AssertionError("No regeneration")
    )
    ai.runninghub_client = SimpleNamespace(
        run_workflow_with_custom_nodes=AsyncMock(
            side_effect=AssertionError("No regeneration")
        )
    )
    ai.image_utils = SimpleNamespace(_build_pattern_prompt=lambda pt: "unused")
    ai.file_service = SimpleNamespace(
        download_from_url=AsyncMock(side_effect=AssertionError("Already persisted"))
    )
    records = {
        "combined:general_2": {
            "result": "/files/results/gemini.png",
            "persisted": True,
        },
        "combined:tuzi_gpt_image_2_vip": {
            "result": "/files/results/gpt.png",
            "persisted": True,
        },
        "combined:runninghub_combined_4": {
            "result": "/files/results/rh.png",
            "persisted": True,
        },
    }
    return ai, records


@pytest.mark.asyncio
@pytest.mark.parametrize("legacy_state", ["submission_unknown", "submitting"])
async def test_legacy_unqueryable_submission_delivers_three_cached_results_without_http(
    cached_combined, legacy_state
):
    ai, records = cached_combined
    source = b"original-source"
    fingerprint = hashlib.sha256(
        SEEDREAM_PATTERN_PROMPT.encode() + b"\0auto" + hashlib.sha256(source).digest()
    ).hexdigest()
    records["combined_detail"] = {
        "baseUrl": ai.seedream_client.base_url,
        "input": fingerprint,
        "state": legacy_state,
    }
    tracker = SeedreamRecovery(records=records)
    token = seedream_recovery.set(tracker)
    try:
        for _ in range(2):
            result = await ai._extract_pattern_combined(source, {})
            assert set(result.split(",")) == {
                "/files/results/gemini.png",
                "/files/results/gpt.png",
                "/files/results/rh.png",
            }
    finally:
        seedream_recovery.reset(token)
    ai.seedream_client._json.assert_not_awaited()
    ai._extract_pattern_gpt_with_fallback.assert_not_awaited()
    ai.runninghub_client.run_workflow_with_custom_nodes.assert_not_awaited()
    ai.file_service.download_from_url.assert_not_awaited()
    assert tracker.records["combined_detail"]["state"] == legacy_state


@pytest.mark.asyncio
async def test_queryable_pending_with_no_other_results_keeps_original_job_diagnostics(
    cached_combined,
):
    ai, records = cached_combined
    for record in records.values():
        record.update(result=None, finished=True)
    pending = SeedreamPendingError(
        "upstream still generating",
        api_name="seedream",
        request_data={"taskid": "existing-job"},
    )
    ai.seedream_client.generate = AsyncMock(side_effect=pending)
    token = seedream_recovery.set(SeedreamRecovery(records=records))
    try:
        with pytest.raises(SeedreamPendingError) as error:
            await ai._extract_pattern_combined(b"source", {})
        assert error.value is pending
        assert error.value.request_data["taskid"] == "existing-job"
    finally:
        seedream_recovery.reset(token)


@pytest.mark.asyncio
async def test_unqueryable_submission_with_no_results_fails_instead_of_watchdog_wait(
    cached_combined,
):
    ai, records = cached_combined
    for record in records.values():
        record.update(result=None, finished=True)
    ai.seedream_client.generate = AsyncMock(
        side_effect=SeedreamSubmissionUnknownError("unknown", api_name="seedream")
    )
    token = seedream_recovery.set(SeedreamRecovery(records=records))
    try:
        with pytest.raises(AIClientException) as error:
            await ai._extract_pattern_combined(b"source", {})
        assert not isinstance(error.value, SeedreamPendingError)
        assert error.value.response_body["summary"]["successfulResults"] == 0
    finally:
        seedream_recovery.reset(token)
