import asyncio
import importlib
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings
from app.models.task import Task
from app.models.batch_task import BatchTask
from app.services.ai_client.ai_client import AIClient
from app.services.ai_client.exceptions import AIClientException
from app.services.ai_client.runninghub_client import RunningHubClient
from app.services.ai_client.runninghub_recovery import (
    RUNNINGHUB_CHECKPOINT_KEY, RunningHubRecovery, RunningHubPendingError,
    runninghub_recovery,
)
from app.services.processing_service import ProcessingService

URL = "https://example.com/result.png"


@pytest.fixture
def client(monkeypatch):
    client = RunningHubClient(api_key="test-key")
    monkeypatch.setattr(client, "_upload_file", AsyncMock(return_value="input.png"))
    monkeypatch.setattr(client, "_submit_task", AsyncMock(return_value="upstream-123"))
    monkeypatch.setattr(client, "_poll_task", AsyncMock(return_value=[URL]))
    return client


async def run(client, options=None, workflow_id="wf"):
    return await client.run_workflow_with_custom_nodes(
        b"image", workflow_id, "184", "image", options,
    )


@pytest.mark.asyncio
async def test_checkpoint_is_saved_before_polling_and_resumed_without_resubmission(client):
    saved = []

    async def timeout(task_id):
        assert saved[-1]["wf|184|image"]["taskId"] == task_id
        raise TimeoutError()

    client._poll_task.side_effect = timeout
    token = runninghub_recovery.set(RunningHubRecovery(save=lambda tasks: saved.append(deepcopy(tasks))))
    try:
        with pytest.raises(RunningHubPendingError):
            await run(client)
    finally:
        runninghub_recovery.reset(token)

    client._poll_task.side_effect = None
    token = runninghub_recovery.set(RunningHubRecovery(tasks=deepcopy(saved[-1])))
    try:
        assert await run(client) == [URL]
        assert await run(client) == [URL]
    finally:
        runninghub_recovery.reset(token)
    client._submit_task.assert_awaited_once()
    client._upload_file.assert_awaited_once()
    assert client._poll_task.await_count == 2


@pytest.mark.asyncio
async def test_distinct_workflows_do_not_overwrite_each_others_ids(client):
    client._submit_task.side_effect = ["job-1", "job-2"]
    tracker = RunningHubRecovery()
    token = runninghub_recovery.set(tracker)
    try:
        await asyncio.gather(run(client, workflow_id="wf-1"), run(client, workflow_id="wf-2"))
    finally:
        runninghub_recovery.reset(token)
    assert {r["taskId"] for r in tracker.tasks.values()} == {"job-1", "job-2"}
    assert all(r["urls"] == [URL] for r in tracker.tasks.values())


@pytest.mark.asyncio
async def test_task_cancellation_retains_submitted_id(client):
    started = asyncio.Event()

    async def hang(task_id):
        started.set()
        await asyncio.sleep(10)

    client._poll_task.side_effect = hang
    tracker = RunningHubRecovery()
    token = runninghub_recovery.set(tracker)
    try:
        task = asyncio.create_task(run(client))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert tracker.tasks["wf|184|image"]["taskId"] == "upstream-123"
    finally:
        runninghub_recovery.reset(token)


@pytest.mark.asyncio
async def test_poll_retries_network_and_server_errors_on_same_task(monkeypatch):
    client = RunningHubClient(api_key="test-key")
    client.poll_interval = 0
    post = AsyncMock(side_effect=[
        AIClientException("network", api_name="RunningHub"),
        AIClientException("busy", status_code=503),
        AIClientException("limited", status_code=429),
        {"code": 0, "data": [{"fileUrl": URL}]},
    ])
    monkeypatch.setattr(client, "_post_json", post)
    assert await client._poll_task("existing-job") == [URL]
    assert all(c.kwargs["json"]["taskId"] == "existing-job" for c in post.await_args_list)


@pytest.mark.asyncio
async def test_poll_permanent_failure_does_not_retry(monkeypatch):
    client = RunningHubClient(api_key="test-key")
    post = AsyncMock(side_effect=AIClientException("unauthorized", status_code=401))
    monkeypatch.setattr(client, "_post_json", post)
    with pytest.raises(AIClientException):
        await client._poll_task("existing-job")
    post.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_transient_errors_are_bounded(monkeypatch):
    module = importlib.import_module("app.services.ai_client.runninghub_client")
    client = RunningHubClient(api_key="test-key")
    client.poll_timeout = 2
    now = [0]

    async def sleep(_interval):
        now[0] += 1

    monkeypatch.setattr(module, "time", SimpleNamespace(monotonic=lambda: now[0]))
    monkeypatch.setattr(module, "asyncio", SimpleNamespace(sleep=sleep))
    post = AsyncMock(side_effect=AIClientException("network"))
    monkeypatch.setattr(client, "_post_json", post)
    with pytest.raises(TimeoutError):
        await client._poll_task("existing-job")
    assert post.await_count == 2


