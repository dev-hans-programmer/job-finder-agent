# QA: Audit logging

## Prerequisites

Start the local infrastructure and apply migrations:

```bash
make services-up
make migrate
make app-up
```

The API is available at `http://localhost:8005` when using `make app-up`.

## Registration audit

Register a user:

```bash
curl -i -X POST http://localhost:8005/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: qa-registration-001' \
  -d '{"email":"audit@example.com","password":"StrongPassword123!"}'
```

Expected result:

- HTTP `201`.
- Response header `X-Request-ID: qa-registration-001`.
- One `user.registered` audit event exists.
- Its `request_id` is `qa-registration-001`.
- Its `actor_user_id` and `resource_id` identify the created user.

## Successful and failed login

```bash
curl -i -X POST http://localhost:8005/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: qa-login-failed-001' \
  -d '{"email":"audit@example.com","password":"wrong-password"}'
```

Expected result:

- HTTP `401`.
- A `user.login.failed` event exists with `success=false`.
- The event does not contain the password.

Login with the correct password and request ID:

```bash
curl -i -X POST http://localhost:8005/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'X-Request-ID: qa-login-success-001' \
  -d '{"email":"audit@example.com","password":"StrongPassword123!"}'
```

Expected result:

- HTTP `200`.
- A `user.logged_in` event exists with `success=true`.
- The event contains the request ID and actor user ID.
- No access or refresh token is stored in the audit row.

## Inspect events directly

Connect to the local PostgreSQL database:

```bash
docker compose exec postgres psql -U jobradar -d jobradar
```

Then run:

```sql
SELECT action, success, actor_user_id, resource_type, resource_id,
       request_id, metadata, created_at
FROM audit_events
ORDER BY created_at DESC
LIMIT 20;
```

Verify that events are present and metadata contains only safe diagnostic
values. The table has no application endpoint for update or delete operations.

## Automated verification

```bash
make test-all
```

Expected result: all tests pass, migrations reach `20260913_011`, and total
coverage is `100.00%`. The test command uses the isolated testing database and
stops its infrastructure afterward.
