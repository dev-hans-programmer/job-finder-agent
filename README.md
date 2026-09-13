# Job Radar Agent

Job Radar Agent is a personal job-discovery service that collects jobs from supported career-board providers, normalizes and deduplicates them, evaluates their fit against user preferences, and exposes explainable results and notification delivery state.

The project is being developed spec-by-spec using Specification-Driven Development (SDD). Each spec is independently testable and contains its requirements, implementation plan, task checklist, and manual QA guide.

## Current status

Implemented capabilities include:

- User preference profiles with versioning and validation
- Greenhouse and Lever ingestion adapters
- Pagination, retries, rate-limit handling, malformed-record isolation, and run counters
- Canonical job normalization and source provenance
- Duplicate detection and upsert behavior
- Explainable rule-based job matching
- Paginated, user-isolated job queries
- Job details, match retrieval, and feedback labels
- Telegram and email notification provider boundaries
- Notification idempotency and delivery status persistence
- Scheduler cadence evaluation and workflow boundaries
- Password authentication, rotating refresh tokens, `/me`, and configurable RBAC
- Separate API, worker, and scheduler processes with Celery/Redis task execution
- Automated PostgreSQL backups with retention, verification, and restore tooling
- Optional OpenTelemetry tracing for API, database, provider, Redis, and Celery activity
- Local Prometheus, Grafana, Loki, Tempo, and OpenTelemetry Collector observability stack
- Health checks, metrics, secret redaction, deletion flow, Docker image, and CI

Semantic embeddings, LLM-based reasoning, continuous scheduler deployment, and production notification retry workers are deliberately kept as extension points for future iterations.

## Technology stack

- Python 3.12+
- FastAPI
- SQLAlchemy asyncio
- PostgreSQL 16
- Redis 7
- Alembic
- Pydantic Settings
- `uv` for dependency and environment management
- Ruff for formatting and linting
- Pytest with branch coverage enforcement
- Docker Compose for local infrastructure

## Architecture

The application follows a layered, loosely coupled design:

```text
HTTP route
    -> dependency provider
    -> application/domain service
    -> repository
    -> PostgreSQL or Redis
```

The main processing flow is:

```text
User preferences
        |
        v
Source configuration -> ingestion adapter -> normalization/deduplication
                                                   |
                                                   v
                                           canonical jobs
                                                   |
                                                   v
                                             rule matching
                                                   |
                                                   v
                                      notification delivery state
```

Important directories:

```text
app/
  main.py                 FastAPI application and lifespan
  config.py               Environment-backed settings
  api/v1/                 HTTP routes
  dependencies/           FastAPI dependency providers
  domain/                 Domain models and business services
  ingestion/              Provider adapters and ingestion contracts
  matching/               Matching and scoring implementation
  notifications/          Notification provider boundaries/templates
  repositories/           Database persistence operations
  scheduler/              Cadence and scheduling boundary
  workers/                Background workflow boundaries
  observability/          Health, metrics, logging, and redaction

tests/
  unit/                   Fast isolated tests
  integration/            PostgreSQL/Redis-backed tests
  api/                    HTTP/API tests

specs/                    Independent SDD specifications
alembic/                  Database migrations
docs/                     PRD, TRD, and operational runbooks
```

## Prerequisites

Install:

- Python 3.12 or newer
- Docker and Docker Compose
- `uv`

