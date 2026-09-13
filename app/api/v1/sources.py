"""Source configuration and ingestion run endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import user_id_from_current_user
from app.dependencies.database import get_session
from app.dependencies.sources import get_ingestion_service, get_source_service
from app.domain.jobs.ingestion_service import IngestionService
from app.domain.jobs.source_service import SourceService
from app.ingestion.schemas import RunResponse, SourceInput, SourceResponse
from app.workers.tasks.ingestion import run_ingestion

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source: SourceInput,
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
    service: SourceService = Depends(get_source_service),
) -> SourceResponse:
    return await service.create(session, user_id, source)


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
    service: SourceService = Depends(get_source_service),
) -> list[SourceResponse]:
    return await service.list(session, user_id)


@router.post("/{source_id}/run", response_model=RunResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_source(
    source_id: uuid.UUID,
    user_id: uuid.UUID = Depends(user_id_from_current_user),
    session: AsyncSession = Depends(get_session),
    service: IngestionService = Depends(get_ingestion_service),
) -> RunResponse:
    try:
        run = await service.start_run(session, source_id, user_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if not getattr(run, "already_running", False):
        run_ingestion.delay(str(source_id), str(run.id))
    return RunResponse(run_id=str(run.id), status=run.status)
