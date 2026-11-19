import asyncio
from copy import deepcopy
from email import policy
from email.parser import BytesParser
from io import BytesIO

import httpx
import pytest
from app.core.config import settings
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
from PIL import Image


def png(width=64, height=64):
    buffer = BytesIO()
    Image.new("RGB", (width, height), "blue").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "seedream_api_key", "seedream-test-key")
    monkeypatch.setattr(settings, "seedream_api_key_file", str(tmp_path / "unused"))
    monkeypatch.setattr(settings, "seedream_base_url", "https://seedream.example")
    monkeypatch.setattr(settings, "seedream_poll_interval_seconds", 0.001)
    monkeypatch.setattr(settings, "seedream_poll_timeout_seconds", 0.02)

    async def run(name, factory):
        assert name == "seedream"
        return await factory()

    monkeypatch.setattr("app.services.ai_client.seedream_client.api_limiter.run", run)
    client = SeedreamClient()
    monkeypatch.setattr(
        client, "_save_image_bytes", lambda raw, prefix: "/files/results/saved.png"
    )
    return client


def install(monkeypatch, handler):
    original = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: original(transport=transport, **kwargs)
    )


async def parts(request):
    header = (
        "Content-Type: "
        + request.headers["Content-Type"]
        + "\r\nMIME-Version: 1.0\r\n\r\n"
    )
    message = BytesParser(policy=policy.default).parsebytes(
        header.encode() + await request.aread()
    )
    return list(message.iter_parts())


@pytest.mark.asyncio
async def test_generate_uploads_multiple_files_polls_downloads_and_caches(
    client, monkeypatch
):
    calls = []
    captured = []

    async def handler(request):
        calls.append((request.method, request.url.path))
        assert request.headers["X-API-Key"] == "seedream-test-key"
        if request.method == "POST":
            form = await parts(request)
            files = [
                p
                for p in form
                if p.get_param("name", header="content-disposition") == "file"
            ]
            assert len(files) == 2
            fields = {
                p.get_param("name", header="content-disposition"): p for p in form
            }
            assert fields["ratio"].get_payload(decode=True) == b"9:16"
            assert fields["prompt"].get_payload(decode=True).decode() == "只改背景"
            assert all(p.get_content_type() == "image/png" for p in files)
            return httpx.Response(200, json={"code": 0, "taskid": "job-1"})
        if request.url.path == "/try_get":
            assert request.url.params["taskid"] == "job-1"
            return httpx.Response(
                200,
                json={
                    "code": 0,
                    "results": [{"url": "/result.png", "name": "result.png"}],
                },
            )
        assert request.url.path == "/result.png"
        return httpx.Response(200, content=png(), headers={"Content-Type": "image/png"})

    install(monkeypatch, handler)

    def save(raw, prefix):
        with Image.open(BytesIO(raw)) as image:
            image.verify()
        captured.append(raw)
        return "/files/results/saved.png"

    monkeypatch.setattr(client, "_save_image_bytes", save)
    checkpointed = []
    tracker = SeedreamRecovery(
        save=lambda records: checkpointed.append(deepcopy(records))
    )
    token = seedream_recovery.set(tracker)
    try:
        args = {"images": [png(64, 128), png()], "prompt": "只改背景"}
        assert await client.generate(**args) == ["/files/results/saved.png"]
        assert await client.generate(**args) == ["/files/results/saved.png"]
    finally:
        seedream_recovery.reset(token)
    assert calls == [("POST", "/add_task"), ("GET", "/try_get"), ("GET", "/result.png")]
    assert len(captured) == 1
    assert any(r["prompt_edit"].get("taskid") == "job-1" for r in checkpointed)
    assert checkpointed[-1]["prompt_edit"]["savedResults"] == [
        "/files/results/saved.png"
    ]


@pytest.mark.asyncio
async def test_pending_job_resumes_with_no_second_paid_submission(client, monkeypatch):
    calls = []
    ready = [False]
    saved = []

    async def handler(request):
        calls.append((request.method, request.url.path))
        if request.method == "POST":
            return httpx.Response(200, json={"code": 0, "taskid": "accepted-job"})
        if request.url.path == "/try_get":
            return httpx.Response(
                200,
                json={"code": 0, "results": [{"url": "/out.png"}]}
                if ready[0]
                else {"code": 1},
            )
        return httpx.Response(200, content=png())

    install(monkeypatch, handler)
    tracker = SeedreamRecovery(save=lambda r: saved.append(deepcopy(r)))
    token = seedream_recovery.set(tracker)
    try:
        with pytest.raises(SeedreamPendingError):
            await client.generate([png()], "edit")
    finally:
        seedream_recovery.reset(token)
    ready[0] = True
    token = seedream_recovery.set(SeedreamRecovery(records=saved[-1]))
    try:
        assert await client.generate([png()], "edit") == ["/files/results/saved.png"]
    finally:
        seedream_recovery.reset(token)
    assert sum(method == "POST" for method, _ in calls) == 1


