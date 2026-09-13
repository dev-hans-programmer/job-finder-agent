# QA: Account security

## Setup

Enable the features in `.env`:

```env
AUTH_PASSWORD_RESET_ENABLED=true
AUTH_EMAIL_VERIFICATION_ENABLED=true
AUTH_ACCOUNT_LOCKOUT_ENABLED=true
AUTH_MAX_LOGIN_ATTEMPTS=3
AUTH_LOCKOUT_MINUTES=15
AUTH_OTP_EXPIRE_MINUTES=10
```

Restart the API after changing settings:

```bash
make services-up
make migrate
make run-api
```

The local code-delivery boundary logs six-digit codes to the API terminal as
`auth_code_issued`. Do not use this delivery mode in production; connect a real
email provider first.

## Email verification

1. Register a new user.
   The user should be persisted with `status=pending_verification` and
   `email_verified_at=NULL`.
2. Copy the `email_verification` code from the API log.
3. Call:

   ```bash
   curl -i -X POST http://localhost:8005/api/v1/auth/email/verify \
     -H 'Content-Type: application/json' \
     -d '{"email":"user@example.com","code":"123456"}'
   ```

4. Login with the user credentials. It should succeed after verification.
5. Reuse the same code. It should return `400`.

## Password reset

1. Request a reset:

   ```bash
   curl -s -X POST http://localhost:8005/api/v1/auth/password-reset/request \
     -H 'Content-Type: application/json' \
     -d '{"email":"user@example.com"}'
   ```

2. Copy the `password_reset` code from the API log.
3. Confirm the new password:

   ```bash
   curl -i -X POST http://localhost:8005/api/v1/auth/password-reset/confirm \
     -H 'Content-Type: application/json' \
     -d '{"email":"user@example.com","code":"123456","password":"NewPassword123!"}'
   ```

4. Existing access/session tokens should return `401` after reset.
5. The old password must fail and the new password must work.
6. Repeat the code. It should return `400`.
7. Request reset for an unknown email. The response must be indistinguishable
   from the known-email response.

## Account lockout

1. Submit the wrong password three times.
2. The next login attempt, including the correct password, should be rejected
   while the account is locked.
3. Verify that the lockout lasts for the configured duration.
4. After the lockout expires, a successful login should work and reset the
   failed-attempt counter.

## Automated verification

Run:

```bash
make test-all
```

This applies migrations `20260913_009` and `20260913_010`, then runs unit, integration, and API
tests with 100% branch coverage.
