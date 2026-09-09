from app.errors import AppError, app_error_handler, error_payload


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
