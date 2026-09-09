# Job Radar Agent — Product Requirements Document

**Status:** Draft
**Version:** 1.0
**Owner:** Product / Engineering
**Last updated:** 2026-09-09

## 1. Product summary

Job Radar Agent is a personal job-discovery assistant that periodically collects relevant jobs from permitted sources, removes duplicates, evaluates each job against structured user preferences plus semantic/LLM reasoning, and delivers only high-value opportunities with an explainable score and an application link.

The product is intentionally a **modular monolith** for the first release. It should be easy to operate for one user, while keeping source adapters, matching, storage, scheduling, and notifications separated enough to evolve independently.

## 2. Problem

Job seekers spend significant time checking multiple sites, reviewing repetitive alerts, and manually deciding whether a job is a good fit. Keyword-only filters are too rigid: a suitable role may use Django instead of FastAPI, or describe a skill without using the exact preferred term. The product should reduce noise without hiding reasonable matches, and every recommendation should show why it was selected and what is missing.

## 3. Goals and success metrics

### Goals

- Let a user describe their job search once in structured preferences.
- Ingest jobs on a schedule from permitted APIs, feeds, ATS endpoints, or user-configured sources.
- Normalize inconsistent job data into one canonical model.
- Deduplicate the same role across sources and refresh changed listings.
- Produce a 0–100 match score using hard rules, semantic similarity, and optional LLM analysis.
- Explain matched, missing, and disqualifying criteria in plain language.
- Notify the user only when a new, eligible job crosses their configured threshold.
- Preserve an audit trail so a score can be inspected and re-evaluated.

### Initial success metrics

- At least 90% of ingested records are normalized with title, company, location, URL, and description status.
- At least 95% of repeated listings are linked to an existing canonical job.
- 100% of delivered alerts contain a working application URL and score explanation.
- Duplicate notifications for the same canonical job are zero by default.
- A user can update preferences and receive results without an engineering change.
- Median time from source ingestion to notification is under 15 minutes for active sources.

Precision and recall should be measured after the user labels at least 50 jobs as relevant or irrelevant. The first release should optimize for precision and trust over maximum coverage.

## 4. Target user and primary journey

### Primary user

A technically experienced job seeker looking for mid-to-senior engineering roles across selected Indian cities and remote/hybrid opportunities.

### Primary journey

1. User creates or uploads a preferences profile.
2. User selects enabled sources and notification channels.
3. Scheduler runs source workers.
4. Jobs are fetched, normalized, validated, and deduplicated.
5. Matching engine evaluates eligible jobs.
6. Jobs above the threshold are queued for notification.
7. User receives a concise alert, opens the application link, and optionally labels the result relevant, irrelevant, saved, or applied.
8. Feedback is retained for reporting and future ranking improvements.

## 5. Preference model

Preferences must be editable as YAML/JSON and through an API. The following is the canonical example:

```yaml
job_preferences:
  titles:
    - Software Engineer
    - Senior Software Engineer
    - Staff Software Engineer
    - Backend Engineer
    - Principal Engineer

  skills:
    must_have:
      - Python
      - FastAPI
      - PostgreSQL
    nice_to_have:
      - AWS
      - Redis
      - Kafka
      - Kubernetes
      - System Design
      - FinTech

  locations:
    preferred:
      - Mumbai
      - Bangalore
      - Hyderabad
      - Pune
      - Kolkata

  work_mode:
    - remote
    - hybrid

  experience:
    min: 7
    max: 15

  salary:
    minimum_lpa: 40

  companies:
    preferred:
      - Razorpay
      - PhonePe
      - Stripe
      - Google

  exclusions:
    - frontend
    - PHP
    - support
    - manual testing

  matching:
    minimum_score: 75
```

The system must distinguish between:

- **Hard exclusions:** reject the job when confidently present in the title or description.
- **Must-have skills:** missing skills reduce the score or reject only if the user explicitly marks them as strict.
- **Preferences:** increase the score but never independently disqualify a job.
- **Unknown values:** do not infer a negative match merely because salary, location, or a skill is not stated.

## 6. Functional requirements

### 6.1 Preference management

- Create, read, update, validate, and version a preference profile.
- Support one active profile in MVP, with a path to multiple profiles later.
- Validate score thresholds, salary units, experience ranges, and supported work modes.
- Allow users to configure source-specific search terms and notification quiet hours.
- Keep the prior profile version attached to every match for reproducibility.

### 6.2 Job-source ingestion

- Implement a source-adapter interface with `fetch`, `normalize`, `health_check`, and rate-limit metadata.
- Prioritize permitted sources: Greenhouse, Lever, company career pages with stable feeds/endpoints, and other approved APIs or feeds.
- Treat LinkedIn and similar restricted platforms as optional integrations only where an approved API, feed, export, or user-provided result source is available.
- Store source name, source job ID, canonical URL, retrieval time, HTTP/status metadata, and raw payload where retention is permitted.
- Make ingestion idempotent and retry transient failures with bounded backoff.
- Record per-source run status, counts, latency, and errors.

