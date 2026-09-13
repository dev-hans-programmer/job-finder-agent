# Spec 013 — Automated Database Backups

## Objective

Create verifiable, retained PostgreSQL backups through an independent process without writing into PostgreSQL's data directory.

## Scope

- Custom-format `pg_dump` backups.
- SHA-256 checksum and metadata sidecars.
- Retention cleanup.
- Backup verification and disposable-target restore commands.
- Dedicated Compose backup process and Makefile operations.

## Acceptance criteria

- Automated backups are written to the configured backup directory.
- Database passwords are passed through `PGPASSWORD` and never included in command arguments or logs.
- A backup is validated with `pg_restore --list` before publication.
- Checksum and metadata sidecars are written for every backup.
- Retention removes only expired backup artifacts.
- Missing, empty, invalid, or checksum-mismatched backups are rejected.
- Unit tests pass with 100% statement and branch coverage.
