from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.observability.rate_limit import rate_limit_middleware


class MemoryRedis:
    def __init__(self):
        self.counts = {}

    async def incr(self, key):
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key, seconds):
        return True


def test_api_returns_quota_headers_and_structured_429():
    app = FastAPI()
    app.state.settings = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        rate_limit_enabled=True,
        rate_limit_general_requests=1,
    )
    app.state.resources = SimpleNamespace(redis=MemoryRedis())
    app.middleware("http")(rate_limit_middleware)

    @app.get("/api/v1/probe")
    async def probe():
        return {"ok": True}

    with TestClient(app) as client:
        allowed = client.get("/api/v1/probe")
        rejected = client.get("/api/v1/probe")

    assert allowed.status_code == 200
    assert allowed.headers["X-RateLimit-Limit"] == "1"
    assert allowed.headers["X-RateLimit-Remaining"] == "0"
    assert rejected.status_code == 429
    assert rejected.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
    assert rejected.headers["Retry-After"]
