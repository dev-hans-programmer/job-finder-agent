import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.domain.auth.service import AuthService
from app.repositories.auth import AuthRepository


class Session:
    def add(self, value):
        pass

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, value):
        value.id = uuid.uuid4()


class Repo:
    def __init__(self, user=None, role=None, token=None):
        self._user, self._role, self._token = user, role, token

    async def user_by_email(self, session, email):
        return self._user

    async def role(self, session, name):
        return self._role

    async def create_role(self, session, name, description):
        return SimpleNamespace(id=uuid.uuid4())

    async def assign_role(self, session, user_id, role_id):
        pass

    async def roles(self, session, user_id):
        return ["user"]

    async def save_refresh_token(self, session, token):
        self.saved = token

    async def refresh_token(self, session, value):
        return self._token

    async def revoke_tokens(self, session, family_id, now):
        pass

    async def user(self, session, user_id):
        return self._user


SETTINGS = SimpleNamespace(
    default_user_role="user",
    refresh_token_expire_days=30,
    jwt_secret_key="secret",
    access_token_expire_minutes=15,
    jwt_issuer="issuer",
    initial_admin_email=None,
)


@pytest.mark.asyncio
async def test_auth_service_security_and_refresh_branches():
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="a@example.com",
        password_hash=hash_password("long password"),
        status="active",
    )
    service = AuthService(Repo(), SETTINGS)
    assert await service.register(Session(), "A@EXAMPLE.COM", "long password")
    admin_settings_values = vars(SETTINGS).copy()
    admin_settings_values["initial_admin_email"] = "admin@example.com"
    admin_settings = SimpleNamespace(**admin_settings_values)
    assert await AuthService(Repo(), admin_settings).register(
        Session(), "ADMIN@EXAMPLE.COM", "long password"
    )
    existing_admin_values = admin_settings_values.copy()
    existing_admin_values["initial_admin_email"] = "admin2@example.com"
    existing_admin = SimpleNamespace(**existing_admin_values)
    assert await AuthService(Repo(role=SimpleNamespace(id=uuid.uuid4())), existing_admin).register(
        Session(), "ADMIN2@EXAMPLE.COM", "long password"
    )
    assert await service.roles_for_user(Session(), user.id) == ["user"]
    created_role = await service.create_role(Session(), "operator", "Operations")
    assert created_role.id
    await AuthService(Repo(user=user, role=SimpleNamespace(id=uuid.uuid4())), SETTINGS).assign_role(
        Session(), user.id, "user"
    )
    with pytest.raises(ValueError):
        await AuthService(Repo(user=None, role=None), SETTINGS).assign_role(
            Session(), user.id, "missing"
        )
    with pytest.raises(ValueError):
        await AuthService(Repo(user=user), SETTINGS).register(
            Session(), "a@example.com", "long password"
        )
    assert await AuthService(Repo(user=user), SETTINGS).authenticate(
        Session(), "a@example.com", "long password"
    )
    for candidate in [
        None,
        SimpleNamespace(password_hash=None, status="active"),
        SimpleNamespace(password_hash=hash_password("different"), status="active"),
        SimpleNamespace(password_hash=user.password_hash, status="disabled"),
    ]:
        with pytest.raises(ValueError):
            await AuthService(Repo(user=candidate), SETTINGS).authenticate(
                Session(), "a@example.com", "long password"
            )
    access, refresh = await service.issue_tokens(Session(), user)
    assert await service.claims(access)
    with pytest.raises(ValueError):
        await service.claims("bad")
    token = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        family_id=uuid.uuid4(),
        user_id=user.id,
    )
    assert (await AuthService(Repo(user=user, token=token), SETTINGS).refresh(Session(), refresh))[
        0
    ]
    for bad in [
        None,
        SimpleNamespace(
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc),
            family_id=uuid.uuid4(),
            user_id=user.id,
        ),
        SimpleNamespace(
            revoked_at=None,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            family_id=uuid.uuid4(),
            user_id=user.id,
        ),
    ]:
        with pytest.raises(ValueError):
            await AuthService(Repo(user=user, token=bad), SETTINGS).refresh(Session(), refresh)
    dead = SimpleNamespace(
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        family_id=uuid.uuid4(),
        user_id=user.id,
    )
    with pytest.raises(ValueError):
        await AuthService(
            Repo(user=SimpleNamespace(status="disabled"), token=dead), SETTINGS
        ).refresh(Session(), refresh)


def test_password_and_jwt_validation():
    hashed = hash_password("password")
    assert verify_password("password", hashed) and not verify_password("wrong", hashed)
    token = create_access_token(uuid.uuid4(), "a@example.com", [], "secret", 1, "issuer")
    assert decode_access_token(token, "secret", "issuer")["type"] == "access"


@pytest.mark.asyncio
async def test_auth_repository_role_and_assignment_branches():
    repository = AuthRepository()
    role = await repository.create_role(Session(), "operator", "Operations")
    assert role.name == "operator"

    class AssignmentSession(Session):
        def __init__(self, existing=None):
            self.existing = existing

        async def scalar(self, query):
            return self.existing

    await repository.assign_role(AssignmentSession(), uuid.uuid4(), role.id)
    await repository.assign_role(AssignmentSession(SimpleNamespace()), uuid.uuid4(), role.id)
