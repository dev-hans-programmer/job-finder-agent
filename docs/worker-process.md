Why separate the processes?
Currently, the API process owns too much responsibility:
```
FastAPI API
 ├── handles HTTP requests
 ├── dispatches background ingestion work
 ├── may run scheduler logic
 └── may execute worker logic

 ```
This creates several problems:
- A slow ingestion job can consume API resources.
- A worker crash can affect the API process.
- API deployments restart background work.
- API and worker workloads cannot scale independently.
- Scheduler execution can accidentally run more than once when multiple API instances exist.
- CPU-heavy or network-heavy jobs compete with request handling.
The target architecture will be:

```
                 ┌──────────────┐
HTTP requests →  │ API process  │
                 └──────┬───────┘
                        │ enqueue job
                        ▼
                 ┌──────────────┐
                 │ Redis queue  │
                 └──────┬───────┘
                        │ consume job
             ┌──────────┴──────────┐
             ▼                     ▼
      Worker process        Scheduler process

```
API process
Responsibilities:
- Serve FastAPI routes.
- Authenticate users.
- Validate requests.
- Create ingestion runs.
- Enqueue work.
- Return 202 Accepted.
It will not execute ingestion work directly.
Worker process
Responsibilities:
- Consume queued ingestion jobs.
- Execute provider adapters.
- Update run status and counters.
- Handle failures without affecting the API process.
Scheduler process
Responsibilities:
- Run continuously on its own cadence.
- Find due sources.
- Create or reuse ingestion runs.
- Enqueue worker jobs.
- Avoid duplicate scheduling.
It will not serve HTTP traffic.
What I will implement
1. Separate process entrypoints
Add explicit commands/modules such as:
```
app/processes/api.py
app/processes/worker.py
app/processes/scheduler.py

```
Commands:
```
make run-api
make run-worker
make run-scheduler

```
The API will use Uvicorn. Worker and scheduler processes will have graceful startup and shutdown handling.
2. Remove API-owned background execution
The current route does this:
```
background_tasks.add_task(dispatch_ingestion_run, ...)
That will be replaced with:
POST /sources/{id}/run
        ↓
create ingestion_run
        ↓
enqueue ingestion job
        ↓
return 202
```
The worker process will consume and execute the job separately.
3. Add a lightweight Redis queue boundary
Because Celery is item 3, I will not introduce Celery yet.
For this item, I will create a small queue abstraction using the existing Redis infrastructure:
```
app/workers/queue.py
```
The API and scheduler will publish job messages. The worker will consume them.
The queue message will contain only identifiers and metadata, for example:
```json
{
  "type": "ingestion",
  "source_id": "...",
  "run_id": "..."
}
```
The worker will load the actual records from PostgreSQL.
4. Make job execution idempotent
The worker must safely handle:
- Duplicate messages
- Worker restarts
- Messages that were already completed
- Missing source records
- Failed provider calls
- Graceful shutdown while processing a job
Existing active-run protection will remain in place.
5. Add Docker Compose services
The local environment will have separate
```services:
services:
  api:
    ...
  worker:
    ...
  scheduler:
    ...
  postgres:
    ...
  redis:
    ...

```
The API, worker, and scheduler will use the same codebase and environment configuration but run different commands.
6. Add Makefile commands
For example:
```
make run-api
make run-worker
make run-scheduler
make run-all
make stop-all
make logs-api
make logs-worker
make logs-scheduler
```
7. Add health and operational behavior
Each process will have:
- Structured startup/shutdown logs
- Process identity in logs
- Graceful shutdown
- Clear error handling
- Redis/PostgreSQL connection cleanup
The API health endpoint will remain HTTP-based. Worker and scheduler health will be represented through logs and process-level checks for now.
8. Add tests
Tests will cover:
- API enqueues a job and returns 202.
- Worker consumes and executes a job.
- Scheduler identifies due sources.
- Scheduler does not create duplicate active runs.
- Duplicate queue messages are safe.
- Worker handles missing sources.
- Worker handles provider failures.
- Shutdown does not corrupt run state.
- API, worker, and scheduler can initialize independently.
- Redis integration tests verify queue behavior.
