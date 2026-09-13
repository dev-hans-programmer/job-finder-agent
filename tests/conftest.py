import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
# Tests must not inherit a developer's real exporter configuration. Individual
# telemetry tests enable instrumentation explicitly with isolated settings.
os.environ["OTEL_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    # API tests are intentionally local-mode; strict-auth behavior is covered
    # explicitly in the authentication tests and manual QA flow.
    return Settings(auth_require_token=False, otel_enabled=False)


@pytest.fixture
def client(settings: Settings):
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client
