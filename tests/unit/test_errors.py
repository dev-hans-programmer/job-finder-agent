from fastapi.exceptions import RequestValidationError

from app.observability.errors import (
    AppError,
    app_error_handler,
    error_payload,
    request_validation_error_handler,
    unexpected_error_handler,
    validation_error_payload,
)


def test_error_payload_defaults_details() -> None:
    payload = error_payload(AppError("BAD", "bad"), "request-1")
    assert payload["error"]["details"] == []
    assert payload["error"]["request_id"] == "request-1"


async def test_app_error_handler_uses_request_id() -> None:
    class State:
        request_id = "request-2"

    class Request:
        state = State()

    response = await app_error_handler(Request(), AppError("BAD", "bad", 409, [{"x": 1}]))
    assert response.status_code == 409
    assert response.body


def test_validation_error_payload_is_client_friendly() -> None:
    error = RequestValidationError(
        [
            {
                "type": "string_too_short",
                "loc": ("body", "password"),
                "msg": "String should have at least 12 characters",
                "input": "secret",
                "ctx": {"min_length": 12},
            },
            {
                "type": "missing",
                "loc": ("query", "page"),
                "msg": "Field required",
                "input": None,
            },
        ]
    )
    payload = validation_error_payload(error, "request-3")
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["details"] == [
        {
            "field": "password",
            "location": "body",
            "code": "string_too_short",
            "message": "Password must be at least 12 characters",
        },
        {
            "field": "page",
            "location": "query",
            "code": "missing",
            "message": "Page is required",
        },
    ]


async def test_request_validation_error_handler_uses_request_id() -> None:
    class State:
        request_id = "request-4"

    class Request:
        state = State()

    error = RequestValidationError(
        [{"type": "value_error", "loc": ("path", "job_id"), "msg": "invalid", "input": "x"}]
    )
    response = await request_validation_error_handler(Request(), error)
    assert response.status_code == 422
    assert b"VALIDATION_ERROR" in response.body


async def test_unexpected_error_handler_hides_exception_and_logs_request_id(caplog) -> None:
    class State:
        request_id = "request-5"

    class Request:
        state = State()
        method = "GET"

    error = RuntimeError("database password=super-secret")
    with caplog.at_level("ERROR", logger="job-radar.errors"):
        response = await unexpected_error_handler(Request(), error)

    assert response.status_code == 500
    assert b"INTERNAL_SERVER_ERROR" in response.body
    assert b"super-secret" not in response.body
    assert "request-5" in caplog.text
