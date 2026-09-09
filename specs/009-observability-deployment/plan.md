# Implementation plan

1. Add structured logging context and redaction filters.
2. Add metrics instrumentation around runs, matching, LLM calls, and delivery.
3. Add live/ready/provider health diagnostics.
4. Add authenticated deletion and retention jobs.
5. Add Docker production files and CI workflow.
6. Add migration, backup/restore, security, and coverage checks.
7. Write runbooks for source outage, provider credentials, migration rollback, and restore.

No destructive production operation may run without an explicit target and audit log.
