# OWASP ASVS checklist

This is a project-specific verification checklist, not a certification.

| Area | Control | Evidence |
|---|---|---|
| V2 | Strong authentication secrets and password hashing | JWT validation, Argon2 password hashing, auth tests |
| V3 | Session and token lifecycle | Refresh rotation, family revocation, replay test |
| V4 | Access control | Protected routes and role tests |
| V5 | Validation and encoding | Pydantic request schemas and API tests |
| V7 | Error handling and logging | Structured errors and audit events without secrets |
| V8 | Data protection | Hashed refresh tokens and OTPs |
| V9 | Communication security | HTTPS/HSTS deployment concern documented; local HTTP remains allowed |
| V12 | Secure configuration | Production JWT secret validation and explicit CORS |
| V14 | Dependency security | `pip-audit` and Trivy CI workflow |
