#!/bin/sh
set -eu

: "${PRODUCTION_IMAGE:?PRODUCTION_IMAGE is required}"
: "${PRODUCTION_IMAGE_TAG:?PRODUCTION_IMAGE_TAG is required}"

COMPOSE="${COMPOSE:-docker compose}"
PROJECT="${PRODUCTION_PROJECT:-job-radar-production}"
ENV_FILE="${PRODUCTION_ENV_FILE:-.env.production}"
STATE_FILE="${PRODUCTION_STATE_FILE:-.production-deployment}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.production.yml"

previous_tag=""
if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC1090
  . "$STATE_FILE"
  previous_tag="${CURRENT_IMAGE_TAG:-}"
fi

if [ -z "$previous_tag" ]; then
  echo "No previous production image is recorded; automatic rollback is unavailable for the first deployment." >&2
fi

export PRODUCTION_IMAGE PRODUCTION_IMAGE_TAG
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES pull api worker scheduler flower backup
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES run --rm backup python -m app.backup.cli backup
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES run --rm migrate
$COMPOSE -p "$PROJECT" --env-file "$ENV_FILE" $COMPOSE_FILES up -d api worker scheduler flower backup

if ! PRODUCTION_URL="${PRODUCTION_URL:-http://localhost:8000}" ./scripts/production-smoke.sh; then
  if [ -n "$previous_tag" ]; then
    PRODUCTION_IMAGE_TAG="$previous_tag" PRODUCTION_STATE_FILE="$STATE_FILE" \
      PRODUCTION_ENV_FILE="$ENV_FILE" PRODUCTION_PROJECT="$PROJECT" \
      ./scripts/production-rollback.sh
  fi
  exit 1
fi

umask 077
{
  echo "CURRENT_IMAGE=$PRODUCTION_IMAGE"
  echo "CURRENT_IMAGE_TAG=$PRODUCTION_IMAGE_TAG"
} > "$STATE_FILE"
echo "production deployment succeeded: $PRODUCTION_IMAGE:$PRODUCTION_IMAGE_TAG"
