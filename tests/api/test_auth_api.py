import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import jwt
import pytest

from app.api.v1.auth import assign_role, create_role, logout
from app.auth.schemas import RefreshInput, RoleInput
from app.auth.security import create_access_token
from app.dependencies.auth import get_current_user, require_role


def test_register_login_me_refresh_and_logout(client):
    email = f"user-{uuid.uuid4()}@example.com"
    password = "correct horse battery staple"
    registered = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert registered.status_code == 201
    assert registered.json()["roles"] == ["user"]

    duplicate = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert duplicate.status_code == 409
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    tokens = login.json()
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200 and me.json()["email"] == email
    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != tokens["refresh_token"]
    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401
    assert (
        client.post(
            "/api/v1/auth/logout", json={"refresh_token": refreshed.json()["refresh_token"]}
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
    assert (await create_role(RoleInput(name="operator"), None, None, service))[
        "name"
    ] == "operator"
    await logout(RefreshInput(refresh_token="x" * 20), None, service)

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
