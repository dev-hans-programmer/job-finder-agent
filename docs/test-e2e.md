1. Start infrastructure
make services-up
make migrate
Verify:
docker compose ps
PostgreSQL and Redis should be healthy.
2. Start API, worker, scheduler, and Flower
make app-up
Verify:
docker compose ps
You should see:
api
worker
scheduler
flower
postgres
redis
Check logs:
make app-logs
Open:
http://localhost:8000/docs
http://localhost:5555
Flower should show the worker once it connects.
3. Verify the API
curl http://localhost:8000/health/live
Expected:
{
  "status": "ok"
}
4. Register a user
Use a unique email:
EMAIL="user-$(date +%s)@example.com"
PASSWORD="UserPassword123!"

REGISTERED=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "$REGISTERED" | jq
Save the user ID:
USER_ID=$(echo "$REGISTERED" | jq -r '.id')
5. Login
LOGIN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

echo "$LOGIN" | jq
Save the access token:
ACCESS_TOKEN=$(echo "$LOGIN" | jq -r '.access_token')
Verify authentication:
curl -s http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
6. Create a Greenhouse source
SOURCE=$(curl -s -X POST http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "kind": "greenhouse",
    "name": "OpenAI Careers",
    "config": {
      "board": "stripe"
    }
  }')

echo "$SOURCE" | jq
Save the source ID:
SOURCE_ID=$(echo "$SOURCE" | jq -r '.id')
7. Dispatch an ingestion task
RUN=$(curl -s -X POST \
  "http://localhost:8000/api/v1/sources/$SOURCE_ID/run" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$RUN" | jq
Expected:
{
  "run_id": "...",
  "status": "running"
}
Save the run ID:
RUN_ID=$(echo "$RUN" | jq -r '.run_id')
At this point:
API → Celery task → Redis → Celery worker → Greenhouse API
8. Monitor the task in Flower
Open:
http://localhost:5555
Look for:
job_radar.ingestion
You should see the task transition through states such as:
PENDING → STARTED → SUCCESS
If the provider fails:
PENDING → STARTED → RETRY
You can also inspect logs:
docker compose logs -f worker
Or inspect active Celery tasks:
docker compose exec worker \
  celery -A app.workers.celery_app inspect active
9. Check the application run status
curl -s \
  "http://localhost:8000/api/v1/runs/$RUN_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
Expected final status may be:
{
  "status": "succeeded",
  "fetched_count": 6,
  "normalized_count": 6,
  "error_count": 0
}
Depending on the provider response, it may also be partial or failed.
10. Confirm jobs were persisted
curl -s http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
11. Test scheduler execution
Create a source with a short schedule:
curl -s -X POST http://localhost:8000/api/v1/sources \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "kind": "greenhouse",
    "name": "Scheduled OpenAI Careers",
    "config": {
      "board": "stripe"
    },
    "schedule": "interval:30",
    "enabled": true
  }' | jq
After the scheduler interval, check:
docker compose logs -f scheduler
docker compose logs -f worker
You should see the scheduler dispatch an ingestion task, followed by the worker processing it. The same task should appear in Flower.
Stop everything
Stop application processes:
make app-down
Stop PostgreSQL and Redis:
make services-down
