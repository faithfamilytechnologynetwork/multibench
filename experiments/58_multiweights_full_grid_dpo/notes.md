# Experiment 58: MultiWeights full-grid DPO (AFB / 100%-train track)

**Status**: In Progress — at the pre-spend gate (no spend yet)

**Date**: 2026-08-06

**Driving issue**: #58 · **Predecessor**: `experiments/48_multiweights_omissive_bias/` (review:
`codev/reviews/48-multiweights-omissive-bias.md`). **Incumbent deliverable**: `mb-sft-dpo`.

## Goal

Does mining the **full scenario grid** (not the #48 40-scenario/tradition scoped subset) for stage-2
DPO produce a head that is **weakly better** than the incumbent `mb-sft-dpo` on all four locked gates?

- **Hypothesis (H1)**: A DPO head trained on the full-grid pair set (~900 within-cell max-gap pairs vs
  the incumbent's 487) is **at least as good** as `mb-sft-dpo` on every gate below.
- **Null (H0, the honest scaling-null)**: More pairs from the same policy add no behavioural signal;
  the incumbent stands. #48 already found DPO here is a *weak-signal* win (train pref_acc ≈ chance,
  0.538) because the SFT model already emits good counsel — so H0 is a live, respectable outcome.

### Decision rule (architect-locked, pre-registered before any numbers)

Ship the new head `mb-dpo-full` **iff it is weakly better (≥) than `mb-sft-dpo` on ALL FOUR gates**:

| # | Gate | Direction | Incumbent (`mb-sft-dpo`) | Threshold to ship |
|---|------|-----------|--------------------------|-------------------|
| 1 | AFB P≥2 (meaningful, cold, gpt-5.6-terra 0–4) | higher better | 0.30 | **≥ 0.300** |
| 2 | Secular-task leakage | must hold | 0.00 | **exactly 0.00** |
| 3 | Opted-out interlocutor P≥1 | lower better | 0.60 | **≤ 0.60** |
| 4 | MMLU | higher better | 0.4424 | **≥ 0.4424** |

Any gate missed → **incumbent stands**, and this is reported as an honest scaling-null. No re-scoring,
no gate relaxation after numbers land.

## Approach (architect-revised 2026-08-06 — incremental, NOT full re-mine)

The #48 scoped pairs **survive** and are **on-policy consistent** with new pairs: both are mined from
`mb-sft-guided`, which is **unchanged** on the volume. So we mine only the *complement* and combine.

1. **Recover** the #48 scoped-mining scenario set from the seed logic (`PER_TRAD=40`, pilot first-10 +
   `Random(3446+i).sample(rest, 30)` per tradition) — verified below.
2. **Mine only the 239 uncovered scenarios** (1,434 cells, K=4 @ temp 1.3 from `mb-sft-guided`).
3. **Band** those sittings full-scope (gemini-3.6-flash), build max-gap pairs (gap ≥ 1.0).
4. **Combine** new pairs with the surviving 487 → a ~900-pair full-grid set.
5. **Train ONE fresh DPO** from the SFT checkpoint (`--sft-run mb-sft-guided`, reference = SFT, **new**
   `--run-name mb-dpo-full`). *Not* a continue-train from `mb-sft-dpo` — that would cost reproducibility
   and muddy the clean incumbent comparison for zero saving.
6. **Lean battery** on `mb-dpo-full` only (AFB-150 cold + 70 over-application probes + capability) →
   apply the locked rule.

### Why reuse is safe — verified (no spend)

- `/pairs/pairs_sft2_mb.jsonl` on `gemma-dpo`: **487 pairs**, schema
  `{tradition, scenario_id, pressure, chosen_score, rejected_score, chosen_turns, rejected_turns}` —
  exactly the fields `modal_gemma_dpo2.py` consumes. `chosen_turns`/`rejected_turns` are full 4-turn
  `[user, assistant, user, assistant]` arrays. Gap present (e.g. +1.0 vs −1.0). **No fallback needed.**
- `/runs/mb-sft-guided/adapter` present (DPO init **and** frozen reference); `/runs/mb-sft-dpo`
  present (incumbent, never overwritten).
- **Seed-recovery is exact**: for every tradition, *zero* pair-producing scenarios fall outside the
  reconstructed mined set (`pair ⊄ mined = 0`, all 7). The reconstruction perfectly contains observed
  coverage → the uncovered complement is correct.

### Recovered grid arithmetic

