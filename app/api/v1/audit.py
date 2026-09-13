import csv
import io
import json
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.api.responses import SuccessResponse, success_response
from app.dependencies.audit_admin import get_audit_admin_service
from app.dependencies.auth import require_role
from app.dependencies.database import get_session
from app.domain.audit.schemas import AuditEventResponse
from app.domain.audit.service import AuditService

router = APIRouter(prefix="/api/v1/admin", tags=["admin-audit"])


def filters(
    actor_user_id: uuid.UUID | None,
    action: str | None,
    resource_type: str | None,
    resource_id: str | None,
    success: bool | None,
    created_after: datetime | None,
    created_before: datetime | None,
):
    return {
        "actor_user_id": actor_user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "success": success,
        "created_after": created_after,
        "created_before": created_before,
    }


@router.get("/audit-events", response_model=SuccessResponse[list[AuditEventResponse]])
async def search_audit_events(
    request: Request,
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    success: bool | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    _admin=Depends(require_role("admin")),
    session=Depends(get_session),
    service: AuditService = Depends(get_audit_admin_service),
):
    events, total = await service.search(
        session,
        page=page,
        page_size=page_size,
        **filters(
            actor_user_id,
            action,
            resource_type,
            resource_id,
            success,
            created_after,
            created_before,
        ),
    )
    return success_response(
        [AuditEventResponse.from_model(event) for event in events],
        request,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/audit-events/export")
async def export_audit_events(
    request: Request,
    format: Literal["json", "csv"] = Query("json"),
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    success: bool | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    _admin=Depends(require_role("admin")),
    session=Depends(get_session),
    service: AuditService = Depends(get_audit_admin_service),
):
    events = await service.export(
        session,
        **filters(
            actor_user_id,
            action,
            resource_type,
            resource_id,
            success,
            created_after,
            created_before,
        ),
    )
    rows = [AuditEventResponse.from_model(event).model_dump(mode="json") for event in events]

    async def stream_json():
        yield json.dumps(rows)

    async def stream_csv():
        output = io.StringIO()
        fieldnames = list(rows[0].keys()) if rows else ["id", "action", "success", "created_at"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        yield output.getvalue()
        for row in rows:
            output = io.StringIO()
            csv.DictWriter(output, fieldnames=fieldnames).writerow(row)
            yield output.getvalue()

    if format == "csv":
        return StreamingResponse(
            stream_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit-events.csv"},
        )
    return StreamingResponse(
        stream_json(),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=audit-events.json"},
    )
