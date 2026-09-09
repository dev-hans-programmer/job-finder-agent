import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.jobs.ingestion_service import IngestionService
from app.ingestion.base import AdapterError, with_retries
from app.ingestion.models import IngestionRun, Source


@pytest.mark.asyncio
async def test_ingestion_service_creates_run():
    repository = AsyncMock()
    source = Source(
        id=uuid.uuid4(), kind="greenhouse", name="Demo", config={}, user_id=uuid.uuid4()
    )
    repository.get.return_value = source
    repository.get_active_run.return_value = None
    run = object()
    repository.create_run.return_value = run
    service = IngestionService(repository, {"greenhouse": object()})
    assert await service.start_run(AsyncMock(), source.id) is run


@pytest.mark.asyncio
async def test_ingestion_service_rejects_missing_or_unsupported_source():
    repository = AsyncMock()
    service = IngestionService(repository, {})
    repository.get.return_value = None
    repository.get_active_run.return_value = None
    with pytest.raises(LookupError):
        await service.start_run(AsyncMock(), uuid.uuid4())
    repository.get.return_value = Source(
        id=uuid.uuid4(), kind="unknown", name="Demo", config={}, user_id=uuid.uuid4()
    )
    with pytest.raises(ValueError, match="unsupported"):
        await service.start_run(AsyncMock(), uuid.uuid4())


@pytest.mark.asyncio
async def test_with_retries_success_retry_and_failures():
    calls = 0

    async def eventually_succeeds():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise AdapterError("temporary", retryable=True)
        return "ok"

    assert await with_retries(eventually_succeeds) == "ok"

    async def permanent_failure():
        raise AdapterError("permanent")

    with pytest.raises(AdapterError):
        await with_retries(permanent_failure)

    async def always_fails():
        raise AdapterError("temporary", retryable=True)

    with pytest.raises(AdapterError):
        await with_retries(always_fails, attempts=2)


class FakeAdapter:
    async def fetch(self, config):
        yield object()


class FailingAdapter:
    async def fetch(self, config):
        raise AdapterError("provider down", retryable=False)
        yield  # pragma: no cover


@pytest.mark.asyncio
async def test_ingestion_execution_records_success_and_failure():
    repository = AsyncMock()
    run = IngestionRun(id=uuid.uuid4(), source_id=uuid.uuid4(), status="running")
    repository.get_run.return_value = run
    success = IngestionService(repository, {"demo": FakeAdapter()})
    await success.execute_run(AsyncMock(), run.id, {}, "demo")
    assert repository.finish_run.await_args.kwargs["status"] == "succeeded"

    repository.reset_mock()
    repository.get_run.return_value = run
    failure = IngestionService(repository, {"demo": FailingAdapter()})
    with pytest.raises(AdapterError):
        await failure.execute_run(AsyncMock(), run.id, {}, "demo")
    assert repository.finish_run.await_args.kwargs["status"] == "failed"

    repository.reset_mock()
    repository.get_run.return_value = None
    await success.execute_run(AsyncMock(), run.id, {}, "demo")
    with pytest.raises(AdapterError):
        await failure.execute_run(AsyncMock(), run.id, {}, "demo")


@pytest.mark.asyncio
async def test_ingestion_source_lock():
    repository = AsyncMock()
    source = Source(
        id=uuid.uuid4(), kind="greenhouse", name="Demo", config={}, user_id=uuid.uuid4()
    )
    repository.get.return_value = source
    repository.get_active_run.return_value = None
    repository.create_run.return_value = object()
    redis = AsyncMock()
    redis.set.return_value = True
    service = IngestionService(repository, {"greenhouse": object()}, redis)
    await service.start_run(AsyncMock(), source.id)
    redis.set.assert_awaited_once()
    redis.set.return_value = False
    with pytest.raises(RuntimeError, match="already running"):
        await service.start_run(AsyncMock(), source.id)


@pytest.mark.asyncio
async def test_duplicate_active_run_is_returned():
    repository = AsyncMock()
    source = Source(
        id=uuid.uuid4(), kind="greenhouse", name="Demo", config={}, user_id=uuid.uuid4()
    )
    active = IngestionRun(id=uuid.uuid4(), source_id=source.id, status="running")
    repository.get.return_value = source
    repository.get_active_run.return_value = active
    service = IngestionService(repository, {"greenhouse": object()})
    assert await service.start_run(AsyncMock(), source.id) is active
    repository.create_run.assert_not_called()
