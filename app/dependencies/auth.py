import uuid

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token
from app.config import get_settings
from app.dependencies.database import get_session
from app.domain.preferences.models import User
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
            await session.commit()
        return user
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        claims = decode_access_token(
            authorization[7:], settings.jwt_secret_key, settings.jwt_issuer
        )
        user = await session.get(User, uuid.UUID(claims["sub"]))
        if getattr(settings, "auth_session_management_enabled", False):
            session_id = claims.get("sid")
            auth_session = (
                await AuthRepository().auth_session(
                    session, uuid.UUID(session_id), uuid.UUID(claims["sub"])
                )
                if session_id
                else None
            )
            if auth_session is None or auth_session.revoked_at is not None:
                raise HTTPException(status_code=401, detail="session is revoked")
            if request is not None:
                request.state.session_id = auth_session.id
    except Exception as error:
        raise HTTPException(status_code=401, detail="invalid authentication token") from error
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="invalid authentication token")
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
            raise HTTPException(status_code=400, detail="X-User-ID must be a UUID") from error
    return user.id


def require_role(role: str):
    async def dependency(user=Depends(get_current_user), session=Depends(get_session)):
        if role not in await AuthRepository().roles(session, user.id):
            raise HTTPException(status_code=403, detail="insufficient role")
        return user

    return dependency
