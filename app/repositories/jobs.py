import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.jobs.models import Job, JobSourceRecord
from app.domain.jobs.normalizer import JobCandidate


class JobRepository:
    async def get(self, session: AsyncSession, job_id: uuid.UUID) -> Job | None:
        return await session.get(Job, job_id)

    async def find_existing(
        self, session: AsyncSession, source_id: uuid.UUID, candidate: JobCandidate
    ) -> Job | None:
        source_match = await session.scalar(
            select(Job)
            .join(JobSourceRecord, JobSourceRecord.job_id == Job.id)
            .where(
                JobSourceRecord.source_id == source_id,
                JobSourceRecord.external_id == candidate.external_id,
            )
        )
        if source_match:
            return source_match
        return await session.scalar(
            select(Job).where(
                Job.application_url == candidate.application_url,
                Job.company_normalized == candidate.company_normalized,
            )
        )

    async def upsert(
        self, session: AsyncSession, source_id: uuid.UUID, candidate: JobCandidate
    ) -> tuple[Job, bool, bool]:
        job = await self.find_existing(session, source_id, candidate)
        created = job is None
        changed = False
        if job is None:
            job = Job(
                title=candidate.title,
                company_name=candidate.company_name,
                company_normalized=candidate.company_normalized,
                description=candidate.description,
                description_hash=candidate.description_hash,
                locations=candidate.locations,
                application_url=candidate.application_url,
            )
            session.add(job)
            await session.flush()
        elif job.description_hash != candidate.description_hash:
            job.title = candidate.title
            job.description = candidate.description
            job.description_hash = candidate.description_hash
            job.locations = candidate.locations
            changed = True
        record = JobSourceRecord(
            job_id=job.id,
            source_id=source_id,
            external_id=candidate.external_id,
            source_url=candidate.application_url,
            raw_payload=candidate.raw_payload,
            raw_payload_hash=hashlib.sha256(str(candidate.raw_payload).encode()).hexdigest(),
        )
        session.add(record)
        await session.commit()
        await session.refresh(job)
        return job, created, changed
