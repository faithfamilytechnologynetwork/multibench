#!/usr/bin/env bash
# Bake the #51 raw tier into the Railway deploy bundle, then deploy (Spec 51 Decision 14).
#
# Railway respects .gitignore by DEFAULT, so the gitignored public/data-raw/ must be force-
# uploaded with `--no-gitignore`; .railwayignore then re-excludes node_modules/dist. The baked
# copy is the same GZ shards as the committed results-raw/ tier (identical fingerprint) — the
# SPA prefers it (same-origin, no GitHub rate limits) and falls back to the committed GitHub
# tier when it's absent or stale.
#
# Run from the REPO ROOT:
#   apps/multibrowser/scripts/bake-and-deploy.sh <run-id> <run-root>...
# e.g.
#   apps/multibrowser/scripts/bake-and-deploy.sh 20260803 \
#     tmp/judging-runs/20260803-merged \
#     tmp/judging-runs/20260803-unstated-opus \
#     tmp/judging-runs/20260803-framings-opus-sample
#
# NOTE: production deploy is architect-driven (post-merge). This script is the documented wiring.
set -euo pipefail

RUN_ID="${1:?usage: bake-and-deploy.sh <run-id> <run-root>...}"; shift
[ "$#" -ge 1 ] || { echo "error: at least one run-root is required" >&2; exit 2; }

OUT="apps/multibrowser/public/data-raw"
echo "› baking gz raw tier for run '$RUN_ID' into $OUT/$RUN_ID …"
rm -rf "${OUT:?}/$RUN_ID"
uv --project workflows/analysis run python -m analysis export-raw "$@" --run-id "$RUN_ID" --out "$OUT"

echo "› deploying (railway up --no-gitignore) …"
( cd apps/multibrowser && railway up --no-gitignore )
echo "✓ done. The baked bundle is served same-origin at /data-raw/$RUN_ID/."
