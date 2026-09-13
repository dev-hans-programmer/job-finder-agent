import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str | None
    success: bool
    ip_address: str | None
    user_agent: str | None
    request_id: str | None
    metadata: dict
    created_at: datetime

    @classmethod
    def from_model(cls, event):
        return cls(
            id=event.id,
            actor_user_id=event.actor_user_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            success=event.success,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            request_id=event.request_id,
            metadata=event.event_metadata or {},
            created_at=event.created_at,
        )
