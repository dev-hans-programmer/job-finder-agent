#!/bin/sh
set -eu

STAGING_URL="${STAGING_URL:-http://localhost:8001}"

live_response=$(curl --fail --silent --show-error "$STAGING_URL/health/live")
case "$live_response" in
  *'"status":"ok"'*) ;;
  *) echo "unexpected liveness response: $live_response" >&2; exit 1 ;;
esac

ready_response=$(curl --fail --silent --show-error "$STAGING_URL/health/ready")
case "$ready_response" in
  *'"status":"ok"'*) ;;
  *) echo "unexpected readiness response: $ready_response" >&2; exit 1 ;;
esac

echo "staging smoke tests passed"
