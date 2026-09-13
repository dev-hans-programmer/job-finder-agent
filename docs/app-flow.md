1. Create a source
You call:
POST /api/v1/sources
Authorization: Bearer <ACCESS_TOKEN>
Example:
{
  "kind": "greenhouse",
  "name": "Stripe Careers",
  "config": {
    "board": "stripe"
  }
}
The request flows through:
HTTP route
  ↓
JWT authentication
  ↓
get_current_user()
  ↓
SourceService
  ↓
SourceRepository
  ↓
PostgreSQL
Internally:
1. The Bearer token is decoded.
2. The user ID is extracted from the JWT.
3. The route passes the authenticated user ID to SourceService.
4. SourceService passes the data to SourceRepository.
5. SourceRepository inserts a row into the sources table.
6. PostgreSQL returns the generated source ID.
7. The API returns 201 Created.
Example response:
{
  "id": "source-id",
  "kind": "greenhouse",
  "name": "Stripe Careers",
  "config": {
    "board": "stripe"
  },
  "enabled": true
}
At this stage, no provider API has been called yet.
2. Start the source run
You call:
POST /api/v1/sources/{source_id}/run
Authorization: Bearer <ACCESS_TOKEN>
The request flows through:
HTTP route
  ↓
JWT authentication
  ↓
IngestionService.start_run()
  ↓
SourceRepository
  ↓
PostgreSQL + Redis
  ↓
Celery task dispatch
  ↓
HTTP 202 response
Internally:
1. The API validates your access token.
2. It obtains your authenticated user ID.
3. IngestionService verifies that the source belongs to you.
4. It checks whether the source kind is supported.
5. It checks whether another run is already active.
6. It creates a short-lived Redis lock:
ingestion:source:<source_id>
7. It inserts an ingestion_runs row with:
status = running
8. The API dispatches the Celery task:
job_radar.ingestion
9. Celery serializes the task arguments:
{
  "source_id": "...",
  "run_id": "..."
}
10. Celery publishes the task to Redis.
11. The API immediately returns 202 Accepted.
Example response:
{
  "run_id": "run-id",
  "status": "running"
}
Important: at this point, the API has only created the run and queued the task. The provider has not necessarily been contacted yet.
3. Redis brokers the Celery task
The task moves through Redis:
API
  ↓
Celery producer
  ↓
Redis broker
  ↓
Celery worker
Redis is acting as the message broker. It temporarily holds the task until a worker consumes it.
Flower observes Celery events but does not execute the task itself.
4. Worker receives the task
The worker container is running:
celery -A app.workers.celery_app worker --loglevel=INFO
The worker:
1. Receives job_radar.ingestion.
2. Marks the Celery task as STARTED.
3. Opens a PostgreSQL session.
4. Loads the source using source_id.
5. Selects the correct adapter.
For a Greenhouse source:
GreenhouseAdapter
For a Lever source:
LeverAdapter
The worker task delegates to the existing application service:
Celery task
  ↓
IngestionService
  ↓
GreenhouseAdapter
  ↓
HTTP request to Greenhouse
Celery is only responsible for task execution. Business logic remains inside the domain service.
5. Provider adapter fetches jobs
For the Stripe source, the adapter calls:
https://boards-api.greenhouse.io/v1/boards/stripe/jobs?page=1
The adapter:
1. Makes the HTTP request.
2. Checks the response status.
3. Parses the JSON payload.
4. Extracts job records.
5. Converts them into the internal RawJobRecord format.
6. Handles malformed records individually.
7. Applies configured pagination and rate limiting.
The raw provider response is not immediately returned to the API. It is processed by the worker.
6. Jobs are normalized and persisted
Each fetched provider job is normalized into the application’s canonical job model.
The flow is:
Provider job
  ↓
RawJobRecord
  ↓
normalize_record()
  ↓
JobRepository.upsert()
  ↓
PostgreSQL
The system creates or updates records in tables such as:
jobs
job_source_records
The system also tracks:
- New jobs
- Updated jobs
- Duplicate jobs
- Source provenance
- Last-seen timestamps
This is when the actual job data becomes available through:
GET /api/v1/jobs
7. The ingestion run is completed
After processing all records, the worker updates the ingestion_runs row.
Example successful result:
{
  "status": "succeeded",
  "fetched_count": 100,
  "normalized_count": 100,
  "error_count": 0
}
The worker also stores:
- Completion time
- Created count
- Updated count
- Duplicate count
- Error summary
Then it releases the Redis source lock:
ingestion:source:<source_id>
The Celery task becomes:
SUCCESS
The application run becomes:
succeeded
These are two separate statuses:
Celery status:
  Was the background task executed successfully?

Application status:
  What happened to the ingestion business operation?
8. What Flower shows
Flower monitors the Celery task lifecycle:
PENDING
  ↓
STARTED
  ↓
SUCCESS
For failures, you may see:
STARTED
  ↓
RETRY
  ↓
SUCCESS
or:
STARTED
  ↓
FAILURE
Flower shows:
- Task name
- Task ID
- Worker name
- Start time
- Runtime
- Arguments
- Retries
- Tracebacks
- Task status
Open:
http://localhost:5555
Look for:
job_radar.ingestion
9. What you can verify
Check source
curl -s http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
Check run status
curl -s http://localhost:8000/api/v1/runs/$RUN_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
Check persisted jobs
curl -s http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
Check worker logs
docker compose logs -f worker
Check scheduler logs
docker compose logs -f scheduler
Check active Celery tasks
docker compose exec worker \
  celery -A app.workers.celery_app inspect active
Complete flow
POST /sources
    ↓
authenticate user
    ↓
SourceService
    ↓
SourceRepository
    ↓
sources table
    ↓
201 Created


POST /sources/{id}/run
    ↓
authenticate user
    ↓
verify source ownership
    ↓
create ingestion_runs row
    ↓
create Redis lock
    ↓
dispatch job_radar.ingestion
    ↓
Redis broker
    ↓
Celery worker
    ↓
GreenhouseAdapter
    ↓
Greenhouse API
    ↓
normalize provider jobs
    ↓
upsert jobs into PostgreSQL
    ↓
update ingestion_runs counters/status
    ↓
release Redis lock
    ↓
Celery SUCCESS
