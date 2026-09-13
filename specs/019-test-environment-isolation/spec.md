# Spec 019 — Isolated testing environment

## Goal

Ensure unit, integration, and API tests never use local development or production PostgreSQL/Redis credentials or data.

## Acceptance criteria

1. Pytest forces `APP_ENV=testing` before application imports.
2. Tests use `jobradar_test` with a dedicated test user/password on PostgreSQL port `5433`.
3. Tests use Redis port `6380`, database index `1`, and dedicated test settings.
4. CI provisions and migrates only the testing PostgreSQL/Redis services.
5. Local test services run under the separate Compose project `job-radar-testing`.
6. Test configuration cannot silently fall back to `.env` development credentials.
7. Unit, API, integration, lint, and 100% branch-coverage checks pass.

There is no application database schema change in this spec.
