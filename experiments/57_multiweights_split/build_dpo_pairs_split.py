"""Experiment 57 — build DPO preference pairs from the mined K=4 split-SFT samples (train-half).

Adapted from #48's build_dpo_pairs.py (kept untouched). Reads the mining sittings + their FULL-scope
gemini bands from this experiment's mining dir, groups by CELL (scenario × pressure), and for each
cell with a within-cell full-score gap ≥ GAP builds ONE max-gap pair (chosen = highest, rejected =
lowest). Since we mined the FULL train-half grid there is no extrapolation — the pairs ARE the yield.

Run: uv --project workflows/judging run python experiments/57_multiweights_split/build_dpo_pairs_split.py
Out: data/output/mining/pairs_sft2_mb_split50.jsonl + printed yield table
"""

from __future__ import annotations

import collections
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
MINE = EXP / "data" / "output" / "mining"
TRADITIONS = [
    "buddhism", "eastern-christianity", "judaism", "roman-catholicism",
    "secular-sage", "sunni-islam", "taoism",
]
GAP = 1.0  # min within-cell full-score gap (≥2 rungs on the 0.5-step −1..+1 ladder) — #48 parity


def main():
    pairs = []
    per_trad = collections.Counter()
    per_trad_cells = collections.Counter()
    gap_hist = collections.Counter()
    for t in TRADITIONS:
        sfile = MINE / t / "sittings.jsonl"
        jfile = MINE / t / "judgments.jsonl"
        if not sfile.exists() or not jfile.exists():
            raise FileNotFoundError(
                f"mining data missing for {t}: {sfile} / {jfile} — run mine_dpo_split.py and band "
                "the output (run_mining_judge.sh) before build_dpo_pairs_split.py (fail-fast).")
        score = {}
        for line in jfile.open():
            j = json.loads(line)
            if j["scope"] != "full":
                continue
            score[(j["subject"], j["scenario_id"], j["pressure"])] = j.get("score")
        turns = {}
        for line in sfile.open():
            r = json.loads(line)
            turns[(r["subject"], r["scenario_id"], r["pressure"])] = r["turns"]
        cells = collections.defaultdict(list)
        for (subj, sid, pr), sc in score.items():
            if sc is not None:
                cells[(sid, pr)].append((subj, sc))
        for (sid, pr), samples in cells.items():
            per_trad_cells[t] += 1
            if len(samples) < 2:
                continue
            best = max(samples, key=lambda x: x[1])
            worst = min(samples, key=lambda x: x[1])
            g = best[1] - worst[1]
            gap_hist[round(g, 1)] += 1
            if g >= GAP:
                pairs.append({
                    "tradition": t, "scenario_id": sid, "pressure": pr,
                    "chosen_score": best[1], "rejected_score": worst[1],
                    "chosen_turns": turns[(best[0], sid, pr)],
                    "rejected_turns": turns[(worst[0], sid, pr)],
                })
                per_trad[t] += 1

    out = MINE / "pairs_sft2_mb_split50.jsonl"
    with out.open("w") as f:
        for p in sorted(pairs, key=lambda x: (x["tradition"], x["scenario_id"], x["pressure"])):
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"=== DPO PAIR YIELD — train-half FULL grid (gap ≥ {GAP} full-score within cell) ===")
    print(f"{'tradition':<22}{'cells':>7}{'pairs':>7}{'yield':>8}")
    tp = tc = 0
    for t in TRADITIONS:
        c, p = per_trad_cells[t], per_trad[t]
        tp += p; tc += c
        if c:
            print(f"{t:<22}{c:>7}{p:>7}{100*p/c:>7.0f}%")
    print(f"{'TOTAL':<22}{tc:>7}{tp:>7}{100*tp/max(tc,1):>7.0f}%")
    print(f"\ngap histogram: {dict(sorted(gap_hist.items()))}")
    print(f"wrote {len(pairs)} pairs -> {out}")


if __name__ == "__main__":
    main()
