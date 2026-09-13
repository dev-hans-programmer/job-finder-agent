# Spec 017 — Production deployment with rollback

## Goal

Deploy immutable application images to production with a pre-migration backup, health validation, and a controlled application-image rollback path.

## Acceptance criteria

1. Production uses an explicit production Compose project and production-only secrets.
2. API, worker, scheduler, Flower, and backup use the same immutable image tag.
3. A database backup runs before migrations.
4. Migrations run explicitly before application services start.
5. Liveness and readiness smoke tests must pass after deployment.
6. A failed post-deployment smoke test automatically restores the previously recorded application image when one exists.
7. A manually approved GitHub production workflow builds/publishes the image and deploys it over SSH.
8. A manually triggered rollback workflow can restore a known-good application image tag.
9. Database schema rollback is never silently performed as part of an application image rollback.

There is no database schema change in this spec.
