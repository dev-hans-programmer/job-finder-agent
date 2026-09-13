import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.responses import SuccessResponse, success_response
from app.auth.schemas import (
    EmailVerificationInput,
    LoginInput,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshInput,
    RegisterInput,
    RoleInput,
    SessionResponse,
    TokenResponse,
    UserResponse,
)
from app.auth.security import hash_refresh_token
from app.config import Settings, get_settings
from app.dependencies.auth import get_current_user, require_role
from app.dependencies.database import get_session
from app.domain.auth.service import AuthService
from app.repositories.auth import AuthRepository

router = APIRouter(prefix="/api/v1", tags=["auth"])


def get_auth_service(settings: Settings = Depends(get_settings)) -> AuthService:
    return AuthService(AuthRepository(), settings)


async def user_response(session, user, service: AuthService):
    return UserResponse(
        id=str(user.id),
        email=user.email or "",
        roles=await service.roles_for_user(session, user.id),
    )


@router.post(
    "/auth/register",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterInput,
    request: Request,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.register(session, data.email, data.password)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if getattr(service.settings, "auth_email_verification_enabled", False):
        await service.issue_code(session, data.email, "email_verification")
    return success_response(await user_response(session, user, service), request)


@router.post("/auth/login", response_model=SuccessResponse[TokenResponse])
async def login(
    data: LoginInput,
    request: Request,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    try:
        user = await service.authenticate(session, data.email, data.password)
        access, refresh = await service.issue_tokens(
            session,
            user,
            session_metadata={
                "device_name": request.headers.get("X-Device-Name"),
                "user_agent": request.headers.get("User-Agent"),
                "ip_address": request.client.host if request.client else None,
            },
        )
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return success_response(TokenResponse(access_token=access, refresh_token=refresh), request)


@router.post("/auth/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh(
    data: RefreshInput,
    request: Request,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    try:
        access, refresh_token = await service.refresh(session, data.refresh_token)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    return success_response(
        TokenResponse(access_token=access, refresh_token=refresh_token), request
    )


@router.post("/auth/password-reset/request", response_model=SuccessResponse[dict], status_code=202)
async def request_password_reset(
    data: PasswordResetRequest,
    request: Request,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    if getattr(service.settings, "auth_password_reset_enabled", False):
        await service.issue_code(session, data.email, "password_reset")
    return success_response(
        {"message": "If the account exists, a reset code has been sent"}, request
    )


@router.post("/auth/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    if not getattr(service.settings, "auth_password_reset_enabled", False):
        raise HTTPException(status_code=404, detail="password reset is disabled")
    try:
        await service.reset_password(session, data.email, data.code, data.password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/auth/email/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    data: EmailVerificationInput,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    if not getattr(service.settings, "auth_email_verification_enabled", False):
        raise HTTPException(status_code=404, detail="email verification is disabled")
    try:
        await service.verify_email(session, data.email, data.code)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/auth/email/resend", response_model=SuccessResponse[dict], status_code=202)
async def resend_email_verification(
    data: PasswordResetRequest,
    request: Request,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    if getattr(service.settings, "auth_email_verification_enabled", False):
        await service.issue_code(session, data.email, "email_verification")
    return success_response(
        {"message": "If the account exists, a verification code has been sent"}, request
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshInput,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    token = await service.repository.refresh_token(session, hash_refresh_token(data.refresh_token))
    if token is not None:
        await service.repository.revoke_tokens(session, token.family_id, datetime.now(timezone.utc))
        if getattr(service.settings, "auth_session_management_enabled", False) and token.session_id:
            await service.repository.revoke_auth_session(
                session, token.session_id, token.user_id, datetime.now(timezone.utc)
            )
        await session.commit()


@router.get("/auth/sessions", response_model=SuccessResponse[list[SessionResponse]])
async def sessions(
    request: Request,
    user=Depends(get_current_user),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    current_id = getattr(request.state, "session_id", None)
    values = [
        SessionResponse(
            id=str(value.id),
            device_name=value.device_name,
            user_agent=value.user_agent,
            ip_address=value.ip_address,
            created_at=value.created_at.isoformat(),
            last_used_at=value.last_used_at.isoformat(),
            current=value.id == current_id,
        )
        for value in await service.list_sessions(session, user.id)
    ]
    return success_response(values, request)


@router.delete("/auth/sessions/others", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_other_sessions(
    request: Request,
    user=Depends(get_current_user),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    current_id = getattr(request.state, "session_id", None)
    if current_id is None:
        raise HTTPException(status_code=409, detail="current session is unavailable")
    try:
        await service.revoke_other_sessions(session, user.id, current_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/auth/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session(
    session_id: uuid.UUID,
    user=Depends(get_current_user),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    try:
        await service.revoke_session(session, user.id, session_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/auth/me", response_model=SuccessResponse[UserResponse])
async def me(
    request: Request,
    user=Depends(get_current_user),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    return success_response(await user_response(session, user, service), request)


@router.post("/roles", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleInput,
    request: Request,
    user=Depends(require_role("admin")),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    role = await service.create_role(session, data.name, data.description)
    return success_response(
        {"id": str(role.id), "name": role.name, "description": role.description}, request
    )


@router.post("/users/{user_id}/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
async def assign_role(
    user_id: uuid.UUID,
    role_name: str,
    user=Depends(require_role("admin")),
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    try:
        await service.assign_role(session, user_id, role_name)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
