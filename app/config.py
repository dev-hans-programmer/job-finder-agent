from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "job-radar-agent"
    log_level: str = "INFO"
    database_url: str = Field(..., min_length=1)
    redis_url: str = Field(..., min_length=1)
    default_timezone: str = "Asia/Kolkata"
    secret_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
