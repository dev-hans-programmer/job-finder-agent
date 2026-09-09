"""Preference-related FastAPI dependencies."""

import uuid

from fastapi import Depends, Header, HTTPException

from app.domain.preferences.service import PreferenceService
from app.repositories.preferences import PreferenceRepository

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def user_id_from_header(x_user_id: str | None = Header(default=None)) -> uuid.UUID:
    if not x_user_id:
        return DEFAULT_USER_ID
    try:
        return uuid.UUID(x_user_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail="X-User-ID must be a UUID") from error


def get_repository() -> PreferenceRepository:
    return PreferenceRepository()


def get_service(repository: PreferenceRepository = Depends(get_repository)) -> PreferenceService:
    return PreferenceService(repository)
