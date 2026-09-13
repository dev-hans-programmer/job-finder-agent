Security hardening
This protects the API from common production attacks and verifies that the existing authentication implementation meets a recognized security baseline. OWASP ASVS provides structured requirements for testing web application security controls (OWASP ASVS).
What it solves
- Browser-based attacks such as clickjacking, MIME sniffing, and unsafe cross-origin requests
- Weak or accidentally missing JWT secrets
- Refresh-token replay after token theft
- Vulnerable Python packages or Docker images reaching deployment
- Security regressions that ordinary functional tests do not detect
Planned implementation
1. Security headers
   - Content-Security-Policy
   - X-Content-Type-Options
   - X-Frame-Options
   - Referrer-Policy
   - Permissions-Policy
   - HSTS when running over HTTPS
2. CORS policy
   - Explicit configurable allowed origins
   - No wildcard origins when credentials are enabled
   - Configurable methods and headers
   - Tests for allowed and rejected origins
3. CSRF protection
   - Since the API currently uses bearer tokens, CSRF risk is limited for access-token requests.
   - I’ll protect any cookie-based authentication flow and document why bearer-only routes do not require the same CSRF mechanism.
   - Refresh-token handling will be reviewed carefully because it is sent in the request body.
4. JWT secret validation
   - Require a minimum secret length
   - Reject default, placeholder, and weak secrets outside testing
   - Add startup validation
   - Keep test environments explicitly exempted
5. Token rotation and replay detection
   - Verify refresh-token family rotation
   - Detect reuse of a revoked refresh token
   - Revoke the complete token family after replay
   - Add audit events and tests for replay attempts
6. Dependency and container scanning
   - Add dependency vulnerability scanning to CI
   - Add Docker image scanning
   - Add secret scanning
   - Fail CI for configured severity thresholds
7. OWASP ASVS checklist
   - Add a security checklist under a new spec
   - Map implemented controls to tests
   - Document accepted risks and future controls
   - Add API security regression tests
Expected tradeoffs
- Some existing local configurations may fail startup because weak JWT secrets will no longer be accepted.
- Browser clients may need an explicitly configured origin.
- HTTPS will be required before enabling HSTS.
- CI will take slightly longer because of security scans.
