import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.responses import SuccessResponse, success_response
from app.auth.schemas import (
    LoginInput,
    RefreshInput,
    RegisterInput,
    RoleInput,
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
        access, refresh = await service.issue_tokens(session, user)
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


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshInput,
    session=Depends(get_session),
    service: AuthService = Depends(get_auth_service),
):
    token = await service.repository.refresh_token(session, hash_refresh_token(data.refresh_token))
    if token is not None:
        await service.repository.revoke_tokens(session, token.family_id, datetime.now(timezone.utc))
        await session.commit()


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
