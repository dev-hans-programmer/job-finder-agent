"""Canonical job query and detail endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.job_query import get_job_query_service
from app.dependencies.matching import get_matching_service
from app.dependencies.preferences import user_id_from_header
from app.domain.jobs.query_schemas import FeedbackInput
from app.domain.jobs.query_service import JobQueryService
from app.domain.matching.service import MatchingService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _job_payload(job) -> dict:
    return {
        "id": str(job.id),
        "title": job.title,
        "company_name": job.company_name,
        "description": job.description,
        "locations": job.locations,
        "work_mode": job.work_mode,
        "application_url": job.application_url,
        "status": job.status,
        "last_seen_at": job.last_seen_at,
    }


def _match_payload(result) -> dict | None:
    if result is None:
        return None
    return {
        "id": str(result.id),
        "score": result.score,
        "confidence": result.confidence,
        "decision": result.decision,
        "components": result.component_scores,
        "matched": result.matched_criteria,
        "missing": result.missing_criteria,
        "concerns": result.concerns,
        "reasoning": result.reasoning,
    }


@router.get("")
async def list_jobs(
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: JobQueryService = Depends(get_job_query_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_score: int | None = Query(None, ge=0, le=100),
    status_filter: str | None = Query(None, alias="status"),
    company: str | None = None,
    location: str | None = None,
) -> dict:
    jobs, total = await service.list(
        session,
        user_id,
        page=page,
        page_size=page_size,
        min_score=min_score,
        status=status_filter,
        company=company,
        location=location,
    )
    return {
        "items": [_job_payload(job) for job in jobs],
        "page": page,
        "page_size": page_size,
        "total": total,
    }


@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: JobQueryService = Depends(get_job_query_service),
) -> dict:
    detail = await service.detail(session, user_id, job_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="job not found")
    feedback = detail["feedback"]
    return {
        "job": _job_payload(detail["job"]),
        "match": _match_payload(detail["match"]),
        "feedback": None
        if feedback is None
        else {"id": str(feedback.id), "label": feedback.label, "note": feedback.note},
    }


@router.get("/{job_id}/match")
async def get_match(
    job_id: uuid.UUID,
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: JobQueryService = Depends(get_job_query_service),
) -> dict:
    detail = await service.detail(session, user_id, job_id)
    if detail is None or detail["match"] is None:
        raise HTTPException(status_code=404, detail="match not found")
    return _match_payload(detail["match"])


@router.post("/{job_id}/feedback", status_code=status.HTTP_200_OK)
async def save_feedback(
    job_id: uuid.UUID,
    data: FeedbackInput,
    user_id: uuid.UUID = Depends(user_id_from_header),
    session: AsyncSession = Depends(get_session),
    service: JobQueryService = Depends(get_job_query_service),
) -> dict:
    feedback = await service.feedback(session, user_id, job_id, data)
    if feedback is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": str(feedback.id),
        "job_id": str(feedback.job_id),
        "label": feedback.label,
        "note": feedback.note,
    }


@router.post("/{job_id}/match")
async def match_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    service: MatchingService = Depends(get_matching_service),
    user_id: uuid.UUID = Depends(user_id_from_header),
) -> dict:
    result = await service.match_job(session, job_id, user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="job or active preferences not found")
    return {
        "id": str(result.id),
        "score": result.score,
        "confidence": result.confidence,
        "decision": result.decision,
        "components": result.component_scores,
        "matched": result.matched_criteria,
        "missing": result.missing_criteria,
        "concerns": result.concerns,
        "reasoning": result.reasoning,
    }
