# Experiment 58: MultiWeights full-grid DPO (AFB / 100%-train track)

**Status**: Complete — scaling-NEGATIVE; incumbent `mb-sft-dpo` stands (capability panel finalizing for the record)

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
| 4 | MMLU (**chat-mode, re-anchored**) | higher better | measured this rerun | **≥ mb-sft-dpo (chat)** |

Any gate missed → **incumbent stands**, and this is reported as an honest scaling-null. No re-scoring,
no gate relaxation after numbers land.

**Chat-mode capability ANCHOR GUARD (architect 2026-08-06, cross-programme calibration)** — from
taqwabench's independent base run, same model + harness mode (lm-eval vllm, `--apply_chat_template
--fewshot_as_multiturn`, max_len 8192):

**Full taqwabench 3-way chat-mode reference (same model + harness; architect 2026-08-06)** — for
cross-programme calibration only; my numbers are my numbers, guard rule unchanged:

| metric (chat mode) | tq base | tq sft | tq dpo | external anchors | my base guard |
|---|---:|---:|---:|---|---|
| MMLU | **82.8** | 84.0 | 83.8 | RedHat 85.4 / Google 85.2 (Pro) | within ~±3 of 82.8 |
| GSM8K-CoT strict | **95.8** | 95.7 | 95.8 | — | within ~±3 of 95.8 |
| IFEval prompt-strict | **91.7** | 89.8 | 91.3 | — | within ~±3 of 91.7 |

Notes: **GSM8K is CEILING-FLAT (~96)** — taqwabench's raw-mode stage-gains vanished in chat mode; a flat
GSM8K row here is the EXPECTED outcome, not a regression. IFEval sft dip (91.7→89.8) is within noise,
dpo recovers (91.3). Their verdict: no deployment-mode regression across the whole chain.

**Guard**: my `base` (this rerun) must land within ~±3 pts of MMLU 82.8 / GSM8K 95.8 / IFEval-prompt
91.7. Outside that band = **CONFIG problem, not model → HALT and ping**; do NOT proceed to the tuned
checkpoints on an off-band base. Report **BOTH prompt-strict AND inst-strict IFEval** for the gate
comparison (don't mix metric variants). **If OUR sft/dpo shows a real chat-mode regression where
taqwabench's didn't** (bigger pooled set) — that's a FINDING; report it plainly, don't hide it.

**Gate-4 re-anchoring (architect 2026-08-06, measurement-defect fix)**: #48's capability panel ran
lm-eval in **raw-completion mode** on an instruction-tuned model, so its MMLU 0.4424 (and all #48
capability numbers) are **completion-mode artifacts** — base gemma-4-31b-it is ~85-class MMLU
chat-formatted, and IFEval barely measured instruction-following at all in that mode. **The 0.4424
threshold is void.** Gate 4 now compares `mb-dpo-full` vs `mb-sft-dpo` on **chat-mode** MMLU
(`--apply_chat_template --fewshot_as_multiturn`, max_len 8192), both measured in ONE four-checkpoint
rerun (base, mb-sft-guided, mb-sft-dpo, mb-dpo-full). **Anchor guard**: before deciding, sanity-check
the chat-mode BASE absolutes vs the model card / RedHat lm-eval anchors; if base lands far off class,
STOP and ping the architect — do not decide on unanchored numbers.

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
| E. AFB-150 cold + 70 probes (`mb-dpo-full` only) | endpoint GPU + terra judge | **$10–15** | endpoint + terra |
| F. **Capability (4-checkpoint chat-mode panel)** | base+sft+incumbent+new head, H200 lm-eval | **$18–28** | +15–25 over the old 1-head completion run (architect) |
| | **TOTAL** | **≈ $130–174** | ~$134 pt + capability re-anchor; architect ~$150–170 |

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

### Mining + pairs (complete)

- **Mining**: 5,736/5,736 uncovered sittings from `mb-sft-guided` @ temp 1.3, K=4 (0 failed after the
  workspace-disable refill). Full-scope gemini banding: 5,736 judgments, 0 failed.
- **New-pair yield (gap ≥ 1.0)**: **416 / 1,434 cells = 29%** — matches the pre-registered estimate.

  | tradition | cells | pairs | yield |
  |---|---:|---:|---:|
  | buddhism | 72 | 33 | 46% |
  | eastern-christianity | 396 | 76 | 19% |
  | judaism | 48 | 7 | 15% |
  | roman-catholicism | 216 | 58 | 27% |
  | secular-sage | 54 | 9 | 17% |
  | sunni-islam | 600 | 225 | 38% |
  | taoism | 48 | 8 | 17% |
  | **TOTAL** | **1,434** | **416** | **29%** |

- **Combined full-grid set**: 487 surviving + 416 new = **903 pairs, 0 cell collisions** (scoped and
  uncovered scenario sets are disjoint by construction). Uploaded → `/pairs/pairs_dpo_full_mb.jsonl`
  (incumbent's `pairs_sft2_mb.jsonl` untouched). Per-tradition: buddhism 94, eastern-christianity 133,
  judaism 92, roman-catholicism 130, secular-sage 64, sunni-islam 323, taoism 67.

### Spend reconciliation (usage-summed, exact where possible)

| leg | actual | method |
|---|---:|---|
| Sampling (mining, Modal GPU) | ~$8–11 | GPU-time (incl. 3 cold-starts + disable retry churn); not token-summable |
| **Banding (gemini, OpenRouter)** | **$80.99** | EXACT: in 25.86M×$1.50 + out 5.62M×$7.50 + cache 0.49M×$0.15 |
| **so far** | **~$89–92** | |
| DPO (B200, 903 pairs) — pending | ~$10–15 | |
| Lean battery (AFB+probes + 4-ckpt chat capability) — pending | ~$28–43 | |
| **projected total** | **~$127–150** | vs $300 ceiling |

### DPO training (complete)

`mb-dpo-full`: 113 steps / full 1-epoch over **903 pairs**, final loss 0.43, pref_acc ~0.5 throughout
(near-chance = the expected weak-signal regime, matching #48's 0.538 — the SFT already emits good
counsel). ref+init = `mb-sft-guided` (fresh; NOT continue-trained from the incumbent). bf16, β0.1,
lr1e-5, seed 3446. Clean completion (resume marker unlinked). Adapter on volume `/runs/mb-dpo-full`.

Running spend: sampling ~$8-11 + banding $80.99 + DPO ~$6 (B200 ~56 min wall) = **~$95-98**. Battery
pending (~$28-43) → projected total **~$123-141** vs $300.

### Lean battery — gates 1–3 (mb-dpo-full, this run)

Measured with the SAME `eval_afb_probes.py` (max_tokens 1024, gpt-5.6-terra 0–4 judge) as #48, so
directly comparable to the incumbent.

| gate | mb-dpo-full | incumbent mb-sft-dpo | threshold | verdict |
|---|---:|---:|---|:--:|
| 1. AFB P≥2 cold | **0.233** | 0.30 | ≥ 0.300 | **FAIL** |
| 2. secular leakage (max P≥1) | **0.20** (creative-professional) | 0.00 | == 0.00 | **FAIL** |
| 3. opted-out P≥1 | **0.60** | 0.60 | ≤ 0.60 | PASS |
| 4. chat MMLU | _(capability running)_ | _(same run)_ | ≥ incumbent | pending |

- AFB cold: mean **0.940** (incumbent 1.173), P≥1 0.47, P≥3 0.15, dist `{0:80, 1:35, 2:12, 3:10, 4:13}`
  — the full-grid head **omits more** (80/150 zeros) than the incumbent. A genuine regression.
- Probe P≥1 by category: coding 0.00, factual 0.00, math 0.00, secular-practical 0.00,
  creative-professional **0.20**, opted-out-interlocutor 0.60, hostile-to-religion 1.00 (mean 2.90 —
  always engages religiously with anti-religion prompts; not a locked gate, reported as a signal).

### Decision — INCUMBENT STANDS; the result is a scaling-NEGATIVE (architect-confirmed)

The locked rule ships `mb-dpo-full` only if weakly better on ALL FOUR gates. It **fails gates 1 and 2**
→ **incumbent `mb-sft-dpo` stands as the deliverable**, independent of gate 4. `mb-dpo-full` is kept as
an **inert adapter for the record** (nothing overwritten; serve endpoint torn down so nothing keeps
serving the regressed head).

**This is a scaling-NEGATIVE, not merely a null — the empirical answer to "would more pairs help?"**
Doubling the pair set (903 vs 487) at a DPO train **pref_acc ≈ 0.5** means ~2× more optimization steps
on **noise**: within-cell preference contrast is textually modest because the SFT already emits good
counsel (the #48 "DPO no-pair cells are uniformly GOOD" diagnosis). The result is not "flat" but a mild
**degradation** — AFB representation drops (P≥2 0.30→0.233; mean 1.173→0.940; 80/150 zeros) and a new
**creative-professional leakage** appears (P≥1 0.20 vs 0.00). **The 487-pair scoped run was near-optimal
for this mechanism**; more of the same pairs pushed the head off-calibration rather than sharpening it.

Side observation (non-gated): **hostile-to-religion P≥1 = 1.00** (mean 2.90) — the head always engages
religiously even with anti-religion prompts. Not one of the four locked gates; flagged for the record.

### Capability — chat-mode four-checkpoint panel (defect-remediation; paper section of record)

Base **anchor-guard PASSES** — mb-base MMLU 82.8 (anchor 82.8), GSM8K-s 95.83 (95.8), IFEval-p 91.68
(91.7), all within ±3 → **the measurement is valid; the AFB regression is real, not a config artifact.**

| checkpoint | MMLU | GSM8K-CoT strict | IFEval prompt-strict | IFEval inst-strict |
|---|---:|---:|---:|---:|
| mb-base | 82.80 | 95.83 | 91.68 | 94.24 |
| mb-sft-guided | 83.28 | 95.15 | 90.57 | 93.41 |
| mb-sft-dpo (incumbent) | 83.14 | 95.07 | 89.28 | 92.45 |
| **mb-dpo-full** | **83.41** | 95.15 | 90.76 | 93.65 |

- **MMLU flat ~83 across all four** (no capability regression either way). Confirms the #48
  completion-mode MMLU 0.4424 was a pure artifact — real chat-mode MMLU is ~83, on-anchor.
- **GSM8K ceiling-flat ~95** (expected; matches taqwabench's chat-mode collapse of raw-mode gains).
- **IFEval-prompt**: base 91.68 → sft 90.57 → dpo(incumbent) 89.28 → **dpo-full 90.76** — same
  dip-then-recover shape as taqwabench (91.7/89.8/91.3); within noise, no real regression.
- **Gate 4 (chat MMLU): mb-dpo-full 83.41 ≥ incumbent 83.14 → PASS.** But gates 1–2 fail, so the
  decision is unchanged.

### Final four-gate verdict (locked rule)

| gate | mb-dpo-full | threshold | verdict |
|---|---:|---|:--:|
| 1. AFB P≥2 cold | 0.233 | ≥ 0.300 | **FAIL** |
| 2. secular leakage (max P≥1) | 0.20 | == 0.00 | **FAIL** |
| 3. opted-out P≥1 | 0.60 | ≤ 0.60 | PASS |
| 4. chat MMLU vs incumbent | 83.41 ≥ 83.14 | ≥ incumbent | PASS |

**DECISION: INCUMBENT `mb-sft-dpo` STANDS.** Capability held (gate 4 passes) — the head fails *only* on
representation/calibration (gates 1–2). That sharpens the mechanism read: the extra 416 pairs didn't
break capability, they **eroded AFB calibration** — 2× optimization steps on near-zero-signal contrast.

## Next step — **PRE-SPEND GATE**

Stopping here per architect directive. Awaiting explicit approval of this costed plan before any
spend. On approval: copy #48 scripts, add the manifest-restriction, deploy the serve endpoint, mine
the 5,736 uncovered sittings, and reconcile the sampling actual before banding.
