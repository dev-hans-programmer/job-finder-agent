import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.domain.preferences.schemas import DEFAULT_WEIGHTS, PreferenceInput, normalize_preferences
from app.domain.preferences.v2_service import V2PreferenceService
from app.errors.exceptions import ActivePreferenceNotFound


def test_preferences_normalize_and_defaults() -> None:
    preferences = PreferenceInput(titles=[" Backend Engineer "])
    assert preferences.titles == ["Backend Engineer"]
    assert preferences.matching.minimum_score == 75
    assert normalize_preferences(preferences)["titles"] == ["Backend Engineer"]
    assert sum(DEFAULT_WEIGHTS.values()) == 100


@pytest.mark.parametrize(
    "payload",
    [
        {"matching": {"minimum_score": 101}},
        {"experience": {"min": 10, "max": 5}},
        {"work_mode": ["distributed"]},
        {"titles": ["Backend", " backend "]},
        {"titles": [""]},
        {"unknown": True},
    ],
)
def test_invalid_preferences_are_rejected(payload) -> None:
    with pytest.raises(ValidationError):
        PreferenceInput.model_validate(payload)


@pytest.mark.asyncio
async def test_v2_preference_service_requires_an_active_profile() -> None:
    repository = SimpleNamespace(get_active=AsyncMock(return_value=None))
    service = V2PreferenceService(repository)
    with pytest.raises(ActivePreferenceNotFound):
        await service.get_active(None, uuid.uuid4())
