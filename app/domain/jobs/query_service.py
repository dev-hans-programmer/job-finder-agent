import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.jobs.feedback import JobFeedback
from app.domain.jobs.query_schemas import FeedbackInput
from app.repositories.job_query import JobQueryRepository
from app.repositories.matching import MatchingRepository


class JobQueryService:
    def __init__(self, jobs=None, matches=None):
        self.jobs = jobs or JobQueryRepository()
        self.matches = matches or MatchingRepository()

    async def list(self, session, user_id, **filters):
        return await self.jobs.list(session, user_id, **filters)

    async def detail(
        self, session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> dict | None:
        job = await self.jobs.get(session, user_id, job_id)
        if job is None:
            return None
        match = await self.matches.latest(session, job_id)
        feedback = await self.jobs.feedback(session, user_id, job_id)
        return {"job": job, "match": match, "feedback": feedback}

    async def feedback(
        self, session: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID, data: FeedbackInput
    ):
        if await self.jobs.get(session, user_id, job_id) is None:
            return None
        existing = await self.jobs.feedback(session, user_id, job_id)
        if existing is not None:
            existing.label, existing.note = data.label, data.note
            await session.commit()
            await session.refresh(existing)
            return existing
        return await self.jobs.save_feedback(
            session, JobFeedback(user_id=user_id, job_id=job_id, label=data.label, note=data.note)
        )
