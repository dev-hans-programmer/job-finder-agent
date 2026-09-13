from datetime import datetime, timedelta, timezone
from pathlib import Path
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


@pytest.mark.asyncio
async def test_audit_service_search_export_and_retention(tmp_path: Path):
    old = SimpleNamespace(
        id="old-id",
        actor_user_id=None,
        action="old",
        resource_type="user",
        resource_id=None,
        success=True,
        ip_address=None,
        user_agent=None,
        request_id=None,
        event_metadata={},
        created_at=datetime.now(timezone.utc) - timedelta(days=400),
    )
    repository = SimpleNamespace(
        search=AsyncMock(return_value=[old]),
        count=AsyncMock(return_value=1),
        before=AsyncMock(return_value=[old]),
        delete_before=AsyncMock(return_value=1),
    )
    service = AuditService(repository)
    events, total = await service.search(Session(), page=2, page_size=10, action="old")
    assert events == [old] and total == 1
    assert await service.export(Session(), action="old") == [old]
    result = await service.apply_retention(
        Session(), retention_days=365, archive_enabled=True, archive_dir=str(tmp_path)
    )
    assert result["archived"] == 1 and result["deleted"] == 1
    assert result["archive_path"].exists()
    result = await service.apply_retention(
        Session(), retention_days=365, archive_enabled=False, archive_dir=str(tmp_path)
    )
    assert result["archived"] == 0


@pytest.mark.asyncio
async def test_audit_repository_query_and_retention_methods():
    class Result:
        def scalars(self):
            return SimpleNamespace(all=lambda: ["event"])

        rowcount = 2

    class QuerySession(Session):
        async def execute(self, query):
            self.query = query
            return Result()

        async def scalar(self, query):
            self.query = query
            return 3

    session = QuerySession()
    repository = AuditRepository()
    values = dict(
        actor_user_id="actor",
        action="action",
        resource_type="user",
        resource_id="resource",
        success=True,
        created_after=datetime.now(timezone.utc) - timedelta(days=1),
        created_before=datetime.now(timezone.utc),
    )
    assert await repository.search(session, **values) == ["event"]
    assert await repository.search(session) == ["event"]
    assert await repository.count(session, **values) == 3
    assert await repository.before(session, datetime.now(timezone.utc)) == ["event"]
    assert await repository.delete_before(session, datetime.now(timezone.utc)) == 2
