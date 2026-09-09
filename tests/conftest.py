import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client
