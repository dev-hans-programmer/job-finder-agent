"""Central translation from application/framework errors to HTTP responses."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors.exceptions import (
    AppError,
    AuthenticationError,
    AuthenticationRequired,
    BadRequestError,
    ConflictError,
    DatabaseUnavailable,
    InvalidAccessToken,
    InvalidInputError,
    NotFoundError,
    PermissionDenied,
    PersistenceFailure,
    SessionRevoked,
)
from app.errors.responses import build_error_payload, error_payload

logger = logging.getLogger("job-radar.errors")

ERROR_STATUS_CODES: tuple[tuple[type[AppError], int], ...] = (
    (DatabaseUnavailable, 503),
    (InvalidInputError, 422),
    (BadRequestError, 400),
    (NotFoundError, 404),
    (ConflictError, 409),
    (AuthenticationError, 401),
    (PermissionDenied, 403),
    (PersistenceFailure, 500),
)

HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
}


def status_for_app_error(error: AppError) -> int:
    for error_type, status_code in ERROR_STATUS_CODES:
        if isinstance(error, error_type):
            return status_code
    return 500


def _is_mapped_app_error(error: AppError) -> bool:
    return any(isinstance(error, error_type) for error_type, _ in ERROR_STATUS_CODES)


def _request_id(request: Request) -> str:
    return getattr(getattr(request, "state", None), "request_id", "unknown")


def _log_persistence_failure(request: Request, error: AppError) -> None:
    cause = error.__cause__
    if cause is None:
        return
    logger.error(
        "persistence_failure method=%s path=%s request_id=%s",
        request.method,
        getattr(getattr(request, "url", None), "path", "unknown"),
        _request_id(request),
        exc_info=(type(cause), cause, cause.__traceback__),
    )


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    if not _is_mapped_app_error(error):
        return await unexpected_error_handler(request, error)
    status_code = status_for_app_error(error)
    if isinstance(error, PersistenceFailure):
        _log_persistence_failure(request, error)
    bearer_challenge_errors = (AuthenticationRequired, InvalidAccessToken, SessionRevoked)
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(error, bearer_challenge_errors) else None
    return JSONResponse(
        status_code=status_code,
        content=error_payload(error, _request_id(request)),
        headers=headers,
    )


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
    return build_error_payload(
        "VALIDATION_ERROR", "The request contains invalid data", request_id, details
    )


async def request_validation_error_handler(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=validation_error_payload(error, _request_id(request)),
    )


async def http_exception_handler(request: Request, error: StarletteHTTPException) -> JSONResponse:
    status_code = error.status_code
    code = HTTP_ERROR_CODES.get(status_code, "HTTP_ERROR")
    message = (
        error.detail if isinstance(error.detail, str) else "The request could not be processed"
    )
    if status_code >= 500:
        code, message = "INTERNAL_SERVER_ERROR", "An unexpected error occurred"
    return JSONResponse(
        status_code=status_code,
        content=build_error_payload(code, message, _request_id(request)),
        headers=error.headers,
    )


async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    request_id = _request_id(request)
    logger.error(
        "unhandled_exception method=%s path=%s request_id=%s",
        request.method,
        getattr(getattr(request, "url", None), "path", "unknown"),
        request_id,
        exc_info=(type(error), error, error.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content=build_error_payload(
            "INTERNAL_SERVER_ERROR", "An unexpected error occurred", request_id
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
