"""Source adapter contracts and shared HTTP policy."""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class RateLimiter:
    def __init__(self, interval_seconds: float = 0.0):
        self.interval_seconds = interval_seconds

    async def wait(self) -> None:
        if self.interval_seconds > 0:
            await asyncio.sleep(self.interval_seconds)


@dataclass(frozen=True)
class RawJobRecord:
    external_id: str
    title: str
    description: str
    application_url: str
    location: str | None = None
    raw_payload: dict[str, Any] | None = None


class SourceAdapter(Protocol):
    async def fetch(self, config: dict[str, Any]) -> AsyncIterator[RawJobRecord]: ...


class AdapterError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


async def with_retries(operation: Callable[[], Awaitable[Any]], attempts: int = 3) -> Any:
    for attempt in range(attempts):
        try:
            return await operation()
        except AdapterError as error:
            if not error.retryable or attempt == attempts - 1:
                raise
            await asyncio.sleep(0)
    raise RuntimeError("retry operation exhausted")  # pragma: no cover


async def get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    rate_limiter: RateLimiter | None = None,
) -> Any:
    if rate_limiter is not None:
        await rate_limiter.wait()
    try:
        response = await client.get(url)
    except httpx.RequestError as error:
        raise AdapterError("source request failed", retryable=True) from error
    if response.status_code == 429 or response.status_code >= 500:
        retry_after = response.headers.get("Retry-After")
        suffix = f"; retry-after={retry_after}" if retry_after else ""
        raise AdapterError(f"source returned HTTP {response.status_code}{suffix}", retryable=True)
    if response.status_code >= 400:
        raise AdapterError(f"source returned HTTP {response.status_code}")
    return response.json()
