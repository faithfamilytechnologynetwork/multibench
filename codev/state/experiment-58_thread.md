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

## 2026-08-06 — GO approved (10:12Z); executing

- Scripts copied into `experiments/58_multiweights_full_grid_dpo/`. `mine_dpo_sample.py` gained a
  `MINE_SCENARIO_MANIFEST` env → mines exactly the uncovered list (verified 239 → 5,736 K=4 tasks).
  serve/capability wired to new head `mb-dpo-full`. Committed (87f722d).
- Serve endpoint deployed for mining (serves `sft`): `https://waleedkadous--multibench-gemma-eval-serve-serve.modal.run`
- Smoke-testing `sft` (background bbq7zgjem) to separate cold-start from broken before the ~5h mine.
- **Next on smoke OK**: launch full uncovered mine (background, resumable) → reconcile sampling actual
  → band (~$95, dominant) → build+combine pairs → DPO `mb-dpo-full` → lean battery → 4-gate compare.

## 2026-08-06 — mine running healthy; capability measurement-defect fix (13:39Z)

- Mine `b6b02mw2u` healthy & ahead of estimate: 4,635/5,736 sittings, 5 traditions complete
  (per-tradition counts exactly match manifest), sunni-islam + taoism remaining.
- **Architect: #48 capability numbers are RAW-COMPLETION artifacts** (MMLU 0.467 vs ~85-class chat).
  Gate-4 MMLU threshold 0.4424 is VOID. Fix applied to exp-58:
  - `modal/modal_gemma_capability.py` rewritten from taqwabench's chat=True script: FOUR-checkpoint
    chat-mode panel (base, mb-sft-guided, mb-sft-dpo, mb-dpo-full), `--apply_chat_template
    --fewshot_as_multiturn`, max_len 8192, `-chat` output dirs. Run once after the head exists.
  - Gate 4 re-anchors to chat-mode MMLU(mb-dpo-full) ≥ MMLU(mb-sft-dpo), both from this rerun.
  - **Anchor guard**: sanity-check chat-mode BASE vs model-card/RedHat before deciding; off-class → STOP+ping.
  - Budget +15–25 for the 4-checkpoint panel → revised total **~$130–174**; ceiling 300 unchanged.
- Mining/banding/DPO legs unaffected — continuing.
