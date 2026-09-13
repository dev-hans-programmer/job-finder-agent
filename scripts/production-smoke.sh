#!/bin/sh
set -eu

PRODUCTION_URL="${PRODUCTION_URL:-http://localhost:8000}"

live_response=$(curl --fail --silent --show-error "$PRODUCTION_URL/health/live")
case "$live_response" in
  *'"status":"ok"'*) ;;
  *) echo "unexpected production liveness response: $live_response" >&2; exit 1 ;;
esac

ready_response=$(curl --fail --silent --show-error "$PRODUCTION_URL/health/ready")
case "$ready_response" in
  *'"status":"ok"'*) ;;
  *) echo "unexpected production readiness response: $ready_response" >&2; exit 1 ;;
esac

echo "production smoke tests passed"
