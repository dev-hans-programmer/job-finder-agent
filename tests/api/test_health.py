from unittest.mock import AsyncMock, patch


def test_live_health(client) -> None:
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_request_id_is_preserved(client) -> None:
    response = client.get("/health/live", headers={"X-Request-ID": "test-request"})
    assert response.headers["X-Request-ID"] == "test-request"


def test_ready_health_success(client) -> None:
    with (
        patch("app.api.v1.health.check_postgres", new=AsyncMock(return_value=True)),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value=True)),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_health_dependency_failure(client) -> None:
    with (
        patch("app.api.v1.health.check_postgres", new=AsyncMock(return_value=False)),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value=True)),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert response.json()["error"]["details"] == {"postgres": False, "redis": True}
