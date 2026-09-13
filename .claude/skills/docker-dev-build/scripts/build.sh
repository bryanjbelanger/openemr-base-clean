#!/usr/bin/env bash
# Create/start the docker/development-easy stack from a fresh or reset
# checkout, and wait through the first-boot install until OpenEMR is ready.
# Usage: scripts/build.sh
# Env overrides: MAX_INSTALL_SECONDS (default 600), MAX_HEALTH_SECONDS (default 120)
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
# shellcheck source=./lib.sh
source "$ROOT/.claude/skills/docker-dev-build/scripts/lib.sh"
cd "$ROOT/docker/development-easy"

MAX_INSTALL_SECONDS="${MAX_INSTALL_SECONDS:-600}"
MAX_HEALTH_SECONDS="${MAX_HEALTH_SECONDS:-120}"

echo "==> Checking Docker"
docker info >/dev/null 2>&1 || { echo "ERROR: Docker daemon is not running." >&2; exit 1; }

echo "==> Bringing up docker/development-easy"
if command -v openemr-cmd >/dev/null 2>&1; then
  echo "    using openemr-cmd (auto-manages HOST_UID/HOST_GID)"
  openemr-cmd up
else
  echo "    openemr-cmd not found; falling back to docker compose"
  HOST_UID="$(id -u)" HOST_GID="$(id -g)" docker compose up -d
fi

echo "==> Waiting for first-boot install (up to ${MAX_INSTALL_SECONDS}s)"
elapsed=0
until docker compose logs openemr 2>/dev/null | grep -q "Starting apache!"; do
  if [ "$elapsed" -ge "$MAX_INSTALL_SECONDS" ]; then
    echo "ERROR: openemr did not finish installing within ${MAX_INSTALL_SECONDS}s." >&2
    dump_logs openemr
    exit 1
  fi
  sleep 10
  elapsed=$((elapsed + 10))
  echo "    ...still installing (${elapsed}s)"
done

echo "==> Confirming container health (up to ${MAX_HEALTH_SECONDS}s)"
if ! wait_for_healthy "$MAX_HEALTH_SECONDS"; then
  echo "WARNING: install finished but health status did not settle. Run the docker-dev-verify skill to check reachability directly." >&2
fi

echo
echo "==> OpenEMR dev stack is up"
print_urls
echo
echo "Run the docker-dev-verify skill on later runs — it's the fast path."
