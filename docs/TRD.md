# Job Radar Agent — Technical Requirements Document

**Status:** Draft
**Version:** 1.0
**Related document:** [PRD](./PRD.md)
**Last updated:** 2026-09-09

## 1. Technical summary

Job Radar Agent will be implemented as an asynchronous modular monolith. FastAPI exposes the management API, PostgreSQL is the system of record, Redis provides locks/cache/queue support, and scheduled workers run ingestion, normalization, deduplication, matching, and notification workflows.

The design optimizes for a reliable single-user MVP while preserving boundaries for future worker separation and multiple users.

## 2. Design principles

- Source adapters are isolated behind stable interfaces.
- PostgreSQL is authoritative; Redis data is disposable.
- Every external operation is retryable and idempotent.
- Matching is deterministic where possible and explainable at every stage.
- LLM output is advisory and schema-constrained; it cannot override hard exclusions.
- Unknown data is represented explicitly and is never silently treated as a mismatch.
- Provider-specific credentials and behavior stay outside domain logic.
- All important decisions carry a reproducible version: preference profile, scoring rules, prompt, model, and source record.

## 3. Proposed stack

| Area | Technology | Requirement |
|---|---|---|
| API | Python, FastAPI, Pydantic | REST API with OpenAPI schema |
| Persistence | PostgreSQL | Transactions, JSONB for source/config payloads, indexed canonical jobs |
| Migrations | Alembic | Forward-only migration scripts |
| Scheduling | APScheduler initially | One scheduler instance with distributed lock |
| Async work | Redis-backed queue boundary | Start with in-process/background workers if appropriate; support Celery/RQ later |
| Cache/locks | Redis | TTL required for locks and ephemeral values |
| HTTP | `httpx` | Timeouts, connection pooling, retry policy |
| Parsing | Typed Python domain services | Deterministic extraction before model calls |
| Semantic matching | Embedding provider abstraction | Cache by normalized text hash |
| LLM reasoning | Structured-output LLM adapter | Model/prompt version recorded per result |
| Notifications | Provider adapters | Telegram and email in MVP; WhatsApp behind feature flag |
| Testing | pytest, pytest-asyncio | Unit, integration, contract, and workflow tests |
| Packaging | `pyproject.toml`, Docker Compose | Reproducible local and deployment environments |

## 4. System architecture

```text
                    +----------------------+
                    | FastAPI REST API     |
                    +----------+-----------+
                               |
                   +-----------v------------+
                   | Application services  |
                   +-----+------------+-----+
                         |            |
                +--------v--+    +----v---------+
                | PostgreSQL |    | Redis        |
                | system     |    | locks/cache  |
                | of record  |    | queue        |
                +--------+---+    +----+---------+
                         |             |
              +----------v-------------v----------+
              | Scheduler / worker workflows       |
              | ingest -> normalize -> dedupe      |
              | -> match -> notify                 |
              +--+---------------+--------------+--+
                 |               |              |
          +------v-----+  +------v-------+ +----v----------+
          | Source     |  | Matching     | | Notification  |
          | adapters   |  | providers    | | adapters      |
          +------------+  +--------------+ +---------------+
```

### Module boundaries

```text
app/
  main.py
  config.py
  api/v1/
    preferences.py
    sources.py
    jobs.py
    runs.py
    health.py
  domain/
    preferences/
    jobs/
    matching/
    notifications/
  ingestion/
    base.py
    greenhouse/
    lever/
    company_careers/
  matching/
    rule_engine.py
    semantic_matcher.py
    llm_matcher.py
    scorer.py
    prompts/
  notifications/
    base.py
    telegram.py
    email.py
    whatsapp.py
  repositories/
  workers/
  scheduler/
  observability/
tests/
alembic/
```

Domain modules must not import concrete provider modules. Provider implementations depend on domain interfaces, not the reverse.

## 5. Runtime workflows

### 5.1 Ingestion workflow

1. Scheduler acquires a Redis lock for the source and creates an `ingestion_run` row.
2. Worker loads source configuration and invokes the adapter.
3. Adapter fetches pages using bounded concurrency, timeouts, and provider rate limits.
4. Raw records are validated into a source-neutral DTO.
5. Normalizer converts the DTO into a canonical job candidate.
6. Job candidate is upserted into `job_source_records` and linked to a canonical `jobs` row.
7. Deduplication either links to an existing job or creates a new canonical job.
8. Changed jobs are marked for matching; unchanged descriptions may reuse the prior match.
9. Run counters and errors are persisted, and the lock is released.

The workflow must continue processing later records after an individual record failure. Fatal adapter/configuration errors fail the run but do not affect other sources.

### 5.2 Matching workflow

