# Experiment 48: MultiWeights — overcoming omissive bias

**Status**: In Progress (setup / pre-collection — no spend yet)

**Date**: 2026-08-04

Spec: [`codev/specs/48-multiweights-omissive-bias.md`](../../codev/specs/48-multiweights-omissive-bias.md)
Reference recipe (JaleesModel / taqwabench):
`/Users/mwk/Development/fftn/taqwabench/tmp/dpo-experiment/methodology-for-multibench.md`
+ script suite in the same directory. Public trail: `github.com/iaser-ai/jaleesbench` issue 21.

## Goal

**Hypothesis (falsifiable).** Judge-filtered context distillation on gemma-4-31b's OWN
guided-framing MultiBench sittings — pooled across all 7 traditions — moves the model's
disposition into the weights such that, on the **AllFaith Benchmark** (150 secular life
questions), religious representation rises from base's ≈0 toward 1–2, **without**
over-applying religion on secular tasks and **without** capability regression.

**Success criteria (the headline lives entirely on the OOD battery — see §"No holdout"):**
1. **Omission ↓ (headline):** AFB mean rises from base ≈0; mass shifts 0 → 1–2; the 3–4
   fraction stays ≈ base; beats the published 0–2% "meaningful (≥2)" ceiling across 27 models.
2. **Calibration, not maximization:** over-application probe suite (below) stays **flat vs
   base** on secular categories; opted-out interlocutors get **zero sermonizing**.
3. **Capability guard flat:** IFEval + MMLU + GSM8K-CoT within noise of base (same vLLM stack).
4. **Fabrication guard:** zero fabricated citation markers in tuned outputs.

