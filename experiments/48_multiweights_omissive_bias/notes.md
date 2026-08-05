# Experiment 48: MultiWeights — overcoming omissive bias

**Status**: In Progress — collection + Gemini banding COMPLETE; at the samplability-diagnostic gate (2026-08-05)

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
| Capability guard | IFEval + MMLU + GSM8K-CoT (lm-eval, same vLLM stack) | flat vs base — **taqwabench jalees baseline in (no regression):** MMLU 0.467/0.468/0.470, GSM8K-CoT-strict 0.792/**0.867**/0.848, IFEval-inst-strict 0.273/0.279/0.282 (base/sft/sft+dpo). Copy their exact lm-eval config: iaser-ai/jaleesbench issue 21, latest comment. Our pooled multi-tradition set is a different treatment → guard still runs every checkpoint. |
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

**Host-mix policy (architect, 2026-08-05): ACCEPT & DOCUMENT, do NOT build host pinning.**
Smoke showed OpenRouter routes per-call — one 2-turn sitting was served by a *mix* (Friendli +
DeepInfra). Rationale for accepting the mix: the distillation data only needs to be text the
model *plausibly emits*; judge-filtering (band ≥ +1 both scopes) + the samplability diagnostic
are robust to mild quantization variance; and the same-stack vLLM control covers eval. So the
writeup caveat is exactly **"own outputs as served by a mix of hosts."** Obligation: when
collection runs, **record the per-call provider distribution as a table** (below). Revisit-trigger:
if one host dominates pathologically OR the mix looks wrong at the samplability-diagnostic stage,
raise it with the architect before training.

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

## Smoke results (2026-08-04, OpenRouter, 2 cells, negligible spend)

- **Pipeline works end-to-end.** `collect --limit 1` on `traditions/sunni-islam` via
  `configs/gemma-collection.yaml`: `{"grid": 1680, "written": 1, "failed": 0}` (1680 = 140 × 6 × 2).
- **Distillation transform confirmed exact.** Guided sitting: the guide sits in `context_prefix`
  ("You are talking with a practising Muslim…") OUTSIDE the judged turns; the stored turns are
  bare scenario text ("My coworker keeps taking credit for my work…"). Dropping `context_prefix`
  ⇒ an exact unstated re-render, as spec §3.1 claims. No framing leak into turns.
- **Serving-host field discovered (verified on a raw response, not guessed):** OpenRouter returns
  a top-level `provider` string; the SDK surfaces it as `resp.provider` (also `resp.model_extra["provider"]`).
- **KEY FINDING — host varies PER CALL, even within one sitting.** A single 2-turn sitting was
  served by **two different hosts**: `usage: [{"in":776,"out":840,"provider":"Friendli"},
  {"in":2349,"out":705,"provider":"DeepInfra"}]`. OpenRouter load-balances per request, so
  quantization/host can differ turn-to-turn. ⇒ per-CALL capture (what the patch does) is the
  correct granularity; a per-sitting host label would be wrong. Sharpens the provenance caveat:
  the distilled source is "own outputs as served by a *mix* of hosts."
- **Provenance patch applied** (`workflows/judging/judging/providers.py`, `_openai_subject`):
  12-line backward-compatible stash of `resp.provider` into the per-turn usage dict. Safe by the
  existing `usage["batch"]` (non-int) precedent — `report._add_usage` sums only the explicit token
  whitelist. Full judging suite: **182 passed, 9 skipped, 0 failed.** **Diff APPROVED** (architect
  2026-08-05), committed `74b58aa`.

### Per-call provider distribution (FILL AT COLLECTION — host-mix policy obligation)

Populate from the collected `sittings.jsonl` once full collection runs (count `usage[].provider`
across all calls). Revisit-trigger: one host dominating pathologically, or a mix that looks wrong
at the samplability-diagnostic stage → raise with architect before training.

Filled from the full collection (12,456 calls, **0 missing provider** — capture worked 100%):

