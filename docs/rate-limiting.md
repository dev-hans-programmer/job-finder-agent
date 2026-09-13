1. Rate limiting
Why do we need it?
Rate limiting controls how many requests a user, IP address, or client can make within a specific time window.
Example:
Login:         5 attempts per minute
Registration:  3 attempts per hour
Token refresh: 20 requests per minute
General API:   100 requests per minute
Redis will store the counters so limits work consistently across multiple API processes and containers.
What problems does it solve?
Rate limiting protects against:
- Brute-force password attacks.
- Credential stuffing.
- Registration abuse.
- Token refresh abuse.
- Accidental infinite request loops.
- API and database overload.
- Excessive external provider usage.
- Basic denial-of-service behavior.
When exceeded, the API returns:
429 Too Many Requests
Retry-After: 30
with the structured error response:
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": [],
    "request_id": "..."
  }
}
What problems will we have without it?
Without rate limiting:
- Attackers can continuously guess passwords.
- Authentication endpoints can become overloaded.
- A buggy client can send thousands of requests.
- Multiple API replicas cannot coordinate request limits.
- Provider quotas can be exhausted.
- Database and Redis load can increase unexpectedly.
- Infrastructure costs and service instability can increase.
- Monitoring and health systems may become less reliable during traffic spikes.
What will be implemented?
- Redis-backed rate limiter.
- Configurable limits through environment variables.
- IP-based limits for unauthenticated requests.
- User-based limits for authenticated requests.
- Separate limits for authentication and normal API routes.
- 429 structured error responses.
- Retry-After headers.
- Rate-limit headers such as remaining requests and reset time.
- Trusted proxy configuration for safe client IP detection.
- Special handling when Redis is unavailable.
- Health and metrics endpoints excluded from normal rate limiting.
- Unit, integration, and API tests.
- Detailed manual QA documentation.
- No database migration.
