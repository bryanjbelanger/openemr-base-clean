#!/usr/bin/env bash
set -uo pipefail

cat >/dev/null
[ "${AGENT_PIPELINE:-}" = "1" ] || exit 0

git_dir="$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --absolute-git-dir)" || exit 1
counter_file="$git_dir/agent-stop-attempts"
marker_file="$git_dir/agent-blocked"

[ -e "$marker_file" ] && exit 0

if out="$("$CLAUDE_PROJECT_DIR/agent-pipeline/checks/check-changed.sh" 2>&1)"; then
  rm -f "$counter_file"
  exit 0
fi

count="$(cat "$counter_file" 2>/dev/null)"
case "$count" in
  '' | *[!0-9]*) count=0 ;;
esac
count=$((10#$count + 1))

if [ "$count" -lt 3 ]; then
  printf '%s\n' "$count" >"$counter_file"
  printf '%s\n' "$out" >&2
  exit 2
fi
printf '%s\n' "$out" >"$marker_file"
rm -f "$counter_file"
exit 0
