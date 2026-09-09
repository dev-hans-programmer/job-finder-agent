import uuid


def test_validate_preferences(client) -> None:
    response = client.post(
        "/api/v1/preferences/validate",
        json={"titles": ["Backend Engineer"], "work_mode": ["remote"]},
    )
    assert response.status_code == 200
    assert response.json()["titles"] == ["Backend Engineer"]


def test_validate_preferences_rejects_invalid_payload(client) -> None:
    response = client.post(
        "/api/v1/preferences/validate",
        json={"matching": {"minimum_score": 101}},
    )
    assert response.status_code == 422


def test_invalid_user_header_is_rejected(client) -> None:
    response = client.get("/api/v1/preferences", headers={"X-User-ID": "not-a-uuid"})
    assert response.status_code == 400
    assert response.json()["detail"] == "X-User-ID must be a UUID"


def test_create_and_get_active_preferences(client) -> None:
    user_id = str(uuid.uuid4())
    payload = {"titles": ["Backend Engineer"], "matching": {"minimum_score": 80}}
    created = client.put("/api/v1/preferences", headers={"X-User-ID": user_id}, json=payload)
    assert created.status_code == 201
    assert created.json()["version"] == 1
    assert created.json()["weights"]["skills"] == 40

    fetched = client.get("/api/v1/preferences", headers={"X-User-ID": user_id})
    assert fetched.status_code == 200
    assert fetched.json()["titles"] == ["Backend Engineer"]


def test_get_preferences_returns_not_found(client) -> None:
    response = client.get("/api/v1/preferences", headers={"X-User-ID": str(uuid.uuid4())})
    assert response.status_code == 404


def test_missing_user_header_uses_default_user(client) -> None:
    response = client.get("/api/v1/preferences")
    assert response.status_code in {200, 404}
