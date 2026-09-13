from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.audit.service import AuditService
from app.repositories.audit import AuditRepository


class Session:
    def add(self, value):
        self.value = value

    async def commit(self):
        pass

    async def refresh(self, value):
        value.id = "event-id"


@pytest.mark.asyncio
async def test_audit_service_builds_safe_structured_event():
    repository = SimpleNamespace(create=AsyncMock(side_effect=lambda _, event: event))
    event = await AuditService(repository).record(
        Session(),
        action="user.logged_in",
        resource_type="user",
        resource_id=123,
        actor_user_id="actor",
        success=False,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="request-1",
        metadata={"reason": "invalid_credentials"},
    )
    assert event.action == "user.logged_in"
    assert event.resource_id == "123"
    assert event.success is False
    assert event.event_metadata == {"reason": "invalid_credentials"}
    repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_audit_repository_persists_and_refreshes_event():
    session = Session()
    event = SimpleNamespace()
    result = await AuditRepository().create(session, event)
    assert result is event
    assert session.value is event
    assert event.id == "event-id"
