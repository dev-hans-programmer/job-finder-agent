# QA Guide

## Prerequisites

```bash
make services-up
make migrate
```

Run the application processes in separate terminals:

```bash
make run-api
make run-worker
make run-scheduler
```

## Automated verification

```bash
make lint
make coverage
docker compose config
```

Expected: all commands succeed, tests report 100% coverage, and Compose reports a valid configuration.

## API-to-worker verification

1. Create a source through the API.
2. Call `POST /api/v1/sources/{source_id}/run`.
3. Immediately expect `202` and a `run_id` with status `running`.
4. Check the worker terminal and expect it to consume the ingestion message.
5. Call `GET /api/v1/runs/{run_id}`.
6. Expect the run to transition to `succeeded`, `partial`, or `failed` and its counters to be populated.

The API terminal must not show provider execution logs from the worker operation.

## Scheduler verification

Create an enabled source with a schedule such as `interval:10`, wait for the scheduler poll, and inspect the worker logs. A run should be created and consumed without an HTTP request. Disable the source and verify new runs are not created.

## Docker verification

```bash
make app-up
docker compose ps
curl http://localhost:8000/health/live
make app-logs
```

Expected: `api`, `worker`, and `scheduler` are running; the liveness endpoint returns success; each process writes its own startup log. `make app-down` stops only the application processes.
