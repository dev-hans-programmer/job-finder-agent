import uuid

import pytest
from sqlalchemy import delete, select

from app.domain.audit.service import AuditService
from app.domain.preferences.models import AuditEvent, User
from app.repositories.audit import AuditRepository


@pytest.mark.asyncio
async def test_audit_event_round_trip(settings):
    from app.db import RuntimeResources

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            session.add(User(id=user_id, email=f"audit-{user_id}@example.com"))
            await session.flush()
            event = await AuditService(AuditRepository()).record(
                session,
                action="user.tested",
                resource_type="user",
                resource_id=user_id,
                actor_user_id=user_id,
                request_id="integration-request",
                metadata={"safe": True},
            )
            saved = await session.scalar(select(AuditEvent).where(AuditEvent.id == event.id))
            assert saved is not None
            assert saved.actor_user_id == user_id
            assert saved.event_metadata == {"safe": True}
            assert saved.request_id == "integration-request"
            await session.execute(delete(AuditEvent).where(AuditEvent.actor_user_id == user_id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
    finally:
        await resources.close()
