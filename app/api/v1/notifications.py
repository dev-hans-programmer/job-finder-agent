import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import user_id_from_current_user
from app.dependencies.database import get_session
from app.dependencies.notifications import get_notification_service
from app.domain.notifications.service import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("/{delivery_id}")
async def get_delivery(
    delivery_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    service: NotificationService = Depends(get_notification_service),
    user_id: uuid.UUID = Depends(user_id_from_current_user),
):
    delivery = await service.get_for_user(session, delivery_id, user_id)
    if delivery is None:
        raise HTTPException(status_code=404, detail="notification delivery not found")
    return {
        "id": str(delivery.id),
        "channel": delivery.channel,
        "status": delivery.status,
        "attempt_count": delivery.attempt_count,
        "provider_message_id": delivery.provider_message_id,
        "error": delivery.error,
    }
