import time
import uuid

import pytest
from redis.asyncio import Redis

from app.config import Settings
from app.observability.rate_limit import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_persists_window_state_in_testing_redis():
    settings = Settings(database_url="postgresql+asyncpg://x", redis_url="redis://localhost:6380/1")
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    key = f"integration:{uuid.uuid4()}"
    try:
        limiter = RateLimiter(redis)
        first = await limiter.check(key, limit=1, window_seconds=60)
        second = await limiter.check(key, limit=1, window_seconds=60)
        assert first.allowed is True
        assert second.allowed is False
        assert await redis.ttl(f"rate-limit:{key}:{int(time.time()) // 60}") > 0
    finally:
        keys = await redis.keys(f"rate-limit:{key}:*")
        if keys:
            await redis.delete(*keys)
        await redis.aclose()
