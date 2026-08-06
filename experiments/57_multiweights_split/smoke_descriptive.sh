#!/usr/bin/env bash
set -uo pipefail
ENVFILE="${TAQWABENCH_ENV:-/Users/mwk/Development/fftn/taqwabench/.env}"
CFG=experiments/57_multiweights_split/configs/multibench_descriptive_split.yaml
RD=experiments/57_multiweights_split/data/output/descriptive_sft_smoke/buddhism
set -a; source "$ENVFILE"; set +a; export EVAL_KEY=EMPTY
echo "=== collect (buddhism, 1 scenario) — cold-starts vLLM endpoint (~10-15m) ==="
uv --project workflows/judging run python -m judging collect traditions/buddhism \
   --config "$CFG" --results-dir "$RD" --scenarios 1
echo "=== judge (gemini) ==="
uv --project workflows/judging run python -m judging judge "$RD/sittings.jsonl" traditions/buddhism \
   --config "$CFG" --results-dir "$RD"
echo "=== SMOKE DONE — judged scores: ==="
python3 -c "import json; [print(j.get('scope'), j.get('framing'), j.get('score')) for j in map(json.loads, open('$RD/judgments.jsonl'))]" 2>/dev/null || echo "(inspect $RD/judgments.jsonl)"
