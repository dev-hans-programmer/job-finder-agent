# Spec 011 — Separate API, Scheduler, and Worker Processes

## Objective

Separate HTTP serving, schedule evaluation, and background execution into independently runnable processes.

## Scope

- API process for HTTP traffic and queue publishing.
- Worker process for Redis queue consumption and ingestion execution.
- Scheduler process for due-source evaluation and queue publishing.
- Redis queue contract containing identifiers only.
- Docker Compose services, Makefile commands, graceful shutdown, and process tests.

## Acceptance criteria

- `POST /api/v1/sources/{id}/run` creates a run, enqueues work, and returns `202` without executing provider work in the API process.
- A worker consumes an ingestion message and updates the persisted run.
- The scheduler enqueues due enabled sources and skips disabled, not-due, active, or invalid sources.
- API, worker, and scheduler have independent startup and shutdown paths.
- The three processes can be run locally and through Docker Compose.
- Unit, integration, and API tests pass with 100% statement and branch coverage.
