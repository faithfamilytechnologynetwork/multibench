#!/usr/bin/env bash
# Poll the gemma-dpo volume until mb-dpo-full training completes (train_log.jsonl written) or a
# workspace-disable is detected. Exits: 0=done, 42=DISABLE (stop-on-disable), 1=timeout.
deadline=$(( $(date +%s) + 4*3600 ))
while :; do
  out=$(modal volume ls gemma-dpo /runs/mb-dpo-full 2>&1)
  if echo "$out" | grep -qi 'disabled'; then echo "DISABLE DETECTED"; exit 42; fi
  if echo "$out" | grep -q 'train_log.jsonl'; then echo "DPO DONE"; echo "$out"; exit 0; fi
  if [ "$(date +%s)" -gt "$deadline" ]; then echo "TIMEOUT"; exit 1; fi
  sleep 300
done
