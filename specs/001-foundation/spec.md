# Spec 001 — Foundation and Runtime

## Objective

Create the runnable Python service foundation used by all later specs.

## Scope

Included: project packaging, typed configuration, FastAPI application factory, dependency injection, PostgreSQL/Redis clients, structured logging, error envelope, health endpoints, Docker Compose, pytest configuration, and Alembic bootstrap.

Excluded: business entities, authentication, source adapters, and notifications.

## Contracts

- `GET /health/live` returns `200 {"status":"ok"}` without checking dependencies.
- `GET /health/ready` returns `200` only when PostgreSQL and Redis are reachable; otherwise `503` with the standard error shape.
- All API errors use `{error: {code, message, details, request_id}}`.
- Configuration fails fast when required values are absent or malformed.
- `alembic upgrade head` runs successfully against a clean PostgreSQL database.

## Acceptance criteria

- A new developer can start API, worker, scheduler, PostgreSQL, and Redis with documented commands.
- API tests cover both health endpoints and failure states.
- Database and Redis connections are closed during application shutdown.
- Request IDs appear in responses and structured logs.
- Baseline coverage is 100% branch coverage for all foundation modules.

## Required tests

Unit: configuration parsing, error mapping, request-ID middleware, dependency lifecycle.

Integration/API: live/ready success, PostgreSQL outage, Redis outage, malformed configuration startup, clean migration, repeated migration.
