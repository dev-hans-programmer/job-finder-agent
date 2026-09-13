# Spec 025: Security hardening

## Goal

Strengthen the HTTP and authentication boundaries without requiring HTTPS
certificates for local development.

## Requirements

- Add safe HTTP security headers and make HSTS explicitly opt-in.
- Configure CORS using an explicit origin allowlist.
- Protect cookie-based authentication with CSRF validation when enabled.
- Validate JWT secrets in staging and production.
- Detect refresh-token reuse and revoke the complete token family.
- Scan Python dependencies and the Docker image in CI.
- Maintain an OWASP ASVS checklist and automated regression tests.
- Keep local development on plain HTTP by default.
