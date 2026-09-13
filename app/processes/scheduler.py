"""Scheduler process entrypoint."""

import asyncio
import logging

from sqlalchemy import select

from app.config import get_settings
from app.db import RuntimeResources
from app.dependencies.sources import build_ingestion_service
from app.domain.jobs.ingestion_service import IngestionService
from app.ingestion.models import Source
from app.workers.queue import enqueue_ingestion

logger = logging.getLogger(__name__)


async def schedule_due_sources(resources: RuntimeResources) -> int:
    async with resources.session_factory() as session:
        result = await session.execute(select(Source).where(Source.enabled.is_(True)))
        sources = list(result.scalars().all())
        service: IngestionService = build_ingestion_service(resources.redis)
        scheduled = 0
        for source in sources:
            if not _is_due(source):
                continue
            try:
                run = await service.start_run(session, source.id, source.user_id)
            except (LookupError, ValueError, RuntimeError):
                continue
            if not getattr(run, "already_running", False):
                await enqueue_ingestion(resources.redis, source.id, run.id)
                scheduled += 1
        return scheduled


def _is_due(source: Source) -> bool:
    from app.scheduler.service import is_due

    return is_due(source)


async def run_scheduler(
    stop_event: asyncio.Event | None = None, poll_seconds: int | None = None
) -> None:  # pragma: no cover
    settings = get_settings()
    resources = RuntimeResources(settings)
    interval = poll_seconds or settings.scheduler_poll_seconds
    try:
        logger.info("scheduler process started")
        while stop_event is None or not stop_event.is_set():
            await schedule_due_sources(resources)
            try:
                await asyncio.wait_for(
                    stop_event.wait() if stop_event is not None else asyncio.sleep(interval),
                    timeout=interval if stop_event is not None else None,
                )
            except asyncio.TimeoutError:
                pass
    finally:
        await resources.close()
        logger.info("scheduler process stopped")


def main() -> None:  # pragma: no cover
    asyncio.run(run_scheduler())


if __name__ == "__main__":  # pragma: no cover
    main()
