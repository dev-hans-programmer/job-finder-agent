def test_v2_preferences_are_enveloped_and_versioned(client):
    response = client.put(
        "/api/v2/preferences",
        json={"preferences": {"titles": ["Staff Backend Engineer"]}},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["meta"]["api_version"] == "v2"
    assert payload["data"]["status"] == "active"
    assert payload["data"]["preferences"]["titles"] == ["Staff Backend Engineer"]
    fetched = client.get("/api/v2/preferences")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["profile_id"] == payload["data"]["profile_id"]


def test_v2_preferences_missing_profile_returns_not_found(client):
    from app.api.v2.preferences import get_preferences_v2
    from app.errors.exceptions import ActivePreferenceNotFound

    class EmptyService:
        async def get_active(self, session, user_id):
            raise ActivePreferenceNotFound()

    import asyncio

    try:
        asyncio.run(get_preferences_v2(None, None, None, EmptyService()))
    except ActivePreferenceNotFound:
        pass
    else:
        raise AssertionError("expected not found")
