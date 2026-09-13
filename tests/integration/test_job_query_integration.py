import uuid

import pytest

from app.domain.jobs.models import Job, JobSourceRecord
from app.domain.jobs.query_schemas import FeedbackInput
from app.domain.jobs.query_service import JobQueryService
from app.domain.preferences.models import User
from app.ingestion.models import Source
from app.repositories.job_query import JobQueryRepository


@pytest.mark.asyncio
async def test_job_queries_filters_pagination_and_feedback(settings):
    from app.db import RuntimeResources

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            user = User(id=user_id)
            source = Source(user_id=user_id, kind="test", name="test", config={})
            session.add_all([user, source])
            await session.flush()
            job = Job(
                title="Backend",
                company_name="Acme",
                company_normalized="acme",
                description="Python",
                description_hash="q",
                locations=["Mumbai"],
                application_url="https://q",
                status="active",
            )
            closed = Job(
                title="Old",
                company_name="Other",
                company_normalized="other",
                description="x",
                description_hash="r",
                locations=["Delhi"],
                application_url="https://r",
                status="closed",
            )
            session.add_all([job, closed])
            await session.flush()
            session.add_all(
                [
                    JobSourceRecord(
                        job_id=job.id,
                        source_id=source.id,
                        external_id="1",
                        source_url="https://q",
                        raw_payload={},
                        raw_payload_hash="1",
                    ),
                    JobSourceRecord(
                        job_id=closed.id,
                        source_id=source.id,
                        external_id="2",
                        source_url="https://r",
                        raw_payload={},
                        raw_payload_hash="2",
                    ),
                ]
            )
            await session.commit()
            repo = JobQueryRepository()
            rows, total = await repo.list(
                session,
                user_id,
                page=1,
                page_size=1,
                min_score=None,
                status=None,
                company="acme",
                location="Mumbai",
            )
            assert total == 1 and rows[0].id == job.id
            rows, total = await repo.list(
                session,
                user_id,
                page=1,
                page_size=10,
                min_score=None,
                status="closed",
                company=None,
                location=None,
            )
            assert total == 1 and rows[0].id == closed.id
            rows, total = await repo.list(
                session,
                user_id,
                page=1,
                page_size=10,
                min_score=50,
                status=None,
                company=None,
                location=None,
            )
            assert rows == [] and total == 0
            assert await repo.get(session, user_id, job.id)
            assert await repo.get(session, uuid.uuid4(), job.id) is None
            service = JobQueryService(repo)
            first = await service.feedback(
                session, user_id, job.id, FeedbackInput(label="saved", note="one")
            )
            second = await service.feedback(
                session, user_id, job.id, FeedbackInput(label="applied", note="two")
            )
            assert first.id == second.id and second.label == "applied"
            assert await repo.feedback(session, user_id, job.id)
            await session.delete(second)
            await session.delete(job)
            await session.delete(closed)
            await session.delete(source)
            await session.delete(user)
            await session.commit()
    finally:
        await resources.close()
