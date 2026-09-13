import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.domain.preferences.models import (
    AuthSession,
    RefreshToken,
    Role,
    User,
    UserRole,
    VerificationCode,
)


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

    async def save_auth_session(self, session, auth_session: AuthSession):
        session.add(auth_session)
        await session.flush()

    async def auth_session(self, session, session_id: uuid.UUID, user_id: uuid.UUID):
        return await session.scalar(
            select(AuthSession).where(AuthSession.id == session_id, AuthSession.user_id == user_id)
        )

    async def auth_sessions(self, session, user_id: uuid.UUID):
        result = await session.execute(
            select(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .order_by(AuthSession.last_used_at.desc())
        )
        return list(result.scalars().all())

    async def revoke_auth_session(self, session, session_id: uuid.UUID, user_id: uuid.UUID, now):
        auth_session = await self.auth_session(session, session_id, user_id)
        if auth_session is None or auth_session.revoked_at is not None:
            return False
        auth_session.revoked_at = now
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.session_id == session_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
        return True

    async def revoke_other_auth_sessions(
        self, session, user_id: uuid.UUID, current_session_id: uuid.UUID, now
    ):
        sessions = await self.auth_sessions(session, user_id)
        count = 0
        for auth_session in sessions:
            if auth_session.id != current_session_id:
                auth_session.revoked_at = now
                count += 1
        if count:
            await session.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.session_id != current_session_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await session.commit()
        return count

    async def verification_code(self, session, user_id, purpose: str, code_hash: str):
        return await session.scalar(
            select(VerificationCode).where(
                VerificationCode.user_id == user_id,
                VerificationCode.purpose == purpose,
                VerificationCode.code_hash == code_hash,
                VerificationCode.consumed_at.is_(None),
            )
        )

    async def save_verification_code(self, session, code: VerificationCode):
        session.add(code)
        await session.commit()

    async def revoke_user_tokens(self, session, user_id: uuid.UUID, now):
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.commit()