Install `uv` if necessary:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Local setup

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd job-earch-agent
```

Install dependencies:

```bash
uv sync
```

Create the environment file:

```bash
cp .env.example .env
```

The local defaults are:

```env
DATABASE_URL=postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=replace-with-a-long-random-secret
AUTH_REQUIRE_TOKEN=false
# Optional first-admin bootstrap; set before registering this email.
INITIAL_ADMIN_EMAIL=admin@example.com
```

Start PostgreSQL and Redis, then apply migrations:

```bash
make services-up
make migrate
```

Start the API:

```bash
make run
```

Run the three application processes independently during development:

```bash
make services-up
make migrate
make run-api       # terminal 1
make run-worker    # terminal 2
make run-scheduler # terminal 3
```

Or start the three application containers together:

```bash
make app-up
make app-logs
```

Database backups are written to `./backups` by default. Create or verify one manually with `make backup` and `make backup-verify BACKUP=backups/file.dump`; the Compose `backup` process runs the same operation automatically on the configured interval. Store production backups in external durable storage rather than only on the application host.

Start the complete local application and observability stack with:

```bash
make app-up
```

The observability tools are available at:

- Grafana: <http://localhost:3000> (`admin` / `admin`)
- Prometheus: <http://localhost:9090>
- Loki: <http://localhost:3100/ready>
- Tempo: <http://localhost:3200/ready>

Grafana automatically provisions Prometheus, Loki, and Tempo, including the `Job Radar Overview` dashboard. The API containers send OpenTelemetry traces to the local collector, which forwards them to Tempo. Container logs are collected by Alloy and sent to Loki.

### Staging deployment

Staging uses separate PostgreSQL/Redis ports, volumes, application ports, and environment values. Copy `.env.staging.example` to `.env.staging`, replace every placeholder, then run:

```bash
make staging-up
make staging-migrate
make staging-smoke
```

Staging is available on ports `8001` (API), `3001` (Grafana), `5556` (Flower), `9091` (Prometheus), `3101` (Loki), and `3201` (Tempo). The GitHub Actions staging workflow builds a commit-tagged image, pulls it on the staging host, applies migrations, starts services, and runs smoke tests. Configure the `staging` GitHub Environment with `STAGING_HOST`, `STAGING_USER`, `STAGING_APP_DIR`, and `STAGING_SSH_KEY` secrets.

The API creates an ingestion run and dispatches a Celery task. Redis brokers the task to the worker, which updates the run. The scheduler dispatches the same task for due sources. Flower provides task and worker monitoring at `http://localhost:5555`.

The API is available at:

- Application: <http://localhost:8000>
- OpenAPI UI: <http://localhost:8000/docs>
- Readiness: <http://localhost:8000/health/ready>
- Metrics: <http://localhost:8000/metrics>

### API versioning example

The existing liveness endpoint is available at:

```bash
curl http://localhost:8000/health/live
```

Version 2 is implemented as a separate router and does not change the v1/legacy response:

```bash
curl http://localhost:8000/api/v2/health/live
```

Response:

```json
{
  "status": "ok",
  "api_version": "v2"
}
```

To add v3, create `app/api/v3/`, add a router with `prefix="/api/v3"`, implement the changed contract there, and include that router in `app/main.py`. Keep v1 and v2 routes intact so existing clients remain compatible. Dependencies, services, and repositories can be shared when their behavior has not changed; create a new service or schema when the business contract changes.

#### Full v2 example: preferences

V1 returns the preference fields directly:

```bash
curl http://localhost:8000/api/v1/preferences
```

V2 changes the contract to an explicit envelope and adds profile metadata:

```bash
curl -X PUT http://localhost:8000/api/v2/preferences \
  -H 'Content-Type: application/json' \
  -d '{"preferences":{"titles":["Staff Backend Engineer"]}}'
```

The request travels through:

```text
/api/v2/preferences
  -> app/api/v2/preferences.py
  -> app/dependencies/preferences_v2.py
  -> app/domain/preferences/v2_service.py
  -> app/repositories/preferences.py
  -> preference_profiles table
```

V2 has its own request/response schemas and service because its HTTP contract changed. It reuses the v1 repository because the database access pattern did not change. If v2 required a new query or table, add that method or a dedicated repository under `app/repositories/`; do not put SQL in the route.

Read the v2 response:

```bash
curl http://localhost:8000/api/v2/preferences
```

```json
{
  "api_version": "v2",
  "profile_id": "...",
  "version": 1,
  "status": "active",
  "preferences": {
    "titles": ["Staff Backend Engineer"]
  },
  "matching_weights": {},
  "created_at": "..."
}
```

## End-to-end example

### 1. Save preferences

Create `preferences.json`:

