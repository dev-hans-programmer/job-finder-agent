"""Automated backup process entrypoint."""

import asyncio
import logging

from app.backup.service import backup_once
from app.config import get_settings

logger = logging.getLogger(__name__)


async def run_backup_process(stop_event: asyncio.Event | None = None) -> None:  # pragma: no cover
    settings = get_settings()
    while stop_event is None or not stop_event.is_set():
        result = backup_once(settings)
        logger.info("database backup created: %s", result.dump_path)
        try:
            await asyncio.wait_for(
                stop_event.wait()
                if stop_event is not None
                else asyncio.sleep(settings.backup_interval_seconds),
                timeout=settings.backup_interval_seconds if stop_event is not None else None,
            )
        except asyncio.TimeoutError:
            pass


def main() -> None:  # pragma: no cover
    asyncio.run(run_backup_process())


if __name__ == "__main__":  # pragma: no cover
    main()
