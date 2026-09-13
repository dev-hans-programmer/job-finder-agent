Audit logging
Audit logging records security-sensitive and important business actions, such as:
- User registration, login, logout, failed login
- Password reset and email verification
- Account lockout
- Role creation and role assignment
- Session/device revocation
- Source creation, updates, and deletion
- Ingestion run triggers and outcomes
- Administrative changes
What it solves
- Security investigations and incident response
- Detecting suspicious activity
- Compliance and accountability
- Understanding who changed what and when
- Debugging production behavior
- Tracking administrative actions
Each audit event should include:
id
timestamp
actor_user_id
action
resource_type
resource_id
success
ip_address
user_agent
request_id
metadata
Example:
{
  "action": "user.login.failed",
  "actor_user_id": null,
  "resource_type": "user",
  "resource_id": "user-id",
  "success": false,
  "ip_address": "192.168.1.10",
  "metadata": {
    "reason": "invalid_credentials"
  }
}
Problems without it
- No reliable record of who performed an action
- Difficult investigation after account compromise
- Failed logins and suspicious activity may be invisible
- Administrative changes cannot be traced
- Logs may be incomplete or inconsistent
- Compliance requirements may not be met
Planned implementation
I’ll add:
1. audit_events PostgreSQL table with an Alembic migration.
2. Audit event model and repository.
3. An audit service with a consistent event API.
4. Integration into authentication and security flows.
5. Integration into role, session, source, and ingestion actions.
6. Request metadata capture:
   - user
   - IP
   - user agent
   - request ID
7. Structured logging for audit events.
8. Tests across unit, integration, and API layers.
9. QA documentation with manual verification steps.
10. 100% test and branch coverage maintained.