```json
{
  "titles": ["Backend Engineer"],
  "locations": {
    "preferred": ["Mumbai", "Bangalore"]
  },
  "skills": {
    "must_have": ["Python"],
    "nice_to_have": ["PostgreSQL", "AWS"]
  },
  "companies": {
    "preferred": []
  },
  "exclusions": ["PHP", "Frontend", "Support"],
  "matching": {
    "minimum_score": 40
  }
}
```

Submit the active profile:

```bash
curl -X PUT http://localhost:8000/api/v1/preferences \
  -H 'Content-Type: application/json' \
  --data @preferences.json
```

The API uses a default development user when `X-User-ID` is not supplied. For explicit user isolation, send:

```bash
-H 'X-User-ID: 00000000-0000-0000-0000-000000000001'
```

### 2. Configure a source

For a Greenhouse board:

```bash
curl -X POST http://localhost:8000/api/v1/sources \
  -H 'Content-Type: application/json' \
  -d '{
    "kind": "greenhouse",
    "name": "OpenAI",
    "config": {"board": "stripe"}
  }'
```

Save the returned source `id` and start ingestion:

```bash
curl -X POST http://localhost:8000/api/v1/sources/SOURCE_ID/run
```

The response contains a run ID. Inspect it with:

```bash
curl http://localhost:8000/api/v1/runs/RUN_ID
```

When the run succeeds, jobs are persisted in PostgreSQL.

### 3. Find and match a job

The job listing endpoint returns canonical jobs owned by the current user:

```bash
curl 'http://localhost:8000/api/v1/jobs?page=1&page_size=10'
```

Optional filters include:

```bash
curl 'http://localhost:8000/api/v1/jobs?min_score=40&company=OpenAI&location=Mumbai&status=active'
```

Match a job:

```bash
curl -X POST http://localhost:8000/api/v1/jobs/JOB_ID/match
```

Retrieve the latest match:

```bash
curl http://localhost:8000/api/v1/jobs/JOB_ID/match
```

The match response includes:

- Score and confidence
- Decision: `notify`, `review`, or `reject`
- Component scores
- Matched criteria
- Missing criteria
- Exclusion concerns
- Explanation text

### 4. Add feedback

```bash
curl -X POST http://localhost:8000/api/v1/jobs/JOB_ID/feedback \
  -H 'Content-Type: application/json' \
  -d '{"label":"saved","note":"Strong backend role"}'
```

Supported labels are `saved`, `applied`, `rejected`, and `hidden`. Repeating the request for the same user/job updates the existing feedback row.

### 5. Inspect delivery state

```bash
curl http://localhost:8000/api/v1/notifications/DELIVERY_ID
```

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | PostgreSQL and Redis readiness |
| GET | `/metrics` | In-memory application metrics |
| POST | `/api/v1/auth/register` | Register a user |
| POST | `/api/v1/auth/login` | Issue access and refresh tokens |
| POST | `/api/v1/auth/refresh` | Rotate a refresh token |
| POST | `/api/v1/auth/logout` | Revoke a refresh-token family |
| GET | `/api/v1/auth/me` | Read the authenticated user and roles |
| POST | `/api/v1/roles` | Create an admin-managed role |
| POST | `/api/v1/users/{user_id}/roles/{role_name}` | Assign an admin-managed role |
| GET/PUT | `/api/v1/preferences` | Read or update active preferences |
| POST | `/api/v1/preferences/validate` | Validate a preference payload |
| GET/POST | `/api/v1/sources` | List or create sources |
| POST | `/api/v1/sources/{id}/run` | Start an ingestion run |
| GET | `/api/v1/runs/{id}` | Read run status and counters |
| GET | `/api/v1/jobs` | Search and paginate jobs |
| GET | `/api/v1/jobs/{id}` | Read job detail, match, and feedback |
| POST | `/api/v1/jobs/{id}/match` | Evaluate and persist a match |
| GET | `/api/v1/jobs/{id}/match` | Read latest match |
| POST | `/api/v1/jobs/{id}/feedback` | Save or update feedback |
| GET | `/api/v1/notifications/{id}` | Read delivery status |
| DELETE | `/api/v1/users/me` | Delete the current user and owned data |

