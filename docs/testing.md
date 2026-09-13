# Testing environment

Tests use an isolated environment and must not connect to development, staging, or production data.

| Dependency | Testing value |
|---|---|
| Environment | `APP_ENV=testing` |
| PostgreSQL database | `jobradar_test` |
| PostgreSQL user | `jobradar_test` |
| PostgreSQL port | `5433` |
| Redis port | `6380` |
| Redis database | `1` |
| Compose project | `job-radar-testing` |

Start and migrate the services with:

```bash
make test-services-up
make test-migrate
```

For a single command that starts the isolated services, applies migrations, runs all checks, and cleans up even when checks fail:

```bash
make test-all
```

Pytest sets `APP_ENV`, `TEST_DATABASE_URL`, and `TEST_REDIS_URL` before importing the application. This prevents a developer's `.env` from changing the test target. CI provisions the same isolated values directly in GitHub Actions service containers.

Unit tests use mocks where appropriate; integration and API tests use only the isolated testing services.
