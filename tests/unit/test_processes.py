import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.processes.api
import app.processes.worker
from app.processes.scheduler import schedule_due_sources
from app.workers.celery_app import celery_app
from app.workers.tasks.ingestion import _run_ingestion, run_ingestion


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
        patch("app.processes.scheduler.run_ingestion.delay") as enqueue,
    ):
        assert await schedule_due_sources(resources) == 1
    service.start_run.assert_awaited_once_with(session, due.id, due.user_id)
    enqueue.assert_called_once_with(str(due.id), str(run.id))


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
        patch("app.processes.scheduler.run_ingestion.delay") as enqueue,
    ):
        assert await schedule_due_sources(resources) == 0
    enqueue.assert_not_called()


def test_api_process_module_exposes_entrypoint():
    assert callable(app.processes.api.main)
    assert callable(app.processes.worker.main)


def test_celery_is_configured_for_reliable_json_tasks():
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.task_track_started is True
    assert run_ingestion.name == "job_radar.ingestion"
    assert run_ingestion.max_retries == 3


@pytest.mark.asyncio
async def test_celery_ingestion_task_skips_missing_source_and_completes():
    resources = MagicMock()
    resources.close = AsyncMock()
    session = MagicMock()
    resources.session_factory.return_value = SessionContext(session)
    service = MagicMock()
    service.repository.get = AsyncMock(return_value=None)
    with (
        patch("app.workers.tasks.ingestion.RuntimeResources", return_value=resources),
        patch("app.workers.tasks.ingestion.build_ingestion_service", return_value=service),
        patch("app.workers.tasks.ingestion.get_settings", return_value=SimpleNamespace()),
    ):
        result = await _run_ingestion(str(uuid.uuid4()), str(uuid.uuid4()))
    assert result["status"] == "skipped"
    resources.close.assert_awaited_once()

    source = SimpleNamespace(id=uuid.uuid4(), config={}, kind="greenhouse", name="Demo")
    service.repository.get = AsyncMock(return_value=source)
    with (
        patch("app.workers.tasks.ingestion.RuntimeResources", return_value=resources),
        patch("app.workers.tasks.ingestion.build_ingestion_service", return_value=service),
        patch("app.workers.tasks.ingestion.get_settings", return_value=SimpleNamespace()),
        patch("app.workers.tasks.ingestion.execute_ingestion_run", new_callable=AsyncMock),
    ):
        result = await _run_ingestion(str(source.id), str(uuid.uuid4()))
    assert result["status"] == "completed"


def test_celery_task_wrapper_runs_async_body():
    with patch("app.workers.tasks.ingestion._run_ingestion", new_callable=AsyncMock) as run:
        run.return_value = {"status": "completed"}
        assert run_ingestion.run(str(uuid.uuid4()), str(uuid.uuid4()))["status"] == "completed"
