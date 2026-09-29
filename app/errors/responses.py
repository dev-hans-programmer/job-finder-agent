"""The shared API error response contract."""

from typing import Any

from pydantic import BaseModel, Field

from app.errors.exceptions import AppError


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)
    request_id: str = "unknown"


class ErrorResponse(BaseModel):
    error: ErrorDetail


def build_error_payload(
    code: str,
    message: str,
    request_id: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    response = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or [],
            request_id=request_id,
        )
    )
    return response.model_dump(mode="json")


def error_payload(error: AppError, request_id: str) -> dict[str, Any]:
    return build_error_payload(error.code, error.message, request_id, error.details)
