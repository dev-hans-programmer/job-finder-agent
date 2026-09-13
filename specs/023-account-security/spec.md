# Spec 023: Password reset, email verification, and account lockout

## Goal

Complete the account-security lifecycle with feature-flagged recovery,
verification, and brute-force protection.

## Requirements

- Support password-reset requests and single-use, expiring reset codes.
- Never reveal whether a reset email belongs to an account.
- Support email verification and resend-code flows using six-digit OTPs.
- Reject login until email verification when that feature is enabled.
- Track failed login attempts and temporarily lock accounts after a configurable threshold.
- Reset failed-attempt counters after successful authentication.
- Revoke refresh tokens and sessions after password reset.
- Preserve existing behavior when each feature flag is disabled.
- Store only hashes of reset/verification codes.
- Provide a local delivery boundary that logs codes for manual QA; production email delivery remains an integration point.

## Acceptance criteria

The feature flags independently control behavior, the migration is reversible,
security data is persisted, invalid/expired/replayed codes fail, lockout works,
and all unit/integration/API tests pass with 100% branch coverage.
