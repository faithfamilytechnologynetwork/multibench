#!/usr/bin/env bash
# Per-builder test DISPATCHER for porch's implement/review test-check.
#
# porch.checks is GLOBAL (no per-project override), so a single hardcoded command would either
# run the wrong app's tests or break builders that lack another app's toolchain. Instead, this
# script runs the test suite of each top-level app/workflow THIS builder actually touched
# (its diff vs origin/main), looked up in the registry below.
#
# Result: a builder that only touched apps/multibrowser runs ONLY vitest; a Python builder that
# only touched apps/tradition_validator (or workflows/*) runs ONLY its pytest — the other app's
# missing toolchain/node_modules is never an issue, and the right app is always verified.
# Adding an app = one registry line. porch runs this from the worktree root.
set -uo pipefail

# Registry: touched top-level dir -> test command (run from the repo root). "" = unregistered.
test_cmd_for() {
  case "$1" in
    apps/tradition_validator) echo "uv --project apps/tradition_validator run pytest" ;;
    apps/multibrowser)        echo "pnpm -C apps/multibrowser test" ;;
    workflows/judging)        echo "uv --project workflows/judging run pytest workflows/judging" ;;
    *)                        echo "" ;;
  esac
}

base="origin/main"
git rev-parse --verify --quiet "$base" >/dev/null || base="main"

changed=$(git diff --name-only "${base}...HEAD" 2>/dev/null)
touched=$(printf '%s\n' "$changed" | grep -oE '^(apps|workflows)/[^/]+' | sort -u)

if [ -z "${touched//[$'\n']/}" ]; then
  echo "test-dispatcher: no app/workflow changed vs ${base} — nothing to test."
  exit 0
fi

status=0
while IFS= read -r app; do
  [ -z "$app" ] && continue
  cmd="$(test_cmd_for "$app")"
  if [ -z "$cmd" ]; then
    echo "test-dispatcher: '$app' has no registered test command — skipping."
    continue
  fi
  echo "test-dispatcher: $app -> $cmd"
  if ! bash -c "$cmd"; then
    echo "test-dispatcher: FAILED for $app"
    status=1
  fi
done <<EOF
$touched
EOF

[ "$status" -eq 0 ] && echo "test-dispatcher: all touched apps passed."
exit "$status"
