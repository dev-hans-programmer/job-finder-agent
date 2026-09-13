from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    app_name: str = "job-radar-agent"
    app_version: str = "0.1.0"
    git_sha: str = "unknown"
    build_timestamp: str = "unknown"
    log_level: str = "INFO"
    database_url: str = Field(..., min_length=1)
    redis_url: str = Field(..., min_length=1)
    default_timezone: str = "Asia/Kolkata"
    secret_key: SecretStr | None = None
    jwt_secret_key: str = "local-development-secret-change-me"
    jwt_issuer: str = "job-radar-agent"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    default_user_role: str = "user"
    initial_admin_email: str | None = None
    auth_require_token: bool = False
    scheduler_poll_seconds: int = 30
    backup_dir: str = "./backups"
    backup_retention_days: int = 7
    backup_interval_seconds: int = 86400
    otel_enabled: bool = False
    otel_service_name: str = "job-radar-agent"
    otel_exporter_otlp_endpoint: str | None = None
    otel_sample_rate: float = Field(1.0, ge=0.0, le=1.0)
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = Field(60, ge=1)
    rate_limit_general_requests: int = Field(100, ge=1)
    rate_limit_auth_requests: int = Field(10, ge=1)
    rate_limit_fail_open: bool = True
    trusted_proxy_ips: str = ""
    auth_session_management_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
