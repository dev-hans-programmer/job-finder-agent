import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.preferences import get_service, user_id_from_header
from app.domain.preferences.schemas import PreferenceInput, PreferenceResponse
from app.domain.preferences.service import PreferenceService

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.get("", response_model=PreferenceResponse)
async def get_preferences(
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: PreferenceService = Depends(get_service),
) -> PreferenceResponse:
    response = await service.get_active(session, user_id)
    if response is None:
        raise HTTPException(status_code=404, detail="No active preference profile")
    return response


@router.post("/validate", response_model=PreferenceInput)
async def validate_preferences(preferences: PreferenceInput) -> PreferenceInput:
    return preferences


@router.put("", response_model=PreferenceResponse, status_code=status.HTTP_201_CREATED)
async def update_preferences(
    preferences: PreferenceInput,
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: PreferenceService = Depends(get_service),
) -> PreferenceResponse:
    return await service.update(session, user_id, preferences)
