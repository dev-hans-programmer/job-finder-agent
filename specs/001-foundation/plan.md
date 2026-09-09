# Implementation plan

1. Create `pyproject.toml`, application package, and test configuration.
2. Add typed settings with environment validation.
3. Implement async SQLAlchemy engine/session and Redis client factories.
4. Implement FastAPI factory, middleware, exception handlers, and health routers.
5. Add Docker Compose and `.env.example` for PostgreSQL and Redis.
6. Initialize Alembic and configure migration test fixtures.
7. Add unit and service-container API tests, then enforce branch coverage.

Database changes: none beyond Alembic baseline.

Verification: run formatting/linting, unit tests, container-backed integration tests, `alembic upgrade head`, and coverage with `--cov-branch --cov-fail-under=100` for foundation scope.
