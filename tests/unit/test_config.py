import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_accept_valid_values() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        app_env="local",
    )
    assert settings.app_env == "local"
    assert settings.default_timezone == "Asia/Kolkata"


def test_settings_require_database_url() -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            Settings(_env_file=None, redis_url="redis://x")


def test_security_settings_validate_production_values() -> None:
    valid = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        app_env="production",
        jwt_secret_key="x" * 32,
    )
    valid.validate_security()
    with pytest.raises(ValueError, match="at least 32"):
        Settings(
            database_url="postgresql+asyncpg://x",
            redis_url="redis://x",
            app_env="production",
            jwt_secret_key="short",
        ).validate_security()
    with pytest.raises(ValueError, match="development default"):
        Settings(
            database_url="postgresql+asyncpg://x",
            redis_url="redis://x",
            app_env="production",
            jwt_secret_key="local-development-secret-change-me",
        ).validate_security()
    with pytest.raises(ValueError, match="wildcard"):
        Settings(
            database_url="postgresql+asyncpg://x",
            redis_url="redis://x",
            cors_allowed_origins="*",
            cors_allow_credentials=True,
        ).validate_security()
