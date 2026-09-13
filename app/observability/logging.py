import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.observability.metrics import record_http_request


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(message)s")


def redact(value: str) -> str:
    return re.sub(
        r"(?i)(password|token|secret|api[_-]?key)(\s*[=:]\s*)[^\s,]+", r"\1\2[REDACTED]", value
    )


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        route = request.scope.get("route")
        record_http_request(request.method, getattr(route, "path", request.url.path), 500)
        raise
    route = request.scope.get("route")
    record_http_request(
        request.method, getattr(route, "path", request.url.path), response.status_code
    )
    response.headers["X-Request-ID"] = request_id
    logging.getLogger("job-radar.http").info(
        "http_request method=%s route=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        getattr(route, "path", request.url.path),
        response.status_code,
        (time.perf_counter() - started) * 1000,
        request_id,
    )
    return response
