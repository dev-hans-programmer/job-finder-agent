import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

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


@pytest.mark.asyncio
async def test_auth_sessions_repository_and_service_paths():
    repository = AuthRepository()
    user_id, current_id, other_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    class SessionQueries(Session):
        def __init__(self, value=None, values=None):
            self.value = value
            self.values = values or []
            self.executed = False

        async def scalar(self, query):
            return self.value

        async def execute(self, query):
            self.executed = True
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: self.values))

    auth_session = SimpleNamespace(id=current_id, revoked_at=None)
    session = SessionQueries(auth_session)
    await repository.save_auth_session(session, SimpleNamespace(id=uuid.uuid4()))
    assert await repository.auth_session(session, current_id, user_id) is auth_session
    assert await repository.auth_sessions(session, user_id) == []
    assert await repository.revoke_auth_session(
        session, current_id, user_id, datetime.now(timezone.utc)
    )
    assert auth_session.revoked_at is not None
    assert not await repository.revoke_auth_session(
        SessionQueries(None), current_id, user_id, datetime.now(timezone.utc)
    )

    sessions = [
        SimpleNamespace(id=current_id, revoked_at=None),
        SimpleNamespace(id=other_id, revoked_at=None),
    ]
    other_query = SessionQueries(values=sessions)
    assert (
        await repository.revoke_other_auth_sessions(
            other_query, user_id, current_id, datetime.now(timezone.utc)
        )
        == 1
    )
    empty_query = SessionQueries(values=[SimpleNamespace(id=current_id, revoked_at=None)])
    assert (
        await repository.revoke_other_auth_sessions(
            empty_query, user_id, current_id, datetime.now(timezone.utc)
        )
        == 0
    )
    verification = SimpleNamespace()
    await repository.save_verification_code(Session(), verification)
    assert await repository.verification_code(session, user_id, "email", "hash") is auth_session
    await repository.revoke_user_tokens(other_query, user_id, datetime.now(timezone.utc))

    settings = SimpleNamespace(
        auth_session_management_enabled=True,
        refresh_token_expire_days=30,
        jwt_secret_key="secret",
        access_token_expire_minutes=15,
        jwt_issuer="issuer",
    )
    session_repo = Repo()
    session_repo.save_auth_session = AsyncMock(
        side_effect=lambda _, value: setattr(value, "id", current_id)
    )
    session_repo.auth_sessions = AsyncMock(return_value=sessions)
    session_repo.revoke_auth_session = AsyncMock(return_value=True)
    session_repo.revoke_other_auth_sessions = AsyncMock(return_value=1)
    service = AuthService(session_repo, settings)
    user = SimpleNamespace(id=user_id, email="a@example.com")
    await service.issue_tokens(Session(), user, session_metadata={"device_name": "Laptop"})
    assert await service.list_sessions(Session(), user_id) == sessions
    await service.revoke_session(Session(), user_id, current_id)
    assert await service.revoke_other_sessions(Session(), user_id, current_id) == 1
    session_repo.revoke_auth_session.return_value = False
    with pytest.raises(ValueError):
        await service.revoke_session(Session(), user_id, current_id)

    disabled = AuthService(Repo(), SimpleNamespace(auth_session_management_enabled=False))
    assert await disabled.list_sessions(Session(), user_id) == []
    with pytest.raises(ValueError):
        await disabled.revoke_session(Session(), user_id, current_id)
    with pytest.raises(ValueError):
        await disabled.revoke_other_sessions(Session(), user_id, current_id)


@pytest.mark.asyncio
async def test_account_security_service_paths():
    user = SimpleNamespace(
        id=uuid.uuid4(),
        email="security@example.com",
        password_hash=hash_password("correct password"),
        status="active",
        failed_login_attempts=0,
        locked_until=None,
        email_verified_at=None,
    )
    settings = SimpleNamespace(
        default_user_role="user",
        auth_password_reset_enabled=True,
        auth_email_verification_enabled=True,
        auth_account_lockout_enabled=True,
        auth_max_login_attempts=2,
        auth_lockout_minutes=15,
        auth_otp_expire_minutes=10,
        refresh_token_expire_days=30,
        jwt_secret_key="secret",
        access_token_expire_minutes=15,
        jwt_issuer="issuer",
    )
    repository = Repo(user=user)
    repository.save_verification_code = AsyncMock()
    repository.verification_code = AsyncMock()
    repository.revoke_user_tokens = AsyncMock()
    service = AuthService(repository, settings)
    pending_user = await AuthService(Repo(user=None), settings).register(
        Session(), "pending@example.com", "correct password"
    )
    assert pending_user.status == "pending_verification"
    assert len(await service.issue_code(Session(), user.email, "password_reset")) == 6
    assert (
        await AuthService(Repo(user=None), settings).issue_code(
            Session(), "missing@example.com", "password_reset"
        )
        is None
    )

    record = SimpleNamespace(
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=1), consumed_at=None
    )
    repository.verification_code.return_value = record
    await service.verify_email(Session(), user.email, "123456")
    assert user.email_verified_at is not None
    assert user.status == "active"
    await service.reset_password(Session(), user.email, "123456", "new password 123")
    assert repository.revoke_user_tokens.await_count == 1
    record.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    with pytest.raises(ValueError):
        await service.verify_email(Session(), user.email, "123456")
    with pytest.raises(ValueError):
        await service.reset_password(Session(), user.email, "123456", "new password 123")

    user.failed_login_attempts = 0
    user.locked_until = None
    for _ in range(2):
        with pytest.raises(ValueError):
            await service.authenticate(Session(), user.email, "wrong password")
    with pytest.raises(ValueError, match="locked"):
        await service.authenticate(Session(), user.email, "new password 123")
    user.locked_until = None
    user.failed_login_attempts = 1
    assert await service.authenticate(Session(), user.email, "new password 123") is user

    settings.auth_email_verification_enabled = True
    user.email_verified_at = None
    with pytest.raises(ValueError, match="verification"):
        await service.authenticate(Session(), user.email, "new password 123")
