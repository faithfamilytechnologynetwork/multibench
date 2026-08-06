#!/usr/bin/env bash
# Experiment 57 — one-command resume after the Modal-disable pause. Redeploys the split endpoint,
# warms it up with a DISABLE-AWARE health check (stop-on-disable stays armed), then resumes the
# mining sampler (keyed dedup → continues from the 360 already written, zero rework).
#
# Exit codes: 0 = sampling ran; 3 = workspace DISABLED again (STOP + ping architect, do NOT retry);
#             2 = endpoint warmup timed out (investigate before retrying).
#
# Run ONLY after the architect confirms Modal is stable. Usage: bash .../resume_mining.sh
set -uo pipefail
ROOT=/Users/mwk/Development/faithfamilytechnologynetwork/multibench/.builders/experiment-57
URL=https://waleedkadous--multibench-gemma-eval-serve-split-serve.modal.run
cd "$ROOT"

echo "=== [1/3] redeploy split endpoint ==="
modal deploy experiments/57_multiweights_split/modal/serve_split_eval.py

echo "=== [2/3] warmup /v1/models (disable-aware; up to ~20 min cold start) ==="
DEADLINE=$(( $(date +%s) + 20*60 ))
while :; do
  R="$(curl -sS --max-time 15 "$URL/v1/models" 2>&1)"
  if echo "$R" | grep -qi "disabled"; then
    echo "WORKSPACE DISABLED AGAIN — stop-on-disable armed. STOP + ping architect, do NOT retry."
    exit 3
  fi
  if echo "$R" | grep -q '"id"'; then
    echo "endpoint live: $(echo "$R" | head -c 200)"
    break
  fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then
    echo "WARMUP TIMEOUT (20m). Last response: $(echo "$R" | head -c 200)"
    exit 2
  fi
  sleep 20
done

echo "=== [3/3] resume mining sampling (keyed dedup from 360) ==="
export EVAL_BASE_URL="$URL/v1"
uv --project workflows/judging run python experiments/57_multiweights_split/mine_dpo_split.py