## Database migrations

Every database schema change must have an Alembic migration.

Apply migrations:

```bash
make migrate
```

Create a migration:

```bash
make migration MSG="describe the schema change"
```

Inspect the current revision:

```bash
uv run alembic current
```

The application imports all model modules in `alembic/env.py` so metadata remains complete during migration generation and testing.

## Testing and quality

Run all tests:

```bash
make test
```

Run test categories independently:

```bash
make test-unit
make test-integration
make test-api
```

Run the enforced coverage gate:

```bash
make coverage
```

The project requires 100% branch coverage for the implemented application packages.

Run formatting and linting:

```bash
make format
make lint
```

Run the complete local quality workflow:

```bash
make qa
```

Install and run pre-commit hooks:

```bash
make install-hooks
make pre-commit
```

The pre-commit configuration checks whitespace, file endings, JSON/YAML/TOML validity, merge conflicts, large files, Ruff formatting, Ruff linting, and the full test coverage gate.

## CI

GitHub Actions runs the quality workflow in `.github/workflows/ci.yml` with PostgreSQL and Redis service containers. It:

1. Installs dependencies with `uv`
2. Applies Alembic migrations
3. Runs formatting checks
4. Runs Ruff
5. Runs unit, integration, and API tests
6. Enforces 100% branch coverage

CI requires these environment variables:

```env
DATABASE_URL=postgresql+asyncpg://jobradar:jobradar@localhost:5432/jobradar
REDIS_URL=redis://localhost:6379/0
```

## Operations

Operational procedures for backups, restore testing, provider outages, credential rotation, migration rollback, and deletion are documented in [docs/OPERATIONS.md](docs/OPERATIONS.md).

Useful commands:

```bash
make services-logs
make services-down
docker compose ps
```

Create a PostgreSQL backup:

```bash
docker compose exec postgres pg_dump -U jobradar jobradar > backup.sql
```

Restore into the running disposable database:

```bash
cat backup.sql | docker compose exec -T postgres psql -U jobradar jobradar
```

## Security notes

- Do not commit `.env` or provider credentials.
- Use `.env.example` only as a configuration template.
- Production credentials should come from a secret manager or deployment environment.
- Logs must pass through the redaction helper before secrets are written.
- User/job queries are scoped through source ownership.
- Deletion is explicit and targeted to the authenticated/default user.
- User-owned API endpoints derive identity from `Authorization: Bearer <access-token>` and are represented by the Swagger `Authorize` control.
- `X-User-ID` is accepted only as a temporary local-development compatibility path when `AUTH_REQUIRE_TOKEN=false`; it is ignored in strict mode.

## SDD specifications

The implementation sequence is documented in `specs/`:

1. `001-foundation` — application foundation and infrastructure
2. `002-preferences` — preference profiles and validation
3. `003-ingestion` — source ingestion and run lifecycle
4. `004-normalization-deduplication` — canonical jobs and provenance
5. `005-matching` — explainable matching
6. `006-job-query-feedback` — search, detail, and feedback
7. `007-notifications` — notification delivery state and providers
8. `008-scheduling-workflows` — cadence and workflow boundaries
9. `009-observability-deployment` — operations, CI, health, and deployment
10. `010-authentication-authorisation` — authentication and role-based authorization
11. `011-separate-processes` — API, worker, and scheduler process boundaries
12. `012-celery-background-jobs` — Celery execution and Flower monitoring

Each spec contains:

```text
spec.md   Requirements and acceptance criteria
plan.md   Implementation plan
tasks.md  Completion checklist
qa.md     Manual end-to-end verification steps
```

## Contributing

For a new feature:

1. Create a new numbered spec directory.
2. Define independently testable acceptance criteria.
3. Add or update migrations for database changes.
4. Keep route → service → repository boundaries intact.
5. Add unit, integration, and API tests.
6. Add manual QA instructions.
7. Run `make qa` before opening a pull request.

## License

No license has been selected yet. Add a license before distributing the project publicly.
