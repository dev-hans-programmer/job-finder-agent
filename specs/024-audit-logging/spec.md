# Spec 024: Audit logging

## Goal

Provide an append-only, structured audit trail for authentication and other
security-sensitive actions.

## Requirements

- Persist audit events in PostgreSQL through a repository and service layer.
- Capture action, resource, actor, outcome, request ID, client metadata, and timestamp.
- Record successful and failed authentication actions.
- Record registration, token refresh, password reset, email verification, and
  other implemented account-security actions.
- Never store passwords, access tokens, refresh tokens, OTP values, or secrets in
  audit metadata.
- Keep the audit table out of normal user CRUD APIs; application code has no
  update/delete path.
- Support nullable actors for anonymous actions such as failed login.
- Preserve audit records when a user is deleted by setting the actor to NULL.

## Acceptance criteria

- Alembic creates `audit_events` with the required indexes and foreign key.
- Auth requests create corresponding success/failure records.
- Each record contains the request ID returned in the HTTP response.
- Unit, integration, and API tests pass with 100% branch coverage.
