Auth: Session and Device Management
I’ll handle session/device management first. Password reset, email/OTP verification, and account lockout will remain the next separate item, following your approved order.
Why we need it
The current authentication flow issues tokens, but it does not give users visibility or control over where they are logged in. Session/device management allows users to see, revoke, and control active sessions.
The behavior will be controlled by a feature flag:
AUTH_SESSION_MANAGEMENT_ENABLED=false
When disabled, authentication behaves exactly as it does today. When enabled, session/device tracking is enforced.
What it solves
- Users can view active sessions
- Users can identify devices by name, user agent, and IP
- Users can revoke one session
- Users can revoke all other sessions
- Compromised devices can be disconnected
- Security teams can investigate unusual login activity
- Refresh-token rotation becomes tied to a tracked session/device
- Logout and token revocation become easier to audit
Problems without it
- Users cannot see where their account is logged in
- A stolen refresh token may remain usable until expiry or manual intervention
- Users cannot revoke a single suspicious device
- Logout behavior is difficult to reason about across devices
- Security incidents have limited context
- Token records do not clearly represent device sessions
Proposed implementation
I’ll add:
- Feature-flagged session management
- Session/device database model and Alembic migration
- Session creation during login
- Device metadata:
  - Device name
  - User agent
  - IP address
  - Created time
  - Last-used time
  - Revoked time
- Session-aware refresh-token rotation
- GET /api/v1/auth/sessions
- DELETE /api/v1/auth/sessions/{id}
- DELETE /api/v1/auth/sessions/others
- Current-session identification
- Protected route/service/repository layering
- Behavior tests with the feature flag enabled and disabled
- Unit, integration, API, and manual QA coverage
- No breaking behavior when the flag is disabled
The database migration will be reversible, and refresh tokens will continue to be stored as hashes rather than plaintext.
