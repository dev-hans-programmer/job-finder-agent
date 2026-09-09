"""Database session dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import session_scope


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with session_scope(request.app.state.resources) as session:
        yield session