### 6.3 Normalization

Normalize source records into:

- title
- company name and optional company ID
- description and description hash
- location(s)
- work mode: remote, hybrid, onsite, or unknown
- minimum and maximum experience, if found
- minimum and maximum salary plus currency/unit, if found
- employment type
- skills and extracted entities
- posted date and last-seen date
- application URL
- source references

The original text must remain available for audit where legally and operationally appropriate. Missing values must be represented as unknown, not guessed.

### 6.4 Deduplication

Deduplicate using a confidence-ranked strategy:

1. Exact source job ID within a source.
2. Normalized application URL.
3. Stable external identifiers from ATS providers.
4. Company + normalized title + normalized location + similar description hash.
5. Fuzzy/semantic comparison as a reviewable fallback.

When duplicates are merged, retain all source links and timestamps. Prefer the most complete and most recently refreshed representation for display.

### 6.5 Matching and ranking

The default score is a weighted score from 0 to 100:

| Criterion | Weight |
|---|---:|
| Skills | 40 |
| Experience | 20 |
| Location/work mode | 15 |
| Role/title | 10 |
| Salary | 10 |
| Company preference | 5 |

The weights must be configurable, but the sum must equal 100. Matching occurs in stages:

1. **Rule gate:** apply exclusions, parse obvious structured values, and identify missing/unknown fields.
2. **Semantic matching:** compare titles, skills, and job description concepts so equivalent technologies and responsibilities are recognized.
3. **LLM explanation:** optionally produce structured reasoning for borderline or high-value jobs; the LLM must not override a hard exclusion.
4. **Score aggregation:** calculate component scores, confidence, final score, and reasons.

The matcher must return structured output similar to:

```json
{
  "score": 97,
  "confidence": 0.91,
  "decision": "notify",
  "components": {
    "skills": 35,
    "experience": 20,
    "location": 15,
    "role": 9,
    "salary": 8,
    "company": 10
  },
  "matched": ["Python", "PostgreSQL", "AWS", "FinTech"],
  "missing": ["FastAPI"],
  "concerns": [],
  "reasoning": "Strong backend and FinTech fit; FastAPI is not mentioned, but Django experience is closely related."
}
```

The system must never claim a skill is present unless it was found in the job text or a traceable semantic inference. Inferred matches must be labeled as inferred.

### 6.6 Notifications

MVP channels: Telegram and email. WhatsApp is supported behind a provider adapter after business/provider approval.

Each notification must include:

- match score and confidence
- title and company
- location and work mode
- salary/experience when available
- matched criteria
- missing criteria
- concerns or unknowns
- direct application link
- actions to save, dismiss, or mark applied where the channel supports them

Notifications must be idempotent, rate-limited, and grouped into a digest when configured. Quiet hours and per-channel delivery failures must be supported.

### 6.7 Feedback and lifecycle

Users can label a job as new, saved, dismissed, applied, interviewing, rejected, or hired. Feedback is not required for matching in MVP, but must be stored so later versions can personalize ranking.

Jobs should transition through `discovered`, `matched`, `notified`, `saved`, `applied`, `closed`, or `expired`. A closed/expired listing must not generate a new alert unless it is materially reposted.

## 7. Non-functional requirements

- **Reliability:** one failed source or notification channel must not stop the whole run.
- **Observability:** structured logs, metrics, run IDs, source health, match latency, notification status, and LLM cost/token usage.
- **Security:** secrets in environment/secret storage; encrypt sensitive user data at rest where available; authenticate all management APIs.
- **Privacy:** collect only data required for the service; support deletion of user profile, raw payloads, and notifications; define retention for raw job descriptions.
- **Compliance:** use only sources and access methods permitted by provider terms; implement robots/rate-limit controls where applicable.
- **Cost control:** cache embeddings, avoid LLM calls for obvious rejects, and set per-run/per-day LLM budgets.
- **Performance:** ingestion should process sources concurrently within configured rate limits; matching should be asynchronous for large batches.
- **Testability:** adapters, scoring, deduplication, prompts, and notification formatting must be unit-testable without external services.

## 8. Proposed architecture

```text
Scheduler (APScheduler initially; Celery-ready boundary)
        |
Source adapters -> Normalizer -> PostgreSQL
                              |
                       Deduplication
                              |
             Rules -> Embeddings -> Optional LLM
                              |
                    Match + decision record
                              |
                 Notification service -> Telegram/email/WhatsApp
```

Suggested implementation stack:

- FastAPI for management and webhook APIs
- PostgreSQL for users, preferences, jobs, matches, runs, and delivery records
- Redis for short-lived locks, rate limits, and job queues/cache
- APScheduler for a single-process MVP, with a migration path to Celery/RQ workers
- Embedding provider and LLM behind interfaces so models can be changed without rewriting domain logic
- Alembic for schema migrations
- Docker Compose for local development

