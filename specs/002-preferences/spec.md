# Spec 002 — Preference Profiles

## Objective

Allow a user to create, validate, version, retrieve, and activate structured job preferences.

## Scope

Implement the preference schema from the PRD, normalization, immutable versions, active-profile selection, and REST endpoints. MVP supports one user but stores `user_id` for future multi-user support.

## API contract

- `GET /api/v1/preferences` returns the active profile and version.
- `PUT /api/v1/preferences` validates input, creates the next immutable version, and activates it.
- `POST /api/v1/preferences/validate` validates without persisting.

Required validation: score 0–100, minimum experience not greater than maximum, non-negative salary, supported work modes, non-empty title/skill strings, and no duplicate values after normalization.

## Acceptance criteria

- Valid YAML-equivalent JSON is normalized and persisted without semantic loss.
- Invalid profiles return field-level validation details and do not create a version.
- Previous versions remain readable and unchanged.
- Exactly one active profile exists per user.
- Every persisted profile change has an Alembic migration if schema changes.
- Unit and API/integration coverage is 100% branch coverage for the spec.

## Required tests

Unit: schema validation, normalization, weight defaults, versioning service, duplicate handling.

Integration/API: create/read/validate, invalid payloads, concurrent updates, active-version constraint, PostgreSQL persistence and rollback.
