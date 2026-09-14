#!/usr/bin/env bash
set -uo pipefail

file="$(jq -r '.tool_input.file_path' 2>/dev/null)" || exit 0
if [ -z "$file" ] || [ "$file" = "null" ]; then
  exit 0
fi

case "$file" in
  /*) ;;
  *) file="$CLAUDE_PROJECT_DIR/$file" ;;
esac
[ -e "$file" ] || exit 0

if out="$("$CLAUDE_PROJECT_DIR/agent-pipeline/checks/lint-file.sh" "$file" 2>&1)"; then
  exit 0
fi
printf '%s\n' "$out" >&2
exit 2
