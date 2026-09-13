# QA — Test environment isolation

## Start isolated test services

```bash
make test-services-up
make test-migrate
```

Expected: PostgreSQL is available on `localhost:5433` as database `jobradar_test` with user `jobradar_test`; Redis is available on `localhost:6380`.

## Run tests

```bash
make check
```

Expected: tests run with `APP_ENV=testing`, the testing database URL, and Redis database index `1`. The quality gate passes without requiring the development `.env` database or Redis services.

For the complete lifecycle in one command:

```bash
make test-all
```

Expected: the command starts the testing services, applies migrations, runs the full quality gate, and stops the testing services automatically after success or failure.

## Verify isolation

```bash
docker compose -p job-radar-testing -f docker-compose.testing.yml ps
docker compose -p job-radar-testing -f docker-compose.testing.yml exec postgres-testing \
  psql -U jobradar_test -d jobradar_test -c 'select current_database(), current_user;'
```

Expected output contains:

```text
jobradar_test | jobradar_test
```

The testing project and `testing_postgres_data` volume must be distinct from the local `job-earch-agent` project and `postgres_data` volume.

## Cleanup

```bash
make test-services-down
```

This stops the isolated testing services. It does not stop or modify local, staging, or production services.

## Sign-off

- [ ] Dedicated test credentials verified.
- [ ] Dedicated test PostgreSQL database verified.
- [ ] Dedicated test Redis instance verified.
- [ ] `APP_ENV=testing` verified.
- [ ] CI uses testing ports and migration target.
