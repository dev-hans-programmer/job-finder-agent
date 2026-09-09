import pytest
from pydantic import ValidationError

from app.domain.preferences.schemas import DEFAULT_WEIGHTS, PreferenceInput, normalize_preferences


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
