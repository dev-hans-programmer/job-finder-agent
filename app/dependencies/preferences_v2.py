from fastapi import Depends

from app.dependencies.preferences import get_repository
from app.domain.preferences.v2_service import V2PreferenceService


def get_v2_preference_service(repository=Depends(get_repository)) -> V2PreferenceService:
    return V2PreferenceService(repository)
