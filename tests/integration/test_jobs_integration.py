import uuid

import pytest
from sqlalchemy import delete, select

from app.domain.jobs.models import Job, JobSourceRecord
from app.domain.jobs.normalizer import normalize_record
from app.domain.preferences.models import User
from app.ingestion.base import RawJobRecord
from app.ingestion.models import Source
from app.repositories.jobs import JobRepository


@pytest.mark.asyncio
async def test_job_repository_creates_deduplicates_and_updates(settings):
    from app.db import RuntimeResources

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            session.add(User(id=user_id))
            await session.flush()
            source = Source(
                user_id=user_id, kind="greenhouse", name="Acme", config={}, enabled=True
            )
            session.add(source)
            await session.flush()
            repository = JobRepository()
            first = normalize_record(
                RawJobRecord("1", "Backend", "Python", "https://apply"), "Acme"
            )
            job, created, changed = await repository.upsert(session, source.id, first)
            assert (created, changed) == (True, False)
            duplicate, created, changed = await repository.upsert(session, source.id, first)
            assert duplicate.id == job.id
            assert (created, changed) == (False, False)
            changed_record = normalize_record(
                RawJobRecord("1", "Backend", "Python and AWS", "https://apply"), "Acme"
            )
            updated, created, changed = await repository.upsert(session, source.id, changed_record)
            assert updated.id == job.id
            assert (created, changed) == (False, True)
            assert (
                len((await session.execute(select(Job).where(Job.id == job.id))).scalars().all())
                == 1
            )
            await session.execute(delete(JobSourceRecord).where(JobSourceRecord.job_id == job.id))
            await session.execute(delete(Job).where(Job.id == job.id))
            await session.execute(delete(Source).where(Source.id == source.id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
    finally:
        await resources.close()
