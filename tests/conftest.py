import os

os.environ["APP_ENV"] = "testing"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://jobradar_test:test_password@localhost:5433/jobradar_test",
)
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/1")
# Tests must not inherit a developer's real exporter configuration. Individual
# telemetry tests enable instrumentation explicitly with isolated settings.
os.environ["OTEL_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    # API tests are intentionally local-mode; strict-auth behavior is covered
    # explicitly in the authentication tests and manual QA flow.
    return Settings(auth_require_token=False, otel_enabled=False, rate_limit_enabled=False)


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
