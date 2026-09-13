from datetime import datetime

from pydantic import BaseModel

from app.domain.preferences.schemas import PreferenceInput


class V2PreferenceResponse(BaseModel):
    api_version: str = "v2"
    profile_id: str
    version: int
    status: str
    preferences: PreferenceInput
    matching_weights: dict[str, int]
    created_at: datetime | None


class V2PreferenceUpdate(BaseModel):
    preferences: PreferenceInput


def to_v2_response(profile) -> V2PreferenceResponse:
    return V2PreferenceResponse(
        profile_id=str(profile.id),
        version=profile.version,
        status="active" if profile.is_active else "inactive",
        preferences=PreferenceInput.model_validate(profile.config),
        matching_weights=profile.matching_weights,
        created_at=profile.created_at,
    )
