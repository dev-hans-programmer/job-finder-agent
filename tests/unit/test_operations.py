import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.metrics import metrics
from app.api.v1.users import delete_me
from app.dependencies.deletion import get_deletion_service
from app.domain.preferences.deletion_service import DeletionService
from app.observability.logging import redact
from app.observability.metrics import increment, snapshot
from app.repositories.sources import SourceRepository


class Session:
    def __init__(self, user=None):
        self.user = user
        self.deleted = None

    async def get(self, model, user_id):
        return self.user

    async def delete(self, user):
        self.deleted = user

    def add(self, value):
        pass

    async def commit(self):
        pass

    async def flush(self):
        pass


@pytest.mark.asyncio
async def test_metrics_redaction_and_deletion():
    assert isinstance(get_deletion_service(), DeletionService)
    increment("runs_total")
    assert snapshot()["runs_total"] >= 1
    assert "[REDACTED]" in redact("token=abc password=xyz")
    assert "abc" not in redact("token=abc")
    user = SimpleNamespace(id=uuid.uuid4())
    session = Session(user)
    assert await DeletionService().delete_user(session, user.id)
    assert not await DeletionService().delete_user(Session(), uuid.uuid4())
    assert await metrics()
    assert await delete_me(user.id, Session(user), DeletionService()) is None
    with pytest.raises(HTTPException):
        await delete_me(uuid.uuid4(), Session(), DeletionService())


@pytest.mark.asyncio
async def test_source_repository_provisions_missing_user():
    class SourceSession(Session):
        async def refresh(self, value):
            value.id = uuid.uuid4()

    session = SourceSession()
    created = await SourceRepository().create(
        session, uuid.uuid4(), {"kind": "test", "name": "Demo", "config": {}}
    )
    assert created.name == "Demo"
