import pytest

from app.core.config import settings
from app.services.task_watchdog_service import TaskWatchdogService


class _FakeRedis:
    def __init__(self):
        self.values = {}

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def eval(self, _script, _numkeys, key, token):
        if self.values.get(key) == token:
            del self.values[key]
            return 1
        return 0


class _FakeDB:
    def close(self):
        return None


@pytest.mark.asyncio
async def test_watchdog_lock_can_be_reacquired_after_release(monkeypatch):
    fake_redis = _FakeRedis()
    service = TaskWatchdogService()

    monkeypatch.setattr(settings, "redis_url", "redis://fake")
    monkeypatch.setattr(
        "app.services.task_watchdog_service.get_redis_client",
        lambda: fake_redis,
    )

    token = await service._acquire_lock(240)
    assert token

    second_attempt = await service._acquire_lock(240)
    assert second_attempt is None

    await service._release_lock(token)

    third_attempt = await service._acquire_lock(240)
    assert third_attempt


@pytest.mark.asyncio
async def test_recover_stuck_tasks_releases_lock_each_cycle(monkeypatch):
    fake_redis = _FakeRedis()
    fake_db = _FakeDB()
    service = TaskWatchdogService()

    monkeypatch.setattr(settings, "task_watchdog_enabled", True)
    monkeypatch.setattr(settings, "redis_url", "redis://fake")
    monkeypatch.setattr(
        "app.services.task_watchdog_service.get_redis_client",
        lambda: fake_redis,
    )
    monkeypatch.setattr(
        "app.services.task_watchdog_service.SessionLocal",
        lambda: fake_db,
    )
    monkeypatch.setattr(service, "_query_stuck_processing", lambda *_args: [])
    monkeypatch.setattr(service, "_query_stuck_queued", lambda *_args: [])

    await service.recover_stuck_tasks()

    next_token = await service._acquire_lock(240)
    assert next_token
