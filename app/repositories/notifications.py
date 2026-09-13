import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.notifications.models import NotificationDelivery


class NotificationRepository:
    async def get_or_create(self, session: AsyncSession, **values):
        query = select(NotificationDelivery).where(
            *[getattr(NotificationDelivery, k) == v for k, v in values.items()]
        )
        row = await session.scalar(query)
        if row:
            return row, False
        row = NotificationDelivery(**values)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row, True

    async def get(self, session: AsyncSession, delivery_id: uuid.UUID):
        return await session.get(NotificationDelivery, delivery_id)