| provider (serving host) | calls | % | | provider | calls | % |
|---|---|---|---|---|---|---|
| Parasail | 6,155 | 49.4% | | Crusoe | 376 | 3.0% |
| Chutes | 1,874 | 15.0% | | Novita | 253 | 2.0% |
| DeepInfra | 1,136 | 9.1% | | ModelRun | 195 | 1.6% |
| CoreWeave | 798 | 6.4% | | Together | 147 | 1.2% |
| SiliconFlow | 475 | 3.8% | | Phala | 122 | 1.0% |
| Morph | 463 | 3.7% | | SambaNova | 42 | 0.3% |
| Friendli | 415 | 3.3% | | Cerebras | 5 | 0.0% |

**Policy read: NOT pathological.** 14 distinct hosts; the top host (Parasail) is a ~49% plurality,
not an overwhelming monoculture — normal OpenRouter load-balancing. The real robustness check is the
samplability diagnostic (host-mix policy revisit-trigger). Flagged to architect for awareness; no
revisit raised. Caveat stands: **"own outputs as served by a mix of hosts."**

## Banding results + samplability preview (2026-08-05) — CORE FINDINGS

**Banding complete:** 12,456 judgments (6,228 × 2 scopes), all 7 traditions on attempt 1, failed=0.
**Actual banding spend ≈ $165.70** (in 56.4M×$1.50 + out 10.8M×$7.50 + cache 1.56M×$0.15). Above my
$151 estimate (~10% — gemini-via-OpenRouter cached less than hoped: cache_read only 1.56M), below
the architect's ~$240 and the $250 authorization. **Total experiment spend so far ≈ $169.67**
(collection $3.97 + banding $165.70).

### Score distributions (−1…+1, MultiBench 5-point scale), per framing × scope

| framing | scope | mean | −1.0 | −0.5 | 0.0 | +0.5 | +1.0 |
|---|---|---|---|---|---|---|---|
| guided | full | **+0.773** | 9.6% | 1.0% | 0.6% | 2.7% | **86.0%** |
| guided | turn1 | +0.867 | 4.5% | 1.1% | 0.5% | 4.4% | 89.6% |
| unstated | full | **−0.230** | **50.8%** | 3.7% | 11.2% | 9.3% | 25.0% |
| unstated | turn1 | +0.003 | 32.9% | 5.8% | 18.9% | 12.6% | 29.8% |

- **Guided ceiling is HIGH across all traditions** (+0.773 full, 86% at +1.0) — the distillation
  source is rich; spec §8's "gemma's guided ceiling might be low on some traditions" risk did NOT
  materialize. The JaleesModel precondition holds.
- **Unstated-under-pressure is NEGATIVE** (−0.230; 51% at −1.0) — base gemma's omissive/secular
  default under the 6 pressures. This is the headroom the tune targets. turn1 ≈ neutral (0.003)
  then pressure drives it down — the "steadfastness under pressure is negative" pattern.

### SFT candidate pool (guided, filter = score ≥ +0.5 on BOTH scopes) — pre-screens/balance

| tradition | pass/total | | tradition | pass/total |
|---|---|---|---|---|
| buddhism | 294/312 (94.2%) | | secular-sage | 254/294 (86.4%) |
| eastern-christianity | 622/636 (97.8%) | | sunni-islam | 641/840 (76.3%) |
| judaism | 269/288 (93.4%) | | taoism | 264/288 (91.7%) |
| roman-catholicism | 389/456 (85.3%) | | **TOTAL** | **2,733/3,114 (87.8%)** |

- **Threshold sensitivity is low:** ≥+0.5 → 2,733; ==+1.0 → 2,586 (only 147 fewer, since guided is
  86% at +1.0). Neither is starved (taqwabench kept 316). **Keeping the ruling default ≥+0.5** — the
  +0.5 tail is still genuinely good counsel; the operative lever is **per-tradition balancing**, not
  the threshold. Balance is lopsided: sunni-islam (641) + eastern-christianity (622) = 46% of the
  pool; judaism/taoism/secular-sage ~260 each. Balancing plan (subsample the big traditions) applies.

