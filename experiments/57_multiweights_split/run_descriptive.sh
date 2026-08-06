#!/usr/bin/env bash
# Experiment 57 — descriptive eval driver: collect (split adapter, unstated) + judge (gemini
# full-scope) over all 7 traditions, into per-tradition results dirs. Resumable (keyed cells): re-run
# to mop up any failed/pending cells. Loads OPENROUTER_API_KEY from taqwabench .env; EVAL_KEY=EMPTY.
#
# Usage: run_descriptive.sh <config> <out-subdir> [scenarios_cap]
#   run_descriptive.sh configs/multibench_descriptive_split.yaml descriptive_sft          # full
#   run_descriptive.sh configs/multibench_descriptive_split.yaml descriptive_sft_smoke 1  # 1-scen smoke
set -uo pipefail

CONFIG="$1"; SUB="$2"; SCAP="${3:-}"
ENVFILE="${TAQWABENCH_ENV:-/Users/mwk/Development/fftn/taqwabench/.env}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"     # multibench repo root (worktree)
OUTBASE="experiments/57_multiweights_split/data/output/$SUB"
TRADS=(buddhism eastern-christianity judaism roman-catholicism secular-sage sunni-islam taoism)

set -a; source "$ENVFILE"; set +a
export EVAL_KEY=EMPTY
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "OPENROUTER_API_KEY missing"; exit 1; }

CAPFLAG=(); [ -n "$SCAP" ] && CAPFLAG=(--scenarios "$SCAP")

cd "$ROOT"
rc=0
for t in "${TRADS[@]}"; do
  RD="$OUTBASE/$t"
  echo "=== [$t] collect -> $RD ==="
  uv --project workflows/judging run python -m judging collect "traditions/$t" \
     --config "$CONFIG" --results-dir "$RD" "${CAPFLAG[@]+"${CAPFLAG[@]}"}" || rc=$?
  echo "=== [$t] judge ==="
  uv --project workflows/judging run python -m judging judge "$RD/sittings.jsonl" "traditions/$t" \
     --config "$CONFIG" --results-dir "$RD" || rc=$?
done
echo "DRIVER DONE rc=$rc"
exit $rc
