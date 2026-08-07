#!/usr/bin/env bash
# Verified upload to the gemma-dpo volume (experiment 57) — guards the exp-58 silent-corruption scar.
# Computes local sha256 + line count, puts, then verifies the VOLUME-SIDE sha256 + lines via
# modal_volume_verify.py, retrying the put until they match (up to 3 tries). Fails loud otherwise.
#
# Usage: verified_put.sh <local-file> <volume-dest e.g. /pairs/pairs_sft2_mb_split50.jsonl>
set -uo pipefail
LOCAL="$1"; DEST="$2"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
[ -f "$LOCAL" ] || { echo "local file missing: $LOCAL"; exit 1; }

LSHA=$(shasum -a 256 "$LOCAL" | awk '{print $1}')
LLINES=$(wc -l < "$LOCAL" | tr -d ' ')
echo "local: sha=$LSHA lines=$LLINES file=$LOCAL"

for attempt in 1 2 3; do
  echo "=== put attempt $attempt -> $DEST ==="
  modal volume put --force gemma-dpo "$LOCAL" "$DEST"
  R=$(modal run experiments/57_multiweights_split/modal/modal_volume_verify.py --path "$DEST" 2>/dev/null | grep '"sha256"' | tail -1)
  VSHA=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['sha256'])" "$R" 2>/dev/null || echo "ERR")
  VLINES=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['lines'])" "$R" 2>/dev/null || echo "ERR")
  echo "volume: sha=$VSHA lines=$VLINES"
  if [ "$VSHA" = "$LSHA" ] && [ "$VLINES" = "$LLINES" ]; then
    echo "VERIFIED OK (sha + lines match) on attempt $attempt"
    exit 0
  fi
  echo "MISMATCH on attempt $attempt — retrying"
done
echo "FAILED: volume copy never matched local after 3 attempts — DO NOT train on it"
exit 2