1. Select new or materially changed canonical jobs that have not been evaluated against the active profile version.
2. Apply deterministic exclusions and structured field extraction.
3. Generate or retrieve cached embeddings for job text and preference text.
4. Calculate semantic similarities for title, skills, and responsibilities.
5. Apply configured component weights.
6. Invoke the LLM only when configured, when data is ambiguous, or when the job is within the configured borderline range.
7. Validate structured LLM output and clamp values to valid ranges.
8. Persist the complete match result, including model metadata and reasons.
9. Enqueue notification only for `notify` decisions.

### 5.3 Notification workflow

1. Create a notification intent with a deterministic idempotency key: `profile_version + canonical_job_id + channel`.
2. Acquire a delivery lock and check for a prior successful delivery.
3. Render channel-specific content from the persisted match result.
4. Send through the selected provider with a bounded timeout.
5. Persist success, failure, provider message ID, and retry metadata.
6. Retry transient failures with exponential backoff; do not retry permanent validation/authentication failures indefinitely.

## 6. Data model

The following is the MVP relational model. IDs should be UUIDs. All tables require `created_at` and `updated_at` timestamps in UTC unless noted.

### `users`

- `id` UUID primary key
- `email` nullable unique
- `timezone` varchar, default `Asia/Kolkata`
- `status` enum: `active`, `disabled`, `deleted`

### `preference_profiles`

- `id` UUID primary key
- `user_id` foreign key
- `version` integer
- `config` JSONB, validated against the preference schema
- `matching_weights` JSONB
- `is_active` boolean
- `created_at`

Unique constraint: `(user_id, version)`.

### `sources`

- `id` UUID primary key
- `user_id` foreign key
- `kind` varchar: `greenhouse`, `lever`, `company_careers`
- `name` varchar
- `config` JSONB without secrets
- `credentials_ref` nullable varchar
- `schedule` varchar or interval representation
- `enabled` boolean
- `last_success_at` nullable timestamp
- `last_error_at` nullable timestamp

### `ingestion_runs`

- `id` UUID primary key
- `source_id` foreign key
- `status` enum: `running`, `succeeded`, `partial`, `failed`
- `started_at`, `completed_at`
- `fetched_count`, `normalized_count`, `created_count`, `updated_count`, `duplicate_count`, `error_count`
- `error_summary` JSONB

### `jobs`

- `id` UUID primary key
- `title` varchar
- `company_name` varchar
- `company_normalized` varchar
- `description` text
- `description_hash` varchar
- `locations` JSONB
- `work_mode` enum: `remote`, `hybrid`, `onsite`, `unknown`
- `experience_min`, `experience_max` nullable numeric
- `salary_min`, `salary_max` nullable numeric
- `salary_currency` nullable varchar
- `salary_unit` nullable varchar
- `employment_type` nullable varchar
- `extracted_skills` JSONB
- `application_url` text
- `posted_at`, `last_seen_at` nullable timestamp
- `status` enum: `active`, `closed`, `expired`

Indexes: `company_normalized`, `status`, `last_seen_at`, `posted_at`, and a full-text index over title/description where supported.

### `job_source_records`

- `id` UUID primary key
- `job_id` foreign key
- `source_id` foreign key
- `external_id` varchar
- `source_url` text
- `raw_payload` JSONB or object-storage reference
- `raw_payload_hash` varchar
- `first_seen_at`, `last_seen_at`

Unique constraint: `(source_id, external_id)` when external ID exists.

### `match_results`

- `id` UUID primary key
- `job_id`, `preference_profile_id` foreign keys
- `job_description_hash`
- `score` numeric constrained to 0–100
- `confidence` numeric constrained to 0–1
- `decision` enum: `reject`, `review`, `notify`
- `component_scores` JSONB
- `matched_criteria` JSONB
- `missing_criteria` JSONB
- `concerns` JSONB
- `reasoning` text
- `matcher_version`, `embedding_model`, `llm_model`, `prompt_version` nullable
- `created_at`

Index: `(job_id, preference_profile_id, created_at desc)`.

### `notification_deliveries`

- `id` UUID primary key
- `job_id`, `match_result_id`, `user_id` foreign keys
- `channel` enum: `telegram`, `email`, `whatsapp`
- `idempotency_key` unique
- `status` enum: `pending`, `sent`, `failed`, `suppressed`
- `provider_message_id` nullable
- `attempt_count`
- `last_error` nullable text
- `sent_at` nullable timestamp

### `user_feedback`

- `id` UUID primary key
- `user_id`, `job_id` foreign keys
- `label` enum: `relevant`, `irrelevant`, `saved`, `dismissed`, `applied`, `interviewing`, `rejected`, `hired`
- `note` nullable text
- `created_at`

## 7. Interfaces

### Source adapter

