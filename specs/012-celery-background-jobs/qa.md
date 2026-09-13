# QA Guide

## Prerequisites

```bash
make services-up
make migrate
make app-up
```

Expected containers: API, worker, scheduler, Flower, PostgreSQL, and Redis are running.

## API task execution

Create a source using a valid Greenhouse board such as `stripe`, then call `POST /api/v1/sources/{source_id}/run`. Expect `202` and a `run_id`. Open `http://localhost:5555` and verify a `job_radar.ingestion` task appears. The task should transition through `STARTED` to `SUCCESS` or `FAILURE`, while the API run endpoint reports the domain status and counters.

## Scheduler task execution

Create an enabled source with `interval:10`. Wait for the scheduler poll and verify a Celery ingestion task appears in Flower without an API request.

## Failure and retry verification

Use a test fixture or mocked provider that raises a temporary connection/timeout error. Verify the task enters `RETRY`, then eventually succeeds or reaches its bounded retry limit. Provider/domain errors should still update `ingestion_runs`.

## Operational commands

```bash
make app-logs
make run-flower
docker compose exec worker celery -A app.workers.celery_app inspect active
```

Expected: worker heartbeats are visible, active tasks can be inspected, and Flower is available at port `5555`.
