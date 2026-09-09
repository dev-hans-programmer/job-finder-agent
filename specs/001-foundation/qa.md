# QA — Foundation and Runtime

## Prerequisites

From the repository root:

```bash
docker compose up -d postgres redis
alembic upgrade head
uvicorn app.main:app --reload
```

## Test 1: Live health

```bash
curl -i http://localhost:8000/health/live
```

Expected: HTTP `200`, body `{"status":"ok"}`, and a request ID header.

## Test 2: Ready health

```bash
curl -i http://localhost:8000/health/ready
```

Expected: HTTP `200` while PostgreSQL and Redis are running. Stop one dependency and repeat; expected HTTP `503` with the standard error envelope. Restart the dependency and confirm the endpoint returns `200` again.

## Test 3: Migration repeatability

Run `alembic upgrade head` twice. Both commands must succeed. Inspect the database and confirm the Alembic version table contains exactly one current revision.

## Test 4: Configuration failure

Start the API with an invalid database URL or missing required setting. Expected: startup fails with a clear configuration error and no secret values in the logs.

## Completion expectation

The service starts from documented commands, health states are truthful, migrations are repeatable, request IDs are visible, and dependency shutdown leaves no hanging connections.
