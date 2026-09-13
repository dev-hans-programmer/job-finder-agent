from datetime import datetime

from sqlalchemy import delete, func, select

from app.domain.preferences.models import AuditEvent


class AuditRepository:
    async def create(self, session, event):
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

    def _query(
        self,
        *,
        actor_user_id=None,
        action=None,
        resource_type=None,
        resource_id=None,
        success=None,
        created_after=None,
        created_before=None,
    ):
        query = select(AuditEvent)
        if actor_user_id is not None:
            query = query.where(AuditEvent.actor_user_id == actor_user_id)
        if action:
            query = query.where(AuditEvent.action == action)
        if resource_type:
            query = query.where(AuditEvent.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditEvent.resource_id == resource_id)
        if success is not None:
            query = query.where(AuditEvent.success == success)
        if created_after is not None:
            query = query.where(AuditEvent.created_at >= created_after)
        if created_before is not None:
            query = query.where(AuditEvent.created_at <= created_before)
        return query

    async def search(self, session, *, offset=0, limit=50, **filters):
        result = await session.execute(
            self._query(**filters)
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, session, **filters):
        query = self._query(**filters).with_only_columns(func.count(AuditEvent.id))
        return int(await session.scalar(query) or 0)

    async def before(self, session, cutoff: datetime):
        result = await session.execute(
            select(AuditEvent).where(AuditEvent.created_at < cutoff).order_by(AuditEvent.created_at)
        )
        return list(result.scalars().all())

    async def delete_before(self, session, cutoff: datetime):
        result = await session.execute(delete(AuditEvent).where(AuditEvent.created_at < cutoff))
        await session.commit()
        return result.rowcount or 0
