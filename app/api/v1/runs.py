"""Ingestion and workflow run status endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.responses import SuccessResponse, success_response
from app.dependencies.auth import user_id_from_current_user
from app.dependencies.database import get_session
from app.ingestion.models import IngestionRun
from app.repositories.sources import SourceRepository

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("/{run_id}")
async def get_run(
    run_id: uuid.UUID,
    request: Request,
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse[dict]:
    run: IngestionRun | None = await SourceRepository().get_run_for_user(session, run_id, user_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return success_response(
        {
            "id": str(run.id),
            "source_id": str(run.source_id),
            "status": run.status,
            "fetched_count": run.fetched_count,
            "normalized_count": run.normalized_count,
            "error_count": run.error_count,
            "error_summary": run.error_summary,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
        },
        request,
    )
