"""Ingestion worker execution boundary."""

import uuid

from app.db import RuntimeResources
from app.dependencies.sources import build_ingestion_service


async def dispatch_ingestion_run(
    resources: RuntimeResources, source_id: uuid.UUID, run_id: uuid.UUID
) -> None:
    async with resources.session_factory() as session:
        service = build_ingestion_service(resources.redis)
        source = await service.repository.get(session, source_id)
        if source is None:
            return
        try:
            await service.execute_run(session, run_id, source.config, source.kind, source_id)
        except Exception:
            # The run record contains the failure details; background task failures
            # must not turn an already accepted HTTP request into a 500 response.
            return
