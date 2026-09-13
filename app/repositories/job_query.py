import uuid

from sqlalchemy import Select, Text, cast, desc, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.jobs.feedback import JobFeedback
from app.domain.jobs.models import Job, JobSourceRecord
from app.domain.matching.models import MatchResult
from app.ingestion.models import Source


class JobQueryRepository:
    def _query(self, user_id: uuid.UUID) -> Select:
        return select(Job).where(
            exists(
                select(1)
                .select_from(JobSourceRecord)
                .join(Source, Source.id == JobSourceRecord.source_id)
                .where(JobSourceRecord.job_id == Job.id, Source.user_id == user_id)
            )
        )

    async def list(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        min_score: int | None = None,
        status: str | None = None,
        company: str | None = None,
        location: str | None = None,
    ) -> tuple[list[Job], int]:
        query = self._query(user_id)
        if status is None:
            query = query.where(Job.status == "active")
        else:
            query = query.where(Job.status == status)
        if company:
            query = query.where(func.lower(Job.company_name).contains(company.casefold()))
        if location:
            query = query.where(cast(Job.locations, Text).contains(location))
        if min_score is not None:
            query = query.join(MatchResult, MatchResult.job_id == Job.id).where(
                MatchResult.score >= min_score
            )
        total = await session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = await session.scalars(
            query.order_by(desc(Job.last_seen_at), Job.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(rows), total

    async def get(self, session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> Job | None:
        return await session.scalar(self._query(user_id).where(Job.id == job_id))

    async def feedback(
        self, session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> JobFeedback | None:
        return await session.scalar(
            select(JobFeedback).where(JobFeedback.user_id == user_id, JobFeedback.job_id == job_id)
        )

    async def save_feedback(self, session: AsyncSession, feedback: JobFeedback) -> JobFeedback:
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return feedback
