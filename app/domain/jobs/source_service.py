"""Source configuration business operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.schemas import SourceInput, SourceResponse
from app.repositories.sources import SourceRepository


class SourceService:
    def __init__(self, repository: SourceRepository):
        self.repository = repository

    async def create(
        self, session: AsyncSession, user_id: uuid.UUID, source: SourceInput
    ) -> SourceResponse:
        created = await self.repository.create(session, user_id, source.model_dump())
        return SourceResponse(id=str(created.id), **source.model_dump())

    async def list(self, session: AsyncSession, user_id: uuid.UUID) -> list[SourceResponse]:
        sources = await self.repository.list_for_user(session, user_id)
        return [
            SourceResponse(
                id=str(source.id),
                kind=source.kind,
                name=source.name,
                config=source.config,
                schedule=source.schedule,
                enabled=source.enabled,
            )
            for source in sources
        ]
