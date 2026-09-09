from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int = 400
    details: list[dict[str, Any]] | None = None


def error_payload(error: AppError, request_id: str) -> dict[str, Any]:
    return {
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details or [],
            "request_id": request_id,
        }
    }


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(status_code=error.status_code, content=error_payload(error, request_id))
