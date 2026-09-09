import uuid

import pytest
from sqlalchemy import delete

from app.domain.preferences.models import User
from app.ingestion.models import IngestionRun, Source
from app.repositories.sources import SourceRepository


@pytest.mark.asyncio
async def test_source_repository_round_trip(settings):
    from app.db import RuntimeResources

    resources = RuntimeResources(settings)
    user_id = uuid.uuid4()
    try:
        async with resources.session_factory() as session:
            repository = SourceRepository()
            session.add(User(id=user_id))
            await session.flush()
            source = await repository.create(
                session,
                user_id,
                {"kind": "lever", "name": "Demo", "config": {"account": "demo"}, "enabled": True},
            )
            assert await repository.get(session, source.id) is not None
            assert source in await repository.list_for_user(session, user_id)
            run = await repository.create_run(session, source.id)
            assert run.status == "running"
            assert await repository.get_run(session, run.id) is not None
            finished = await repository.finish_run(
                session, run, status="succeeded", fetched_count=2
            )
            assert finished.normalized_count == 2
            await session.execute(delete(IngestionRun).where(IngestionRun.source_id == source.id))
            await session.execute(delete(Source).where(Source.id == source.id))
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()
    finally:
        await resources.close()
