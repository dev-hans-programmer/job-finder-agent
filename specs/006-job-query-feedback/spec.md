# Spec 006 — Job Queries and User Feedback

## Objective

Expose canonical jobs, match explanations, lifecycle state, and user feedback through a stable API.

## Scope

Implement paginated/filterable job listing, detail endpoint, match retrieval, feedback labels, and lifecycle updates. Notification delivery is specified separately.

## API contract

- `GET /api/v1/jobs` supports score, status, company, location, source, date, page, page size, and sort filters.
- `GET /api/v1/jobs/{job_id}` returns canonical data, provenance, latest match, delivery state, and feedback.
- `GET /api/v1/jobs/{job_id}/match` returns the latest active-profile match.
- `POST /api/v1/jobs/{job_id}/feedback` stores a supported label and optional note.

## Acceptance criteria

- Pagination is stable and does not expose another user's jobs.
- Not-found and invalid-filter errors use the standard envelope.
- Feedback is persisted, queryable, and idempotent where defined.
- Closed/expired jobs remain readable but are excluded from new-match queries by default.
- API and PostgreSQL tests achieve 100% branch coverage for this scope.
