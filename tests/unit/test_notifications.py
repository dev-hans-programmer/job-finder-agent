# ruff: noqa: E501
import uuid
from types import SimpleNamespace

import pytest

from app.api.v1.notifications import get_delivery
from app.dependencies.notifications import get_notification_service
from app.domain.notifications.service import NotificationService
from app.notifications.base import NotificationMessage, is_retryable
from app.notifications.email import EmailProvider
from app.notifications.telegram import TelegramProvider
from app.notifications.whatsapp import WhatsAppProvider


class Session:
    async def commit(self):
        pass

    async def refresh(self, value):
        pass


class Repo:
    def __init__(self, row=None):
        self.row, self.created = row, row is None

    async def get_or_create(self, session, **values):
        if self.row is None:
            self.row = SimpleNamespace(
                **values,
                status="pending",
                attempt_count=0,
                provider_message_id=None,
                error=None,
                id=uuid.uuid4(),
            )
            return self.row, True
        return self.row, False

    async def get(self, session, delivery_id):
        return self.row


class Provider:
    async def send(self, message):
        return "provider-1"


def match(decision="notify"):
    return SimpleNamespace(
        decision=decision, score=90, matched_criteria=["Python"], missing_criteria=[], concerns=[]
    )


def job():
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="Backend",
        company_name="Acme",
        locations=["Mumbai"],
        work_mode="hybrid",
        application_url="https://apply",
    )


@pytest.mark.asyncio
async def test_notification_delivery_and_idempotency():
    service, session = NotificationService(Repo()), Session()
    row = await service.deliver(
        session, uuid.uuid4(), job(), uuid.uuid4(), match(), "email", Provider()
    )
    assert row.status == "delivered" and row.attempt_count == 1
    again = await service.deliver(
        session, uuid.uuid4(), job(), uuid.uuid4(), match("review"), "email", Provider()
    )
    assert again is None
    existing = Repo(SimpleNamespace(id=uuid.uuid4(), status="delivered", attempt_count=1))
    assert (
        await NotificationService(existing).deliver(
            session, uuid.uuid4(), job(), uuid.uuid4(), match(), "email", Provider()
        )
        is existing.row
    )
    assert isinstance(get_notification_service(), NotificationService)


@pytest.mark.asyncio
async def test_retryable_and_permanent_provider_errors():
    class Failing:
        def __init__(self, error):
            self.error = error

        async def send(self, message):
            raise self.error

    for error, expected in [(TimeoutError("timeout"), "retryable"), (ValueError("bad"), "failed")]:
        service = NotificationService(Repo())
        row = await service.deliver(
            Session(), uuid.uuid4(), job(), uuid.uuid4(), match(), "email", Failing(error)
        )
        assert row.status == expected
    assert (
        await NotificationService(Repo()).deliver(
            Session(), uuid.uuid4(), job(), uuid.uuid4(), match("reject"), "email", Provider()
        )
        is None
    )


def test_retry_classification_and_providers():
    assert is_retryable(TimeoutError()) and is_retryable(ConnectionError())
    assert is_retryable(SimpleNamespace(status_code=429)) and is_retryable(
        SimpleNamespace(status_code=503)
    )
    assert not is_retryable(SimpleNamespace(status_code=400)) and not is_retryable(ValueError())
    with pytest.raises(ValueError):
        import asyncio

        asyncio.run(EmailProvider("bad").send(NotificationMessage("s", "b")))
    import asyncio

    assert asyncio.run(
        EmailProvider("a@example.com").send(NotificationMessage("s", "b"))
    ).startswith("outbox:")
    with pytest.raises(NotImplementedError):
        import asyncio

        asyncio.run(WhatsAppProvider().send(NotificationMessage("s", "b")))


@pytest.mark.asyncio
async def test_telegram_provider_success_and_validation():
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"result": {"message_id": 7}}

    class Client:
        async def post(self, *args, **kwargs):
            return Response()

    assert (
        await TelegramProvider("token", "chat", Client()).send(NotificationMessage("s", "b")) == "7"
    )
    with pytest.raises(ValueError):
        await TelegramProvider("", "chat", Client()).send(NotificationMessage("s", "b"))


@pytest.mark.asyncio
async def test_notification_api_status():
    repo = Repo(
        SimpleNamespace(
            id=uuid.uuid4(),
            channel="email",
            status="delivered",
            attempt_count=1,
            provider_message_id="x",
            error=None,
        )
    )
    service = NotificationService(repo)
    response = await get_delivery(uuid.uuid4(), None, service)
    assert response["status"] == "delivered"
    repo.row = None
    with pytest.raises(Exception):
        await get_delivery(uuid.uuid4(), None, service)
