def test_version_endpoint_returns_deployment_metadata(client):
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["application"] == "job-radar-agent"
    assert payload["data"]["environment"] == "testing"
    assert payload["data"]["commit_sha"] == "unknown"
    assert payload["meta"]["api_version"] == "v1"
