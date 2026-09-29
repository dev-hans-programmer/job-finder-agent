import uuid

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token
from app.config import get_settings
from app.dependencies.database import get_session
from app.domain.preferences.models import User
from app.errors.database import commit_session
from app.errors.exceptions import (
    AuthenticationRequired,
    InvalidAccessToken,
    InvalidUserIdentifier,
    PermissionDenied,
    SessionRevoked,
)
from app.repositories.auth import AuthRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    session=Depends(get_session),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings=Depends(get_settings),
    request: Request = None,
):
    # Direct unit calls do not receive FastAPI dependency injection.
    if hasattr(settings, "dependency"):
        settings = get_settings()
    if isinstance(credentials, str):
        authorization = credentials
    else:
        authorization = (
            None if credentials is None else f"{credentials.scheme} {credentials.credentials}"
        )
    if authorization is None and not settings.auth_require_token:
        user = await session.get(User, uuid.UUID("00000000-0000-0000-0000-000000000001"))
        if user is None:
            user = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                email="local@example.com",
                status="active",
            )
            session.add(user)
            await commit_session(session)
        return user
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationRequired()
    try:
        claims = decode_access_token(
            authorization[7:], settings.jwt_secret_key, settings.jwt_issuer
        )
        user_id = uuid.UUID(claims["sub"])
        session_id = uuid.UUID(claims["sid"]) if claims.get("sid") else None
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise InvalidAccessToken() from error

    user = await session.get(User, user_id)
    if getattr(settings, "auth_session_management_enabled", False):
        auth_session = (
            await AuthRepository().auth_session(session, session_id, user_id)
            if session_id is not None
            else None
        )
        if auth_session is None or auth_session.revoked_at is not None:
            raise SessionRevoked()
        if request is not None:
            request.state.session_id = auth_session.id
    if user is None or user.status != "active":
        raise InvalidAccessToken()
    return user


async def user_id_from_current_user(
    request: Request,
    user=Depends(get_current_user),
    settings=Depends(get_settings),
) -> uuid.UUID:
    """Return JWT identity; accept X-User-ID only as a local migration aid."""
    legacy_id = request.headers.get("x-user-id")
    if legacy_id and not settings.auth_require_token:
        try:
            return uuid.UUID(legacy_id)
        except ValueError as error:
            raise InvalidUserIdentifier() from error
    return user.id


def require_role(role: str):
    async def dependency(user=Depends(get_current_user), session=Depends(get_session)):
        if role not in await AuthRepository().roles(session, user.id):
            raise PermissionDenied()
        return user

    return dependency
