import logging
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
from app.domain.preferences.models import AuthSession, RefreshToken, User, VerificationCode
from app.repositories.auth import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository, settings):
        self.repository, self.settings = repository, settings

    @property
    def lockout_enabled(self):
        return getattr(self.settings, "auth_account_lockout_enabled", False)

    async def register(self, session, email: str, password: str):
        email = email.lower()
        if await self.repository.user_by_email(session, email):
            raise ValueError("email is already registered")
        verification_enabled = getattr(self.settings, "auth_email_verification_enabled", False)
        user = User(
            email=email,
            password_hash=hash_password(password),
            status="pending_verification" if verification_enabled else "active",
        )
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
        now = datetime.now(timezone.utc)
        if (
            user is not None
            and self.lockout_enabled
            and user.locked_until
            and user.locked_until > now
        ):
            raise ValueError("account is temporarily locked")
        verification_enabled = getattr(self.settings, "auth_email_verification_enabled", False)
        if (
            user is None
            or user.password_hash is None
            or not verify_password(password, user.password_hash)
            or (
                user.status != "active"
                and not (verification_enabled and user.status == "pending_verification")
            )
        ):
            if user is not None and self.lockout_enabled:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= self.settings.auth_max_login_attempts:
                    user.locked_until = now + timedelta(minutes=self.settings.auth_lockout_minutes)
                await session.commit()
            raise ValueError("invalid credentials")
        if verification_enabled and not user.email_verified_at:
            raise ValueError("email verification required")
        if self.lockout_enabled:
            user.failed_login_attempts = 0
            user.locked_until = None
            await session.commit()
        return user

    async def issue_tokens(self, session, user, session_id=None, session_metadata=None):
        roles = await self.repository.roles(session, user.id)
        if getattr(self.settings, "auth_session_management_enabled", False) and session_id is None:
            metadata = session_metadata or {}
            auth_session = AuthSession(
                user_id=user.id,
                device_name=metadata.get("device_name"),
                user_agent=metadata.get("user_agent"),
                ip_address=metadata.get("ip_address"),
            )
            await self.repository.save_auth_session(session, auth_session)
            session_id = auth_session.id
        refresh = secrets.token_urlsafe(48)
        token = RefreshToken(
            user_id=user.id,
            session_id=session_id,
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
            session_id=session_id,
        )
        return access, refresh

    async def refresh(self, session, raw_token: str):
        token = await self.repository.refresh_token(session, hash_refresh_token(raw_token))
        now = datetime.now(timezone.utc)
        if token is None or token.revoked_at is not None or token.expires_at <= now:
            if token is not None:
                await self.repository.revoke_tokens(session, token.family_id, now)
                await session.commit()
            if token is not None and token.revoked_at is not None:
                raise ValueError("refresh token replay detected")
            raise ValueError("invalid refresh token")
        await self.repository.revoke_tokens(session, token.family_id, now)
        await session.commit()
        user = await self.repository.user(session, token.user_id)
        if user is None or user.status != "active":
            raise ValueError("invalid refresh token")
        return await self.issue_tokens(session, user, session_id=getattr(token, "session_id", None))

    async def list_sessions(self, session, user_id):
        if not getattr(self.settings, "auth_session_management_enabled", False):
            return []
        return await self.repository.auth_sessions(session, user_id)

    async def revoke_session(self, session, user_id, session_id):
        if not getattr(self.settings, "auth_session_management_enabled", False):
            raise ValueError("session management is disabled")
        if not await self.repository.revoke_auth_session(
            session, session_id, user_id, datetime.now(timezone.utc)
        ):
            raise ValueError("session not found")

    async def revoke_other_sessions(self, session, user_id, current_session_id):
        if not getattr(self.settings, "auth_session_management_enabled", False):
            raise ValueError("session management is disabled")
        return await self.repository.revoke_other_auth_sessions(
            session, user_id, current_session_id, datetime.now(timezone.utc)
        )

    async def issue_code(self, session, email: str, purpose: str):
        user = await self.repository.user_by_email(session, email.lower())
        if user is None:
            return None
        code = f"{secrets.randbelow(1_000_000):06d}"
        record = VerificationCode(
            user_id=user.id,
            purpose=purpose,
            code_hash=hash_refresh_token(code),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=self.settings.auth_otp_expire_minutes),
        )
        await self.repository.save_verification_code(session, record)
        logging.getLogger("job-radar.auth").info(
            "auth_code_issued purpose=%s email=%s code=%s", purpose, email.lower(), code
        )
        return code

    async def verify_email(self, session, email: str, code: str):
        user = await self.repository.user_by_email(session, email.lower())
        record = (
            None
            if user is None
            else await self.repository.verification_code(
                session, user.id, "email_verification", hash_refresh_token(code)
            )
        )
        if user is None or record is None or record.expires_at <= datetime.now(timezone.utc):
            raise ValueError("invalid or expired verification code")
        record.consumed_at = datetime.now(timezone.utc)
        user.email_verified_at = datetime.now(timezone.utc)
        user.status = "active"
        await session.commit()

    async def reset_password(self, session, email: str, code: str, password: str):
        user = await self.repository.user_by_email(session, email.lower())
        record = (
            None
            if user is None
            else await self.repository.verification_code(
                session, user.id, "password_reset", hash_refresh_token(code)
            )
        )
        if user is None or record is None or record.expires_at <= datetime.now(timezone.utc):
            raise ValueError("invalid or expired reset code")
        record.consumed_at = datetime.now(timezone.utc)
        user.password_hash = hash_password(password)
        await self.repository.revoke_user_tokens(session, user.id, datetime.now(timezone.utc))

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
