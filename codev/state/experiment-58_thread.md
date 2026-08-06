# experiment-58 thread — MultiWeights full-grid DPO (AFB / 100%-train)

## 2026-08-06 — hypothesis + design done; AT PRE-SPEND GATE

**Task**: full-grid DPO for the AFB 100%-train head. Architect revised (10:07Z) to an **incremental**
plan: reuse #48's surviving 487 pairs, mine only the ~239 uncovered scenarios, combine, train ONE fresh
DPO from the SFT checkpoint. Decision rule pre-locked (4 gates vs incumbent `mb-sft-dpo`). Ceiling $300.

**No-spend verification done:**
- Modal `gemma-dpo` volume reachable. `mb-sft-guided` (SFT+ref), `mb-sft-dpo` (incumbent),
  `/pairs/pairs_sft2_mb.jsonl` all present — nothing overwritten.
- Surviving pairs file: **487 pairs**, schema has every field `modal_gemma_dpo2.py` needs
  (`chosen_turns`/`rejected_turns` = full 4-turn arrays). **Reuse is safe, no fallback.**
- Seed-recovery of the #48 mined set is **exact**: `pair ⊄ mined = 0` for all 7 traditions.
  Uncovered = **239 scenarios / 1,434 cells / 5,736 sittings (K=4)**. Manifest committed at
  `experiments/58_multiweights_full_grid_dpo/data/output/uncovered_scenarios.json`.

**Costed plan (from #48 usage anchors):** mine ~$6–8 + **band ~$85–107** (dominant, only >$50 step) +
DPO ~$10–15 + lean battery ~$15–22 = **~$116–152** (pt ~$134). Well under $300.
- Batching won't cut banding: `batch-judge` ~50% off is **Anthropic-only**; our gemini judge falls
  back to live. Banding stays live.

**Next**: STOP. Notified architect with the exact costed plan. Awaiting explicit approval before any
spend. On go: copy #48 scripts, add a `MINE_SCENARIO_MANIFEST` restriction (the one code change),
deploy serve endpoint, mine 5,736 uncovered sittings, reconcile sampling actual before banding.
