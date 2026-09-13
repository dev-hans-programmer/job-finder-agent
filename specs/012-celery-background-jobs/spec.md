# Spec 012 — Celery Background Jobs and Monitoring

## Objective

Provide reliable, observable background task execution using Celery with Redis as broker and result backend.

## Scope

- Celery application configuration.
- Ingestion task adapter that delegates to existing domain services.
- API and scheduler task dispatch.
- Retry, acknowledgement, task lifecycle, and worker concurrency configuration.
- Flower monitoring service.
- Local Makefile and Docker Compose operation.

## Acceptance criteria

- API and scheduler dispatch registered Celery tasks instead of the custom Redis list queue.
- Workers acknowledge tasks after execution and reject tasks when lost.
- Retryable task failures use bounded exponential backoff.
- Task state is visible in Flower.
- Existing PostgreSQL ingestion-run status remains the business source of truth.
- Unit, integration, and API tests pass with 100% statement and branch coverage.
