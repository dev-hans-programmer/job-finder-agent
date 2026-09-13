"""Ingestion worker execution boundary."""

import uuid
from typing import Any

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
            await service.execute_run(
                session, run_id, source.config, source.kind, source_id, source.name
            )
        except Exception:
            # The run record contains the failure details; worker failures must
            # not terminate the process or make the API request fail.
            return


async def process_ingestion_message(resources: RuntimeResources, message: dict[str, Any]) -> None:
    if message.get("type") != "ingestion":
        return
    await dispatch_ingestion_run(
        resources,
        uuid.UUID(message["source_id"]),
        uuid.UUID(message["run_id"]),
    )
