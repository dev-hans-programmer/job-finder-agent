# Implementation plan

1. Add a Compose override with isolated staging resources, ports, volumes, and environment values.
2. Add a staging environment template with required secret placeholders.
3. Add a migration service and readiness smoke-test script.
4. Add Makefile commands for staging lifecycle operations.
5. Add a manually triggered GitHub Actions workflow that builds a GHCR image and deploys it over SSH.
6. Document host prerequisites, required secrets, deployment flow, and boundaries with rollback.
7. Validate Compose interpolation, workflow syntax, smoke-script syntax, and the application quality gate.
