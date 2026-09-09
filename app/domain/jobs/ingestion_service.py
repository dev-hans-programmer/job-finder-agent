import uuid
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.base import AdapterError, SourceAdapter, with_retries
from app.ingestion.models import IngestionRun
from app.repositories.sources import SourceRepository


class IngestionService:
    def __init__(
        self,
        repository: SourceRepository,
        adapters: dict[str, SourceAdapter],
        redis: Redis | None = None,
    ):
        self.repository = repository
        self.adapters = adapters
        self.redis = redis

    async def start_run(self, session: AsyncSession, source_id: uuid.UUID) -> IngestionRun:
        source = await self.repository.get(session, source_id)
        if source is None:
            raise LookupError("source not found")
        if source.kind not in self.adapters:
            raise ValueError(f"unsupported source kind: {source.kind}")
        active = await self.repository.get_active_run(session, source_id)
        if active is not None:
            setattr(active, "already_running", True)
            return active
        if self.redis is not None:
            lock = await self.redis.set(f"ingestion:source:{source_id}", "1", nx=True, ex=900)
            if not lock:
                raise RuntimeError("source ingestion is already running")
        return await self.repository.create_run(session, source_id)

    async def execute_run(
        self,
        session: AsyncSession,
        run_id: uuid.UUID,
        config: dict[str, Any],
        kind: str,
        source_id: uuid.UUID | None = None,
    ) -> None:
        adapter = self.adapters[kind]
        fetched: list[Any] = []
        try:

            async def collect():
                async for record in adapter.fetch(config):
                    fetched.append(record)

            await with_retries(collect)
            run = await self.repository.get_run(session, run_id)
            if run is not None:
                malformed_count = getattr(adapter, "malformed_count", 0)
                await self.repository.finish_run(
                    session,
                    run,
                    status="partial" if malformed_count else "succeeded",
                    fetched_count=len(fetched),
                    error_count=malformed_count,
                    error_summary={"malformed_records": malformed_count} if malformed_count else {},
                )
        except AdapterError as error:
            run = await self.repository.get_run(session, run_id)
            if run is not None:
                await self.repository.finish_run(
                    session,
                    run,
                    status="failed",
                    fetched_count=len(fetched),
                    error_count=1,
                    error_summary={"message": str(error)},
                )
            raise
        finally:
            if self.redis is not None and source_id is not None:
                await self.redis.delete(f"ingestion:source:{source_id}")
