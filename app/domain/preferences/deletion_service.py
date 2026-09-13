import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.preferences.models import User


class DeletionService:
    async def delete_user(self, session: AsyncSession, user_id: uuid.UUID) -> bool:
        user = await session.get(User, user_id)
        if user is None:
            return False
        await session.delete(user)
        await session.commit()
        return True
