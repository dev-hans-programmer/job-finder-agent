# Spec 016 — Staging deployment

## Goal

Provide an isolated, production-like staging environment and a repeatable CI deployment workflow.

## Acceptance criteria

1. Staging uses separate PostgreSQL/Redis ports and persistent volumes.
2. Staging requires explicit non-production secrets through `.env.staging`.
3. The staging API, worker, scheduler, Flower, backup, and observability services use the same image tag.
4. Migrations run as an explicit staging deployment step.
5. Smoke tests verify liveness and readiness after deployment.
6. GitHub Actions can build and publish a commit-tagged image and deploy it over SSH using the staging environment secrets.
7. Rollback is intentionally deferred to Spec 017.

There is no database schema change in this spec.
