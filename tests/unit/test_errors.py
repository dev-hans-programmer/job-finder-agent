from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors.database import (
    commit_session,
    flush_session,
    raise_database_error,
    refresh_session,
    translate_database_error,
)
from app.errors.exceptions import (
    AuthenticationRequired,
    ConflictError,
    DatabaseUnavailable,
    DataConflict,
    PersistenceFailure,
    UserAlreadyExists,
)
from app.errors.handlers import http_exception_handler, status_for_app_error
from app.observability.errors import (
    AppError,
    app_error_handler,
    error_payload,
    request_validation_error_handler,
    unexpected_error_handler,
    validation_error_payload,
)


def make_request(request_id="unknown"):
    return SimpleNamespace(
        state=SimpleNamespace(request_id=request_id),
        method="GET",
        url=SimpleNamespace(path="/jobs"),
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

    response = await app_error_handler(Request(), ConflictError("BAD", "bad", details=[{"x": 1}]))
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


def test_unknown_application_error_uses_generic_status() -> None:
    assert status_for_app_error(AppError()) == 500


@pytest.mark.asyncio
async def test_unmapped_app_error_uses_generic_handler() -> None:
    response = await app_error_handler(make_request("request-6"), AppError())
    assert response.status_code == 500
    assert b"INTERNAL_SERVER_ERROR" in response.body
    assert b"request-6" in response.body


@pytest.mark.asyncio
async def test_persistence_error_logs_cause_only_when_present(caplog) -> None:
    request = make_request("request-7")
    without_cause = await app_error_handler(request, PersistenceFailure())
    assert without_cause.status_code == 500

    error = PersistenceFailure()
    error.__cause__ = RuntimeError("driver failed")
    with caplog.at_level("ERROR", logger="job-radar.errors"):
        with_cause = await app_error_handler(request, error)
    assert with_cause.status_code == 500
    assert "persistence_failure" in caplog.text
    assert "request-7" in caplog.text


@pytest.mark.asyncio
async def test_authentication_error_includes_bearer_challenge() -> None:
    response = await app_error_handler(make_request(), AuthenticationRequired())
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_http_exception_handler_maps_client_and_server_errors() -> None:
    request = make_request("request-8")
    client_error = await http_exception_handler(
        request, StarletteHTTPException(404, detail="Missing", headers={"X-Error": "yes"})
    )
    assert client_error.status_code == 404
    assert client_error.headers["X-Error"] == "yes"
    assert b"Missing" in client_error.body

    server_error = await http_exception_handler(
        request, StarletteHTTPException(503, detail={"internal": "secret"})
    )
    assert server_error.status_code == 503
    assert b"INTERNAL_SERVER_ERROR" in server_error.body
    assert b"secret" not in server_error.body


def test_database_error_translation_covers_integrity_and_connectivity() -> None:
    user_constraint = RuntimeError("duplicate user")
    user_constraint.diag = SimpleNamespace(constraint_name="uq_users_email")
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, user_constraint)), UserAlreadyExists
    )

    user_message = RuntimeError("duplicate key on users.email")
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, user_message)), UserAlreadyExists
    )

    constraint_fallback = RuntimeError("other duplicate")
    constraint_fallback.constraint_name = "uq_jobs_external_id"
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, constraint_fallback)),
        PersistenceFailure,
    )

    unique_state = RuntimeError("duplicate")
    unique_state.sqlstate = "23505"
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, unique_state)), DataConflict
    )

    unique_pgcode = RuntimeError("duplicate")
    unique_pgcode.pgcode = "23505"
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, unique_pgcode)), DataConflict
    )

    unique_message = RuntimeError("unique constraint failed")
    assert isinstance(
        translate_database_error(IntegrityError("insert", {}, unique_message)), DataConflict
    )

    disconnected = DBAPIError("select", {}, RuntimeError("offline"), connection_invalidated=True)
    assert isinstance(translate_database_error(disconnected), DatabaseUnavailable)

    sqlstate_connection = RuntimeError("offline")
    sqlstate_connection.sqlstate = "08006"
    connection_error = DBAPIError("select", {}, sqlstate_connection)
    assert isinstance(translate_database_error(connection_error), DatabaseUnavailable)

    generic_driver_error = DBAPIError("select", {}, RuntimeError("query failed"))
    assert isinstance(translate_database_error(generic_driver_error), PersistenceFailure)
    assert isinstance(translate_database_error(SQLAlchemyError("query failed")), PersistenceFailure)


@pytest.mark.asyncio
async def test_database_error_helpers_rollback_and_translate() -> None:
    for helper, method, args in (
        (commit_session, "commit", ()),
        (flush_session, "flush", ()),
        (refresh_session, "refresh", (object(),)),
    ):
        session = SimpleNamespace(
            commit=AsyncMock(side_effect=SQLAlchemyError("commit failed")),
            flush=AsyncMock(side_effect=SQLAlchemyError("flush failed")),
            refresh=AsyncMock(side_effect=SQLAlchemyError("refresh failed")),
            rollback=AsyncMock(),
        )
        with pytest.raises(PersistenceFailure):
            await helper(session, *args)
        getattr(session, method).assert_awaited_once()
        session.rollback.assert_awaited_once()

    original = SQLAlchemyError("query failed")
    failed_rollback = SimpleNamespace(rollback=AsyncMock(side_effect=SQLAlchemyError("rollback")))
    with pytest.raises(PersistenceFailure) as raised:
        await raise_database_error(failed_rollback, original)
    assert raised.value.__cause__ is original
