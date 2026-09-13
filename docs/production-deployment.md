# Production deployment

Production deployment is intentionally manual and approval-gated. The deployment uses immutable container image tags, creates a database backup before migrations, starts the new application version, and runs liveness/readiness smoke tests.

## Required host setup

The production host must have Docker Compose, the repository checkout, authenticated access to the container registry, and a `.env.production` file created from `.env.production.example`. Never commit that file or production credentials.

## Deployment

The normal deployment command is:

```bash
export PRODUCTION_IMAGE=ghcr.io/your-org/job-radar-agent
export PRODUCTION_IMAGE_TAG=commit-sha
./scripts/production-deploy.sh
```

The script uses Compose project `job-radar-production`, runs a backup, applies migrations, starts the application processes, runs smoke checks, and records the successful image in `.production-deployment`.

## Rollback

Rollback restores application containers to a known-good image tag:

```bash
export PRODUCTION_IMAGE=ghcr.io/your-org/job-radar-agent
export PRODUCTION_IMAGE_TAG=known-good-commit-sha
./scripts/production-rollback.sh
```

The deployment script invokes this automatically when a previous image is recorded and post-deployment smoke tests fail. Database schema changes are not automatically rolled back. Use the verified backup and an explicitly approved restore procedure when database recovery is required.

## GitHub Actions

The `Production deployment` workflow builds and publishes a commit-tagged image, then deploys over SSH through the protected `production` environment. The `Production rollback` workflow accepts a known-good image tag and runs the rollback script. Configure production environment approval rules and the secrets listed in the Spec 017 QA guide.
