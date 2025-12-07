import logging
from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """
    Lazy init a shared Redis asyncio client using application settings.
    Using lru_cache to avoid creating multiple connections per process.
    """
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    logger.info("Initialized Redis client for URL %s", settings.redis_url)
    return client


async def close_redis_client():
    """Close the shared Redis client if it was created."""
    client = get_redis_client()
    try:
        await client.close()
    except Exception as exc:
        logger.warning("Failed to close Redis client: %s", exc)
