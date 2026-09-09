import httpx
import pytest

from app.ingestion.greenhouse import GreenhouseAdapter
from app.ingestion.lever import LeverAdapter


@pytest.mark.asyncio
async def test_greenhouse_adapter_maps_fixture(monkeypatch):
    async def fake_get_json(client, url, **kwargs):
        return {
            "jobs": [
                {
                    "id": 1,
                    "title": "Backend",
                    "content": "Python",
                    "absolute_url": "https://apply",
                    "location": {"name": "Mumbai"},
                }
            ]
        }

    monkeypatch.setattr("app.ingestion.greenhouse.adapter.get_json", fake_get_json)
    records = [record async for record in GreenhouseAdapter().fetch({"board": "demo"})]
    assert records[0].external_id == "1"
    assert records[0].location == "Mumbai"


@pytest.mark.asyncio
async def test_greenhouse_pagination_and_malformed(monkeypatch):
    responses = iter([{"jobs": [{"title": "Malformed"}]}, {"jobs": []}])

    async def fake_get_json(client, url, **kwargs):
        return next(responses)

    monkeypatch.setattr("app.ingestion.greenhouse.adapter.get_json", fake_get_json)
    adapter = GreenhouseAdapter()
    records = [record async for record in adapter.fetch({"board": "demo", "max_pages": 2})]
    assert len(records) == 0
    assert adapter.malformed_count == 1


@pytest.mark.asyncio
async def test_lever_adapter_maps_fixture(monkeypatch):
    async def fake_get_json(client, url, **kwargs):
        return [
            {
                "id": "a",
                "text": "Backend",
                "descriptionPlain": "Python",
                "hostedUrl": "https://apply",
                "categories": {"location": "Remote"},
            }
        ]

    monkeypatch.setattr("app.ingestion.lever.adapter.get_json", fake_get_json)
    records = [record async for record in LeverAdapter().fetch({"account": "demo"})]
    assert records[0].external_id == "a"
    assert records[0].location == "Remote"


@pytest.mark.asyncio
async def test_lever_pagination_and_malformed(monkeypatch):
    responses = iter([[{"id": "a"}], []])

    async def fake_get_json(client, url, **kwargs):
        return next(responses)

    monkeypatch.setattr("app.ingestion.lever.adapter.get_json", fake_get_json)
    adapter = LeverAdapter()
    records = [record async for record in adapter.fetch({"account": "demo", "max_pages": 2})]
    assert len(records) == 0
    assert adapter.malformed_count == 1


@pytest.mark.asyncio
async def test_adapter_error_classification():
    from app.ingestion.base import AdapterError, get_json

    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(503, request=request)

    class Client:
        async def get(self, url):
            return response

    with pytest.raises(AdapterError, match="503") as error:
        await get_json(Client(), "https://example.test")
    assert error.value.retryable is True


@pytest.mark.asyncio
async def test_adapter_error_for_client_and_json_failures():
    from app.ingestion.base import AdapterError, get_json

    class FailingClient:
        async def get(self, url):
            raise httpx.ConnectError("down", request=httpx.Request("GET", url))

    with pytest.raises(AdapterError, match="request failed") as error:
        await get_json(FailingClient(), "https://example.test")
    assert error.value.retryable is True

    request = httpx.Request("GET", "https://example.test")

    class ClientError:
        async def get(self, url):
            return httpx.Response(404, request=request)

    with pytest.raises(AdapterError, match="404") as error:
        await get_json(ClientError(), "https://example.test")
    assert error.value.retryable is False

    from app.ingestion.base import RateLimiter

    await RateLimiter(0.00001).wait()

    class ClientSuccess:
        async def get(self, url):
            return httpx.Response(200, request=request, json={"ok": True})

    assert await get_json(ClientSuccess(), "https://example.test") == {"ok": True}
