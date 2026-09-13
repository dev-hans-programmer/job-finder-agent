"""Small scheduler boundary that can be replaced by APScheduler/Celery later."""

from datetime import datetime, timedelta, timezone


def interval_seconds(schedule: str | None) -> int | None:
    if not schedule or not schedule.startswith("interval:"):
        return None
    try:
        value = int(schedule.split(":", 1)[1])
    except ValueError:
        return None
    return value if value > 0 else None


def is_due(source, now: datetime | None = None) -> bool:
    seconds = interval_seconds(source.schedule)
    if seconds is None or not source.enabled:
        return False
    if source.last_success_at is None:
        return True
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    last = source.last_success_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return current >= last + timedelta(seconds=seconds)


class SchedulerService:
    def __init__(self, source_service, runner):
        self.source_service, self.runner = source_service, runner

    async def tick(self, session, user_id, now=None) -> list:
        results = []
        for source in await self.source_service.list(session, user_id):
            if is_due(source, now):
                try:
                    results.append(await self.runner(session, source))
                except Exception as error:
                    results.append(error)
        return results
