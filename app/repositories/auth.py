import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.domain.preferences.models import RefreshToken, Role, User, UserRole


class AuthRepository:
    async def user_by_email(self, session, email: str):
        return await session.scalar(select(User).where(User.email == email.lower()))

    async def user(self, session, user_id: uuid.UUID):
        return await session.get(User, user_id)

    async def roles(self, session, user_id: uuid.UUID) -> list[str]:
        result = await session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id, Role.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def role(self, session, name: str):
        return await session.scalar(select(Role).where(Role.name == name))

    async def create_role(self, session, name: str, description: str | None):
        role = Role(name=name, description=description)
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role

    async def assign_role(self, session, user_id: uuid.UUID, role_id: uuid.UUID):
        existing = await session.scalar(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        if existing is None:
            session.add(UserRole(user_id=user_id, role_id=role_id))
            await session.commit()

    async def revoke_tokens(self, session, family_id: uuid.UUID, now: datetime):
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )

    async def refresh_token(self, session, token_hash: str):
        return await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

    async def save_refresh_token(self, session, token: RefreshToken):
        session.add(token)
        await session.commit()
