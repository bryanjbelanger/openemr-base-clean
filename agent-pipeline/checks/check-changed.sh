#!/usr/bin/env bash
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1
lint_file="agent-pipeline/checks/lint-file.sh"

git fetch --quiet origin main 2>/dev/null || true
if ! git rev-parse --verify --quiet origin/main >/dev/null; then
  echo "check-changed: origin/main not found"
  exit 1
fi

base="$(git merge-base HEAD origin/main)"
php_files=()
js_files=()
while IFS= read -r f; do
  [ -f "$f" ] || continue
  case "$f" in
    *.php) php_files+=("$f") ;;
    *.js | *.mjs) js_files+=("$f") ;;
  esac
done < <({ git diff --name-only --diff-filter=ACMR "$base"; git ls-files --others --exclude-standard; } | sort -u)

if [ ${#php_files[@]} -eq 0 ] && [ ${#js_files[@]} -eq 0 ]; then
  exit 0
fi

fail() {
  echo "check-changed: $1 failed"
  printf '%s\n' "${2%$'\n'}" | tail -n 40
  exit 1
}

lint_out=""
for f in ${php_files[@]+"${php_files[@]}"} ${js_files[@]+"${js_files[@]}"}; do
  if ! out="$("$lint_file" "$f" 2>&1)"; then
    lint_out+="-- $f"$'\n'"$out"$'\n'
  fi
done
[ -z "$lint_out" ] || fail lint "$lint_out"

if [ ${#php_files[@]} -gt 0 ]; then
  if ! out="$(vendor/bin/phpstan analyze --no-progress --error-format=raw --memory-limit=4G --configuration=.phpstan/phpstan.ci.neon "${php_files[@]}" 2>&1)"; then
    case "$out" in
      *"No files found to analyse"*) ;;
      *) fail phpstan "$out" ;;
    esac
  fi
  out="$(vendor/bin/phpunit -c phpunit-isolated.xml 2>&1)" || fail phpunit "$out"
fi

if [ ${#js_files[@]} -gt 0 ]; then
  out="$(npm run --silent test:js 2>&1)" || fail jest "$out"
fi

exit 0
