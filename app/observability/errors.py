import logging
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("job-radar.errors")


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


def _validation_message(error: dict[str, Any], field: str) -> str:
    code = error.get("type", "")
    context = error.get("ctx") or {}
    label = field.replace("_", " ").capitalize()
    messages = {
        "missing": f"{label} is required",
        "string_too_short": f"{label} must be at least {context.get('min_length')} characters",
        "string_too_long": f"{label} must be at most {context.get('max_length')} characters",
        "value_error": f"{label} is invalid",
        "value_error.email": f"{label} must be a valid email address",
    }
    return messages.get(code, f"{label} is invalid")


def validation_error_payload(error: RequestValidationError, request_id: str) -> dict[str, Any]:
    details = []
    for item in error.errors():
        location = item.get("loc", ())
        field = ".".join(str(part) for part in location[1:]) or "request"
        details.append(
            {
                "field": field,
                "location": str(location[0]) if location else "request",
                "code": item.get("type", "validation_error"),
                "message": _validation_message(item, field),
            }
        )
    return {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "The request contains invalid data",
            "details": details,
            "request_id": request_id,
        }
    }


async def request_validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content=validation_error_payload(error, request_id),
    )


async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled_exception method=%s path=%s request_id=%s",
        request.method,
        getattr(getattr(request, "url", None), "path", "unknown"),
        request_id,
        exc_info=(type(error), error, error.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": [],
                "request_id": request_id,
            }
        },
    )
