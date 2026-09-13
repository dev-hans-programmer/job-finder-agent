from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.scheduler.service import SchedulerService, interval_seconds, is_due
from app.workers.notifications import run_with_dead_letter
from app.workers.workflow import run_source_workflow


def source(**kwargs):
    values = {"schedule": "interval:60", "enabled": True, "last_success_at": None, "id": "s1"}
    values.update(kwargs)
    return SimpleNamespace(**values)


def test_schedule_due_boundaries():
    assert interval_seconds("interval:60") == 60
    assert interval_seconds(None) is None and interval_seconds("cron:*") is None
    assert interval_seconds("interval:nope") is None and interval_seconds("interval:0") is None
    assert is_due(source())
    now = datetime.now(timezone.utc)
    assert not is_due(source(enabled=False), now)
    assert not is_due(source(last_success_at=now), now)
    assert is_due(source(last_success_at=now - timedelta(seconds=61)), now)


@pytest.mark.asyncio
async def test_scheduler_isolates_failures_and_workflow_stages():
    async def list_sources(session, user):
        return [
            source(id="a"),
            source(id="b"),
            source(id="c", schedule="cron:*"),
            source(id="d", enabled=False),
        ]

    async def runner(session, item):
        if item.id == "a":
            raise RuntimeError("failed")
        return "ok"

    results = await SchedulerService(SimpleNamespace(list=list_sources), runner).tick(None, "u")
    assert len(results) == 2 and isinstance(results[0], RuntimeError)

    async def stage(value):
        async def run(session, item):
            return value

        return run

    item = await run_source_workflow(
        None, source(), await stage("ingest"), await stage("match"), await stage("notify")
    )
    assert item["notifications"] == "notify"
    minimal = await run_source_workflow(None, source(), await stage("ingest"))
    assert "matching" not in minimal
    assert is_due(source(last_success_at=datetime.now()), datetime.now()) is False


@pytest.mark.asyncio
async def test_dead_letter_retry_policy():
    count = 0

    async def operation():
        nonlocal count
        count += 1
        raise TimeoutError("down")

    result = await run_with_dead_letter(operation, max_attempts=2)
    assert result["status"] == "dead_letter" and result["attempts"] == 2

    async def permanent():
        raise ValueError("bad")

    result = await run_with_dead_letter(permanent)
    assert result["attempts"] == 1
    assert await run_with_dead_letter(permanent, max_attempts=0) is None
