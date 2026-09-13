import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.preferences import user_id_from_header
from app.dependencies.preferences_v2 import get_v2_preference_service
from app.domain.preferences.v2_schemas import V2PreferenceResponse, V2PreferenceUpdate
from app.domain.preferences.v2_service import V2PreferenceService

router = APIRouter(prefix="/api/v2/preferences", tags=["preferences-v2"])


@router.get("", response_model=V2PreferenceResponse)
async def get_preferences_v2(
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: V2PreferenceService = Depends(get_v2_preference_service),
):
    response = await service.get_active(session, user_id)
    if response is None:
        raise HTTPException(status_code=404, detail="No active preference profile")
    return response


@router.put("", response_model=V2PreferenceResponse, status_code=status.HTTP_201_CREATED)
async def update_preferences_v2(
    data: V2PreferenceUpdate,
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: V2PreferenceService = Depends(get_v2_preference_service),
):
    return await service.update(session, user_id, data)
