import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.audit import export_audit_events, search_audit_events


def event():
    return SimpleNamespace(
        id=uuid.uuid4(),
        actor_user_id=None,
        action="user.logged_in",
        resource_type="user",
        resource_id="user-id",
        success=True,
        ip_address="127.0.0.1",
        user_agent="pytest",
        request_id="request-id",
        event_metadata={"safe": True},
        created_at=datetime.now(timezone.utc),
    )


def request():
    return SimpleNamespace(state=SimpleNamespace(request_id="api-request"))


@pytest.mark.asyncio
async def test_admin_audit_search_passes_filters_and_pagination():
    service = SimpleNamespace(search=AsyncMock(return_value=([event()], 1)))
    response = await search_audit_events(
        request(),
        actor_user_id=None,
        action="user.logged_in",
        resource_type="user",
        resource_id="user-id",
        success=True,
        created_after=datetime(2020, 1, 1, tzinfo=timezone.utc),
        created_before=datetime(2030, 1, 1, tzinfo=timezone.utc),
        page=2,
        page_size=5,
        _admin=SimpleNamespace(),
        session=SimpleNamespace(),
        service=service,
    )
    assert response.data[0].action == "user.logged_in"
    assert response.meta.page == 2
    assert response.meta.total == 1
    service.search.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_audit_exports_json_and_csv():
    service = SimpleNamespace(export=AsyncMock(return_value=[event()]))
    json_response = await export_audit_events(
        request(),
        format="json",
        _admin=SimpleNamespace(),
        session=SimpleNamespace(),
        service=service,
    )
    json_parts = [part async for part in json_response.body_iterator]
    assert b"user.logged_in" in b"".join(
        part if isinstance(part, bytes) else part.encode() for part in json_parts
    )

    csv_response = await export_audit_events(
        request(),
        format="csv",
        _admin=SimpleNamespace(),
        session=SimpleNamespace(),
        service=service,
    )
    csv_parts = [part async for part in csv_response.body_iterator]
    assert b"action" in b"".join(
        part if isinstance(part, bytes) else part.encode() for part in csv_parts
    )
    service.export.return_value = []
    empty_csv = await export_audit_events(
        request(),
        format="csv",
        _admin=SimpleNamespace(),
        session=SimpleNamespace(),
        service=service,
    )
    empty_parts = [part async for part in empty_csv.body_iterator]
    assert b"action" in b"".join(
        part if isinstance(part, bytes) else part.encode() for part in empty_parts
    )
