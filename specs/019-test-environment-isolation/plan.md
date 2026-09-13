# Implementation plan

1. Add isolated testing PostgreSQL and Redis Compose services.
2. Force test environment variables in `tests/conftest.py` before importing application modules.
3. Add Makefile lifecycle and migration commands for the test services.
4. Update CI service ports, credentials, and migration command.
5. Add testing environment documentation and manual verification.
6. Validate that the test stack is separated from local/staging/production projects and run the full quality gate.
