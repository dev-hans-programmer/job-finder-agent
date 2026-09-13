# Spec 026: Audit log administration

## Goal

Give administrators a safe, paginated way to inspect, filter, export, and
retain audit events without exposing audit data to ordinary users.

## Scope

- Admin-only `GET /api/v1/admin/audit-events` search endpoint.
- Filters for actor, action, resource type/id, success, and time range.
- Pagination metadata in the standard success response envelope.
- Admin-only JSON and CSV export.
- Configurable retention command with optional JSONL archival.
- Unit, API, and service-level tests with 100% branch coverage.

There is no schema change in this spec; the existing `audit_events` table from
Spec 024 is used, so no new Alembic migration is required.

## Security requirements

- Every search/export endpoint requires the `admin` role.
- Audit events remain append-only from the application API.
- There is no public delete endpoint.
- Retention is an explicit operational command, not an HTTP operation.
- Archive files must be stored in the configured backup location and protected
  like database backups.

## Configuration

```env
AUDIT_RETENTION_DAYS=365
AUDIT_ARCHIVE_ENABLED=false
AUDIT_ARCHIVE_DIR=./backups/audit
```

When archival is enabled, events older than the cutoff are written as JSONL
before they are deleted. When disabled, old events are deleted without an
archive. The operation is run with `make audit-retention`.
