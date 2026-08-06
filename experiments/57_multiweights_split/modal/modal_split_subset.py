"""Build the train-half SFT subset on the Modal gemma-dpo volume (experiment 57).

The 2,732-example SFT set `/pairs/sft_guided_mb.jsonl` (from #48, WITH `scenario_id` fields) is
subset to the 259 train-half scenarios of the committed 50/50 split. The output
`/pairs/sft_guided_mb_split50train.jsonl` is what `modal_gemma_sft.py` trains `mb-sft-split50` on.

CROSS-CHECK: the kept count MUST equal 1,362 (the exposure-derived train-half SFT count from
split_manifest.json). A mismatch means the exposure-based costing assumption is wrong — STOP.

Zero training, CPU-only, negligible cost. Run from repo root:
  modal run experiments/57_multiweights_split/modal/modal_split_subset.py
"""

import modal

app = modal.App("mb-split-subset")
vol = modal.Volume.from_name("gemma-dpo")
image = modal.Image.debian_slim(python_version="3.12")

EXPECTED_KEPT = 1362  # from experiments/57_multiweights_split/split/split_manifest.json


@app.function(image=image, volumes={"/vol": vol}, timeout=600)
def build(src: str, dst: str, train_ids: list, expected: int):
    import collections
    import json

    train = set(train_ids)
    rows = [json.loads(l) for l in open(f"/vol{src}")]
    kept = [r for r in rows if r["scenario_id"] in train]
    scen_present = {r["scenario_id"] for r in kept}
    per_prefix = collections.Counter(r["scenario_id"].split("-")[0] for r in kept)

    with open(f"/vol{dst}", "w") as f:
        for r in kept:
            f.write(json.dumps(r) + "\n")
    vol.commit()

    print(f"src rows      = {len(rows)}")
    print(f"kept          = {len(kept)}  (expected {expected})")
    print(f"train scen in SFT set = {len(scen_present)} / {len(train)} train scenarios "
          f"({len(train) - len(scen_present)} zero-exposure train scen not present)")
    print(f"sample row keys = {sorted(rows[0].keys())}")
    print(f"per id-prefix   = {dict(sorted(per_prefix.items()))}")
    assert len(kept) == expected, f"KEPT {len(kept)} != EXPECTED {expected} — exposure assumption wrong, STOP"
    print(f"wrote /vol{dst}")
    return {"kept": len(kept), "scen_present": len(scen_present)}


@app.local_entrypoint()
def main(src: str = "/pairs/sft_guided_mb.jsonl",
         dst: str = "/pairs/sft_guided_mb_split50train.jsonl"):
    import json
    import pathlib

    ids = json.loads(
        pathlib.Path("experiments/57_multiweights_split/split/train_scenarios.json").read_text()
    )["scenario_ids"]
    res = build.remote(src, dst, ids, EXPECTED_KEPT)
    print("RESULT:", res)
