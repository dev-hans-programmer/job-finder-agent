# Implementation plan

1. Add user verification/lockout fields and verification-code persistence.
2. Add configuration flags and security policy to the auth service.
3. Add password-reset, email-verification, and resend endpoints.
4. Revoke active sessions after password reset.
5. Add reversible Alembic migration and layered repository/service tests.
6. Add manual QA documentation using local auth-code logs.
