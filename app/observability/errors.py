"""Backward-compatible exports for error handling moved to ``app.errors``."""

from app.errors.exceptions import AppError
from app.errors.handlers import (
    app_error_handler,
    http_exception_handler,
    register_exception_handlers,
    request_validation_error_handler,
    status_for_app_error,
    unexpected_error_handler,
    validation_error_payload,
)
from app.errors.responses import error_payload

__all__ = [
    "AppError",
    "app_error_handler",
    "error_payload",
    "http_exception_handler",
    "register_exception_handlers",
    "request_validation_error_handler",
    "status_for_app_error",
    "unexpected_error_handler",
    "validation_error_payload",
]
