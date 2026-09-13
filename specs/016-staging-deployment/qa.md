# QA — Staging deployment

## Local isolated staging

1. Copy `.env.staging.example` to `.env.staging`.
2. Replace the password, JWT secret, and image name with staging-only values.
3. Build the image:

```bash
docker build -t job-radar-agent:staging .
```

4. Start dependencies and staging services:

```bash
make staging-up
make staging-migrate
make staging-smoke
```

Expected: staging uses Compose project `job-radar-staging`, API port `8001`, PostgreSQL port `5433`, and Redis port `6380`; smoke tests print `staging smoke tests passed`.

## Isolation checks

```bash
docker compose -p job-radar-staging --env-file .env.staging -f docker-compose.yml -f docker-compose.staging.yml ps
```

Expected: staging PostgreSQL uses the `staging_postgres_data` volume and the staging services are separate from the default local ports.

## Staging observability

- Grafana: `http://localhost:3001`
- Prometheus: `http://localhost:9091`
- Flower: `http://localhost:5556`
- Loki: `http://localhost:3101/ready`
- Tempo: `http://localhost:3201/ready`

Expected: the staging API is scraped and its logs/traces carry staging service names.

## CI deployment prerequisites

On the staging host, install Docker Compose, clone the repository, create `.env.staging`, and authenticate Docker to GHCR. In the GitHub `staging` Environment configure:

- `STAGING_HOST`
- `STAGING_USER`
- `STAGING_APP_DIR`
- `STAGING_SSH_KEY`

Manually run **Staging deployment** from GitHub Actions and optionally provide an image tag. Expected workflow order: build/push image, SSH to host, pull images, run migrations, start services, and run smoke tests.

## Boundary

This spec does not replace the currently running deployment automatically and does not implement rollback. Those behaviors belong to the next deployment spec.

## Sign-off

- [ ] Local staging starts with isolated ports and volumes.
- [ ] Migrations succeed.
- [ ] Smoke tests pass.
- [ ] Staging observability endpoints respond.
- [ ] CI secrets are configured without committing secrets.
