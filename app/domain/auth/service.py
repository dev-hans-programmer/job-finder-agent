import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.domain.preferences.models import RefreshToken, User
from app.repositories.auth import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository, settings):
        self.repository, self.settings = repository, settings

    async def register(self, session, email: str, password: str):
        email = email.lower()
        if await self.repository.user_by_email(session, email):
            raise ValueError("email is already registered")
        user = User(email=email, password_hash=hash_password(password))
        session.add(user)
        await session.flush()
        role = await self.repository.role(session, self.settings.default_user_role)
        if role is None:
            role = await self.repository.create_role(
                session, self.settings.default_user_role, "Default user role"
            )
        await self.repository.assign_role(session, user.id, role.id)
        initial_admin_email = getattr(self.settings, "initial_admin_email", None)
        if initial_admin_email and email == initial_admin_email.lower():
            admin_role = await self.repository.role(session, "admin")
            if admin_role is None:
                admin_role = await self.repository.create_role(
                    session, "admin", "Administrator role"
                )
            await self.repository.assign_role(session, user.id, admin_role.id)
        return user

    async def authenticate(self, session, email: str, password: str):
        user = await self.repository.user_by_email(session, email.lower())
        if (
            user is None
            or user.password_hash is None
            or not verify_password(password, user.password_hash)
            or user.status != "active"
        ):
            raise ValueError("invalid credentials")
        return user

    async def issue_tokens(self, session, user):
        roles = await self.repository.roles(session, user.id)
        refresh = secrets.token_urlsafe(48)
        token = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh),
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.repository.save_refresh_token(session, token)
        access = create_access_token(
            user.id,
            user.email,
            roles,
            self.settings.jwt_secret_key,
            self.settings.access_token_expire_minutes,
            self.settings.jwt_issuer,
        )
        return access, refresh

    async def refresh(self, session, raw_token: str):
        token = await self.repository.refresh_token(session, hash_refresh_token(raw_token))
        now = datetime.now(timezone.utc)
        if token is None or token.revoked_at is not None or token.expires_at <= now:
            if token is not None:
                await self.repository.revoke_tokens(session, token.family_id, now)
                await session.commit()
            raise ValueError("invalid refresh token")
        await self.repository.revoke_tokens(session, token.family_id, now)
        await session.commit()
        user = await self.repository.user(session, token.user_id)
        if user is None or user.status != "active":
            raise ValueError("invalid refresh token")
        return await self.issue_tokens(session, user)

    async def claims(self, token: str):
        try:
            return decode_access_token(
                token, self.settings.jwt_secret_key, self.settings.jwt_issuer
            )
        except (jwt.InvalidTokenError, ValueError) as error:
            raise ValueError("invalid access token") from error

    async def roles_for_user(self, session, user_id):
        return await self.repository.roles(session, user_id)

    async def create_role(self, session, name: str, description: str | None):
        return await self.repository.create_role(session, name, description)

    async def assign_role(self, session, user_id, role_name: str):
        target = await self.repository.user(session, user_id)
        role = await self.repository.role(session, role_name)
        if target is None or role is None:
            raise ValueError("user or role not found")
        await self.repository.assign_role(session, user_id, role.id)