@pytest.mark.asyncio
async def test_uncertain_submission_is_not_retried(client, monkeypatch):
    calls = []

    async def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("unknown submission", request=request)

    install(monkeypatch, handler)
    tracker = SeedreamRecovery()
    token = seedream_recovery.set(tracker)
    try:
        for _ in range(2):
            with pytest.raises(SeedreamSubmissionUnknownError):
                await client.generate([png()], "edit")
    finally:
        seedream_recovery.reset(token)
    assert len(calls) == 1
    assert tracker.records["prompt_edit"]["state"] == "submission_unknown"


@pytest.mark.asyncio
async def test_cross_origin_result_never_receives_credentials(client, monkeypatch):
    calls = []

    async def handler(request):
        calls.append(request.url.host)
        if request.method == "POST":
            return httpx.Response(200, json={"code": 0, "taskid": "safe"})
        return httpx.Response(
            200,
            json={"code": 0, "results": [{"url": "https://evil.example/image.png"}]},
        )

    install(monkeypatch, handler)
    with pytest.raises(AIClientException, match="跨域"):
        await client.generate([png()], "edit")
    assert calls == ["seedream.example", "seedream.example"]


@pytest.mark.asyncio
async def test_redirects_are_not_followed(client, monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.example"})

    install(monkeypatch, handler)
    with pytest.raises(AIClientException):
        await client.generate([png()], "edit")
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_failed_download_recovers_without_resubmitting(client, monkeypatch):
    posts = []
    available = [False]

    async def handler(request):
        if request.method == "POST":
            posts.append(request)
            return httpx.Response(200, json={"code": 0, "taskid": "download-job"})
        if request.url.path == "/try_get":
            return httpx.Response(
                200, json={"code": 0, "results": [{"url": "/out.png"}]}
            )
        return (
            httpx.Response(200, content=png()) if available[0] else httpx.Response(503)
        )

    install(monkeypatch, handler)
    tracker = SeedreamRecovery()
    token = seedream_recovery.set(tracker)
    try:
        with pytest.raises(SeedreamPendingError):
            await client.generate([png()], "edit")
        available[0] = True
        assert await client.generate([png()], "edit") == ["/files/results/saved.png"]
    finally:
        seedream_recovery.reset(token)
    assert len(posts) == 1


@pytest.mark.asyncio
async def test_quota_error_is_clear_and_does_not_resubmit(client, monkeypatch):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(403, json={"code": -1, "message": "剩余处理次数为0"})

    install(monkeypatch, handler)
    with pytest.raises(AIClientException, match="剩余处理次数") as error:
        await client.generate([png()], "edit")
    assert error.value.status_code == 403
    assert len(calls) == 1
    assert "seedream-test-key" not in str(error.value)


@pytest.mark.asyncio
async def test_cancelled_submission_retains_uncertain_record(client, monkeypatch):
    started = asyncio.Event()
    calls = []

    async def handler(request):
        calls.append(request)
        started.set()
        await asyncio.sleep(10)

    install(monkeypatch, handler)
    tracker = SeedreamRecovery()
    token = seedream_recovery.set(tracker)
    try:
        task = asyncio.create_task(client.generate([png()], "edit"))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        with pytest.raises(SeedreamSubmissionUnknownError):
            await client.generate([png()], "edit")
    finally:
        seedream_recovery.reset(token)
    assert len(calls) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,content", [(503, b"upstream failure"), (200, b"not JSON")]
)
async def test_uncertain_server_response_never_resubmits(
    client, monkeypatch, status, content
):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, content=content)

    install(monkeypatch, handler)
    token = seedream_recovery.set(SeedreamRecovery())
    try:
        for _ in range(2):
            with pytest.raises(SeedreamSubmissionUnknownError):
                await client.generate([png()], "edit")
    finally:
        seedream_recovery.reset(token)
    assert len(calls) == 1


def test_limit_override_keeps_custom_values_and_includes_new_provider():
    from app.core.config import Settings

    configured = Settings(_env_file=None, api_concurrency_limits={"apyi_gemini": 17})
    assert configured.api_concurrency_limits == {"apyi_gemini": 17, "seedream": 2}


