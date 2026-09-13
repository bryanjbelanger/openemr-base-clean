#!/usr/bin/env bash
# Start (or restart) the already-created docker/development-easy stack and
# verify it's actually reachable, not just "healthy" per Docker.
# Usage: scripts/verify.sh
# Env overrides: MAX_HEALTH_SECONDS (default 180)
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
# shellcheck source=../../docker-dev-build/scripts/lib.sh
source "$ROOT/.claude/skills/docker-dev-build/scripts/lib.sh"
cd "$ROOT/docker/development-easy"

HTTPS_PORT="${WT_HTTPS_PORT:-9300}"
MAX_HEALTH_SECONDS="${MAX_HEALTH_SECONDS:-180}"

if [ -z "$(docker compose ps -a -q 2>/dev/null)" ]; then
  echo "ERROR: no containers found for docker/development-easy. Run the docker-dev-build skill first." >&2
  exit 2
fi

if [ -z "$(docker compose ps --status running -q 2>/dev/null)" ]; then
  echo "==> Starting stopped containers"
  docker compose start
fi

echo "==> Waiting for mysql + openemr to report healthy (up to ${MAX_HEALTH_SECONDS}s)"
if ! wait_for_healthy "$MAX_HEALTH_SECONDS"; then
  echo "ERROR: stack did not become healthy within ${MAX_HEALTH_SECONDS}s." >&2
  dump_logs openemr mysql
  exit 1
fi

echo "==> Checking reachability"
if ! check_reachable "$HTTPS_PORT"; then
  echo "ERROR: OpenEMR is not reachable on https://localhost:${HTTPS_PORT}" >&2
  dump_logs openemr
  exit 1
fi

echo
echo "==> OpenEMR is up and reachable"
print_urls
