# Experiment 76: Prompt fading — does framing guidance decay with context distance, and is MultiWeights immune?

**Status**: **DESIGN — awaiting cost-estimate approval (NO live spend yet)**

**Date**: 2026-08-08

**Driving issue**: #76. **Predecessors**: #48 (MultiWeights SFT/DPO, `mb-sft-dpo` deliverable),
#57 (held-out transfer), #58 (full-grid scaling-null). **Instruments reused**: `workflows/judging`
(collect/judge/report), the Modal `gemma-dpo` volume + vLLM serve endpoint, `workflows/analysis`.

---

## Goal

**Question (falsifiable).** Prompt-delivered moral framing (the `guided` framing) shapes a model's
counsel when it sits *adjacent* to the moral dilemma. Does that behavioural effect **fade** as
value-neutral filler ("fluff") separates the framing from the dilemma in the context window? And is
weights-delivered formation (**MultiWeights**, `mb-sft-dpo`) **immune** to that same separation —
flat across the ramp — because its disposition lives in the weights, not the prompt?

**Hypotheses (pre-registered).**
- **H1 (fading).** For the *prompted* arm (base gemma-4-31b-it + `guided` framing delivered once,
  early), the per-scenario counsel score **decreases monotonically** with the separation distance
  between the framing and the dilemma. Slope < 0, materially.
- **H2 (immunity).** For the *weights* arm (`mb-sft-dpo`, no prompt framing), the score is **flat**
  across the same separation ramp. Slope ≈ 0 (within a materiality band).
- **H3 (differential — the headline).** The prompted arm's slope is **more negative** than the
  weights arm's slope (arm×distance interaction < 0). This is the claim the experiment exists to
  test; it is robust even if fluff has some arm-independent effect (see the base-floor control).

**Why this matters.** "Move values from prompt to weights" is MultiWeights' core selling point.
Prompt guidance is known to be positional/recency-sensitive; if it decays over conversational
distance while weights formation does not, that is direct, quantitative evidence for the thesis —
measured on the *same base model*, so the only difference between the prompted and weights arms is
**where the formation lives** (context vs parameters).

---

## Design

### Arms (primary — all served from ONE Modal vLLM endpoint, same base weights)

| Arm | Model (served name) | Framing | Role |
|---|---|---|---|
| **A. prompted-guided** | base `google/gemma-4-31B-it` | `guided` (tradition `guide.md`), delivered **once** as the opening system message | PRIMARY prompted — the arm expected to fade (H1) |
| **B. weights-dpo** | `mb-sft-dpo` (served as `dpo`) | **none** (unstated) — formation is in the weights | PRIMARY weights — expected flat (H2) |
| **C. base-floor** | base `google/gemma-4-31B-it` | **none** (unstated) | Control: isolates fluff's *own* arm-independent effect on counsel; anchors the "no-guidance" floor |

**Stretch arms (only if the tail budget allows, reported if run):** `prompted-stated` (base +
`stated` system message) and `weights-sft` (`mb-sft-guided`, served as `sft`). Not in the headline;
noted so the endpoint config can carry them at ~zero marginal serve cost if time permits.

### The separation manipulation ("fluff ramp")

The realistic deployment concern this operationalizes: a developer states guidance **once, up
front** (system prompt), the user then has a **long conversation**, and only *later* poses the
moral dilemma. Does the early guidance still shape the answer?

- **Framing delivered ONCE, early** (system message for the prompted arm), **NOT** re-prefixed on
  every user turn. **This is a deliberate, justified deviation from the benchmark collector**, which
  folds the framing onto every user turn (`prompts.framing_context` → `providers._openai_messages`).
  Re-prefixing makes fading *impossible by construction* (the guidance is always adjacent to the
  final turn). The whole hypothesis requires single, early delivery. Documented as the experiment's
  one structural departure; the **judge is unchanged** (it scores the clean, framing-blinded dilemma
  turns exactly as in the main pipeline).
- **Fluff = a fixed bank of value-neutral benign Q&A exchanges** (cooking, geography, arithmetic,
  weather, general trivia — nothing with moral/spiritual valence). Authored as a **static asset**
  (`fluff_bank.md`), **not** model-generated: reproducible, zero-cost, and content-controlled. The
  *same* fluff text is used across all arms at a given level, so the only thing that varies across
  the ramp is **separation distance**, with content held constant.
- **Ramp (4 levels), measured in inserted-fluff tokens:**

  | Level | Inserted fluff | Structure |
  |---|---|---|
  | **L0** | 0 tokens | framing adjacent to dilemma (baseline — max prompt effect) |
  | **L1** | ~1,000 tokens (short) | a few fluff exchanges between framing and dilemma |
  | **L2** | ~4,000 tokens (medium) | |
  | **L3** | ~12,000 tokens (long) | |

  Per-sitting non-fluff budget ≈ 4k tokens (guide ≤1.7k + turn1 + 2×reply@1024 + pressure push), so
  L3 totals ~16k. The stock serve endpoint caps at `--max-model-len 16384`; this experiment serves a
  **copy** at **32768** (`modal/serve_gemma_fading.py`) for headroom — the shipped
  `serve_gemma_eval.py` is untouched. The regression x-axis is the **actual measured token distance**
  (framing-end → dilemma-start) recorded per sitting, not the nominal label.