| tradition | scenarios | mined (#48) | uncovered | uncov. cells |
|---|---:|---:|---:|---:|
| buddhism | 52 | 40 | 12 | 72 |
| eastern-christianity | 106 | 40 | 66 | 396 |
| judaism | 48 | 40 | 8 | 48 |
| roman-catholicism | 76 | 40 | 36 | 216 |
| secular-sage | 49 | 40 | 9 | 54 |
| sunni-islam | 140 | 40 | 100 | 600 |
| taoism | 48 | 40 | 8 | 48 |
| **TOTAL** | **519** | **280** | **239** | **1,434** |

Uncovered sittings to mine: **1,434 × K=4 = 5,736**. Manifest committed at
`data/output/uncovered_scenarios.json` (deterministic; regenerable from the seed). Expected new pairs
≈ 29% yield × 1,434 ≈ **~416** → combined **~903** pairs.

## Costed plan (exact, anchored to #48 usage actuals)

**Per-sitting banding anchor from #48 actuals**: mining band cost $0.0149/sitting ($100 / 6,720 and
$75 / 5,040 both reconcile). Sampling (endpoint GPU) $5 / 5,040 sittings. DPO $7 / 487 pairs (B200,
~1.1 h). All figures below computed from those anchors.

| Step | Work | Est. | Basis |
|------|------|-----:|-------|
| A. Mine uncovered | 5,736 sittings, endpoint GPU | **$6–8** | 5.7k × ($5/5.04k) + spin/idle |
| B. **Band uncovered** (gemini full-scope) | 5,736 judgments | **$85–107** | 5,736 × $0.0149–0.0187 |
| C. Build + combine pairs | local, no API | **$0** | — |
| D. DPO train (B200, ~900 pairs) | 1 epoch, fresh from SFT | **$10–15** | 900/487 × $7 |
| E. Lean battery (`mb-dpo-full` only) | AFB-150 cold + 70 probes + capability | **$15–22** | endpoint GPU + terra + MMLU |
| | **TOTAL** | **≈ $116–152** | point est. ~$134; architect ~$145 |

- **Hard ceiling $300** — plan lands at ~40–50% of ceiling with ~$150 headroom.
- **Dominant line: banding (B), ~$95.** This is the only step >$50 and the only real swing risk.
- **Batching does NOT help here**: `judging batch-judge` gives ~50% off only for **Anthropic** judges;
  our judge is gemini-3.6-flash via OpenRouter → it falls back to the live `judge` path (no saving).
  So banding stays live at full cost. (This corrects the generic "batch it" note from #48's lessons —
  that saving is Anthropic-judge-specific.)
- **Spend discipline**: usage-reconciled actuals reported at every step; sampling actual reconciled
  before authorizing the ~$95 banding; banding actual reconciled before the cheap DPO+eval tail.
  Estimates are for planning only, never for a ceiling decision (#48 lesson 1 / standing rule).

## Environment & reproduction

- **Modal volume** `gemma-dpo`: `mb-sft-guided` (SFT source+adapter, DPO init+ref), `mb-sft-dpo`
  (incumbent), `/pairs/pairs_sft2_mb.jsonl` (surviving 487). **Never overwrite; new names only** →
  new adapter `mb-dpo-full`, new pairs `/pairs/pairs_dpo_full_mb.jsonl`.
- **Scripts** (reused from `experiments/48_multiweights_omissive_bias/`, unchanged where possible):
  `mine_dpo_sample.py` (needs a scenario-list restriction to the uncovered manifest — the one code
  change, see Open items), `modal/serve_gemma_eval.py`, `build_dpo_pairs.py`, `modal/modal_gemma_dpo2.py`,
  `eval_afb_probes.py`, `modal/modal_gemma_capability.py`, `configs/samplability.yaml`.
- **Resumability**: mining (per-cell dedup on append), DPO (`--detach` + `.spawn()` + step-checkpoints)
  — both survive client/network drops (#48 lesson 2). Banding: per-tradition, re-runnable.
- **Banding command** (per tradition): `python -m judging judge <sittings.jsonl> traditions/<t> \
  --config experiments/58_.../configs/samplability.yaml --results-dir <out>`.

## Open items / the one code change

- `mine_dpo_sample.py` currently selects scenarios via `PER_TRAD`. For exp-58 it must mine **exactly**
  the uncovered manifest. Cleanest: add a `MINE_SCENARIO_MANIFEST` env that, when set, overrides
  `scoped_scenarios` with `manifest["uncovered"][t]`. No behavioural change to sampling itself (same
  K=4, temp 1.3, same subject aliases, same on-policy source). Will copy the #48 scripts into this
  experiment dir and make that single edit during execute.

## Results

_(pending gate approval + execution)_

## Next step — **PRE-SPEND GATE**

Stopping here per architect directive. Awaiting explicit approval of this costed plan before any
spend. On approval: copy #48 scripts, add the manifest-restriction, deploy the serve endpoint, mine
the 5,736 uncovered sittings, and reconcile the sampling actual before banding.
