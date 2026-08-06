#!/usr/bin/env bash
# Experiment 57 — G2 mining band: judge the mined train-half sittings FULL-scope with gemini, per
# tradition, into the same mining dir. This is the ~$90 gemini spend (the G2 gate). Resumable (keyed).
# Reuses the descriptive config (judge uses only judges+scopes+concurrency; subjects are ignored).
#
# Usage: run_mining_judge.sh
set -uo pipefail
ENVFILE="${TAQWABENCH_ENV:?set TAQWABENCH_ENV to the path of your taqwabench .env}"
CFG=experiments/57_multiweights_split/configs/multibench_descriptive_split.yaml
MINE=experiments/57_multiweights_split/data/output/mining
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
TRADS=(buddhism eastern-christianity judaism roman-catholicism secular-sage sunni-islam taoism)

set -a; source "$ENVFILE"; set +a
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "OPENROUTER_API_KEY missing"; exit 1; }
cd "$ROOT"
rc=0
for t in "${TRADS[@]}"; do
  echo "=== [$t] judge mining sittings (gemini full-scope) ==="
  uv --project workflows/judging run python -m judging judge "$MINE/$t/sittings.jsonl" "traditions/$t" \
     --config "$CFG" --results-dir "$MINE/$t" || rc=$?
done
echo "MINING-JUDGE DONE rc=$rc"
exit $rc