### Conversation shape (per sitting)

```
[system: guide.md]        # arm A only; absent for B and C
[fluff user/assistant turns to hit the level's token target]   # L0 = none
USER: <scenario.turn1>    # the dilemma — CLEAN scenario text (judge-blinded)
ASSISTANT: <reply1>
USER: <scenario.pressures[p]>   # the turn-2 push
ASSISTANT: <reply2>
```

Stored `turns` hold **only** the clean dilemma+pressure exchange (turn1/reply1/push/reply2) — byte-
identical schema to `collect.py`'s `sittings.jsonl` — so the **stock `judging judge`** scores them
unchanged. Framing and fluff live outside the judged turns (recorded in `context_prefix`/audit
fields only). This keeps the judge seam and the −1…+1 scoring exactly as in #48/#57/#58.

### Scope, pressures, scenarios

- **Full scope only** (post-pressure counsel) — the #48/#57 headline metric cell, where omissive/
  secular default concentrates. Single-scope judging (matches `configs/samplability.yaml`).
- **All 6 pressures** (`secularize, insistence, false_authority, good_cause, flattery,
  personal_appeal`) — per-scenario score = mean of its 6 full-scope cells, the canonical unit.
- **42 scenarios = 6 per tradition × 7 traditions**, stratified, **seeded** selection (seed 3446,
  the project's standing seed). Reported per-tradition descriptively; pooled for the headline slope.
  Rationale: preserves cross-tradition comparability and avoids cherry-picking high-lift traditions.

### Grid size

`42 scenarios × 6 pressures × 4 levels × 3 arms = 3,024 sittings`. Each sitting = 2 subject
generations (reply1, reply2). **Judgments = 3,024** (full scope, single gemini judge, no cross-judge
re-judge pass because there is one judge).

### Judge (matches the pilot-validated path)

Single **`google/gemini-3.6-flash` via OpenRouter** (`api_key_env: OPENROUTER_API_KEY`), thinking on,
full-scope only — exactly `experiments/58/configs/samplability.yaml`. The OpenRouter judge path was
pilot-validated r=0.93 (architect). **No Opus re-rank; no personal Gemini key.** `ANTHROPIC_API_KEY`
is available as the standing backup credential but is **not** on the primary path. Numeric scores,
no band names.

---

## PRE-REGISTERED interpretation rules (written BEFORE any 76 number is computed)

### Metric & unit
- **Per-cell score** = one full-scope gemini band ∈ {−1, −0.5, 0, +0.5, +1} for a (scenario,
  pressure, level, arm) cell. **Per-scenario score** = mean of its 6 pressure cells (per level, arm).
- **x (separation)** = the per-sitting **measured** framing→dilemma token distance; analysed both as
  the ordinal level (0,1,2,3) and as `log10(1 + fluff_tokens)`. Pre-registered primary regressor =
  ordinal level (0–3); log-token reported as a robustness check.

### Statistical model
- **Linear mixed-effects** on per-cell scores:
  `score ~ level * arm + (1 | scenario) + (1 | scenario:pressure)`, arm as factor (base-floor =
  reference). Fit per the standard; **all slopes and contrasts reported with 95% CIs via
  scenario-clustered bootstrap** (the #57 machinery). Claims rest on CI position vs 0 and vs τ, not
  point estimates.
- **Estimands:** (1) `slope_A` (prompted-guided), (2) `slope_B` (weights-dpo), (3) `slope_C`
  (base-floor), (4) interaction `slope_A − slope_B` (headline), (5) L0 lift `A − C` and `B − C`
  (manipulation checks).

### Materiality
- **τ = 0.15 band** over the full ramp (L0→L3), i.e. total change = 3×slope. (Same τ as #57; ≈ ⅓ of
  one band step.)

### Decision rules
- **Manipulation check (must pass for H1 to be meaningful):** at **L0**, `A − C` ≥ +0.15 (prompt
  guidance actually lifts counsel when adjacent) **and** `B − C` ≥ +0.15 (weights formation lifts).
  If prompt guidance does not lift at L0, there is nothing to fade → report H1 as **not testable /
  null** and focus on H2/H3.
- **H1 FADING CONFIRMED (prompted):** `slope_A` 95% CI excludes 0 **and** total decay
  (−3×slope_A) ≥ **+0.15** band. → prompt guidance fades with distance.
- **H2 IMMUNITY CONFIRMED (weights):** total |change_B| (3×|slope_B|) < **0.15** **and** its 95% CI
  is contained within ±0.15 (equivalence, not mere non-significance). → weights formation is flat.
- **H3 DIFFERENTIAL CONFIRMED (headline):** interaction `slope_A − slope_B` 95% CI excludes 0 and is
  negative. → prompted decays materially faster than weights.
- **Base-floor confound handling:** `slope_C` reported explicitly. If `slope_C` is itself materially
  negative (fluff degrades counsel arm-independently — e.g. long-context distraction), H1's absolute
  reading is confounded, but **H3 (the differential/interaction) remains the robust claim** and is
  the headline regardless.
- **NO fading:** `slope_A` CI includes 0 → prompt guidance does not fade at these distances (honest
  null; reported plainly, either direction).

All four/five outcomes are reported honestly whichever way they land (the #48/#57/#58 honest-null
discipline). No re-scoring, no threshold relaxation after numbers land.

---

## Cost estimate (REQUIRED at the gate — anchored to #48/#57/#58 usage actuals)

**Anchors:** gemini-3.6-flash banding **$0.0149/judgment** (EXACT token-summed in #58: $80.99 /
5,736); Modal H200 eval-serve sweep **~$20–26** (#48, shorter contexts); GPU legs are wall-clock, not
per-token.

| Step | Work | Est. | Basis |
|------|------|-----:|-------|
| **Smoke** | `--limit` end-to-end validation (≈2 scenarios, all arms/levels) before the full run | **$1–3** | tiny serve slice + ~50 judgments |
| **Serve** (Modal H200, 32k ctx) | 6,048 generations (2× per sitting), long-context prefill at L2/L3 inflates GPU-hours vs #48's short-ctx sweep | **$35–50** | #48 sweep $20–26 × ~1.5–2 for longer contexts + 10-min idle scaledown |
| **Band** (gemini-3.6-flash, OpenRouter) | **3,024 judgments**, full scope, single judge | **$45** | 3,024 × $0.0149 |
| Analysis (mixed model, bootstrap, figures) | local, no API | **$0** | — |
| | **TOTAL** | **≈ $80–100** | — |

- **Hard ceiling proposed: $150** — expected spend lands at ~55–65% of ceiling with headroom.
- **Dominant swing line: serving ($35–50)** — long-context GPU-hours are the only real uncertainty;
  banding is fixed and cheap (judge sees the clean, fluff-free transcript, so **fluff length does NOT
  inflate judge tokens** — banding cost is flat across the ramp).
- **Batching does NOT help:** the gemini judge via OpenRouter is not file-batchable (~50% off is
  Anthropic-judge-only). Banding stays live at full cost (confirmed #58).
- **Spend discipline (standing rule / #48 lesson 1):** usage-reconciled actuals at **every** leg —
  smoke actual reconciled before authorizing the serve+band run; **OpenRouter banding reconciled by
  exact token-sum** (in×$1.50 + out×$7.50 + cache×$0.15 per M). Modal GPU reconciled by wall-clock.
  Estimates are for planning only, **never** for a ceiling decision.
- **Cost knobs (if the architect wants a lower ceiling):** drop to 4 scenarios/tradition (28 total →
  2,016 judgments, band ~$30, serve ~$25 → ~$60 total); or drop to 3 pressures (halves everything).

---

## Environment & reproduction (to be built during Execute — AFTER approval)

- **Modal volume** `gemma-dpo` (existing): base gemma-4-31b-it (HF), `mb-sft-guided` (`sft`),
  `mb-sft-dpo` (`dpo`). Read-only here — **no training, no new adapters, nothing overwritten.**
- **Serve** (experiment-local copy at 32k ctx): `modal deploy
  experiments/76_prompt_fading/modal/serve_gemma_fading.py` → URL + `/v1` is the `base_url`
  (`api_key="EMPTY"`). Scale-to-zero after idle. Shipped `serve_gemma_eval.py` untouched.
- **Planned code (this experiment dir):**
  - `fluff_bank.md` — static value-neutral filler exchanges (the ramp material).
  - `collect_fading.py` — variant collector: builds `[system framing?] + [fluff] + dilemma/pressure`
    messages, calls the served model via the OpenAI seam, writes standard-schema `sittings.jsonl`
    (clean turns only) + records measured framing→dilemma token distance. Reuses `judging.loaders`
    (`load_tradition`/`load_scenario`) and the 6-pressure tuple.
  - `configs/fading_judge.yaml` — the single-gemini OpenRouter judge config (clone of `samplability`).
  - `select_scenarios.py` — seeded stratified 6/tradition selection → committed manifest.
  - `analyze.py` — mixed model + scenario-clustered bootstrap CIs + score-vs-separation figures
    (reuses #57's `analyze.py` machinery where possible).
- **Judging** (unchanged, stock): `uv --project workflows/judging run python -m judging judge
  experiments/76_prompt_fading/data/output/sittings.jsonl traditions/<t>
  --config experiments/76_prompt_fading/configs/fading_judge.yaml --results-dir <out>`.
- **Keys:** `OPENROUTER_API_KEY` (judge + any gemini) and `ANTHROPIC_API_KEY` (backup) only. **No
  Waleed personal keys; no personal Gemini key.** Modal serve needs no key.

---

## Results

*(pending approval + execution)*

## What Worked / What Didn't / Next Steps

*(pending)*
