import hashlib
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

from app.config import Settings


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    reset_at: int


class RateLimiter:
    """A Redis-backed fixed-window limiter.

    INCR and EXPIRE are intentionally kept together in one small component so
    the policy can be unit-tested without coupling routes to Redis details.
    """

    def __init__(self, redis) -> None:
        self.redis = redis

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = int(time.time())
        bucket = now // window_seconds
        redis_key = f"rate-limit:{key}:{bucket}"
        count = await self.redis.incr(redis_key)
        if count == 1:
            await self.redis.expire(redis_key, window_seconds)
        reset_at = (bucket + 1) * window_seconds
        retry_after = max(1, reset_at - now)
        return RateLimitResult(
            allowed=count <= limit,
            limit=limit,
            remaining=max(0, limit - count),
            retry_after=retry_after,
            reset_at=reset_at,
        )


def _client_ip(request: Request, settings: Settings) -> str:
    peer = request.client.host if request.client else "unknown"
    trusted = {item.strip() for item in settings.trusted_proxy_ips.split(",") if item.strip()}
    if peer in trusted:
        forwarded = request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        if forwarded:
            return forwarded
    return peer


def _identity_key(request: Request, settings: Settings) -> str:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer ") and authorization[7:]:
        digest = hashlib.sha256(authorization[7:].encode()).hexdigest()[:24]
        return f"token:{digest}"
    return f"ip:{_client_ip(request, settings)}"


def _is_auth_path(path: str) -> bool:
    return path.startswith("/api/v1/auth/") or path.startswith("/api/v2/auth/")


def _is_exempt(path: str) -> bool:
    return path.startswith("/health") or path in {
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    }


def _error_content(request: Request, code: str, message: str) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": [],
            "request_id": getattr(request.state, "request_id", "unknown"),
        }
    }


def _headers(result: RateLimitResult) -> dict[str, str]:
    return {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_at),
        "Retry-After": str(result.retry_after),
    }


async def rate_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    settings: Settings = request.app.state.settings
    if (
        not settings.rate_limit_enabled
        or not request.url.path.startswith("/api/")
        or _is_exempt(request.url.path)
    ):
        return await call_next(request)

    is_auth = _is_auth_path(request.url.path)
    limit = settings.rate_limit_auth_requests if is_auth else settings.rate_limit_general_requests
    limiter = RateLimiter(request.app.state.resources.redis)
    try:
        result = await limiter.check(
            _identity_key(request, settings), limit, settings.rate_limit_window_seconds
        )
    except RedisError:
        if settings.rate_limit_fail_open and not is_auth:
            return await call_next(request)
        return JSONResponse(
            status_code=503,
            content=_error_content(request, "RATE_LIMIT_UNAVAILABLE", "rate limiting unavailable"),
        )

    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content=_error_content(request, "RATE_LIMIT_EXCEEDED", "too many requests"),
            headers=_headers(result),
        )
    response = await call_next(request)
    for name, value in _headers(result).items():
        response.headers[name] = value
    return response
