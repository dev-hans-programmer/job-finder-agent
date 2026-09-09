# Spec 009 — Observability, Security, and Deployment

## Objective

Make the service operable, secure, testable, and deployable locally and in a production MVP environment.

## Scope

Implement structured logs, metrics, health diagnostics, secret handling, retention/deletion flows, Docker production configuration, backup documentation, CI coverage gates, and operational runbooks.

## Acceptance criteria

- Logs include request/run/source/job/profile identifiers where applicable and redact secrets.
- Required metrics and health checks are emitted.
- CI runs migrations, unit tests, integration/API tests, linting, and branch coverage.
- Coverage fails below 100% for the full implemented product before release.
- User/job/raw-payload deletion follows documented retention rules.
- Production configuration contains no hard-coded secrets and passes a configuration safety test.
- PostgreSQL backup and restore procedure is documented and tested in a disposable environment.
