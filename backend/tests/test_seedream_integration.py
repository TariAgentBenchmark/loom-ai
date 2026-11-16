import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.core.config import settings
from app.core.database import Base
from app.models.task import Task
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.seedream_client import SEEDREAM_PATTERN_PROMPT
from app.services.ai_client.seedream_recovery import (
    SEEDREAM_STATE_KEY,
    SeedreamPendingError,
    SeedreamRecovery,
    seedream_recovery,
)
from app.services.membership_service import MembershipService
from app.services.processing_service import ProcessingService
from app.services.service_pricing import resolve_pricing_key
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.mark.asyncio
async def test_prompt_edit_pro_uses_user_instruction_both_images_and_auto_ratio():
    ai = AIClient.__new__(AIClient)
    ai.seedream_client = SimpleNamespace(
        generate=AsyncMock(return_value=["/files/results/pro.png"])
    )
    ai.image_utils = SimpleNamespace(
        prompt_edit_image=AsyncMock(side_effect=AssertionError("legacy should not run"))
    )
    result = await ai.prompt_edit_image(
        b"primary",
        {
            "model": "seedream_pro",
            "instruction": "  只改变背景  ",
            "secondary_image_bytes": b"reference",
        },
    )
    assert result == "/files/results/pro.png"
    ai.seedream_client.generate.assert_awaited_once_with(
        images=[b"primary", b"reference"],
        prompt="只改变背景",
        ratio="auto",
        slot="prompt_edit",
    )
    ai.image_utils.prompt_edit_image.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("model", ["new", "original", "pro_4k"])
async def test_legacy_prompt_models_keep_existing_provider(model):
    ai = AIClient.__new__(AIClient)
    ai.seedream_client = SimpleNamespace(generate=AsyncMock())
    ai.image_utils = SimpleNamespace(
        prompt_edit_image=AsyncMock(return_value="legacy.png")
    )
    assert (
        await ai.prompt_edit_image(b"image", {"model": model, "instruction": "edit"})
        == "legacy.png"
    )
    ai.seedream_client.generate.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("gpt_result", ["https://provider.example/gpt.png", None])
async def test_slow_seedream_does_not_regenerate_paid_companion_branches(
    monkeypatch, gpt_result
):
    ai = AIClient.__new__(AIClient)
    gemini = SimpleNamespace(
        generate_image_preview=AsyncMock(return_value={}),
        _extract_image_url=lambda response: "https://provider.example/banana-pro.png",
    )
    ai._gemini_preview_client_for_provider = lambda provider: gemini
    ai.image_utils = SimpleNamespace(
        _build_pattern_prompt=lambda pt: "gemini prompt",
        extract_pattern=AsyncMock(
            side_effect=AssertionError("old ordinary Banana must not run")
        ),
    )
    ai._extract_pattern_gpt_with_fallback = AsyncMock(return_value=gpt_result)
    ai.runninghub_client = SimpleNamespace(
        run_workflow_with_custom_nodes=AsyncMock(
            return_value=["https://provider.example/rh.png"]
        )
    )
    ai.seedream_client = SimpleNamespace(
        generate=AsyncMock(
            side_effect=[
                SeedreamPendingError("pending"),
                ["/files/results/seedream.png"],
            ]
        )
    )
    count = [0]

    async def save(content, name, folder, **kwargs):
        count[0] += 1
        return f"/files/results/companion-{count[0]}.png"

    ai.file_service = SimpleNamespace(
        is_managed_oss_ref=lambda ref: False,
        download_from_url=AsyncMock(return_value=b"result"),
        save_upload_file=save,
    )
    stored = []
    tracker = SeedreamRecovery(save=lambda value: stored.append(deepcopy(value)))
    token = seedream_recovery.set(tracker)
    try:
        with pytest.raises(SeedreamPendingError):
            await ai._extract_pattern_combined(b"image", {})
    finally:
        seedream_recovery.reset(token)
    assert len(tracker.records) == 3
    token = seedream_recovery.set(SeedreamRecovery(records=stored[-1]))
    try:
        result = await ai._extract_pattern_combined(b"image", {})
    finally:
        seedream_recovery.reset(token)
    assert len(result.split(",")) == (4 if gpt_result else 3)
    assert "/files/results/seedream.png" in result.split(",")
    gemini.generate_image_preview.assert_awaited_once()
    ai._extract_pattern_gpt_with_fallback.assert_awaited_once()
    ai.runninghub_client.run_workflow_with_custom_nodes.assert_awaited_once()
    assert ai.file_service.download_from_url.await_count == (3 if gpt_result else 2)
    ai.image_utils.extract_pattern.assert_not_awaited()
    assert (
        ai.seedream_client.generate.await_args.kwargs["prompt"]
        == SEEDREAM_PATTERN_PROMPT
    )


