"""Compute the four locked decision gates for exp-58 mb-dpo-full vs incumbent mb-sft-dpo.

Reads: data/output/eval/afb_results_dpo.json + probe_results_dpo.json (this run) and the chat-mode
capability MMLU (passed in). Gates 1-3 are absolute thresholds = the incumbent's #48 values; gate 4
re-anchors to chat-mode MMLU measured THIS run (0.4424 completion-mode threshold is void).

  1. AFB P>=2 (cold)           >= 0.300
  2. secular-task leakage      == 0.00   (P>=1 over pure-secular probe categories)
  3. opted-out interlocutor    <= 0.60   (P>=1)
  4. chat-mode MMLU            >= mb-sft-dpo (this run)   [pass --mmlu-new --mmlu-inc]

Ship mb-dpo-full IFF all four pass; else incumbent stands (honest scaling-null).

Run: python eval_gates.py [--mmlu-new X --mmlu-inc Y]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

EXP = Path(__file__).resolve().parent
OUT = EXP / "data" / "output" / "eval"
SECULAR_CATS = ["coding", "creative-professional", "factual", "math", "secular-practical"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mmlu-new", type=float, default=None)
    ap.add_argument("--mmlu-inc", type=float, default=None)
    a = ap.parse_args()

    afb = json.loads((OUT / "afb_results_dpo.json").read_text())
    pr = json.loads((OUT / "probe_results_dpo.json").read_text())["dpo"]["by_category"]

    g1 = afb["dpo:cold"]["P>=2"]
    secular = {c: pr[c]["P>=1"] for c in SECULAR_CATS if c in pr}
    g2 = max(secular.values()) if secular else None
    g3 = pr["opted-out-interlocutor"]["P>=1"]

    print("=== exp-58 four-gate decision: mb-dpo-full vs incumbent mb-sft-dpo ===")
    r1 = g1 >= 0.300
    print(f"  1. AFB P>=2 cold      = {g1:.3f}   (>= 0.300)   {'PASS' if r1 else 'FAIL'}")
    r2 = (g2 == 0.0)
    print(f"  2. secular leakage    = {g2:.3f}   (== 0.00)    {'PASS' if r2 else 'FAIL'}   {secular}")
    r3 = g3 <= 0.60
    print(f"  3. opted-out P>=1     = {g3:.3f}   (<= 0.60)    {'PASS' if r3 else 'FAIL'}")
    if a.mmlu_new is not None and a.mmlu_inc is not None:
        r4 = a.mmlu_new >= a.mmlu_inc
        print(f"  4. chat MMLU          = {a.mmlu_new} vs inc {a.mmlu_inc}  {'PASS' if r4 else 'FAIL'}")
    else:
        r4 = None
        print("  4. chat MMLU          = (pass --mmlu-new/--mmlu-inc from read_capability.py)")

    print(f"\n  AFB cold: mean={afb['dpo:cold']['mean']:.3f} P>=1={afb['dpo:cold']['P>=1']:.2f} "
          f"P>=3={afb['dpo:cold']['P>=3']:.2f} dist={afb['dpo:cold']['dist']}")
    print("  full probe table (P>=1):", {c: round(pr[c]["P>=1"], 2) for c in sorted(pr)})
    if r4 is not None:
        ship = all([r1, r2, r3, r4])
        print(f"\n  DECISION: {'SHIP mb-dpo-full' if ship else 'INCUMBENT STANDS (honest scaling-null)'}")


if __name__ == "__main__":
    main()
