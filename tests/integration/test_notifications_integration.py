# ruff: noqa: E501, E702
import uuid

import pytest

from app.domain.jobs.models import Job
from app.domain.matching.models import MatchResult
from app.domain.notifications.service import NotificationService
from app.domain.preferences.models import PreferenceProfile, User


@pytest.mark.asyncio
async def test_notification_delivery_is_persisted(settings):
    from app.db import RuntimeResources
    from app.repositories.notifications import NotificationRepository

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            user = User(id=user_id)
            profile = PreferenceProfile(
                user_id=user_id,
                version=1,
                config={"titles": []},
                matching_weights={},
                is_active=True,
            )
            job = Job(
                title="Backend",
                company_name="Acme",
                company_normalized="acme",
                description="Python",
                description_hash="n",
                locations=["Mumbai"],
                application_url="https://apply",
            )
            session.add(user)
            await session.flush()
            session.add_all([profile, job])
            await session.flush()
            match = MatchResult(
                job_id=job.id,
                preference_profile_id=profile.id,
                job_description_hash="n",
                score=90,
                confidence=0.9,
                decision="notify",
                component_scores={},
                matched_criteria=["Python"],
                missing_criteria=[],
                concerns=[],
                reasoning="ok",
            )
            session.add(match)
            await session.flush()

            class Provider:
                async def send(self, message):
                    return "m1"

            delivery = await NotificationService().deliver(
                session, user_id, job, profile.id, match, "email", Provider()
            )
            assert delivery.status == "delivered"
            duplicate = await NotificationService().deliver(
                session, user_id, job, profile.id, match, "email", Provider()
            )
            assert duplicate.id == delivery.id
            assert await NotificationRepository().get(session, delivery.id)
            await session.delete(delivery)
            await session.delete(match)
            await session.delete(job)
            await session.delete(profile)
            await session.delete(user)
            await session.commit()
    finally:
        await resources.close()
