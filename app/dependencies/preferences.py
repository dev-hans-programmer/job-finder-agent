"""Preference-related FastAPI dependencies."""

from fastapi import Depends

from app.domain.preferences.service import PreferenceService
from app.repositories.preferences import PreferenceRepository


def get_repository() -> PreferenceRepository:
    return PreferenceRepository()


def get_service(repository: PreferenceRepository = Depends(get_repository)) -> PreferenceService:
    return PreferenceService(repository)
