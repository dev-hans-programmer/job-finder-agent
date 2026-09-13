# Plan

1. Add backup, retention, and restore settings.
2. Implement testable PostgreSQL dump, checksum, metadata, and cleanup operations.
3. Add one-shot CLI commands for backup, verify, and restore.
4. Add an independent periodic backup process and Compose service.
5. Add PostgreSQL client tooling to the runtime image.
6. Add unit tests for success, failure, retention, checksum, and credential handling.
7. Document local and production storage/recovery procedures.