def test_exif_orientation_is_respected_for_auto_ratio():
    image = Image.new("RGB", (300, 200))
    exif = Image.Exif()
    exif[274] = 6
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    images, ratio = SeedreamClient.prepare_images([buffer.getvalue()], "auto")
    assert ratio == "2:3"
    with Image.open(BytesIO(images[0])) as normalized:
        assert normalized.size == (200, 300)


def test_private_file_key_and_mail_prompt(client, monkeypatch, tmp_path):
    key = tmp_path / "key"
    key.write_text("private-file-key\n")
    monkeypatch.setattr(settings, "seedream_api_key", "")
    monkeypatch.setattr(settings, "seedream_api_key_file", str(key))
    assert SeedreamClient().api_key == "private-file-key"
    assert SEEDREAM_PATTERN_PROMPT.startswith("帮我把图案完全展开")
    assert "禁止生成褶皱" in SEEDREAM_PATTERN_PROMPT
    assert len(SEEDREAM_PATTERN_PROMPT) == 511


@pytest.mark.asyncio
@pytest.mark.parametrize("slot_error", [TimeoutError, ConnectionError])
async def test_no_slot_never_marks_post_started_and_can_retry_safely(
    client, monkeypatch, slot_error
):
    from app.services.ai_client.seedream_client import api_limiter

    allowed = api_limiter.run
    calls = []
    snapshots = []
    tracker = SeedreamRecovery(save=lambda records: snapshots.append(deepcopy(records)))

    async def denied(name, factory):
        raise slot_error("Acquire failed: no HTTP request executed")

    async def handler(request):
        calls.append(request.method)
        if request.method == "POST":
            assert tracker.records["prompt_edit"]["state"] == "submitting"
            return httpx.Response(
                200, json={"code": 0, "taskid": "eventually-accepted"}
            )
        if request.url.path == "/try_get":
            return httpx.Response(
                200, json={"code": 0, "results": [{"url": "/out.png"}]}
            )
        return httpx.Response(200, content=png())

    install(monkeypatch, handler)
    monkeypatch.setattr(api_limiter, "run", denied)
    token = seedream_recovery.set(tracker)
    try:
        with pytest.raises(AIClientException) as error:
            await client.generate([png()], "edit")
        assert not isinstance(
            error.value, (SeedreamPendingError, SeedreamSubmissionUnknownError)
        )
        assert error.value.status_code == 429
        assert error.value.request_data["operation"] == "acquire"
        assert tracker.records["prompt_edit"]["state"] == "waiting_for_slot"
        assert (
            tracker.records["prompt_edit"]["lastError"]["exceptionType"]
            == slot_error.__name__
        )
        assert calls == []
        assert all(s["prompt_edit"]["state"] == "waiting_for_slot" for s in snapshots)
        monkeypatch.setattr(api_limiter, "run", allowed)
        assert await client.generate([png()], "edit") == ["/files/results/saved.png"]
    finally:
        seedream_recovery.reset(token)
    assert calls == ["POST", "GET", "GET"]


@pytest.mark.asyncio
async def test_cancellation_while_waiting_does_not_create_uncertain_paid_submission(
    client, monkeypatch
):
    from app.services.ai_client.seedream_client import api_limiter

    waiting = asyncio.Event()
    calls = []

    async def no_slot_yet(name, factory):
        waiting.set()
        await asyncio.Event().wait()

    install(monkeypatch, lambda request: calls.append(request))
    monkeypatch.setattr(api_limiter, "run", no_slot_yet)
    tracker = SeedreamRecovery()
    token = seedream_recovery.set(tracker)
    try:
        task = asyncio.create_task(client.generate([png()], "edit"))
        await waiting.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    finally:
        seedream_recovery.reset(token)
    assert calls == []
    assert tracker.records["prompt_edit"]["state"] == "waiting_for_slot"


@pytest.mark.asyncio
async def test_invalid_job_id_is_terminal_unknown_and_never_resubmitted(
    client, monkeypatch
):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"code": 0, "taskid": ""})

    install(monkeypatch, handler)
    tracker = SeedreamRecovery()
    token = seedream_recovery.set(tracker)
    try:
        for _ in range(2):
            with pytest.raises(SeedreamSubmissionUnknownError):
                await client.generate([png()], "edit")
    finally:
        seedream_recovery.reset(token)
    assert len(calls) == 1
    assert tracker.records["prompt_edit"]["state"] == "submission_unknown"
