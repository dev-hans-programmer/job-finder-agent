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
