# QA: Load testing

## Prerequisites

Start the local deployment first:

```bash
make services-up
make migrate
make app-up
```

For a realistic test, use a staging URL and a dedicated test account/data.
Do not run load tests against production without explicit traffic approval.

## Interactive test

Run:

```bash
make loadtest
```

Open `http://localhost:8089`, enter users and spawn rate, then start the test.
The Locust statistics page should show named requests such as `GET /jobs`,
`GET /auth/me`, and `GET /sources`.

## Headless test

```bash
LOADTEST_TARGET_URL=http://localhost:8000 \
LOADTEST_USERS=10 \
LOADTEST_SPAWN_RATE=2 \
LOADTEST_RUN_TIME=1m \
LOADTEST_MAX_FAILURE_PERCENT=0 \
LOADTEST_MAX_P95_MS=1000 \
make loadtest-headless
```

Expected artifacts are `artifacts/loadtest/report.html` and CSV files prefixed
with `artifacts/loadtest/results`. The command exits successfully only when
aggregate failure percentage and p95 latency meet the configured thresholds.

To include ingestion triggering, set `LOADTEST_SOURCE_ID` to an existing source
ID. Use a test source/provider board so the test does not overload a third-party
provider.

## What to inspect

- Aggregate request count and requests per second
- p50, p95, and p99 latency
- Failure percentage and named failing endpoints
- PostgreSQL connection pool saturation
- Redis memory/latency and rate-limit responses
- Celery queue depth and worker throughput
- API, worker, and database CPU/memory

Treat the first run as a baseline. Thresholds should be tightened only after
the staging baseline and expected traffic profile are known.
