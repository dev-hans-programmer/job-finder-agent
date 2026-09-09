"""Ingestion and workflow run status endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.ingestion.models import IngestionRun
from app.repositories.sources import SourceRepository

router = APIRouter(prefix="/api/v1/runs", tags=["runs"])


@router.get("/{run_id}")
async def get_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict:
    run: IngestionRun | None = await SourceRepository().get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    return {
        "id": str(run.id),
        "source_id": str(run.source_id),
        "status": run.status,
        "fetched_count": run.fetched_count,
        "normalized_count": run.normalized_count,
        "error_count": run.error_count,
        "error_summary": run.error_summary,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }
