"""Experiment 57 — seeded, stratified 50/50 scenario-level split.

Splits the 519 MultiBench scenarios into a TRAIN half and a held-out (HOLDOUT)
half, stratified by tradition, deterministically seeded. The train half drives a
fresh SFT (+DPO) run; the held-out half is a true prompt-level holdout for the
transfer claim. This is the single-fold retrain deferred by #48 (§4.3) and #53.

Scenario universe + exposure come from the committed base reference
`experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv`
(scenario_id, tradition, exposure, base, sft, lift). `exposure` (0..6) is the
count of that scenario's pressure-cells that entered #48's 2,732-example SFT set,
so summing it over the train half gives the EXACT train-half SFT example count
with no re-collection or re-banding — the train-half SFT set is a scenario_id
subset of `/pairs/sft_guided_mb.jsonl` on the Modal gemma-dpo volume.

Deterministic split rule (records fully so it reproduces byte-for-byte):
  for each tradition, sort its scenario_ids ascending, shuffle with
  random.Random(SEED) (Mersenne Twister — stable across CPython 3.x), take the
  first ceil(n/2) as HOLDOUT and the rest as TRAIN. Only secular-sage (49) is
  odd; every other tradition splits evenly. => holdout 260, train 259.

Zero spend, pure local. Run:
  python3 experiments/57_multiweights_split/split.py
"""

import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

SEED = 5757  # experiment 57, 50/50 split — recorded; the lists below are the authority

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
BASE_CSV = REPO / "experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv"
OUT = HERE / "split"

# Expected per-tradition scenario counts (corpus glob == per_scenario.csv), for a hard check.
EXPECTED_COUNTS = {
    "buddhism": 52,
    "eastern-christianity": 106,
    "judaism": 48,
    "roman-catholicism": 76,
    "secular-sage": 49,
    "sunni-islam": 140,
    "taoism": 48,
}


def load_scenarios():
    rows = []
    with BASE_CSV.open() as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "scenario_id": r["scenario_id"],
                    "tradition": r["tradition"],
                    "exposure": int(r["exposure"]),
                }
            )
    return rows


def sha256_list(ids):
    h = hashlib.sha256()
    for sid in ids:
        h.update(sid.encode())
        h.update(b"\n")
    return h.hexdigest()


def main():
    rows = load_scenarios()
    by_trad = defaultdict(list)
    for r in rows:
        by_trad[r["tradition"]].append(r)

    # Hard checks: universe integrity before we split anything.
    assert len(rows) == 519, f"expected 519 scenarios, got {len(rows)}"
    counts = {t: len(v) for t, v in by_trad.items()}
    assert counts == EXPECTED_COUNTS, f"tradition counts mismatch: {counts}"

    train, holdout = [], []
    per_trad = {}
    for trad in sorted(by_trad):
        recs = sorted(by_trad[trad], key=lambda r: r["scenario_id"])
        ids = [r["scenario_id"] for r in recs]
        rng = random.Random(SEED)
        rng.shuffle(ids)
        n_hold = math.ceil(len(ids) / 2)  # holdout gets the extra on odd counts
        hold_ids = sorted(ids[:n_hold])
        train_ids = sorted(ids[n_hold:])
        expo = {r["scenario_id"]: r["exposure"] for r in recs}
        per_trad[trad] = {
            "n_total": len(ids),
            "n_train": len(train_ids),
            "n_holdout": len(hold_ids),
            "train_sft_examples": sum(expo[s] for s in train_ids),
            "holdout_sft_examples": sum(expo[s] for s in hold_ids),
        }
        train += [{"scenario_id": s, "tradition": trad} for s in train_ids]
        holdout += [{"scenario_id": s, "tradition": trad} for s in hold_ids]

    train_ids = sorted(r["scenario_id"] for r in train)
    holdout_ids = sorted(r["scenario_id"] for r in holdout)

    # Disjointness + completeness.
    assert set(train_ids).isdisjoint(holdout_ids), "train/holdout overlap"
    assert set(train_ids) | set(holdout_ids) == {r["scenario_id"] for r in rows}, "union != universe"

    total_train_sft = sum(p["train_sft_examples"] for p in per_trad.values())
    total_holdout_sft = sum(p["holdout_sft_examples"] for p in per_trad.values())
    assert total_train_sft + total_holdout_sft == 2732, "SFT exposure sum != 2732"

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "seed": SEED,
        "rule": "per-tradition: sort ids asc, random.Random(SEED).shuffle, holdout=first ceil(n/2), train=rest",
        "source": "experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv",
        "n_train": len(train_ids),
        "n_holdout": len(holdout_ids),
        "train_sft_examples": total_train_sft,
        "holdout_sft_examples": total_holdout_sft,
        "sft_set_total": total_train_sft + total_holdout_sft,
        "train_sha256": sha256_list(train_ids),
        "holdout_sha256": sha256_list(holdout_ids),
        "per_tradition": per_trad,
    }
    (OUT / "train_scenarios.json").write_text(
        json.dumps({"seed": SEED, "n": len(train_ids), "scenario_ids": train_ids}, indent=2) + "\n"
    )
    (OUT / "holdout_scenarios.json").write_text(
        json.dumps({"seed": SEED, "n": len(holdout_ids), "scenario_ids": holdout_ids}, indent=2) + "\n"
    )
    (OUT / "split_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Human-readable summary to stdout.
    print(f"SEED={SEED}  train={len(train_ids)} scenarios  holdout={len(holdout_ids)} scenarios")
    print(f"train-half SFT examples = {total_train_sft}  (holdout {total_holdout_sft}, sum {total_train_sft + total_holdout_sft})")
    print(f"{'tradition':<22} {'total':>5} {'train':>5} {'hold':>5} {'trainSFT':>9} {'holdSFT':>8}")
    for t in sorted(per_trad):
        p = per_trad[t]
        print(f"{t:<22} {p['n_total']:>5} {p['n_train']:>5} {p['n_holdout']:>5} {p['train_sft_examples']:>9} {p['holdout_sft_examples']:>8}")
    print(f"train_sha256={manifest['train_sha256'][:16]}…  holdout_sha256={manifest['holdout_sha256'][:16]}…")


if __name__ == "__main__":
    main()