@pytest.mark.asyncio
async def test_no_results_with_submitted_jobs_remains_recoverable(monkeypatch):
    client = AIClient.__new__(AIClient)
    client.runninghub_client = SimpleNamespace(
        run_workflow_with_custom_nodes=AsyncMock(side_effect=RunningHubPendingError("still running")),
    )
    monkeypatch.setattr(settings, "extract_pattern_general_workflow_attempts", 2)
    with pytest.raises(RunningHubPendingError):
        await client._extract_pattern_general_1(b"image", {"num_images": 4})
    assert client.runninghub_client.run_workflow_with_custom_nodes.await_count == 4


@pytest.mark.asyncio
async def test_pending_job_keeps_processing_without_refund_and_cleans_context(monkeypatch, client):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        task = Task(
            task_id="pending-test", user_id=1, type="extract_pattern",
            status="queued", original_image_url="/files/source.png",
            original_filename="source.png", original_file_size=1, credits_used=1.5,
            options={"pattern_type": "general", "num_images": 1},
            extra_metadata={"creditsReserved": True},
        )
        db.add(task)
        db.commit()
    service = ProcessingService()
    monkeypatch.setattr(settings, "task_watchdog_enabled", True)
    monkeypatch.setattr("app.core.database.SessionLocal", sessions)
    monkeypatch.setattr(service.file_service, "read_file", AsyncMock(return_value=b"image"))
    monkeypatch.setattr(service.file_service, "ensure_accessible_url", AsyncMock(return_value="/files/source.png"))
    refund = AsyncMock()
    monkeypatch.setattr(service, "_refund_reserved_credits", refund)
    client._poll_task.side_effect = TimeoutError()
    ai = AIClient.__new__(AIClient)
    ai.runninghub_client = client
    monkeypatch.setattr(
        "app.services.processing_service.ai_client.extract_pattern",
        ai._extract_pattern_general_1,
    )

    await service._process_task_async("pending-test")

    with sessions() as db:
        task = db.query(Task).filter(Task.task_id == "pending-test").one()
        assert task.status == "processing"
        assert float(task.credits_used) == 1.5
        records = task.extra_metadata[RUNNINGHUB_CHECKPOINT_KEY]
        assert next(iter(records.values()))["taskId"] == "upstream-123"
    refund.assert_not_awaited()
    assert runninghub_recovery.get() is None
    engine.dispose()


def test_recovered_children_update_batch_progress():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    service = ProcessingService()
    with sessions() as db:
        batch = BatchTask(
            batch_id="recovery-batch", user_id=1, task_type="extract_pattern",
            status="processing", total_images=2,
        )
        db.add(batch)
        db.flush()
        children = [
            Task(
                task_id=f"batch-child-{i}", batch_id=batch.id,
                user_id=1, type="extract_pattern", status="processing",
                original_image_url="/files/source.png", original_filename="source.png",
                original_file_size=1, credits_used=1.5,
            ) for i in range(2)
        ]
        db.add_all(children)
        db.commit()
        children[0].status = "completed"
        service._sync_batch_progress(db, children[0])
        assert batch.completed_images == 1
        assert batch.status == "processing"
        children[1].status = "failed"
        service._sync_batch_progress(db, children[1])
        assert batch.completed_images == 1
        assert batch.failed_images == 1
        assert batch.status == "partial"
        assert batch.completed_at is not None
    engine.dispose()


def test_checkpoint_is_durable_and_stale_workers_cannot_overwrite_it():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    service = ProcessingService()
    with sessions() as db:
        task = Task(
            task_id="recovery-test", user_id=1, type="extract_pattern",
            status="processing", original_image_url="/files/source.png",
            original_filename="source.png", original_file_size=1, credits_used=1.5,
            extra_metadata={"processing_token": "owner", "creditsReserved": True},
        )
        db.add(task)
        db.commit()
        task_id = task.id
        tracker = service._runninghub_recovery_for_task(db, task, "owner")
        tracker.checkpoint("wf", {"taskId": "paid-job"})
    with sessions() as db:
        task = db.get(Task, task_id)
        assert task.extra_metadata[RUNNINGHUB_CHECKPOINT_KEY]["wf"]["taskId"] == "paid-job"
        assert task.extra_metadata["creditsReserved"] is True
        assert service._runninghub_recovery_for_task(db, task, "owner").tasks["wf"]["taskId"] == "paid-job"
        stale = service._runninghub_recovery_for_task(db, task, "old-owner")
        with pytest.raises(asyncio.CancelledError):
            stale.checkpoint("wf", {"taskId": "wrong-job"})
        db.refresh(task)
        assert task.extra_metadata[RUNNINGHUB_CHECKPOINT_KEY]["wf"]["taskId"] == "paid-job"
    engine.dispose()
