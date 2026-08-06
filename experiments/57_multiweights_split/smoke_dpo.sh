#!/usr/bin/env bash
set -uo pipefail
ENVFILE="${TAQWABENCH_ENV:?set TAQWABENCH_ENV to the path of your taqwabench .env}"
CFG=experiments/57_multiweights_split/configs/multibench_descriptive_split_dpo.yaml
RD=experiments/57_multiweights_split/data/output/descriptive_dpo_smoke/buddhism
set -a; source "$ENVFILE"; set +a; export EVAL_KEY=EMPTY
echo "=== collect dpo (buddhism, 1 scen) — cold-starts endpoint, validates dpo adapter serves ==="
uv --project workflows/judging run python -m judging collect traditions/buddhism \
   --config "$CFG" --results-dir "$RD" --scenarios 1
echo "=== judge (gemini) ==="
uv --project workflows/judging run python -m judging judge "$RD/sittings.jsonl" traditions/buddhism \
   --config "$CFG" --results-dir "$RD"
echo "=== dpo smoke scores ==="
python3 -c "import json; [print(j.get('subject'),j.get('scope'),j.get('score')) for j in map(json.loads, open('$RD/judgments.jsonl'))]" 2>/dev/null
