import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.matching.models import MatchResult


class MatchingRepository:
    async def create(self, session: AsyncSession, result: MatchResult) -> MatchResult:
        session.add(result)
        await session.commit()
        await session.refresh(result)
        return result

    async def latest(self, session: AsyncSession, job_id: uuid.UUID) -> MatchResult | None:
        result = await session.execute(
            select(MatchResult)
            .where(MatchResult.job_id == job_id)
            .order_by(MatchResult.created_at.desc())
        )
        return result.scalars().first()