```python
class SourceAdapter(Protocol):
    async def health_check(self, config: SourceConfig) -> HealthStatus: ...
    async def fetch(self, config: SourceConfig) -> AsyncIterator[RawJobRecord]: ...
    def normalize(self, record: RawJobRecord) -> JobCandidate: ...
```

Adapters must expose provider rate limits, pagination behavior, retryable status codes, and whether raw payload retention is permitted.

### Matcher

```python
class Matcher(Protocol):
    async def evaluate(
        self,
        job: CanonicalJob,
        preferences: PreferenceProfile,
    ) -> MatchDecision: ...
```

`MatchDecision` must contain score, confidence, decision, component scores, matched criteria, missing criteria, concerns, reasoning, and model/version metadata.

### Notification provider

```python
class NotificationProvider(Protocol):
    async def send(self, message: NotificationMessage) -> DeliveryResult: ...
    async def health_check(self) -> HealthStatus: ...
```

Providers must classify failures as retryable or permanent.

## 8. Matching implementation

### Rule stage

Rules should normalize case, punctuation, common aliases, and technology synonyms. They must support title/description context to reduce false positives, such as `PHP` appearing only in an exclusion comparison or a company name.

Hard-exclusion behavior:

- Reject only on a high-confidence match in title, role category, or required responsibility.
- Store the matched text span and exclusion term.
- Do not reject based solely on an unknown field.

### Semantic stage

Use separate text representations for:

- title and seniority
- skills and technologies
- responsibilities/domain
- location/work mode

Embeddings are keyed by `content_hash + embedding_model`. A provider failure should fall back to rule-based scoring and mark confidence lower.

### LLM stage

The LLM receives only the normalized preferences and relevant job text. The prompt must request JSON matching a versioned schema. The application must validate:

- score ranges
- allowed enum values
- arrays of strings
- no unsupported claims
- evidence spans or quoted keywords for inferred matches where available

Prompt injection content in job descriptions must be treated as untrusted data. The LLM must be instructed not to follow job-description instructions unrelated to matching.

### Score calculation

```text
final_score =
  skills_score      * skills_weight      / 100 +
  experience_score  * experience_weight  / 100 +
  location_score    * location_weight    / 100 +
  role_score        * role_weight        / 100 +
  salary_score      * salary_weight      / 100 +
  company_score     * company_weight     / 100
```

The scorer must be a pure function with golden test cases. The configured notification threshold is applied after hard exclusions and score calculation.

## 9. API design

### `PUT /api/v1/preferences`

Validates and stores a new immutable profile version. Returns the normalized configuration and version number.

### `POST /api/v1/sources/{source_id}/run`

Creates an asynchronous run and returns `202 Accepted` with `run_id`. A duplicate active request for the same source returns the existing run ID.

### `GET /api/v1/jobs`

Supports `page`, `page_size`, `min_score`, `status`, `company`, `location`, `source`, `from_date`, `to_date`, and `sort`.

### `GET /api/v1/jobs/{job_id}`

Returns canonical job data, source references, latest match result, notification state, and feedback.

### `POST /api/v1/jobs/{job_id}/feedback`

Accepts a label and optional note. Must be idempotent for the same user/job/label request where practical.

### Error format

All errors use a stable shape:

```json
{
  "error": {
    "code": "PREFERENCE_VALIDATION_FAILED",
    "message": "minimum_score must be between 0 and 100",
    "details": [{"path": "matching.minimum_score", "reason": "out_of_range"}],
    "request_id": "..."
  }
}
```

## 10. Scheduling, concurrency, and retries

- Default source schedule: every 4 hours, configurable per source.
- Scheduler uses a Redis lock key `scheduler:source:{source_id}` with an expiry longer than the expected run duration.
- Worker concurrency is bounded globally and per provider.
- HTTP timeout defaults: connect 5 seconds, read 30 seconds, total 45 seconds; provider-specific overrides are allowed.
- Retry transient network errors and 429/5xx responses with exponential backoff and jitter.
- Respect `Retry-After` when provided.
- Dead-letter failed records after a configurable number of attempts.
- Never retry malformed source records indefinitely.

## 11. Security and privacy

- Use environment variables or a managed secret store for API keys, SMTP credentials, bot tokens, and LLM keys.
- Do not put secrets in source configuration JSONB or logs.
- Authenticate API requests; use a single-user token in MVP and a proper identity provider before multi-user release.
- Validate URLs and prevent server-side request forgery in configurable source endpoints.
- Restrict outbound requests to approved schemes/domains where possible.
- Redact email addresses, tokens, and provider payload secrets from logs.
- Support user data deletion and cascading removal/anonymization of related records.
- Define raw payload and prompt retention separately from canonical job retention.

## 12. Observability

### Structured logs