Recommended module boundaries:

```text
app/
  api/v1/
  domain/{jobs,preferences,matching,notifications}/
  ingestion/{greenhouse,lever,company_careers}/
  matching/{rule_engine,semantic_matcher,llm_matcher}/
  notifications/{telegram,email,whatsapp}/
  scheduler/
  repositories/
  workers/
tests/
alembic/
```

## 9. Core data entities

- **User:** identity, timezone, notification settings, status.
- **PreferenceProfile:** versioned YAML/JSON preferences and matching weights.
- **Source:** adapter type, configuration, schedule, enabled state, credentials reference.
- **IngestionRun:** source, start/end time, status, counters, errors.
- **Job:** canonical normalized listing and lifecycle state.
- **JobSourceRecord:** source-specific ID, URL, raw payload reference, retrieval metadata.
- **MatchResult:** profile version, component scores, final score, confidence, reasons, model metadata.
- **NotificationDelivery:** channel, recipient, idempotency key, status, timestamps, provider response.
- **UserFeedback:** job, label, note, timestamp.

## 10. API requirements

Minimum API surface:

- `GET /api/v1/preferences`
- `PUT /api/v1/preferences`
- `POST /api/v1/preferences/validate`
- `GET /api/v1/sources`
- `POST /api/v1/sources/{source_id}/run`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/match`
- `POST /api/v1/jobs/{job_id}/feedback`
- `GET /api/v1/runs`
- `GET /api/v1/health`

All list endpoints need pagination and filters for score, status, source, company, location, and date. Management endpoints require authentication before multi-user support is enabled.

## 11. MVP scope

### Included

- One user and one active preference profile.
- YAML/JSON preference import plus API read/update.
- Greenhouse and Lever adapters, plus a simple configurable company-career adapter where permitted.
- Scheduled ingestion and manual run trigger.
- Canonical PostgreSQL storage and URL/title/company deduplication.
- Rule-based score plus embedding similarity.
- Optional LLM explanation for jobs near or above the threshold.
- Telegram and email notifications.
- Job detail/list APIs, feedback labels, structured logs, and basic metrics.

### Explicitly deferred

- Aggressive authenticated LinkedIn/browser scraping.
- Automatic job applications or recruiter messaging.
- Multi-user billing, teams, and complex permissions.
- Fully autonomous preference changes.
- Learning-to-rank from a small feedback sample.
- WhatsApp until a compliant provider and delivery model are selected.

## 12. Acceptance criteria

The MVP is ready when:

1. A valid preference document can be saved and retrieved without loss of meaning.
2. An ingestion run can fetch at least one configured source, report failures, and be safely rerun.
3. The same listing from two source records becomes one canonical job with both references retained.
4. A job containing Python, PostgreSQL, backend responsibilities, matching location, and suitable experience receives a materially higher score than an excluded frontend/support role.
5. Missing FastAPI does not automatically reject a job when semantically related backend experience is present, unless FastAPI is configured as a strict must-have.
6. A hard exclusion prevents notification even if the unfiltered score is high.
7. Every notification contains score, reasons, missing/unknown criteria, and a working application URL.
8. Re-running the same source does not create duplicate jobs or duplicate notifications.
9. A source outage is visible in run status and does not prevent other sources from completing.
10. Automated tests cover scoring weights, exclusion behavior, deduplication, notification idempotency, and preference validation.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Source terms or anti-automation controls change | Prefer approved APIs/feeds/ATS endpoints; isolate adapters; disable non-compliant source quickly. |
| LLM produces confident but incorrect reasoning | Use structured schemas, citations to job text spans, confidence, deterministic gates, and prompt/model versioning. |
| Salary/location data is missing or ambiguous | Represent unknown explicitly; avoid false rejection; show uncertainty in alerts. |
| Too many alerts reduce trust | Default to threshold + deduplication + digest; collect dismiss/save feedback. |
| Embedding/LLM costs grow with volume | Pre-filter, cache by description hash, batch embeddings, and enforce budgets. |
| Duplicate listings create repeated work | Use layered deduplication and idempotency keys at ingestion and notification stages. |

## 14. Future roadmap

1. Web UI with search, saved jobs, source health, and score explanations.
2. More compliant ATS/API connectors and user-provided feeds.
3. Personalized ranking from feedback and application outcomes.
4. Multiple profiles, e.g. backend engineering vs platform engineering.
5. WhatsApp and additional notification channels.
6. Change detection for reposted jobs and deadline reminders.
7. Resume-aware matching and tailored application notes, with explicit user approval before any submission.

## 15. Open decisions

- Which embedding and LLM providers are acceptable for job-description data?
- Should salary matching treat missing salary as neutral, penalized, or configurable?
- What exact source list and refresh frequency are allowed for the first deployment?
- Is the first user interface API/YAML-only, or should a minimal web form ship with MVP?
- What retention period is acceptable for raw job descriptions and model prompts?
- Which WhatsApp provider and template approval process will be used?
