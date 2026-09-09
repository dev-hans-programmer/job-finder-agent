from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings


class RuntimeResources:
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_async_engine(settings.database_url, pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.redis: Redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def close(self) -> None:
        await self.redis.aclose()
        await self.engine.dispose()


@asynccontextmanager
async def session_scope(resources: RuntimeResources) -> AsyncGenerator[AsyncSession, None]:
    async with resources.session_factory() as session:
        yield session


async def check_postgres(resources: RuntimeResources) -> bool:
    try:
        async with resources.engine.connect() as connection:
            await connection.exec_driver_sql("SELECT 1")
        return True
    except Exception:
        return False


async def check_redis(resources: RuntimeResources) -> bool:
    try:
        return await resources.redis.ping()
    except Exception:
        return False
