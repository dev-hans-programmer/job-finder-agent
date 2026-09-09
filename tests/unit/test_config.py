import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_accept_valid_values() -> None:
    settings = Settings(database_url="postgresql+asyncpg://x", redis_url="redis://x")
    assert settings.app_env == "local"
    assert settings.default_timezone == "Asia/Kolkata"


def test_settings_require_database_url() -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            Settings(redis_url="redis://x")
