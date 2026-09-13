"""Worker process entrypoint."""

import asyncio
import logging

from app.config import get_settings
from app.db import RuntimeResources
from app.workers.ingestion import process_ingestion_message
from app.workers.queue import dequeue

logger = logging.getLogger(__name__)


async def run_worker(stop_event: asyncio.Event | None = None) -> None:  # pragma: no cover
    resources = RuntimeResources(get_settings())
    try:
        logger.info("worker process started")
        while stop_event is None or not stop_event.is_set():
            message = await dequeue(resources.redis)
            if message is not None:
                try:
                    await process_ingestion_message(resources, message)
                except Exception:
                    logger.exception("worker message failed")
    finally:
        await resources.close()
        logger.info("worker process stopped")


def main() -> None:  # pragma: no cover
    asyncio.run(run_worker())


if __name__ == "__main__":  # pragma: no cover
    main()
