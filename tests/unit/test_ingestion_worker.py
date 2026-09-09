import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.ingestion import dispatch_ingestion_run


@pytest.mark.asyncio
async def test_worker_ignores_missing_source():
    session = AsyncMock()
    service = MagicMock()
    service.repository.get = AsyncMock(return_value=None)
    resources = MagicMock()
    resources.session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
    resources.session_factory.return_value.__aexit__ = AsyncMock()
    with patch("app.workers.ingestion.build_ingestion_service", return_value=service):
        await dispatch_ingestion_run(resources, uuid.uuid4(), uuid.uuid4())
    service.execute_run.assert_not_called()


@pytest.mark.asyncio
async def test_worker_swallows_background_failure():
    session = AsyncMock()
    service = MagicMock()
    service.repository.get = AsyncMock(return_value=MagicMock(config={}, kind="greenhouse"))
    service.execute_run = AsyncMock(side_effect=RuntimeError("worker failed"))
    resources = MagicMock()
    resources.session_factory.return_value.__aenter__ = AsyncMock(return_value=session)
    resources.session_factory.return_value.__aexit__ = AsyncMock()
    with patch("app.workers.ingestion.build_ingestion_service", return_value=service):
        await dispatch_ingestion_run(resources, uuid.uuid4(), uuid.uuid4())
    service.execute_run.assert_awaited_once()
