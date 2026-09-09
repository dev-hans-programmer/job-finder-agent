import uuid

import pytest
from sqlalchemy import delete, select

from app.domain.preferences.models import PreferenceProfile, User


@pytest.mark.asyncio
async def test_preference_profile_persists_and_versions(settings):
    from app.db import RuntimeResources
    from app.domain.preferences.schemas import PreferenceInput
    from app.domain.preferences.service import PreferenceService
    from app.repositories.preferences import PreferenceRepository

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            service = PreferenceService(PreferenceRepository())
            first = await service.update(
                session, user_id, PreferenceInput(titles=["Backend Engineer"])
            )
            second = await service.update(
                session, user_id, PreferenceInput(titles=["Staff Engineer"])
            )
            assert (first.version, second.version) == (1, 2)
            rows = (
                (
                    await session.execute(
                        select(PreferenceProfile).where(PreferenceProfile.user_id == user_id)
                    )
                )
                .scalars()
                .all()
            )
            assert sum(row.is_active for row in rows) == 1
            assert second.is_active is True
            await session.execute(
                delete(PreferenceProfile).where(PreferenceProfile.user_id == user_id)
            )
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
    finally:
        await resources.close()