**Disproved looks like:** AFB stays flat (distillation didn't move it), OR AFB rises but the
probe suite rises too (over-application — result inverts), OR capability panel regresses.

## Approach

Two-stage recipe validated by JaleesModel (taqwabench, gemma-4-31b, ~$110), transferred to
MultiBench's 7-tradition corpus:

1. **Stage 1 — judge-filtered context distillation (the result):** SFT gemma on its OWN
   guided-framing sittings, selection-judge band ≥ +1 on BOTH scopes (whole sitting AND
   turn-1), screened (no guide references, no dangling `[n]` citations), **re-rendered bare**.
   MultiBench compat is exact: framing lives in `context_prefix` OUTSIDE the judged turns
   (`workflows/judging/judging/collect.py` — verified: `turns` store clean scenario text only,
   `context_prefix` is audit-only), so the bare transform needs no stripping.
2. **Stage 2 — on-policy DPO anchored at the SFT checkpoint (optional sharpening):** K=4
   chains from the distilled policy, within-cell max-gap pairs, DPO with the **SFT checkpoint
   as reference** (not raw base). Buys pressure-robustness.
3. **The warning that saves ~$100:** five DPO-on-base arms were all statistically zero
   (samplability boundary). → **run the samplability diagnostic BEFORE training anything.**

**One pooled multi-tradition SFT set** (Waleed 2026-08-04, no per-tradition arm). Balance
risk is real — scenario counts are lopsided:

| tradition | scenarios | | tradition | scenarios |
|---|---|---|---|---|
| sunni-islam | 140 | | roman-catholicism | 76 |
| eastern-christianity | 106 | | secular-sage | 49 |
| buddhism | 52 | | judaism | 48 |
| | | | taoism | 48 |
| **total** | **519** | | | |

sunni-islam alone is 27% of scenarios; without balancing it dominates the pool. Plan: after
banding, subsample or tighten the band threshold per tradition so no tradition dominates
(decide from the per-tradition samplability histogram — §Gates).

### No holdout (Waleed 2026-08-04)
Train on ALL 519 scenarios. The test battery (AFB representation, capability panel,
over-application probes) is entirely OOD, so a MultiBench holdout buys nothing for the
headline. **Consequence, stated honestly:** we CANNOT claim "MultiBench scores improved" —
any on-bench before/after is memorization-confounded and is reported descriptive-only, if at
all. Also recorded: gemini-3.6-flash (thinking) is the SOLE judge for both selection AND
evaluation (no Opus holdout), so "selection-judge gaming" can't be ruled out for any
gemini-judged metric — another reason the headline metrics are the AFB / capability battery,
which use their own judges/harnesses (AFB judge-of-record ≠ gemini — open decision §7.2).

## Measurement battery

| Axis | Instrument | Success |
|---|---|---|
| **Omission (headline)** | AFB 150 Qs, official 0–4 judge; judge-of-record ≠ gemini | mean ↑ from ≈0; mass 0→1–2; 3–4 ≈ base; beats 0–2% ≥2 ceiling |
| Capability guard | IFEval + MMLU + GSM8K-CoT (lm-eval, same vLLM stack) | flat vs base (taqwabench config lands 08-05) |
| Over-application guard | `probes/over_application_probes.{md,jsonl}` (70 prompts, AFB judge) + AFB 4-fraction | flat vs base on secular; 0 sermonizing on opt-out |
| Fabrication guard | citation-marker scan on tuned outputs | zero (jalees: 0) |
| MultiBench (descriptive only) | trained-scenario bare/unstated, gemini-thinking judge | color only; NOT a claim |

**AFB conditions:** (a) cold, no persona (honest headline); (b) light faith-context prefixes
("I'm a practicing Catholic…") — tests whether representation is *responsive* not blanket.
The over-application probe category E is the negative mirror of condition (b).

## Environment & Reproduction

- **AFB instrument** vendored at `data/input/afb/` (150 Qs + official scorer, MIT; see SOURCE.md).
- **Over-application probes** authored at `probes/` (70 prompts, designed pre-training).
- **Collection**: gemma-4-31b is NOT yet a MultiBench subject. Add it as a `SubjectSpec`
  (`workflows/judging/judging/config.py`) via a run config; the OpenAI-compat `base_url` +
  `api_key_env` seam routes either OpenRouter (verify slug) or self-serve vLLM. `collect.py`
  globs `traditions/*/tradition.yaml` and runs the grid — adding a subject is config-only.
  - guided framing (training source): 519 × 6 pressures = 3,114 sittings.
  - unstated framing (before/after baseline): 3,114 sittings.
- **Training/eval**: Modal 1×H200, QLoRA r32, custom loops. Port from taqwabench:
  `modal_gemma_sft.py`, `modal_gemma_sample.py` (samplability + stage-2), `modal_gemma_dpo2.py`,
  `modal_gemma_eval.py`, `modal_gemma_capability.py`. vLLM bf16 + LoRA for eval serving.

**Keys**: request from architect when needed (do not hunt). None used yet.

## Gates & sequencing (architect, 2026-08-04)

1. **[HARD BLOCK] Framings expansion is running** on the shared OpenRouter key + Gemini
   quota → do NOT start gemma collection until architect gives the word (finishes within hours).
2. **[HARD GATE] Samplability diagnostic** — K=4 unstated samples/scenario from base gemma,
   gemini-banded, per-tradition histogram. **Report to architect before ANY training.**
   Expected (per jalees): good-band behavior barely appears → stage-1-first mandatory.
3. **[SPEND GATE] Any step >$50** — tell architect BEFORE, not after. Budget ≈ $220–300 total
   (collection $120–200 dominates).
4. Capability-panel config (IFEval/MMLU/GSM8K) forwarded by architect 08-05.

**Open decisions (spec §7, architect/Waleed's to make — not mine):** funding source
(David's CEFEAI key vs out-of-pocket); AFB judge-of-record (Terra vs Sonnet-5); naming;
green-light for the prerequisite gemma collection.

## Progress log

### 2026-08-04 — setup (this session)
- Read spec + taqwabench methodology + reference script suite + therapeutic-priors doc.
- Vendored AFB instrument (150 Qs + official 0–4 scorer, MIT) → `data/input/afb/`.
- **Designed the over-application probe suite** (70 prompts, 7 categories) → `probes/`.
  Required BEFORE training per methodology §5.6; over-application is the spec's headline risk.
- Confirmed collection is a config-only change (SubjectSpec seam) — no core edits.
- Confirmed corpus counts (519; sunni-islam 140 dominant → balancing needed).
- **No spend, no shared-key use, nothing collected or trained.** Awaiting green-light on (1).

## Next steps (ordered)

1. **[now, no spend]** Port/adapt the Modal scripts into `experiments/48.../modal/` (SFT,
   sample, dpo2, eval, capability) parameterized for the pooled MultiBench set; write the
   gemma `SubjectSpec` run config (dormant until green-light).
2. **[now, ask for key]** Verify the OpenRouter slug for `google/gemma-4-31B-it`; if routing
   is doubtful, plan self-serve vLLM collection through the SAME stack used for eval (kills
   the serving-stack confound at the source, spec §8).
3. **[on green-light]** Run gemma collection (guided + unstated, 7 traditions) → Gemini banding.
4. **[HARD GATE]** Samplability diagnostic → report per-tradition histogram to architect.
5. **[on approval + capability config]** Stage-1 SFT → eval battery → stage-2 DPO → full battery.
6. Write up: AFB before/after figure, over-application table, capability panel, MultiBench (descriptive).
