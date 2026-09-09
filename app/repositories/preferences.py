"""Persistence operations for preference profiles."""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.preferences.models import PreferenceProfile, User


class PreferenceRepository:
    async def ensure_user(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        if await session.get(User, user_id) is None:
            session.add(User(id=user_id))
            await session.flush()

    async def get_active(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> PreferenceProfile | None:
        result = await session.execute(
            select(PreferenceProfile).where(
                PreferenceProfile.user_id == user_id,
                PreferenceProfile.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_version(self, session: AsyncSession, user_id: uuid.UUID) -> int:
        return (
            await session.scalar(
                select(func.max(PreferenceProfile.version)).where(
                    PreferenceProfile.user_id == user_id
                )
            )
            or 0
        )

    async def deactivate_active(self, session: AsyncSession, user_id: uuid.UUID) -> None:
        await session.execute(
            update(PreferenceProfile)
            .where(
                PreferenceProfile.user_id == user_id,
                PreferenceProfile.is_active.is_(True),
            )
            .values(is_active=False)
        )

    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        version: int,
        config: dict,
        matching_weights: dict,
    ) -> PreferenceProfile:
        profile = PreferenceProfile(
            user_id=user_id,
            version=version,
            config=config,
            matching_weights=matching_weights,
            is_active=True,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        return profile
