import uuid

import pytest

from app.domain.jobs.models import Job
from app.domain.matching.service import MatchingService
from app.domain.preferences.models import PreferenceProfile, User
from app.repositories.matching import MatchingRepository


@pytest.mark.asyncio
async def test_matching_service_persists_result(settings):
    from app.db import RuntimeResources

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            session.add(User(id=user_id))
            await session.flush()
            profile = PreferenceProfile(
                user_id=user_id,
                version=1,
                config={"titles": ["Backend Engineer"], "matching": {"minimum_score": 1}},
                matching_weights={},
                is_active=True,
            )
            session.add(profile)
            await session.flush()
            job = Job(
                title="Backend Engineer",
                company_name="Acme",
                company_normalized="acme",
                description="Python",
                description_hash="hash",
                locations=[],
                application_url="https://apply",
            )
            session.add(job)
            await session.flush()
            result = await MatchingService().match_job(session, job.id, user_id)
            assert result.score >= 0
            assert await MatchingRepository().latest(session, job.id) is not None
            await session.delete(result)
            await session.delete(job)
            await session.delete(profile)
            await session.delete(user_id) if False else None
            await session.commit()
    finally:
        await resources.close()
