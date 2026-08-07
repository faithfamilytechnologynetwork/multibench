#!/usr/bin/env bash
# Fire once mining sampling is underway (count climbs past the 360 resume point), then measure the
# true throughput + ETA. Catches a pathologically slow endpoint early. Bounded; ends the turn.
set -u
MINE=experiments/57_multiweights_split/data/output/mining
BASE=360; TARGET=6216
cnt(){ cat $MINE/*/sittings.jsonl 2>/dev/null | wc -l | tr -d ' '; }
DEADLINE=$(( $(date +%s) + 25*60 ))
until [ "$(cnt)" -gt $((BASE+30)) ]; do
  [ "$(date +%s)" -ge "$DEADLINE" ] && { echo "SAMPLING NOT PROGRESSING after 25m (warmup slow/failed/disabled?) — count=$(cnt)"; exit 2; }
  sleep 30
done
c1=$(cnt); t1=$(date +%s); sleep 90; c2=$(cnt); t2=$(date +%s)
rate=$(python3 -c "print(f'{($c2-$c1)/($t2-$t1)*60:.1f}')")
eta=$(python3 -c "r=($c2-$c1)/($t2-$t1); print('stalled' if r<=0 else f'{($TARGET-$c2)/r/60:.0f} min')")
echo "THROUGHPUT: $c1 -> $c2 = $rate sittings/min; count $c2/$TARGET; ETA ~$eta"
