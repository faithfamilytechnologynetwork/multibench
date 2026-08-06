"""Read the chat-mode capability panel results (exp-58) from local copies of the volume dirs, print
the cross-programme calibration table, and run the base anchor-guard.

Pull the volume dirs first:
  modal volume get gemma-dpo /runs/capability/base-chat        <local>/base-chat
  ... (mb-sft-guided-chat, mb-sft-dpo-chat, mb-dpo-full-chat)
then: python read_capability.py <dir-holding-the-*-chat-subdirs>

Anchor-guard (architect 2026-08-06, taqwabench base, same harness):
  MMLU 82.8 / GSM8K-CoT strict 95.8 / IFEval prompt-strict 91.7 — base must land within ±3 pts,
  else CONFIG problem → HALT+ping (do not proceed to tuned checkpoints).
"""
from __future__ import annotations
import glob
import json
import sys
from pathlib import Path

ANCHORS = {"mmlu": 82.8, "gsm8k_strict": 95.8, "ifeval_prompt": 91.7}
TOL = 3.0
CKPTS = ["base", "mb-sft-guided", "mb-sft-dpo", "mb-dpo-full"]


def _find_results(d: Path):
    hits = sorted(glob.glob(str(d / "**" / "results*.json"), recursive=True))
    if not hits:
        raise FileNotFoundError(f"no results*.json under {d}")
    return json.loads(Path(hits[-1]).read_text())["results"]


def _metrics(res: dict):
    def g(task, *keys):
        r = res.get(task, {})
        for k in keys:
            if k in r:
                return round(100 * r[k], 2)
        return None
    return {
        "mmlu": g("mmlu", "acc,none"),
        "gsm8k_strict": g("gsm8k_cot", "exact_match,strict-match", "exact_match,flexible-extract"),
        "ifeval_prompt": g("ifeval", "prompt_level_strict_acc,none"),
        "ifeval_inst": g("ifeval", "inst_level_strict_acc,none"),
    }


def main():
    root = Path(sys.argv[1])
    rows = {}
    for c in CKPTS:
        d = root / f"{c}-chat"
        rows[c] = _metrics(_find_results(d)) if d.exists() else None
    print(f"{'checkpoint':<16}{'MMLU':>8}{'GSM8K-s':>9}{'IFEval-p':>10}{'IFEval-i':>10}")
    for c in CKPTS:
        m = rows[c]
        if not m:
            print(f"{c:<16}{'(missing)':>8}")
            continue
        print(f"{c:<16}{m['mmlu']:>8}{m['gsm8k_strict']:>9}{m['ifeval_prompt']:>10}{m['ifeval_inst']:>10}")
    print(f"\ntaqwabench base anchor: MMLU {ANCHORS['mmlu']} / GSM8K-s {ANCHORS['gsm8k_strict']} / "
          f"IFEval-p {ANCHORS['ifeval_prompt']}  (±{TOL})")
    b = rows["base"]
    if not b:
        print("ANCHOR-GUARD: base-chat MISSING — cannot verify. HALT+ping.")
        sys.exit(2)
    off = {k: (b[k], ANCHORS[k]) for k in ANCHORS if b[k] is None or abs(b[k] - ANCHORS[k]) > TOL}
    if off:
        print(f"ANCHOR-GUARD: ❌ OFF-BAND {off} → CONFIG problem, HALT+ping (do NOT decide).")
        sys.exit(1)
    print("ANCHOR-GUARD: ✅ base on-band (±3). Gate-4 = MMLU(mb-dpo-full) vs MMLU(mb-sft-dpo), this run.")
    print(f"\nGATE 4 (chat MMLU): mb-dpo-full={rows['mb-dpo-full']['mmlu']} vs "
          f"incumbent mb-sft-dpo={rows['mb-sft-dpo']['mmlu']} → "
          f"{'PASS' if rows['mb-dpo-full']['mmlu'] >= rows['mb-sft-dpo']['mmlu'] else 'FAIL'}")


if __name__ == "__main__":
    main()
