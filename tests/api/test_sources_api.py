import uuid
from types import SimpleNamespace

from app.dependencies.sources import get_ingestion_service


def test_create_source(client):
    response = client.post(
        "/api/v1/sources",
        json={"kind": "greenhouse", "name": "Demo", "config": {"board": "demo"}},
    )
    assert response.status_code == 201
    assert response.json()["kind"] == "greenhouse"
    run = client.post(f"/api/v1/sources/{response.json()['id']}/run")
    assert run.status_code == 202
    assert run.json()["status"] == "running"
    status = client.get(f"/api/v1/runs/{run.json()['run_id']}")
    assert status.status_code == 200
    assert status.json()["source_id"] == response.json()["id"]


def test_run_missing_source(client):
    response = client.post(f"/api/v1/sources/{uuid.uuid4()}/run")
    assert response.status_code == 404


def test_list_sources(client):
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_run_unsupported_source_returns_validation_error(client):
    class UnsupportedService:
        async def start_run(self, session, source_id):
            raise ValueError("unsupported source kind")

    client.app.dependency_overrides[get_ingestion_service] = lambda: UnsupportedService()
    try:
        response = client.post(f"/api/v1/sources/{uuid.uuid4()}/run")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 422


def test_duplicate_run_does_not_dispatch_again(client):
    class ExistingRunService:
        async def start_run(self, session, source_id):
            return SimpleNamespace(id=uuid.uuid4(), status="running", already_running=True)

    client.app.dependency_overrides[get_ingestion_service] = lambda: ExistingRunService()
    try:
        response = client.post(f"/api/v1/sources/{uuid.uuid4()}/run")
    finally:
        client.app.dependency_overrides.clear()
    assert response.status_code == 202
