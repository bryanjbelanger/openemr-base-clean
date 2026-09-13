#!/usr/bin/env bash
# Shared helpers for the docker-dev-build / docker-dev-verify skills.
# Source this file; it is not meant to be executed directly.
# Assumes the caller has already `cd`ed into docker/development-easy.

# wait_for_healthy <max_seconds>
# Polls the mysql + openemr services' Docker healthcheck status.
# Prints the last-seen statuses to stderr and returns 1 on timeout.
wait_for_healthy() {
  local max_seconds="$1" elapsed=0
  local mysql_id openemr_id mysql_status openemr_status
  while [ "$elapsed" -lt "$max_seconds" ]; do
    mysql_id="$(docker compose ps -q mysql)"
    openemr_id="$(docker compose ps -q openemr)"
    mysql_status="$(docker inspect --format '{{.State.Health.Status}}' "$mysql_id" 2>/dev/null || echo unknown)"
    openemr_status="$(docker inspect --format '{{.State.Health.Status}}' "$openemr_id" 2>/dev/null || echo unknown)"
    if [ "$mysql_status" = healthy ] && [ "$openemr_status" = healthy ]; then
      return 0
    fi
    sleep 5
    elapsed=$((elapsed + 5))
  done
  echo "mysql=${mysql_status:-unknown} openemr=${openemr_status:-unknown}" >&2
  return 1
}

# check_reachable <https_port>
# Curls the internal health endpoint and the login page through the mapped
# host port. Self-signed dev cert, so --insecure is expected, not a real
# TLS problem.
check_reachable() {
  local https_port="$1" http_code
  curl --insecure --fail --silent --show-error "https://localhost:${https_port}/meta/health/readyz" >/dev/null || return 1
  http_code="$(curl --insecure --silent --output /dev/null --write-out '%{http_code}' "https://localhost:${https_port}/")"
  case "$http_code" in
    2??|3??) return 0 ;;
    *) echo "login page returned HTTP ${http_code}" >&2; return 1 ;;
  esac
}

# print_urls
# Human-readable summary of where the stack is reachable, honoring any
# WT_* port overrides (see docker-dev-build/references/environment.md).
print_urls() {
  echo "    https://localhost:${WT_HTTPS_PORT:-9300}  (login: admin / pass)"
  echo "    http://localhost:${WT_HTTP_PORT:-8300}"
  echo "    phpMyAdmin: http://localhost:${WT_PMA_PORT:-8310}"
}

# dump_logs <service> [service...]
# Prints the tail of the named services' logs to stderr for diagnosis.
dump_logs() {
  docker compose logs --tail 50 "$@" >&2
}
