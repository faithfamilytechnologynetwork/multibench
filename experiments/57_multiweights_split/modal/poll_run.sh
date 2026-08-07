#!/usr/bin/env bash
# Poll the gemma-dpo volume for a run's completion marker (config.json is written only on clean
# finish; train_state.pt is unlinked on completion). Background wait — ends the caller's turn.
# Usage: poll_run.sh <run-name> <max-minutes> [done-file]
set -u
RUN="$1"; MAXMIN="${2:-90}"; DONE="${3:-config.json}"
DEADLINE=$(( $(date +%s) + MAXMIN * 60 ))
while :; do
  LS="$(modal volume ls gemma-dpo "/runs/$RUN" 2>/dev/null)"
  if echo "$LS" | grep -q "$DONE"; then
    echo "COMPLETE: /runs/$RUN has $DONE"
    echo "$LS"
    exit 0
  fi
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then
    echo "TIMEOUT after ${MAXMIN}m waiting for /runs/$RUN/$DONE"
    echo "$LS"
    exit 2
  fi
  sleep 60
done
