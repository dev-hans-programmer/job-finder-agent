"""Canonical job query and detail endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_session
from app.dependencies.matching import get_matching_service
from app.dependencies.preferences import user_id_from_header
from app.domain.matching.service import MatchingService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


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
