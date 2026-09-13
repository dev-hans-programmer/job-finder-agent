import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from app.api.v1.auth import (
    assign_role,
    confirm_password_reset,
    create_role,
    logout,
    register,
    request_password_reset,
    resend_email_verification,
    revoke_other_sessions,
    revoke_session,
    sessions,
    verify_email,
)
from app.auth.schemas import (
    EmailVerificationInput,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshInput,
    RegisterInput,
    RoleInput,
)
from app.auth.security import create_access_token
from app.dependencies.auth import get_current_user, require_role


def test_register_login_me_refresh_and_logout(client):
    email = f"user-{uuid.uuid4()}@example.com"
    password = "correct horse battery staple"
    registered = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert registered.status_code == 201
    assert registered.json()["success"] is True
    assert registered.json()["data"]["roles"] == ["user"]

    duplicate = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert duplicate.status_code == 409
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    tokens = login.json()["data"]
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200 and me.json()["data"]["email"] == email
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["refresh_token"] != tokens["refresh_token"]
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401
    assert (
        client.post(
            "/api/v1/auth/logout", json={"refresh_token": refreshed.json()["data"]["refresh_token"]}
        ).status_code
        == 204
    )


def test_auth_rejects_invalid_credentials_and_tokens(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "none@example.com", "password": "incorrect password"}
    )
    assert response.status_code == 401
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid-refresh-token-value"}
        ).status_code
        == 401
    )


@pytest.mark.asyncio
async def test_auth_role_routes_and_dependency_branches():
    role = SimpleNamespace(id=uuid.uuid4(), name="operator", description="ops")
    service = SimpleNamespace(
        create_role=AsyncMock(return_value=role),
        assign_role=AsyncMock(),
        repository=SimpleNamespace(
            refresh_token=AsyncMock(return_value=None),
        ),
    )
    response = await create_role(RoleInput(name="operator"), None, None, None, service)
    assert response.data["name"] == "operator"
    await logout(RefreshInput(refresh_token="x" * 20), None, service)
    service.settings = SimpleNamespace(auth_session_management_enabled=True)
    service.repository.refresh_token.return_value = SimpleNamespace(
        family_id=uuid.uuid4(), session_id=None, user_id=uuid.uuid4()
    )
    service.repository.revoke_tokens = AsyncMock()
    session = SimpleNamespace(commit=AsyncMock())
    await logout(RefreshInput(refresh_token="x" * 20), session, service)

    assert await assign_role(uuid.uuid4(), "user", None, None, service) is None
    service.assign_role.side_effect = ValueError("user or role not found")
    with pytest.raises(Exception):
        await assign_role(uuid.uuid4(), "missing", None, None, service)

    with pytest.raises(Exception):
        await require_role("admin")(SimpleNamespace(id=uuid.uuid4()), SimpleNamespace())


@pytest.mark.asyncio
async def test_auth_dependency_modes():
    user = SimpleNamespace(id=uuid.uuid4(), status="active")

    class Session:
        async def get(self, model, user_id):
            return user

        def add(self, value):
            pass

        async def commit(self):
            pass

    with patch(
        "app.dependencies.auth.get_settings",
        return_value=SimpleNamespace(auth_require_token=False, jwt_secret_key="s", jwt_issuer="i"),
    ):
        assert await get_current_user(Session(), None) is user

        class EmptySession(Session):
            async def get(self, model, user_id):
                return None

        local_user = await get_current_user(EmptySession(), None)
        assert local_user.email == "local@example.com"
    with patch(
        "app.dependencies.auth.get_settings",
        return_value=SimpleNamespace(auth_require_token=True, jwt_secret_key="s", jwt_issuer="i"),
    ):
        with pytest.raises(Exception):
            await get_current_user(Session(), None)
        with pytest.raises(Exception):
            await get_current_user(Session(), "Basic x")
        token = create_access_token(user.id, "a@b.com", [], "s", 1, "i")
        assert await get_current_user(Session(), f"Bearer {token}") is user
        with pytest.raises(Exception):
            await get_current_user(Session(), "Bearer invalid")

        class InactiveSession(Session):
            async def get(self, model, user_id):
                return SimpleNamespace(id=user_id, status="disabled")

        with pytest.raises(Exception):
            await get_current_user(InactiveSession(), f"Bearer {token}")

        request = SimpleNamespace(state=SimpleNamespace())
        session_settings = SimpleNamespace(
            auth_require_token=True,
            auth_session_management_enabled=True,
            jwt_secret_key="s",
            jwt_issuer="i",
        )
        session_token = create_access_token(user.id, "a@b.com", [], "s", 1, "i", user.id)
        with patch(
            "app.dependencies.auth.AuthRepository",
            return_value=SimpleNamespace(
                auth_session=AsyncMock(return_value=SimpleNamespace(id=user.id, revoked_at=None))
            ),
        ):
            assert await get_current_user(
                Session(), f"Bearer {session_token}", session_settings, request
            )
        assert request.state.session_id == user.id
        with patch(
            "app.dependencies.auth.AuthRepository",
            return_value=SimpleNamespace(
                auth_session=AsyncMock(return_value=SimpleNamespace(id=user.id, revoked_at=None))
            ),
        ):
            assert (
                await get_current_user(Session(), f"Bearer {session_token}", session_settings)
                is user
            )

    with patch(
        "app.dependencies.auth.AuthRepository",
        return_value=SimpleNamespace(roles=AsyncMock(return_value=[])),
    ):
        with pytest.raises(Exception):
            await require_role("admin")(user, Session())
    with patch(
        "app.dependencies.auth.AuthRepository",
        return_value=SimpleNamespace(roles=AsyncMock(return_value=["admin"])),
    ):
        assert await require_role("admin")(user, Session()) is user


