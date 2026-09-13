import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.domain.preferences.models import AuditEvent


class AuditService:
    """Application boundary for append-only audit events."""

    def __init__(self, repository):
        self.repository = repository

    async def record(
        self,
        session,
        *,
        action: str,
        resource_type: str,
        resource_id=None,
        actor_user_id=None,
        success: bool = True,
        ip_address=None,
        user_agent=None,
        request_id=None,
        metadata: dict | None = None,
    ):
        event = AuditEvent(
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            event_metadata=metadata or {},
        )
        return await self.repository.create(session, event)

    async def search(self, session, *, page=1, page_size=50, **filters):
        offset = (page - 1) * page_size
        events = await self.repository.search(session, offset=offset, limit=page_size, **filters)
        total = await self.repository.count(session, **filters)
        return events, total

    async def export(self, session, *, page_size=1000, **filters):
        return await self.repository.search(session, offset=0, limit=page_size, **filters)

    async def apply_retention(self, session, *, retention_days, archive_enabled, archive_dir):
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        events = await self.repository.before(session, cutoff)
        archive_path = None
        if archive_enabled and events:
            archive_path = Path(archive_dir)
            archive_path.mkdir(parents=True, exist_ok=True)
            archive_path /= f"audit-{cutoff.date().isoformat()}.jsonl"
            with archive_path.open("a", encoding="utf-8") as output:
                for event in events:
                    output.write(
                        json.dumps(
                            {
                                "id": str(event.id),
                                "actor_user_id": (
                                    str(event.actor_user_id) if event.actor_user_id else None
                                ),
                                "action": event.action,
                                "resource_type": event.resource_type,
                                "resource_id": event.resource_id,
                                "success": event.success,
                                "ip_address": event.ip_address,
                                "user_agent": event.user_agent,
                                "request_id": event.request_id,
                                "metadata": event.event_metadata or {},
                                "created_at": event.created_at.isoformat(),
                            }
                        )
                        + "\n"
                    )
        deleted = await self.repository.delete_before(session, cutoff)
        return {
            "cutoff": cutoff,
            "archived": len(events) if archive_enabled else 0,
            "deleted": deleted,
            "archive_path": archive_path,
        }
