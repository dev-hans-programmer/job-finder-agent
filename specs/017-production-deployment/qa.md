# QA — Production deployment and rollback

## Local dry-run configuration

1. Copy `.env.production.example` to `.env.production`.
2. Replace all placeholder secrets and set a locally available image:

```env
PRODUCTION_IMAGE=job-radar-agent
PRODUCTION_IMAGE_TAG=production
```

3. Build the image:

```bash
docker build -t job-radar-agent:production .
```

4. Validate the merged production configuration:

```bash
docker compose -p job-radar-production \
  --env-file .env.production \
  -f docker-compose.yml -f docker-compose.production.yml config --quiet
```

Expected: configuration validation succeeds and production infrastructure ports are not exposed publicly except the API port.

## Deployment verification

On the production host, run from the repository directory:

```bash
export PRODUCTION_IMAGE=job-radar-agent
export PRODUCTION_IMAGE_TAG=production
./scripts/production-deploy.sh
```

Expected order:

1. Pull application images.
2. Create a database backup.
3. Run Alembic migrations.
4. Start API, worker, scheduler, Flower, and backup.
5. Verify liveness and readiness.
6. Record `CURRENT_IMAGE` and `CURRENT_IMAGE_TAG` in `.production-deployment`.

## Automatic rollback verification

1. Complete one successful deployment so `.production-deployment` records a known-good tag.
2. Deploy an intentionally broken image tag.
3. Confirm smoke tests fail.
4. Inspect the service image tags and deployment output.

Expected: the previous application image tag is pulled and started, and rollback smoke tests pass. The database is not automatically downgraded.

## Manual rollback verification

```bash
export PRODUCTION_IMAGE=ghcr.io/your-org/job-radar-agent
export PRODUCTION_IMAGE_TAG=known-good-commit-sha
./scripts/production-rollback.sh
```

Expected: API, worker, scheduler, Flower, and backup run the requested known-good image and smoke tests pass.

## GitHub Actions verification

Configure the `production` GitHub Environment with:

- `PRODUCTION_HOST`
- `PRODUCTION_USER`
- `PRODUCTION_APP_DIR`
- `PRODUCTION_SSH_KEY`
- `PRODUCTION_IMAGE` for the rollback workflow

Require reviewer approval on the environment. Run **Production deployment** manually and verify build, image publication, SSH deployment, migrations, and smoke tests. Use **Production rollback** with a known-good image tag when rollback is required.

## Migration safety

Use expand-and-contract migrations. Test backups and restores separately. If a destructive schema change must be reversed, stop the application and perform an explicitly approved database restore; an image rollback alone is insufficient.

## Sign-off

- [ ] Production configuration validates.
- [ ] Backup runs before migration.
- [ ] Deployment smoke tests pass.
- [ ] Deployment state records the current image.
- [ ] Automatic application rollback was tested.
- [ ] Manual rollback workflow is protected by production approval.
