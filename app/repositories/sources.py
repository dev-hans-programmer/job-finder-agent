import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.models import IngestionRun, Source


class SourceRepository:
    async def create(self, session: AsyncSession, user_id: uuid.UUID, data: dict) -> Source:
        source = Source(user_id=user_id, **data)
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source

    async def get(self, session: AsyncSession, source_id: uuid.UUID) -> Source | None:
        return await session.get(Source, source_id)

    async def create_run(self, session: AsyncSession, source_id: uuid.UUID) -> IngestionRun:
        run = IngestionRun(source_id=source_id, status="running")
        session.add(run)
        await session.commit()
        await session.refresh(run)
        return run

    async def get_active_run(
        self, session: AsyncSession, source_id: uuid.UUID
    ) -> IngestionRun | None:
        result = await session.execute(
            select(IngestionRun)
            .where(
                IngestionRun.source_id == source_id,
                IngestionRun.status == "running",
            )
            .order_by(IngestionRun.started_at.desc())
        )
        return result.scalars().first()

    async def get_run(self, session: AsyncSession, run_id: uuid.UUID) -> IngestionRun | None:
        return await session.get(IngestionRun, run_id)

    async def finish_run(
        self,
        session: AsyncSession,
        run: IngestionRun,
        *,
        status: str,
        fetched_count: int,
        error_count: int = 0,
        error_summary: dict | None = None,
    ) -> IngestionRun:
        run.status = status
        run.completed_at = datetime.now(timezone.utc)
        run.fetched_count = fetched_count
        run.normalized_count = fetched_count
        run.error_count = error_count
        run.error_summary = error_summary or {}
        await session.commit()
        await session.refresh(run)
        return run

    async def list_for_user(self, session: AsyncSession, user_id: uuid.UUID) -> list[Source]:
        result = await session.execute(select(Source).where(Source.user_id == user_id))
        return list(result.scalars().all())
