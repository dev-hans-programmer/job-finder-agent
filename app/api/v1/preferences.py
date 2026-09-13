import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import SuccessResponse, success_response
from app.dependencies.auth import user_id_from_current_user
from app.dependencies.database import get_session
from app.dependencies.preferences import get_service
from app.domain.preferences.schemas import PreferenceInput, PreferenceResponse
from app.domain.preferences.service import PreferenceService

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.get("", response_model=SuccessResponse[PreferenceResponse])
async def get_preferences(
    request: Request,
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
    service: PreferenceService = Depends(get_service),
) -> PreferenceResponse:
    response = await service.get_active(session, user_id)
    if response is None:
        raise HTTPException(status_code=404, detail="No active preference profile")
    return success_response(response, request)


@router.post("/validate", response_model=SuccessResponse[PreferenceInput])
async def validate_preferences(preferences: PreferenceInput, request: Request):
    return success_response(preferences, request)


@router.put(
    "", response_model=SuccessResponse[PreferenceResponse], status_code=status.HTTP_201_CREATED
)
async def update_preferences(
    preferences: PreferenceInput,
    request: Request,
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
    service: PreferenceService = Depends(get_service),
) -> PreferenceResponse:
    return success_response(await service.update(session, user_id, preferences), request)
