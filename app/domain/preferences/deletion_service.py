import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.preferences.models import User
from app.errors.database import commit_session
from app.errors.exceptions import UserNotFound


class DeletionService:
    async def delete_user(self, session: AsyncSession, user_id: uuid.UUID) -> bool:
        user = await session.get(User, user_id)
        if user is None:
            raise UserNotFound()
        await session.delete(user)
        await commit_session(session)
        return True
