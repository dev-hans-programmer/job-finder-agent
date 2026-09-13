"""Small Redis queue boundary used until the Celery worker is introduced."""

import json
import uuid
from typing import Any

from redis.asyncio import Redis

INGESTION_QUEUE = "job-radar:queue:ingestion"


async def enqueue_ingestion(redis: Redis, source_id: uuid.UUID, run_id: uuid.UUID) -> None:
    await redis.rpush(
        INGESTION_QUEUE,
        json.dumps(
            {
                "type": "ingestion",
                "source_id": str(source_id),
                "run_id": str(run_id),
            }
        ),
    )


async def dequeue(redis: Redis, timeout: int = 1) -> dict[str, Any] | None:
    item = await redis.blpop(INGESTION_QUEUE, timeout=timeout)
    if item is None:
        return None
    _, raw = item
    return json.loads(raw)
