from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.db import RuntimeResources, check_postgres, check_redis, session_scope
from app.errors.exceptions import PersistenceFailure


@pytest.fixture
def resources():
    with (
        patch("app.db.create_async_engine") as create_engine,
        patch("app.db.Redis.from_url") as from_url,
    ):
        engine = MagicMock()
        engine.dispose = AsyncMock()
        redis = AsyncMock()
        create_engine.return_value = engine
        from_url.return_value = redis
        value = RuntimeResources(
            Settings(
                database_url="postgresql+asyncpg://x",
                redis_url="redis://x",
                otel_enabled=False,
            )
        )
        yield value, engine, redis


@pytest.mark.asyncio
async def test_database_health_success(resources):
    value, engine, _ = resources
    connection = AsyncMock()
    engine.connect.return_value.__aenter__.return_value = connection
    assert await check_postgres(value) is True
    connection.exec_driver_sql.assert_awaited_once_with("SELECT 1")


@pytest.mark.asyncio
async def test_database_health_failure(resources):
    value, engine, _ = resources
    engine.connect.side_effect = RuntimeError("down")
    assert await check_postgres(value) is False


@pytest.mark.asyncio
async def test_redis_health_success_and_failure(resources):
    value, _, redis = resources
    redis.ping.return_value = True
    assert await check_redis(value) is True
    redis.ping.side_effect = RuntimeError("down")
    assert await check_redis(value) is False


@pytest.mark.asyncio
async def test_resources_close(resources):
    value, engine, redis = resources
    await value.close()
    redis.aclose.assert_awaited_once()
    engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_scope(resources):
    value, _, _ = resources
    session = AsyncMock()
    value.session_factory = MagicMock(return_value=session)
    session.__aenter__.return_value = session
    async with session_scope(value) as current:
        assert current is session
    session.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_scope_translates_sqlalchemy_errors(resources):
    value, _, _ = resources
    session = AsyncMock()

    class SessionContext:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *_):
            return False

    value.session_factory = MagicMock(return_value=SessionContext())
    with pytest.raises(PersistenceFailure):
        async with session_scope(value) as current:
            assert current is session
            raise SQLAlchemyError("query failed")
    session.rollback.assert_awaited_once()
