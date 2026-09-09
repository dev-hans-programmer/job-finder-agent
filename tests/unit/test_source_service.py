import uuid
from unittest.mock import AsyncMock

import pytest

from app.domain.jobs.source_service import SourceService
from app.ingestion.models import Source
from app.ingestion.schemas import SourceInput


@pytest.mark.asyncio
async def test_source_service_delegates_creation_and_maps_response():
    repository = AsyncMock()
    source_id = uuid.uuid4()
    repository.create.return_value = Source(
        id=source_id,
        user_id=uuid.uuid4(),
        kind="greenhouse",
        name="Demo",
        config={"board": "demo"},
        enabled=True,
    )
    service = SourceService(repository)
    source = SourceInput(kind="greenhouse", name="Demo", config={"board": "demo"})

    response = await service.create(AsyncMock(), uuid.uuid4(), source)

    assert response.id == str(source_id)
    assert response.kind == "greenhouse"
    repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_source_service_lists_sources():
    repository = AsyncMock()
    repository.list_for_user.return_value = []
    service = SourceService(repository)
    assert await service.list(AsyncMock(), uuid.uuid4()) == []
