# Operations runbook

## Run locally

`make qa` starts PostgreSQL/Redis, applies migrations, and runs the quality gate.

## Backup and restore

Create a backup with `docker compose exec postgres pg_dump -U jobradar jobradar > backup.sql`.
Restore into a disposable database with `cat backup.sql | docker compose exec -T postgres psql -U jobradar jobradar`.
Verify with `make migrate` and a representative `SELECT` query.

## Incident procedures

- Provider outage: inspect `/health/ready`, delivery status, and retry/dead-letter counts.
- Migration rollback: stop the application, run `alembic downgrade -1`, then deploy the compatible image.
- Credential rotation: update `.env`/secret manager and restart; never commit credentials.
- Data deletion: call `DELETE /api/v1/users/me` with the user identity header and record the request ID.
