#!/usr/bin/env bash
# exp-58 banding: full-scope gemini judge over the mined sittings, per tradition (resumable).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
set -a; source /Users/mwk/Development/fftn/taqwabench/.env; set +a
CFG=experiments/58_multiweights_full_grid_dpo/configs/samplability.yaml
M=experiments/58_multiweights_full_grid_dpo/data/output/mining
for t in buddhism eastern-christianity judaism roman-catholicism secular-sage sunni-islam taoism; do
  echo "=== banding $t ($(wc -l < $M/$t/sittings.jsonl) sittings) ==="
  uv --project workflows/judging run python -m judging judge \
     "$M/$t/sittings.jsonl" "traditions/$t" --results-dir "$M/$t" --config "$CFG"
done
echo "ALL BANDING DONE"
