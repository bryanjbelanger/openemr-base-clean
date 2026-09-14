#!/usr/bin/env bash
set -uo pipefail

if [ $# -lt 1 ]; then
  echo "usage: lint-file.sh <file>" >&2
  exit 2
fi

[ -e "$1" ] || exit 0
file="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
cd "$(git rev-parse --show-toplevel)" || exit 1

report=""
run_tool() {
  local name="$1"
  shift
  local out
  if ! out="$("$@" 2>&1)"; then
    report+="== $name =="$'\n'"$out"$'\n'
  fi
}

case "$file" in
  *.php)
    run_tool "php -l" php -l "$file"
    run_tool "phpcs" vendor/bin/phpcs -q --warning-severity=0 --report=emacs "$file"
    ;;
  *.js | *.mjs)
    run_tool "eslint" npx --no-install eslint --quiet "$file"
    ;;
  *)
    exit 0
    ;;
esac

if [ -n "$report" ]; then
  printf '%s' "$report" | head -n 20
  exit 1
fi
exit 0
