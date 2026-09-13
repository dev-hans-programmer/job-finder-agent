from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.deletion import get_deletion_service
from app.dependencies.preferences import user_id_from_header
from app.domain.preferences.deletion_service import DeletionService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user_id=Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: DeletionService = Depends(get_deletion_service),
) -> None:
    if not await service.delete_user(session, user_id):
        raise HTTPException(status_code=404, detail="user not found")
