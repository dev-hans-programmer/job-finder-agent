import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.preferences.schemas import DEFAULT_WEIGHTS, normalize_preferences
from app.domain.preferences.v2_schemas import V2PreferenceResponse, to_v2_response
from app.repositories.preferences import PreferenceRepository


class V2PreferenceService:
    def __init__(self, repository: PreferenceRepository):
        self.repository = repository

    async def get_active(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> V2PreferenceResponse | None:
        profile = await self.repository.get_active(session, user_id)
        return None if profile is None else to_v2_response(profile)

    async def update(
        self, session: AsyncSession, user_id: uuid.UUID, preferences
    ) -> V2PreferenceResponse:
        await self.repository.ensure_user(session, user_id)
        version = await self.repository.get_latest_version(session, user_id) + 1
        await self.repository.deactivate_active(session, user_id)
        profile = await self.repository.create(
            session,
            user_id=user_id,
            version=version,
            config=normalize_preferences(preferences.preferences),
            matching_weights=DEFAULT_WEIGHTS.copy(),
        )
        return to_v2_response(profile)
