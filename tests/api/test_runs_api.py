import uuid


def test_run_status_not_found(client):
    response = client.get(f"/api/v1/runs/{uuid.uuid4()}")
    assert response.status_code == 404
