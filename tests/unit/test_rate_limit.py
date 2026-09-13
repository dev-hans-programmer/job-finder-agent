import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, Request, Response
from redis.exceptions import ConnectionError

from app.config import Settings
from app.observability.rate_limit import (
    RateLimiter,
    _client_ip,
    _identity_key,
    _is_auth_path,
    _is_exempt,
    rate_limit_middleware,
)


def request(path="/api/v1/jobs", headers=None, peer="10.0.0.2") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [
            (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
        ],
        "client": (peer, 1234),
        "app": FastAPI(),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_limiter_sets_expiry_on_first_request_and_rejects_after_limit(monkeypatch):
    redis = AsyncMock()
    redis.incr.side_effect = [1, 3]
    limiter = RateLimiter(redis)
    monkeypatch.setattr("app.observability.rate_limit.time.time", lambda: 100)

    first = await limiter.check("ip:test", 2, 60)
    rejected = await limiter.check("ip:test", 2, 60)

    assert first.allowed is True
    assert first.remaining == 1
    assert rejected.allowed is False
    assert rejected.remaining == 0
    redis.expire.assert_awaited_once()


def test_identity_uses_peer_unless_trusted_proxy():
    settings = Settings(
        database_url="postgresql+asyncpg://x", redis_url="redis://x", trusted_proxy_ips="10.0.0.2"
    )
    direct = request(headers={"X-Forwarded-For": "192.0.2.10"})
    trusted = request(headers={"X-Forwarded-For": "192.0.2.10, 10.0.0.3"})
    assert _client_ip(direct, settings) == "192.0.2.10"  # peer is trusted
    assert _identity_key(trusted, settings).startswith("ip:192.0.2.10")
    assert _client_ip(request(peer="10.0.0.2"), settings) == "10.0.0.2"
    assert _client_ip(request(peer="10.0.0.3"), settings) == "10.0.0.3"


def test_token_identity_is_hashed_and_paths_are_classified():
    settings = Settings(database_url="postgresql+asyncpg://x", redis_url="redis://x")
    value = _identity_key(request(headers={"Authorization": "Bearer secret"}), settings)
    assert value.startswith("token:")
    assert "secret" not in value
    assert _is_auth_path("/api/v1/auth/login")
    assert _is_auth_path("/api/v2/auth/refresh")
    assert not _is_auth_path("/api/v1/jobs")
    assert _is_exempt("/health/live")
    assert _is_exempt("/metrics")
    assert _is_exempt("/docs")
    assert not _is_exempt("/api/v1/jobs")


@pytest.mark.asyncio
async def test_middleware_skips_non_api_paths():
    redis = AsyncMock()
    settings = Settings(
        database_url="postgresql+asyncpg://x", redis_url="redis://x", rate_limit_enabled=True
    )
    req, _ = app_request("/", settings, redis)
    response = await rate_limit_middleware(req, AsyncMock(return_value=Response("ok")))
    assert response.status_code == 200
    redis.incr.assert_not_awaited()


def app_request(path="/api/v1/jobs", settings=None, redis=None, headers=None):
    app = FastAPI()
    app.state.settings = settings or Settings(
        database_url="postgresql+asyncpg://x", redis_url="redis://x", rate_limit_enabled=True
    )
    app.state.resources = SimpleNamespace(redis=redis or AsyncMock())
    value = request(path, headers=headers)
    value.scope["app"] = app
    return value, app


@pytest.mark.asyncio
async def test_middleware_exempts_disabled_and_adds_headers(monkeypatch):
    redis = AsyncMock()
    redis.incr.return_value = 1
    settings = Settings(
        database_url="postgresql+asyncpg://x", redis_url="redis://x", rate_limit_enabled=True
    )
    req, _ = app_request(redis=redis, settings=settings)
    response = await rate_limit_middleware(req, lambda _: AsyncMock(return_value=Response("ok"))())
    assert response.status_code == 200
    assert response.headers["X-RateLimit-Remaining"] == "99"

    settings.rate_limit_enabled = False
    req, _ = app_request(redis=redis, settings=settings, path="/api/v1/jobs")
    await rate_limit_middleware(req, lambda _: AsyncMock(return_value=Response("ok"))())
    redis.incr.assert_awaited_once()


@pytest.mark.asyncio
async def test_middleware_returns_429_for_exceeded_request():
    redis = AsyncMock()
    redis.incr.return_value = 11
    settings = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        rate_limit_enabled=True,
        rate_limit_auth_requests=10,
    )
    req, _ = app_request("/api/v1/auth/login", settings, redis)
    response = await rate_limit_middleware(req, AsyncMock())
    assert response.status_code == 429
    assert response.headers["Retry-After"]
    assert json.loads(response.body)["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_middleware_fail_open_for_general_and_fail_closed_for_auth():
    settings = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        rate_limit_enabled=True,
        rate_limit_fail_open=True,
    )
    redis = AsyncMock()
    redis.incr.side_effect = ConnectionError()
    next_call = AsyncMock(return_value=Response("ok"))
    req, _ = app_request("/api/v1/jobs", settings, redis)
    assert (await rate_limit_middleware(req, next_call)).status_code == 200
    req, _ = app_request("/api/v1/auth/login", settings, redis)
    assert (await rate_limit_middleware(req, next_call)).status_code == 503

    settings.rate_limit_fail_open = False
    req, _ = app_request("/api/v1/jobs", settings, redis)
    assert (await rate_limit_middleware(req, next_call)).status_code == 503
