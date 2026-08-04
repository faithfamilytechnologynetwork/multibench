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
- **Collection route (architect REVISED, Waleed 2026-08-04): OpenRouter, not self-serve vLLM**
  — keeps spend on the funded key. Config-only `SubjectSpec` via the OpenAI-compat seam:
  `configs/gemma-collection.yaml` — subject `google/gemma-4-31b-it` (lowercase, **not** the
  `:free` variant), `base_url: https://openrouter.ai/api/v1`, `api_key_env: OPENROUTER_API_KEY`.
  `collect.py` globs `traditions/*/tradition.yaml` and runs the grid.
  - guided framing (training source): 519 × 6 pressures = 3,114 sittings.
  - unstated framing (before/after baseline): 3,114 sittings.
- **Eval/training stack stays Modal + vLLM** (H200/H100, QLoRA r32, custom loops). Port from
  taqwabench: `modal_gemma_sft.py`, `modal_gemma_sample.py` (samplability + stage-2),
  `modal_gemma_dpo2.py`, `modal_gemma_eval.py`, `modal_gemma_capability.py`. Serving reference
  in hand: shannon `apps/modal/serve.py` (proven vLLM OpenAI-server for gemma-4-31B on H100,
  gemma4 chat-template + cached weights in the `shannon-gemma-vllm-hf-cache` volume). Modal is
  authed (`waleedkadous`); the `huggingface` secret + `gemma-dpo` volume already exist.

### Cross-stack methodology consequences of OpenRouter collection (architect 2026-08-04)
1. **The same-stack base control absorbs the collection-vs-eval stack shift.** Collection is on
   OpenRouter; eval serving is vLLM. Running **base gemma through the identical vLLM eval
   stack** is the control that makes an OpenRouter-collected training set compatible with a
   vLLM-evaluated result — the shift is measured, not assumed away. (jalees saw a −0.058
   provider-vs-vLLM shift, larger than several DPO arms' effects.)
2. **Provenance caveat — "own outputs AS SERVED."** OpenRouter may route gemma to a
   **quantized** host, so the distillation source is the model's outputs as that host produced
   them. **Record the serving host from response metadata for every collection call** where
   OpenRouter returns it (field to be verified on a real response at smoke time — no guessing;
   see Next steps). Host pinning is NOT expressible in the current config schema — disclose in
   the writeup.
3. **The Modal/vLLM work is not wasted** — it is the eval stack AND the same-stack base control.

**Keys**: `OPENROUTER_API_KEY` via `(set -a; source /Users/mwk/Development/fftn/taqwabench/.env; set +a)`.
**NEVER** copy the key into repo / logs / PR text — public repo, funded key.

## Gates & sequencing (architect, 2026-08-04)

1. **[HARD BLOCK] Framings expansion / mop-up is running** on the shared OpenRouter key +
   Gemini quota. Gemma collection now goes through THAT SAME key → do NOT start collection OR
   Gemini banding until architect gives the word (mop-up likely done within hours).
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
- Probe suite tightenings (architect): cat E guard → P(score ≥ 1) ≈ base (opt-out makes even a
  passing mention a violation); cat F → comparative-vs-base only (prompt itself names religion).
- **Route pivot (architect revised):** collection → OpenRouter funded key (slug
  `google/gemma-4-31b-it`, not `:free`), not self-serve vLLM. Wrote dormant
  `configs/gemma-collection.yaml`. Recorded the 3 cross-stack consequences (same-stack control
  absorbs the shift; quantized-host provenance caveat + record serving host; Modal = eval stack).
- Environment verified: Modal authed (`waleedkadous`), `huggingface` secret + `gemma-dpo`
  volume exist, shannon `serve.py` is the vLLM-server reference for the eval stack.
- **No spend, no shared-key use, nothing collected or trained.** Collection + banding both now
  gated on the framings mop-up finishing (shares the funded key) — awaiting architect's word.

## Next steps (ordered)

1. **[DONE]** Dormant OpenRouter collection config → `configs/gemma-collection.yaml`.
   Over-application probe suite designed (`probes/`). AFB instrument vendored.
2. **[on collection go-word] SMOKE**: `collect --config configs/gemma-collection.yaml --limit 1`
   against one scenario. At smoke time, **inspect a real OpenRouter response object to find the
   serving-host field** (e.g. `resp.provider` / `model_extra`) — verify, don't guess — then
   decide the minimal, backward-compatible capture so full collection records host per call.
   Verify sittings are clean (framing in `context_prefix` only; turns hold bare scenario text).
3. **[on clean smoke]** Full collection (guided + unstated, 7 traditions) → report actuals.
4. **[on banding go-word]** Gemini band all guided + unstated sittings (selection judge).
5. **[HARD GATE]** Samplability diagnostic (K=4 unstated from base gemma, per-tradition
   histogram) → **report to architect before ANY training.**
6. **[on approval + capability config]** Build pooled bare SFT set (adapt taqwabench
   `build_sft_guided.py` to `scenario_id`/tradition, no split, per-tradition balancing) →
   stage-1 SFT → eval battery → stage-2 DPO → full battery (AFB + probes + capability panel).
7. Write up: AFB before/after figure, over-application table, capability panel, MultiBench (descriptive).