def test_decode_rejects_wrong_token_type():
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "type": "refresh", "iss": "i"}, "s", algorithm="HS256"
    )
    with pytest.raises(jwt.InvalidTokenError):
        from app.auth.security import decode_access_token

        decode_access_token(token, "s", "i")


@pytest.mark.asyncio
async def test_session_route_error_branches():
    request = SimpleNamespace(state=SimpleNamespace(session_id=None))
    user = SimpleNamespace(id=uuid.uuid4())
    service = SimpleNamespace(list_sessions=AsyncMock(return_value=[]))
    response = await sessions(request, user, None, service)
    assert response.data == []
    with pytest.raises(Exception):
        await revoke_other_sessions(request, user, None, service)
    request.state.session_id = uuid.uuid4()
    service.revoke_other_sessions = AsyncMock(side_effect=ValueError("disabled"))
    with pytest.raises(Exception):
        await revoke_other_sessions(request, user, None, service)
    service.revoke_session = AsyncMock(side_effect=ValueError("not found"))
    with pytest.raises(Exception):
        await revoke_session(uuid.uuid4(), user, None, service)


@pytest.mark.asyncio
async def test_account_security_routes_feature_flags():
    request = SimpleNamespace(state=SimpleNamespace())
    settings = SimpleNamespace(
        auth_password_reset_enabled=True, auth_email_verification_enabled=True
    )
    service = SimpleNamespace(settings=settings, issue_code=AsyncMock())
    service.register = AsyncMock(
        return_value=SimpleNamespace(id=uuid.uuid4(), email="security@example.com")
    )
    service.roles_for_user = AsyncMock(return_value=["user"])
    registered = await register(
        RegisterInput(email="security@example.com", password="NewPassword123!"),
        request,
        None,
        service,
    )
    assert registered.data.email == "security@example.com"
    response = await request_password_reset(
        PasswordResetRequest(email="security@example.com"), request, None, service
    )
    assert response.data["message"].startswith("If the account exists")
    await resend_email_verification(
        PasswordResetRequest(email="security@example.com"), request, None, service
    )
    service.verify_email = AsyncMock()
    await verify_email(
        EmailVerificationInput(email="security@example.com", code="123456"), None, service
    )
    service.reset_password = AsyncMock()
    await confirm_password_reset(
        PasswordResetConfirm(
            email="security@example.com", code="123456", password="NewPassword123!"
        ),
        None,
        service,
    )
    settings.auth_password_reset_enabled = False
    settings.auth_email_verification_enabled = False
    await request_password_reset(
        PasswordResetRequest(email="security@example.com"), request, None, service
    )
    await resend_email_verification(
        PasswordResetRequest(email="security@example.com"), request, None, service
    )
    with pytest.raises(Exception):
        await confirm_password_reset(
            PasswordResetConfirm(
                email="security@example.com", code="123456", password="NewPassword123!"
            ),
            None,
            service,
        )
    with pytest.raises(Exception):
        await verify_email(
            EmailVerificationInput(email="security@example.com", code="123456"), None, service
        )
    settings.auth_password_reset_enabled = True
    service.reset_password.side_effect = ValueError("expired")
    with pytest.raises(Exception):
        await confirm_password_reset(
            PasswordResetConfirm(
                email="security@example.com", code="123456", password="NewPassword123!"
            ),
            None,
            service,
        )
    settings.auth_email_verification_enabled = True
    service.verify_email.side_effect = ValueError("expired")
    with pytest.raises(Exception):
        await verify_email(
            EmailVerificationInput(email="security@example.com", code="123456"), None, service
        )


def test_session_management_flag_tracks_and_revokes_sessions(client):
    client.app.state.settings.auth_session_management_enabled = True
    email = f"sessions-{uuid.uuid4()}@example.com"
    password = "SessionPassword123!"
    assert (
        client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        ).status_code
        == 201
    )
    first = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Device-Name": "MacBook"},
    ).json()["data"]
    second = client.post("/api/v1/auth/login", json={"email": email, "password": password}).json()[
        "data"
    ]
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    sessions = client.get("/api/v1/auth/sessions", headers=first_headers)
    assert sessions.status_code == 200
    assert len(sessions.json()["data"]) == 2
    assert any(item["current"] for item in sessions.json()["data"])
    assert client.delete("/api/v1/auth/sessions/others", headers=first_headers).status_code == 204
    remaining = client.get("/api/v1/auth/sessions", headers=first_headers)
    assert len(remaining.json()["data"]) == 1
    session_id = remaining.json()["data"][0]["id"]
    assert (
        client.delete(f"/api/v1/auth/sessions/{session_id}", headers=first_headers).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me", headers=first_headers).status_code == 401
    assert second["refresh_token"]
