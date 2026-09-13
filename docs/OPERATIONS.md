# Operations runbook

## Run locally

`make qa` starts PostgreSQL/Redis, applies migrations, and runs the quality gate.

## Backup and restore

Create a timestamped backup with `make backup`. Backups are written to `./backups` locally and include a custom-format dump, SHA-256 sidecar, and metadata file. Verify one with `make backup-verify BACKUP=backups/jobradar-....dump`.
Restore only into a disposable or explicitly approved target with `make restore BACKUP=backups/jobradar-....dump`, then run `make migrate` and representative queries. The automated Compose `backup` service runs this process every `BACKUP_INTERVAL_SECONDS` and retains `BACKUP_RETENTION_DAYS` of local files.

## Incident procedures

- Provider outage: inspect `/health/ready`, delivery status, and retry/dead-letter counts.
- Migration rollback: stop the application, run `alembic downgrade -1`, then deploy the compatible image.
- Credential rotation: update `.env`/secret manager and restart; never commit credentials.
- Data deletion: call `DELETE /api/v1/users/me` with the user identity header and record the request ID.
