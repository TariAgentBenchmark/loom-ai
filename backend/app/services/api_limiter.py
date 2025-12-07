import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Dict, Optional

from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class ApiLimiter:
    """
    Redis-backed distributed semaphore per downstream API.

    - Each api_name has a token list (available slots) and a set of all tokens.
    - Acquire uses BRPOP with timeout; release LPUSHes the token back.
    - A short lease key per token avoids permanent leaks if a worker crashes;
      expired leases are reclaimed before acquisition attempts.
    """

    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        limits: Optional[Dict[str, int]] = None,
        prefix: str = "api_limit",
    ):
        self._redis: Redis = redis_client or get_redis_client()
        self._limits: Dict[str, int] = limits or settings.api_concurrency_limits
        self._prefix = prefix
        self._initialized = set()
        self._applied_limits: Dict[str, int] = {}

    def _tokens_key(self, api_name: str) -> str:
        return f"{self._prefix}:{api_name}:tokens"

    def _all_tokens_key(self, api_name: str) -> str:
        return f"{self._prefix}:{api_name}:all_tokens"

    def _lease_key(self, api_name: str, token: str) -> str:
        return f"{self._prefix}:{api_name}:lease:{token}"

    def _active_key(self) -> str:
        return f"{self._prefix}:active"

    async def initialize_all(self) -> None:
        """Ensure token pools exist for all configured APIs."""
        tasks = [self._initialize_api(api_name, limit) for api_name, limit in self._limits.items()]
        if tasks:
            await asyncio.gather(*tasks)

    async def _initialize_api(self, api_name: str, limit: int) -> None:
        """
        Create or reconcile token pool for an API.
        If并发上限变更，重建可用令牌列表以与新配置对齐（保留租约中的令牌）。
        """
        current = self._applied_limits.get(api_name)
        if api_name in self._initialized and current == limit:
            return

        allowed_tokens = [f"token-{i}" for i in range(1, limit + 1)]
        leases = await self._redis.keys(self._lease_key(api_name, "*"))
        leased_tokens = {lease.split(":")[-1] for lease in leases}

        # 可用的令牌 = 允许令牌 - 正在租约的令牌
        available_tokens = [t for t in allowed_tokens if t not in leased_tokens]

        pipe = self._redis.pipeline()
        pipe.delete(self._tokens_key(api_name))
        if available_tokens:
            pipe.lpush(self._tokens_key(api_name), *available_tokens)
        pipe.delete(self._all_tokens_key(api_name))
        if allowed_tokens:
            pipe.sadd(self._all_tokens_key(api_name), *allowed_tokens)
        await pipe.execute()

        self._initialized.add(api_name)
        self._applied_limits[api_name] = limit
        logger.info(
            "Initialized/reconciled API limiter for %s with limit=%s (available=%s leased=%s)",
            api_name,
            limit,
            len(available_tokens),
            len(leased_tokens),
        )

    async def _reclaim_expired_tokens(self, api_name: str) -> int:
        """
        Reclaim tokens whose leases expired (crash/timeout cases).
        This is lightweight because limits are small.
        """
        all_tokens = await self._redis.smembers(self._all_tokens_key(api_name))
        if not all_tokens:
            return 0

        available = set(await self._redis.lrange(self._tokens_key(api_name), 0, -1))

        # Check leases in batch
        check_tasks = [
            self._redis.exists(self._lease_key(api_name, token)) for token in all_tokens
        ]
        exists_results = await asyncio.gather(*check_tasks)
        leased = {
            token for token, exists_flag in zip(all_tokens, exists_results) if exists_flag
        }

        missing = [token for token in all_tokens if token not in available and token not in leased]
        reclaimed = 0
        if missing:
            pipe = self._redis.pipeline()
            for token in missing:
                pipe.lpush(self._tokens_key(api_name), token)
                reclaimed += 1
            await pipe.execute()
            if reclaimed:
                logger.warning(
                    "Reclaimed %s expired token(s) for API %s", reclaimed, api_name
                )
        return reclaimed

    async def acquire(
        self,
        api_name: str,
        timeout_seconds: int = 30,
        lease_seconds: int = 600,
    ) -> str:
        """Acquire a token for the given API or raise TimeoutError."""
        limit = self._limits.get(api_name)
        if not limit or limit <= 0:
            raise ValueError(f"Invalid concurrency limit for API '{api_name}'")

        await self._initialize_api(api_name, limit)
        await self._reclaim_expired_tokens(api_name)

        result = await self._redis.brpop(self._tokens_key(api_name), timeout=timeout_seconds)
        if not result:
            raise TimeoutError(f"Acquire timeout for API '{api_name}'")

        _, token = result
        lease_key = self._lease_key(api_name, token)

        pipe = self._redis.pipeline()
        pipe.set(lease_key, "1", ex=lease_seconds)
        pipe.hincrby(self._active_key(), api_name, 1)
        await pipe.execute()
        return token

    async def release(self, api_name: str, token: str) -> None:
        """Release a token back to the pool."""
        # 如果 token 已不在当前允许集合（例如配置下调），释放时丢弃，不再放回池中
        allowed = await self._redis.sismember(self._all_tokens_key(api_name), token)

        pipe = self._redis.pipeline()
        pipe.delete(self._lease_key(api_name, token))
        if allowed:
            pipe.lpush(self._tokens_key(api_name), token)
        pipe.hincrby(self._active_key(), api_name, -1)
        try:
            await pipe.execute()
        except Exception as exc:
            logger.error("Failed to release token %s for %s: %s", token, api_name, exc)
            raise

    @asynccontextmanager
    async def slot(
        self,
        api_name: str,
        timeout_seconds: int = 30,
        lease_seconds: int = 600,
    ):
        """Async context manager for acquiring and releasing a token."""
        token = await self.acquire(api_name, timeout_seconds, lease_seconds)
        try:
            yield token
        finally:
            try:
                await self.release(api_name, token)
            except Exception:
                logger.exception("Token release failed for %s (token=%s)", api_name, token)

    async def run(
        self,
        api_name: str,
        coro_factory: Callable[[], Awaitable[Any]],
        timeout_seconds: int = 30,
        lease_seconds: int = 600,
    ) -> Any:
        """Acquire slot, run coroutine factory, always release."""
        async with self.slot(api_name, timeout_seconds, lease_seconds):
            return await coro_factory()

    async def get_metrics(self, api_name: str) -> Dict[str, Any]:
        """Return simple metrics for observability."""
        limit = self._limits.get(api_name)
        if not limit:
            raise ValueError(f"Unknown API '{api_name}'")

        available = await self._redis.llen(self._tokens_key(api_name))
        active_hash = await self._redis.hget(self._active_key(), api_name)
        active = int(active_hash or 0)

        leases = await self._redis.keys(self._lease_key(api_name, "*"))

        return {
            "api": api_name,
            "limit": limit,
            "available": available,
            "active": active,
            "leased_tokens": len(leases),
        }


# Shared instance for convenience
api_limiter = ApiLimiter()
