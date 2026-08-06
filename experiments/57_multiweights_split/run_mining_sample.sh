#!/usr/bin/env bash
set -uo pipefail
export EVAL_BASE_URL=https://waleedkadous--multibench-gemma-eval-serve-split-serve.modal.run/v1
cd /Users/mwk/Development/faithfamilytechnologynetwork/multibench/.builders/experiment-57
uv --project workflows/judging run python experiments/57_multiweights_split/mine_dpo_split.py
