#!/usr/bin/env bash
# Send a push notification through ntfy.sh. Usage: notify.sh <title> <message> [url]
# Reads the topic from NTFY_TOPIC. Never prints the topic. Always exits 0.
set -uo pipefail

title=${1:-}
message=${2:-}
url=${3:-}
topic=$(printf '%s' "${NTFY_TOPIC:-}" | tr -d '[:space:]')

if [ -z "$topic" ]; then
    echo "notify: ntfy skipped, NTFY_TOPIC is not set" >&2
    exit 0
fi

if ! jq -n --arg topic "$topic" --arg title "$title" --arg message "$message" --arg click "$url" \
    '{topic: $topic, title: $title, message: $message} + (if $click == "" then {} else {click: $click} end)' |
    curl -fsS -o /dev/null -X POST -H 'Content-Type: application/json' --data @- https://ntfy.sh/ 2>/dev/null; then
    echo "notify: ntfy delivery failed" >&2
fi
exit 0
