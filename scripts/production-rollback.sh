#!/bin/sh
set -eu

: "${PRODUCTION_IMAGE:?PRODUCTION_IMAGE is required}"
: "${PRODUCTION_IMAGE_TAG:?PRODUCTION_IMAGE_TAG is required}"

COMPOSE="${COMPOSE:-docker compose}"
PROJECT="${PRODUCTION_PROJECT:-job-radar-production}"
ENV_FILE="${PRODUCTION_ENV_FILE:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.production.yml"

export PRODUCTION_IMAGE PRODUCTION_IMAGE_TAG
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES pull api worker scheduler flower backup
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES up -d api worker scheduler flower backup
PRODUCTION_URL="${PRODUCTION_URL:-http://localhost:8000}" ./scripts/production-smoke.sh

umask 077
{
  echo "CURRENT_IMAGE=$PRODUCTION_IMAGE"
  echo "CURRENT_IMAGE_TAG=$PRODUCTION_IMAGE_TAG"
} > "${PRODUCTION_STATE_FILE:-.production-deployment}"
echo "production rollback succeeded: $PRODUCTION_IMAGE:$PRODUCTION_IMAGE_TAG"
