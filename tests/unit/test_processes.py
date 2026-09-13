import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.processes.api
from app.processes.scheduler import run_scheduler, schedule_due_sources
from app.processes.worker import run_worker
from app.workers.ingestion import process_ingestion_message
from app.workers.queue import INGESTION_QUEUE, dequeue, enqueue_ingestion


class Redis:
    def __init__(self, item=None):
        self.values = []
        self.item = item

    async def rpush(self, key, value):
        self.values.append((key, value))

    async def blpop(self, key, timeout):
        return self.item


@pytest.mark.asyncio
async def test_queue_round_trip_and_empty_poll():
    source_id, run_id = uuid.uuid4(), uuid.uuid4()
    redis = Redis()
    await enqueue_ingestion(redis, source_id, run_id)
    assert redis.values[0][0] == INGESTION_QUEUE
    redis.item = (INGESTION_QUEUE, redis.values[0][1])
    message = await dequeue(redis)
    assert message == {"type": "ingestion", "source_id": str(source_id), "run_id": str(run_id)}
    redis.item = None
    assert await dequeue(redis) is None


@pytest.mark.asyncio
async def test_process_ingestion_message_ignores_other_types_and_dispatches():
    resources = MagicMock()
    with patch("app.workers.ingestion.dispatch_ingestion_run", new_callable=AsyncMock) as dispatch:
        await process_ingestion_message(resources, {"type": "other"})
        dispatch.assert_not_awaited()
        source_id, run_id = uuid.uuid4(), uuid.uuid4()
        await process_ingestion_message(
            resources,
            {"type": "ingestion", "source_id": str(source_id), "run_id": str(run_id)},
        )
        dispatch.assert_awaited_once_with(resources, source_id, run_id)


class SessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, *_):
        return None


@pytest.mark.asyncio
async def test_scheduler_enqueues_only_due_sources():
    due = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        enabled=True,
        schedule="interval:60",
        last_success_at=None,
    )
    not_due = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        enabled=False,
        schedule="interval:60",
        last_success_at=None,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [due, not_due]
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    resources = MagicMock()
    resources.session_factory.return_value = SessionContext(session)
    run = SimpleNamespace(id=uuid.uuid4(), already_running=False)
    service = MagicMock()
    service.start_run = AsyncMock(return_value=run)
    with (
        patch("app.processes.scheduler.build_ingestion_service", return_value=service),
        patch("app.processes.scheduler.enqueue_ingestion", new_callable=AsyncMock) as enqueue,
    ):
        assert await schedule_due_sources(resources) == 1
    service.start_run.assert_awaited_once_with(session, due.id, due.user_id)
    enqueue.assert_awaited_once_with(resources.redis, due.id, run.id)


@pytest.mark.asyncio
async def test_scheduler_skips_start_errors_and_running_runs():
    source = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        enabled=True,
        schedule="interval:60",
        last_success_at=None,
    )
    result = MagicMock()
    result.scalars.return_value.all.return_value = [source]
    session = MagicMock()
    session.execute = AsyncMock(return_value=result)
    resources = MagicMock()
    resources.session_factory.return_value = SessionContext(session)
    service = MagicMock()
    service.start_run = AsyncMock(side_effect=RuntimeError("locked"))
    with patch("app.processes.scheduler.build_ingestion_service", return_value=service):
        assert await schedule_due_sources(resources) == 0
    service.start_run.side_effect = None
    service.start_run.return_value = SimpleNamespace(id=uuid.uuid4(), already_running=True)
    with (
        patch("app.processes.scheduler.build_ingestion_service", return_value=service),
        patch("app.processes.scheduler.enqueue_ingestion", new_callable=AsyncMock) as enqueue,
    ):
        assert await schedule_due_sources(resources) == 0
    enqueue.assert_not_awaited()


@pytest.mark.asyncio
async def test_worker_and_scheduler_shutdown_cleanly():
    settings = SimpleNamespace(scheduler_poll_seconds=1)
    resources = MagicMock()
    resources.redis = MagicMock()
    resources.close = AsyncMock()
    stop = asyncio.Event()

    async def process(resources, message):
        stop.set()

    with (
        patch("app.processes.worker.RuntimeResources", return_value=resources),
        patch("app.processes.worker.get_settings", return_value=settings),
        patch("app.processes.worker.dequeue", new_callable=AsyncMock, return_value={"type": "x"}),
        patch("app.processes.worker.process_ingestion_message", side_effect=process),
    ):
        await run_worker(stop)
    resources.close.assert_awaited_once()

    scheduler_resources = MagicMock()
    scheduler_resources.close = AsyncMock()
    scheduler_stop = asyncio.Event()

    async def scheduled(resources):
        scheduler_stop.set()
        return 0

    with (
        patch("app.processes.scheduler.RuntimeResources", return_value=scheduler_resources),
        patch("app.processes.scheduler.get_settings", return_value=settings),
        patch("app.processes.scheduler.schedule_due_sources", side_effect=scheduled),
    ):
        await run_scheduler(scheduler_stop, poll_seconds=1)
    scheduler_resources.close.assert_awaited_once()


def test_api_process_module_exposes_entrypoint():
    assert callable(app.processes.api.main)
