from pydantic import BaseModel

from app.config import Settings


class RuntimeMetadata(BaseModel):
    application: str
    version: str
    commit_sha: str
    build_timestamp: str
    environment: str


def runtime_metadata(settings: Settings) -> RuntimeMetadata:
    return RuntimeMetadata(
        application=settings.app_name,
        version=settings.app_version,
        commit_sha=settings.git_sha,
        build_timestamp=settings.build_timestamp,
        environment=settings.app_env,
    )