Every log should include `request_id`, `run_id`, `source_id`, `job_id`, `profile_version`, and `event` when available.

Required events include:

- source run started/completed/failed
- record normalized/rejected/merged
- match completed
- LLM call completed/failed
- notification sent/failed/suppressed

### Metrics

- `ingestion_runs_total{source,status}`
- `ingestion_records_total{source,result}`
- `ingestion_duration_seconds{source}`
- `deduplication_merges_total`
- `matches_total{decision}`
- `match_duration_seconds`
- `llm_calls_total{model,status}`
- `llm_cost_estimate_total`
- `notifications_total{channel,status}`
- `notification_delivery_latency_seconds{channel}`
- `source_last_success_timestamp`

### Health endpoints

- `/health/live`: process is running.
- `/health/ready`: PostgreSQL and Redis are reachable.
- `/health/providers`: optional authenticated diagnostic for source and notification providers.

## 13. Testing strategy

### Unit tests

- Preference schema validation and normalization.
- Title, skill, salary, location, and experience extraction.
- Rule exclusions and alias handling.
- Pure score calculation and threshold behavior.
- Deduplication keys and fuzzy-match decisions.
- Notification rendering and idempotency-key generation.

### Contract tests

- Each source adapter converts representative fixtures into the canonical DTO.
- Each notification adapter handles success, retryable failure, permanent failure, and provider response parsing.
- LLM response parser rejects malformed or unsafe output.

### Integration tests

- PostgreSQL migrations and repository operations.
- Redis lock behavior and duplicate-run suppression.
- End-to-end ingestion of fixture records through matching and notification queues.

### End-to-end tests

- Configure preferences, run a source, inspect a match, deliver a notification, and submit feedback.
- Rerun the same source and assert no duplicate job or notification.
- Simulate one provider failure and assert other sources continue.

External providers should be mocked in CI. A separately triggered smoke test may use sandbox credentials.

## 14. Deployment

### Local development

Docker Compose should run:

- API container
- worker container
- scheduler container
- PostgreSQL
- Redis

Environment configuration must be documented in `.env.example`, with no real credentials committed.

### Production MVP

Deploy API, scheduler, and worker as separate processes from the same image. Use managed PostgreSQL and Redis where possible. Apply migrations as an explicit deployment step before starting new application code.

Required deployment properties:

- health checks and automatic restart
- encrypted transport to managed services
- centralized logs
- daily PostgreSQL backups with restore verification
- bounded worker autoscaling or fixed resource limits
- feature flags for optional providers and LLM calls

## 15. Configuration

Configuration should be typed and fail fast on startup. Examples:

```env
APP_ENV=local
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
DEFAULT_TIMEZONE=Asia/Kolkata
MATCHING_LLM_ENABLED=false
MATCHING_LLM_MODEL=...
EMBEDDING_MODEL=...
TELEGRAM_ENABLED=false
SMTP_ENABLED=false
RAW_PAYLOAD_RETENTION_DAYS=30
LLM_DAILY_BUDGET=...
```

Provider credentials must be supplied through secrets, not committed configuration files.

## 16. Delivery plan

### Phase 1 — Foundation

- Project scaffolding, configuration, logging, migrations, Docker Compose.
- User and preference profile APIs.
- Base domain types and repository interfaces.

### Phase 2 — Ingestion

- Source adapter contract.
- Greenhouse and Lever adapters with fixtures.
- Canonical job persistence, normalization, run tracking, and deduplication.

### Phase 3 — Matching

- Rule engine and pure scorer.
- Embedding provider interface and cache.
- Match persistence, thresholds, and explainable result format.

### Phase 4 — Delivery

- Telegram and email adapters.
- Notification queue, idempotency, retries, and templates.
- Job listing/detail/feedback APIs.

### Phase 5 — Hardening

- Metrics and dashboards.
- Security review, retention/deletion flows, failure testing, restore test.
- Optional LLM explanation behind a feature flag.

## 17. Technical acceptance checklist

- [ ] `alembic upgrade head` creates all MVP tables and indexes.
- [ ] API starts with documented environment variables and exposes OpenAPI documentation.
- [ ] Source runs are idempotent and isolated by source lock.
- [ ] Canonical jobs retain source provenance and description hashes.
- [ ] Match results are reproducible from stored profile and model/version metadata.
- [ ] Hard exclusions cannot be overridden by semantic or LLM matching.
- [ ] LLM output is validated and safely falls back on failure.
- [ ] Notification retries are bounded and duplicate sends are prevented.
- [ ] Logs and metrics expose run, match, LLM, and delivery status.
- [ ] Automated tests cover the PRD acceptance criteria.
- [ ] Provider terms, credentials, retention, and deletion behavior are documented before production use.
