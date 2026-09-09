# Job Radar Agent — SDD Specifications

Each folder is an independently implementable specification. A spec is complete only when its code, tests, migration(s), documentation, and acceptance criteria are complete.

## Spec structure

Every spec contains:

- `spec.md` — problem, scope, contracts, behavior, acceptance criteria, and test requirements.
- `plan.md` — implementation approach, design decisions, dependencies, and verification plan.
- `tasks.md` — ordered implementation checklist.
- `qa.md` — manual end-to-end verification steps, test data, expected results, and sign-off checklist.

Tests are organized in three top-level folders: `tests/unit/`, `tests/integration/`, and `tests/api/`. Shared test configuration belongs in `tests/conftest.py`; do not create spec subfolders inside `tests/`.

## Implementation order

```text
001-foundation
    ↓
002-preferences
    ↓
003-ingestion
    ↓
004-normalization-deduplication
    ↓
005-matching
    ↓
006-job-query-feedback
    ↓
007-notifications
    ↓
008-scheduling-workflows
    ↓
009-observability-deployment
```

Specs may be developed in parallel only where their dependency is already implemented. Each spec must leave the repository passing all existing tests.

## Global definition of done

- Unit tests cover every branch of new domain logic.
- Integration tests run against real PostgreSQL and Redis containers where those services are used.
- API tests exercise success, validation, authentication, not-found, conflict, and provider/error paths applicable to the spec.
- New database changes include an Alembic migration and migration tests.
- Coverage is measured with branch coverage and must be 100% for the changed package/spec scope; the CI gate must enforce 100% total coverage before release.
- External providers are mocked in normal CI and exercised with explicit contract fixtures.
- No secrets, provider credentials, or production data are committed.

## Local services

PostgreSQL and Redis are required through Docker Compose. Tests must use an isolated database/schema and apply Alembic migrations before running.