@pytest.mark.asyncio
async def test_worker_restart_does_not_resubmit_unqueryable_companion_calls():
    ai = AIClient.__new__(AIClient)
    ai._extract_pattern_gpt_with_fallback = AsyncMock()
    gemini = SimpleNamespace(generate_image_preview=AsyncMock())
    ai._gemini_preview_client_for_provider = lambda provider: gemini
    ai.image_utils = SimpleNamespace(_build_pattern_prompt=lambda pt: "never")
    ai.runninghub_client = SimpleNamespace(run_workflow_with_custom_nodes=AsyncMock())
    ai.seedream_client = SimpleNamespace(
        generate=AsyncMock(return_value=["/files/results/pro.png"])
    )
    token = seedream_recovery.set(
        SeedreamRecovery(
            records={
                "combined:general_2": {"started": True},
                "combined:tuzi_gpt_image_2_vip": {"started": True},
                "combined:runninghub_combined_4": {"finished": True, "result": None},
            }
        )
    )
    try:
        assert (
            await ai._extract_pattern_combined(b"image", {}) == "/files/results/pro.png"
        )
    finally:
        seedream_recovery.reset(token)
    gemini.generate_image_preview.assert_not_awaited()
    ai._extract_pattern_gpt_with_fallback.assert_not_awaited()
    ai.runninghub_client.run_workflow_with_custom_nodes.assert_not_awaited()


def test_seedream_checkpoint_is_durable_and_owner_guarded():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    service = ProcessingService()
    with sessions() as db:
        task = Task(
            task_id="seedream-test",
            user_id=1,
            type="prompt_edit",
            status="processing",
            original_image_url="/files/original.png",
            original_filename="original.png",
            original_file_size=1,
            credits_used=1,
            options={"model": "seedream_pro"},
            extra_metadata={"processing_token": "owner", "creditsReserved": True},
        )
        db.add(task)
        db.commit()
        task_id = task.id
        tracker = service._seedream_recovery_for_task(db, task, "owner")
        tracker.checkpoint("prompt_edit", {"taskid": "accepted"})
    with sessions() as db:
        task = db.get(Task, task_id)
        assert (
            task.extra_metadata[SEEDREAM_STATE_KEY]["prompt_edit"]["taskid"]
            == "accepted"
        )
        stale = service._seedream_recovery_for_task(db, task, "old-owner")
        with pytest.raises(asyncio.CancelledError):
            stale.checkpoint("prompt_edit", {"taskid": "wrong"})
        db.refresh(task)
        assert (
            task.extra_metadata[SEEDREAM_STATE_KEY]["prompt_edit"]["taskid"]
            == "accepted"
        )
    engine.dispose()


@pytest.mark.asyncio
async def test_new_model_shares_ordinary_credit_price(db_session):
    service = MembershipService()
    await service.initialize_packages(db_session)
    ordinary = await service.calculate_service_cost(
        db_session, "prompt_edit", options={"model": "new"}
    )
    pro = await service.calculate_service_cost(
        db_session, "prompt_edit", options={"model": "seedream_pro"}
    )
    assert ordinary == pro
    assert (
        resolve_pricing_key("prompt_edit", {"model": "seedream_pro"}) == "prompt_edit"
    )
    assert (
        resolve_pricing_key("prompt_edit", {"model": "pro_4k"}) == "prompt_edit_pro_4k"
    )


@pytest.mark.asyncio
async def test_pending_seedream_task_preserves_credits_and_context(monkeypatch):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        db.add(
            Task(
                task_id="seedream-pending",
                user_id=1,
                type="prompt_edit",
                status="queued",
                original_image_url="/files/input.png",
                original_filename="input.png",
                original_file_size=1,
                credits_used=1,
                options={"model": "seedream_pro", "instruction": "edit"},
                extra_metadata={"creditsReserved": True},
            )
        )
        db.commit()
    service = ProcessingService()
    monkeypatch.setattr(settings, "task_watchdog_enabled", True)
    monkeypatch.setattr("app.core.database.SessionLocal", sessions)
    monkeypatch.setattr(
        service.file_service, "read_file", AsyncMock(return_value=b"image")
    )
    monkeypatch.setattr(
        service.file_service,
        "ensure_accessible_url",
        AsyncMock(return_value="/files/input.png"),
    )
    refund = AsyncMock()
    monkeypatch.setattr(service, "_refund_reserved_credits", refund)

    async def pending(*args, **kwargs):
        recovery = seedream_recovery.get()
        assert recovery is not None
        recovery.checkpoint("prompt_edit", {"taskid": "existing-job"})
        raise SeedreamPendingError("still generating")

    monkeypatch.setattr(
        "app.services.processing_service.ai_client.prompt_edit_image", pending
    )
    await service._process_task_async("seedream-pending")
    with sessions() as db:
        task = db.query(Task).filter(Task.task_id == "seedream-pending").one()
        assert task.status == "processing"
        assert float(task.credits_used) == 1
        assert (
            task.extra_metadata[SEEDREAM_STATE_KEY]["prompt_edit"]["taskid"]
            == "existing-job"
        )
    refund.assert_not_awaited()
    assert seedream_recovery.get() is None
    engine.dispose()