### Samplability PREVIEW (single-shot proxy — NOT the K=4 gate)

Fraction of **unstated single-shot** cells scoring good (≥+0.5, full), per tradition — a K=1 proxy
for the samplability question (the real gate resamples K=4 per cell; taqwabench base gemma: 317/420
cells were ZERO):

| tradition | good single-shot | | tradition | good single-shot |
|---|---|---|---|---|
| roman-catholicism | 18.6% | | eastern-christianity | 31.1% |
| sunni-islam | 21.2% | | secular-sage | 54.1% |
| judaism | 39.9% | | taoism | 53.8% |
| buddhism | 56.7% | | **TOTAL** | **34.3%** |

- **Samplability tracks tradition DIFFICULTY exactly** (therapeutic-priors doc): hard traditions
  (RC 18.6%, Islam 21.2% — counsel that collides with the priors) sample good behavior rarely
  unstated; easy traditions (Buddhism 56.7%, Taoism 53.8% — rarely demand what the priors resist)
  sample it often. This is itself a clean cross-tradition result.
- **Implication:** base gemma samples good behavior more than taqwabench's did (34% vs their near-
  zero), so the samplability boundary may be milder here — BUT the proper GO/NO-GO needs the K=4
  per-cell "ever good" histogram. Whichever way it lands, **stage-1 (context distillation) is still
  the mechanism** (guided ceiling +0.77 >> unstated −0.23), and it is safe regardless of the K=4
  result. The K=4 diagnostic mainly informs whether stage-2 DPO-on-SFT is worth it (it needs
  samplable contrast). Design + spend confirmation pending with architect.

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

### 2026-08-05 — GO: full collection launched
- Architect cleared full collection (guided + unstated, 7 traditions) at concurrency 32 (the
  proven OpenRouter envelope; runs alongside the ~1k-cell mop-up tail). Gemini banding cleared to
  follow on completion. Report actual spend at end (est ~$10–20 incl. banding).
- Launched resumable background driver `b3w8q535y` (`scratchpad/collect_driver.sh`): per-tradition
  collect with whole-run resume, rides out network-flap waves (re-run on `failed>0`, bail a
  tradition only after 3 no-progress attempts). Output → `data/output/collection/<tradition>/`
  (gitignored). Verified alive (buddhism writing sittings within seconds).
- Capability baseline received (taqwabench, no regression — GSM8K improved); reference logged in
  the battery table for the capability-guard step. No action now.

### 2026-08-05 — COLLECTION COMPLETE
- Driver `b3w8q535y` exit 0, `{"status":"complete"}`. All 7 traditions done on **attempt 1**,
  `failed=0` each, **no flap retries needed**. **6,228 sittings** = 3,114 guided + 3,114 unstated
  (exact). 12,456 calls, **0 missing provider**.
- Tokens: in 10.85M, out 8.25M, cache_read 8.0M. **Actual collection spend ≈ $3.97**
  ($0.10/$0.34 Mtok; in $1.08 + out $2.80 + cache $0.08) — well under the ~$10–20 est and the $50 gate.
- Provider distribution table filled above (Parasail 49.4% plurality across 14 hosts; not pathological).

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
   **SFT selection filter (architect ruling 2026-08-05): `score ≥ +0.5` on BOTH scopes
   (full AND turn1).** This is the faithful translation of taqwabench's "band ≥ +1" =
   top-2-of-5 on their −2..+2 ladder; MultiBench's 5 canonical scores (−1,−0.5,0,+0.5,+1) are
   the same ladder rescaled, so top-2 = {+0.5, +1.0}. Screens carry over (no guide refs, no
   dangling `[n]`). If the yield is starved/over-permissive vs taqwabench's 316/~420 (ours from
   3,114 guided should keep proportionally more), flag the counts → may tighten to `== +1.0`.
7. Write up: AFB before/after figure, over-application table, capability panel, MultiBench (descriptive).
