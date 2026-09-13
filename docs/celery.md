Why Celery + Redis?
Currently we have a custom Redis queue:
API/Scheduler → Redis list → Worker
This proves process separation, but it is still a basic queue implementation. We manually manage message publishing, consumption, failures, and worker behavior.
Celery provides a production-tested task execution framework around this process.
The target architecture becomes:
API/Scheduler
      ↓
Celery task
      ↓
Redis broker
      ↓
Celery worker
      ↓
PostgreSQL/provider APIs
Redis acts as the message broker, while Celery manages task execution.
What Celery solves
Reliable task execution
Celery provides task acknowledgement and retry behavior.
It can handle:
- Worker crashes
- Temporary provider failures
- Redis interruptions
- Task retries
- Task time limits
- Duplicate task protection
- Task routing
Our current custom queue removes a message before execution. If the worker crashes after consuming it, the message may be lost.
Automatic retries
Provider APIs can fail because of:
- Rate limits
- Temporary network failures
- HTTP 5xx responses
- Provider downtime
- Database connection interruptions
Celery lets us configure retries:
Attempt 1 → failure
Wait 30 seconds
Attempt 2 → failure
Wait 2 minutes
Attempt 3 → failure
Mark as failed
This avoids implementing retry and backoff logic manually for every worker.
Concurrency
Celery workers can process multiple jobs concurrently.
For example:
celery -A app.workers.celery_app worker --concurrency=4
We can independently scale worker capacity without scaling the API:
1 API process
3 worker processes
1 scheduler process
Task lifecycle tracking
Celery gives tasks states such as:
PENDING
STARTED
RETRY
SUCCESS
FAILURE
REVOKED
This is separate from our domain-level ingestion_runs status.
The distinction is useful:
Celery task status:
  Is the background task executing?

Application run status:
  What happened to the ingestion business operation?
Monitoring
Celery can be monitored using Flower.
Flower provides:
- Active workers
- Registered tasks
- Running tasks
- Failed tasks
- Retry counts
- Task duration
- Worker availability
- Task arguments and results
- Task history
The monitoring flow becomes:
Celery worker → Redis → Flower dashboard
Flower could be accessed locally at:
http://localhost:5555
Operational controls
Celery allows operators to:
- Inspect active tasks
- Revoke tasks
- Retry failed tasks
- Shut down workers gracefully
- Inspect registered tasks
- Check worker heartbeats
- Route task types to specific queues
For example:
ingestion queue
matching queue
notification queue
Later, we could dedicate different worker pools to different workloads.
What problems we have without Celery
If we keep the custom Redis queue, we would need to build and maintain:
- Reliable message acknowledgement
- Retry policies
- Exponential backoff
- Dead-letter queues
- Task state tracking
- Worker heartbeats
- Task cancellation
- Task timeout handling
- Queue monitoring
- Failed-task inspection
- Manual concurrency management
- Recovery after worker crashes
- Task routing
- Operational dashboards
The current queue is adequate for a prototype, but this logic becomes increasingly risky as ingestion, matching, and notification jobs grow.
Proposed implementation
I would implement:
Celery application
app/workers/celery_app.py
Configure:
- Redis broker URL
- Redis result backend
- JSON serialization
- UTC timezone
- Task acknowledgement behavior
- Retry settings
- Worker shutdown behavior
Celery tasks
app/workers/tasks/
  ingestion.py
  matching.py
  notifications.py
Initially, ingestion would be migrated:
@celery_app.task(...)
def run_ingestion(source_id, run_id):
    ...
The task would call the existing domain service, preserving:
task → service → repository
Celery should orchestrate work, not contain business logic.
API integration
The API route would replace the custom queue call:
POST /sources/{id}/run
        ↓
create ingestion run
        ↓
celery_task.delay(source_id, run_id)
        ↓
return 202
Scheduler integration
The scheduler would dispatch the same Celery task:
Scheduler → Celery task → Redis → Worker
Remove the custom queue
After successful migration:
- Remove the custom Redis list queue.
- Keep Redis as Celery’s broker/backend.
- Preserve the existing worker process boundary.
- Preserve ingestion run statuses in PostgreSQL.
Flower monitoring
Add a Compose service:
flower:
  command: celery -A app.workers.celery_app flower
  ports:
    - "5555:5555"
Add Makefile commands:
make run-celery-worker
make run-flower
make celery-inspect
Tests
Tests would cover:
- Task registration
- API dispatch
- Scheduler dispatch
- Successful task execution
- Retryable provider failure
- Permanent failure
- Maximum retry limit
- Task status behavior
- Worker initialization
- Flower configuration
- Existing domain service behavior
The domain tests should remain independent of Celery. Celery-specific behavior would be tested separately.
Tradeoffs
Benefits:
- Reliable task execution
- Built-in retries
- Better monitoring
- Independent worker scaling
- Operational controls
- Standard production pattern
Costs:
- More dependencies
- More configuration
- Redis becomes operationally important
- Celery task code must remain thin
- Monitoring adds another service
- Async SQLAlchemy integration requires care because Celery tasks are commonly synchronous
