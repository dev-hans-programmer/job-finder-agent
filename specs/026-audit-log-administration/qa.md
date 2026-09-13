# QA: Audit log administration

## Preconditions

Start the local stack and apply migrations:

```bash
make services-up
make migrate
make app-up
```

The endpoints require an authenticated user with the `admin` role. Use an
admin access token from the authentication flow, then set:

```bash
export TOKEN='<admin-access-token>'
```

## 1. Search audit events

```bash
curl -sS 'http://localhost:8000/api/v1/admin/audit-events?page=1&page_size=10&success=true' \
  -H "Authorization: Bearer $TOKEN" | jq
```

Expected:

- HTTP `200`.
- A consistent `data` response envelope.
- `data` is an array of audit events.
- `meta` contains `page`, `page_size`, and `total`.
- Results are newest first.

Try additional filters:

```text
?actor_user_id=<USER_UUID>
?action=auth.login
?resource_type=user
?resource_id=<RESOURCE_ID>
?created_after=2026-01-01T00:00:00Z&created_before=2026-12-31T23:59:59Z
```

The result should contain only events matching every supplied filter.

## 2. Authorization

Call the same endpoint with no token, an expired token, and a non-admin token.
Each must be rejected (`401` for missing/invalid authentication or `403` for an
authenticated user without the admin role). No audit data should be returned.

## 3. Export JSON

```bash
curl -sS -OJ 'http://localhost:8000/api/v1/admin/audit-events/export?format=json' \
  -H "Authorization: Bearer $TOKEN"
jq 'length' audit-events.json
```

Expected: HTTP `200`, a JSON array, and the `audit-events.json` attachment
header. Its records should match the same filters used by search.

## 4. Export CSV

```bash
curl -sS -OJ 'http://localhost:8000/api/v1/admin/audit-events/export?format=csv&success=false' \
  -H "Authorization: Bearer $TOKEN"
head -2 audit-events.csv
```

Expected: HTTP `200`, `Content-Type: text/csv`, a header row, and only failed
events. Exporting a filter with no matches must still return a valid CSV header.

## 5. Retention and archive

For a safe local test, set a short retention period and enable archival in the
environment used by the command:

```bash
AUDIT_RETENTION_DAYS=1 \
AUDIT_ARCHIVE_ENABLED=true \
AUDIT_ARCHIVE_DIR=./backups/audit \
uv run python -m app.audit_admin
```

Expected output is JSON containing `cutoff`, `archived`, `deleted`, and
`archive_path`. Events older than the cutoff are removed from PostgreSQL. If
events were archived, the JSONL file exists under `backups/audit` and contains
one complete event per line. Recent events remain searchable.

The normal operational command is:

```bash
make audit-retention
```

This command is intentionally not a scheduler. Run it from an external cron,
container scheduler, or deployment platform according to the retention policy.

## Automated verification

```bash
uv run pytest tests/unit tests/integration tests/api --cov=app --cov-branch --cov-fail-under=100 -q
make test-all
```

Pass criteria: all tests pass, branch coverage is 100%, non-admin access is
rejected, filters are applied, both exports are valid, and retention produces
the documented archive/delete result.
