from app.config import Settings
from app.version import runtime_metadata


def test_runtime_metadata_contains_deployment_identity():
    settings = Settings(
        database_url="postgresql+asyncpg://x",
        redis_url="redis://x",
        app_name="test-app",
        app_version="2026.09.13",
        git_sha="abc123",
        build_timestamp="2026-09-13T10:00:00Z",
        app_env="staging",
    )
    metadata = runtime_metadata(settings)
    assert metadata.model_dump() == {
        "application": "test-app",
        "version": "2026.09.13",
        "commit_sha": "abc123",
        "build_timestamp": "2026-09-13T10:00:00Z",
        "environment": "staging",
    }
