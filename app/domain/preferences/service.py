"""Preference profile business operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.preferences.schemas import (
    DEFAULT_WEIGHTS,
    PreferenceInput,
    PreferenceResponse,
    normalize_preferences,
)
from app.repositories.preferences import PreferenceRepository


class PreferenceService:
    def __init__(self, repository: PreferenceRepository):
        self.repository = repository

    async def get_active(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> PreferenceResponse | None:
        profile = await self.repository.get_active(session, user_id)
        if profile is None:
            return None
        return PreferenceResponse(
            **profile.config,
            version=profile.version,
            is_active=profile.is_active,
            weights=profile.matching_weights,
        )

    async def update(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        preferences: PreferenceInput,
    ) -> PreferenceResponse:
        await self.repository.ensure_user(session, user_id)
        version = await self.repository.get_latest_version(session, user_id) + 1
        await self.repository.deactivate_active(session, user_id)
        profile = await self.repository.create(
            session,
            user_id=user_id,
            version=version,
            config=normalize_preferences(preferences),
            matching_weights=DEFAULT_WEIGHTS.copy(),
        )
        return PreferenceResponse(
            **profile.config,
            version=profile.version,
            is_active=profile.is_active,
            weights=profile.matching_weights,
        )
