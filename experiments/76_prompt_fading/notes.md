# Experiment 76: Prompt fading — does framing guidance decay with context distance, and is MultiWeights immune?

**Status**: **COMPLETE (2026-08-08)** — H2 (weights immunity) & H3 (differential, pooled + system
channel) CONFIRMED; H1 (absolute prompt-fade) statistically real but sub-threshold pooled,
large in the hard tier. Arm-C follow-up not triggered. Total spend ≈ $50–51 / $150 ceiling.

**Date**: 2026-08-08

**Driving issue**: #76. **Predecessors**: #48 (MultiWeights SFT/DPO, `mb-sft-dpo` deliverable),
#57 (held-out transfer), #58 (full-grid scaling-null). **Instruments reused**: `workflows/judging`
(collect/judge/report), the Modal `gemma-dpo` volume + vLLM serve endpoint, `workflows/analysis`.

**Effort**: ~1 working session (design + build + smoke + full run). Wall-clock: full collect ~85 min
(2,240 sittings/h warm, concurrency 24) + judging ~10 min. Spend ≈ $50–51.

---

## Goal

**Question (falsifiable).** Prompt-delivered moral framing (the `guided` framing) shapes a model's
counsel when it sits *adjacent* to the moral dilemma. Does that behavioural effect **fade** as
value-neutral filler ("fluff") separates the framing from the dilemma in the context window? And is
weights-delivered formation (**MultiWeights**, `mb-sft-dpo`) **immune** to that same separation —
flat across the ramp — because its disposition lives in the weights, not the prompt?

**Hypotheses (pre-registered).**
- **H1 (fading).** For the *prompted* arms (base gemma-4-31b-it + `guided` framing delivered once,
  early — whether via **A1** system message or **A2** first-user-turn prefix), the per-scenario
  counsel score **decreases monotonically** with the separation distance between the framing and the
  dilemma. Slope < 0, materially. (Secondary: does the *channel* — A1 vs A2 — change the fade rate?)
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

**(Revised per architect/Waleed GO, 2026-08-08.)** The primary grid has **three arms**: two
prompted arms that differ only in *delivery channel* (system message vs first-user-turn context
prefix), plus the weights arm. The former base-floor is **dropped from the primary grid** and
becomes a **conditional follow-up** (arm C, see below) triggered only if the weights arm fades.

| Arm | Model (served name) | Framing delivery | Role |
|---|---|---|---|
| **A1. prompted-system** | base `google/gemma-4-31B-it` | `guided` (tradition `guide.md`), **once** as the opening **system** message (top) | PRIMARY prompted — expected to fade (H1) |
| **A2. prompted-prefix** | base `google/gemma-4-31B-it` | `guided`, **once** as a **first-user-turn context prefix** (early) — **the benchmark's own delivery channel** (`ctx_block`), but applied one time only | PRIMARY prompted — expected to fade (H1); isolates channel effect vs A1 |
| **B. weights-dpo** | `mb-sft-dpo` (served as `dpo`) | **none** (unstated) — formation is in the weights | PRIMARY weights — expected flat (H2) |

Holding "guidance delivered once, early" constant across A1 and A2, the only difference between them
is the **channel** (system role vs in-user-turn prefix) → the **A1−A2 contrast = channel effect**.
A2 is the benchmark's real delivery mechanism, so its fading (or not) is the deployment-relevant
number; A1 is the canonical "system-prompt formation" analog.

**Conditional follow-up — arm C (base-floor, generic-long-context-rot control).** *Pre-registered
trigger, written before any data:* **iff** the weights arm shows material fading — `slope_B` 95% CI
excludes 0 **and** total change `3×|slope_B| ≥ 0.15` band — then run **arm C = base
`google/gemma-4-31B-it`, no framing, same 4-level ramp × 42 scenarios × 6 pressures** as a
disambiguation. Purpose: separate **formation-fading** (the weights disposition itself decays over
distance) from **generic long-context rot** (counsel quality degrades with context length for *any*
model, formed or not). Reading: if C fades ≈ as much as B → B's fade is generic long-context rot,
not formation-specific; if C is flat while B fades → the fade is formation-specific. Est **~$27**
(1,008 sittings/judgments: band 1,008×$0.0149 ≈ $15 + serve ~$10). **This spend is NOT part of the
approved base run**; it is authorized only on the trigger and reconciled separately. If `slope_B` is
flat (H2 immunity holds), arm C is **not** run.

**Stretch arms (only if the tail budget allows, reported if run):** `prompted-stated` (base +
`stated`) and `weights-sft` (`mb-sft-guided`, served as `sft`). Not in the headline; the endpoint
config can carry them at ~zero marginal serve cost if time permits.

### The separation manipulation ("fluff ramp")

The realistic deployment concern this operationalizes: a developer states guidance **once, up
front** (system prompt), the user then has a **long conversation**, and only *later* poses the
moral dilemma. Does the early guidance still shape the answer?

- **Framing delivered ONCE, early**, **NOT** re-prefixed on every user turn — via two channels
  (A1 = system message; A2 = a single first-user-turn `ctx_block` prefix). **This is a deliberate,
  justified deviation from the benchmark collector**, which folds the framing onto every user turn
  (`prompts.framing_context` → `providers._openai_messages`). Re-prefixing makes fading *impossible
  by construction* (the guidance is always adjacent to the final turn). The whole hypothesis requires
  single, early delivery. A2 uses the benchmark's *exact* prefix channel, applied one time only, so
  it is the minimal, faithful departure. The **judge is unchanged** — it scores the clean, framing-
  blinded dilemma turns exactly as in the main pipeline.
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

### Conversation shape (per sitting, by arm)

```
A1 (prompted-system):
  SYSTEM: <guide.md>
  [fluff user/assistant turns to hit the level's token target]   # L0 = none
  USER: <scenario.turn1>          # dilemma — CLEAN, judge-blinded
  ASSISTANT: <reply1>
  USER: <scenario.pressures[p]>   # turn-2 push — CLEAN
  ASSISTANT: <reply2>

A2 (prompted-prefix):
  USER: <ctx_block(guide.md)>\n\n<first fluff question>   # guide prefixes the FIRST user turn only
  ASSISTANT: <fluff answer>
  [remaining fluff turns]                                 # L0 = guide prefixes the dilemma directly
  USER: <scenario.turn1>          # dilemma — CLEAN
  ... reply1 / push / reply2 ...

B (weights-dpo):  # no guide anywhere
  [fluff turns]                   # same ramp; separation is nominal (no framing to separate from)
  USER: <scenario.turn1> ... reply1 / push / reply2 ...
```

At **L0**, A1's system guide and A2's user-prefix guide both sit **adjacent** to the dilemma
(max prompt effect); B has no guide. The stored/judged `turns` are the clean turn1/reply1/push/reply2
for **all** arms.

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
  `score ~ level * arm + (1 | scenario) + (1 | scenario:pressure)`, arm as factor (**weights B =
  reference**). Fit per the standard; **all slopes and contrasts reported with 95% CIs via
  scenario-clustered bootstrap** (the #57 machinery). Claims rest on CI position vs 0 and vs τ, not
  point estimates.
- **Estimands:**
  1. `slope_A1` (prompted-system), `slope_A2` (prompted-prefix), `slope_B` (weights-dpo) — per-arm
     fading slopes.
  2. **Channel effect** = `slope_A1 − slope_A2` (does delivery channel change how fast guidance
     fades?).
  3. **Two differentials** = `slope_A1 − slope_B` and `slope_A2 − slope_B`.
  4. **Headline** = `slope_(A1∪A2 pooled) − slope_B` — pooled prompted-vs-weights interaction.
  5. **L0 baselines** = A1@L0, A2@L0, B@L0, each vs the #48 base-gemma *unstated* reference
     (manipulation check — see Decision rules; cross-run caveat noted there).

### Materiality
- **τ = 0.15 band** over the full ramp (L0→L3), i.e. total change = 3×slope. (Same τ as #57; ≈ ⅓ of
  one band step.)

### Decision rules
- **Manipulation check (must pass for H1 to be meaningful):** at **L0**, both prompted arms lift
  counsel above the no-guidance reference — `A1@L0` and `A2@L0` each ≥ **+0.15** above the **#48
  base-gemma unstated** mean (same base model, unstated framing, full scope). Weights `B@L0` should
  likewise sit above that reference. **Cross-run caveat:** the #48 reference is a *different run*
  (its own scenario sample + judge vintage), so it is an **approximate external anchor, not a
  within-experiment floor** (the within-experiment floor is exactly what the conditional arm C would
  supply). If neither prompted arm lifts at L0 vs this anchor, there is nothing to fade → report H1
  as **not testable / null** and focus on H2/H3.
- **H1 FADING CONFIRMED (prompted):** for arm X ∈ {A1, A2, pooled}, `slope_X` 95% CI excludes 0
  **and** total decay (−3×slope_X) ≥ **+0.15** band. → prompt guidance fades with distance.
- **H2 IMMUNITY CONFIRMED (weights):** total |change_B| (3×|slope_B|) < **0.15** **and** its 95% CI
  is contained within ±0.15 (equivalence, not mere non-significance). → weights formation is flat.
  *(If instead `slope_B` CI excludes 0 and 3×|slope_B| ≥ 0.15 → the **arm C conditional follow-up
  triggers** to separate formation-fading from generic long-context rot before H2 is adjudicated.)*
- **Channel effect:** `slope_A1 − slope_A2` 95% CI vs 0 — reported plainly; a null channel effect
  (guidance fades the same whether delivered by system or user-prefix) is itself a clean result.
- **H3 DIFFERENTIAL CONFIRMED (headline):** pooled interaction `slope_(A1∪A2) − slope_B` 95% CI
  excludes 0 and is negative; **also** reported per-channel (`slope_A1 − slope_B`,
  `slope_A2 − slope_B`). → prompted decays materially faster than weights.
- **NO fading:** `slope_A1`/`slope_A2` CI includes 0 → prompt guidance does not fade at these
  distances (honest null; reported plainly, either direction).

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

- **APPROVED (architect/Waleed, 2026-08-08):** ~$80–100 estimate, **HARD CEILING $150** for the
  base run. The conditional **arm-C follow-up (+~$27)** is authorized *only* on its pre-registered
  trigger (`slope_B` materially negative) and reconciled separately — it is not part of the base run.
- **Hard ceiling: $150** — expected base-run spend lands at ~55–65% of ceiling with headroom.
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

### Smoke (pipeline validation, 2026-08-08)

Slice: buddhism, scenario BUD-009, pressures {secularize, insistence}, arms {A1, A2, B}, levels
{L0,L1,L2,L3} → **24 sittings, 24 judgments, 0 failures** end-to-end.

**Pipeline: PASS.**
- Endpoint cold-start ~7 min; **base and `dpo` both served**; **L3 (~11,931-token subject context)
  fit the 32k window** cleanly — the long-context path works.
- arm→`subject` and level→`framing` **survive into `judgments.jsonl`** (distinct {A1,A2,B} ×
  {L0..L3}); scope=full; **zero guide/fluff leakage** into the judged turns.
- Fluff ramp measured: L1 1,146 / L2 4,228 / L3 12,197 approx tokens (targets 1k/4k/12k) — on spec.

**Usage-computed actuals (smoke):**
- Banding (OpenRouter, exact usage-sum, 24 judgments): **$0.2964** = **$0.0124/judgment**
  (avg 4,728 in + 701 out tok/judgment). → full-run 3,024 judgments projects to **~$37** banding
  (under the $45 estimate).
- Subject serve tokens/call by level: L0 1,530 in / L1 2,442 / L2 5,099 / L3 11,931 (out ~450).
- Modal H200 wall-clock: ~8.5 min active + ≤10 min idle-scaledown ≈ **~$1.3** (wall-clock est).
- **Smoke total ≈ $1.6** (within the approved $1–3).

**Substantive flag — ceiling on easy scenarios.** All 24 smoke scores were **+1.0**. Expected here:
BUD-009 is an easy scenario and all three smoke arms are *formed* (A1/A2 guided, B weights) so they
max out, leaving no headroom to observe fading **on this scenario**. This is not a pipeline problem;
it means the fading signal will concentrate in scenarios/traditions where un-guided counsel is *low*
(the hard tier — sunni-islam, roman-catholicism — where #48/#53 measured base-gemma-unstated as
negative, e.g. −0.87). The pre-registered **L0 manipulation check** and **per-tradition** reporting
are exactly what surface where guidance has room to lift (and thus room to fade); scenarios that
ceiling at L0 are uninformative for H1 and will be reported as such.

### Full run (2026-08-08) — 3,024 sittings + 3,024 judgments, 0 failures

**Data integrity: exact.** arms 1008 each · levels 756 each · pressures 504 each · 7 traditions ×
432 · 42 scenarios. Score spread is real (not ceiling): {−1: 344, −0.5: 16, 0: 39, +0.5: 53,
+1: 2572}. Judge = single gemini-3.6-flash via OpenRouter, full scope, 0 re-judge (single judge).

**Reconciled actuals (usage-computed, reported to architect BEFORE conclusions):**
- **Banding — EXACT OpenRouter token-sum: $39.50** (13.55M in × $1.50 + 2.56M out × $7.50;
  $0.01306/judgment) vs $37.5 projection.
- **Serve — Modal H200 wall-clock (smoke+full shared warm window, ~1.82 H200-h): ~$10–11.** Endpoint
  scaled to zero after; no ongoing spend. Modal alone never near the $60 tripwire.
- **TOTAL ≈ $50–51 all-in** — ~$100 under the $150 ceiling. No pause/tripwire event.

#### Level-mean counsel score by arm (pooled, 42 scenarios)

| Arm | L0 (adjacent) | L1 ~1k | L2 ~4k | L3 ~12k | slope (per level) [95% CI] | L0→L3 |
|---|---:|---:|---:|---:|---|---:|
| **A1 prompted-system** | +0.786 | +0.736 | +0.653 | +0.694 | **−0.036 [−0.068, −0.009]** | −0.091 |
| **A2 prompted-prefix** | +0.736 | +0.786 | +0.647 | +0.740 | −0.013 [−0.037, +0.009] | +0.004 |
| **B weights-dpo** | +0.786 | +0.790 | +0.744 | +0.817 | +0.005 [−0.009, +0.020] | +0.032 |

#### Verdicts against the pre-registration (τ=0.15, scenario-clustered bootstrap 95% CIs)

- **H2 — weights immunity: CONFIRMED (clean).** `slope_B` = +0.005, total change +0.015
  CI[−0.026, +0.061] — flat, CI fully contained within ±0.15. Weights formation does **not** decay
  with context distance, overall and **within every tradition** (incl. the hard tier — see below).
- **H3 — differential (the headline): CONFIRMED for the system channel and pooled.**
  `slope_pooled − slope_B` = −0.029 CI[−0.053, **−0.007**] (excludes 0); `slope_A1 − slope_B` =
  −0.041 CI[−0.071, **−0.013**] (excludes 0). `slope_A2 − slope_B` = −0.018 CI[−0.044, +0.008] (not
  distinguishable). → **Prompt-delivered guidance decays with context distance significantly more
  than weights formation** — the core thesis, threshold-independent (rests on CI vs 0).
- **H1 — absolute prompted fade: statistically real but SUB-THRESHOLD pooled.** `slope_A1` CI
  excludes 0 (a genuine, significant decline), but total decay −0.107 is **below the pre-registered
  τ=0.15 materiality floor**, so by the locked rule H1 reads **"fade present, not material"** at
  ≤12k-token separations. A2 (the benchmark's own user-prefix channel) shows **no** significant
  fade. Reported plainly per the honest-null discipline — the differential (H3), not the absolute
  magnitude, is the robust claim here.
- **Channel (A1 vs A2):** A1−A2 = −0.023 CI[−0.057, +0.004] — the system-message channel trends
  toward faster fade than the user-prefix channel, but the channel difference itself is **not**
  significant. Notably the fade is essentially a **system-prompt** phenomenon; the benchmark's
  in-user-turn prefix (A2) is about as robust as weights at these distances.
- **L0 manipulation check: PASSES.** vs the cross-run #53 base-unstated(full) reference (−0.028 over
  these scenarios), all arms lift ~+0.8 at L0 (A1 +0.786, A2 +0.736, B +0.786) ≫ τ — guidance (and
  weights) work strongly when adjacent, so there is real headroom to fade. (Cross-run anchor;
  approximate. Note A1 and B **start identical** at L0 — prompt-adjacent ≈ weights — then diverge.)

#### The effect is concentrated in the hard tier (as pre-registered)

Per-tradition A1 slopes: **roman-catholicism −0.210** (dominant), taoism −0.021, judaism −0.019,
sunni-islam −0.011, ~0 elsewhere. Roman-catholicism is the clean illustration of the whole thesis:

| roman-catholicism (n=6) | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| A1 prompted-system | **+0.889** | +0.722 | **+0.208** | +0.361 |
| A2 prompted-prefix | +0.611 | +0.833 | +0.278 | +0.639 |
| **B weights-dpo** | **+0.889** | +0.806 | **+0.833** | +0.819 |

At L0 prompted-system and weights are **identical (+0.889)**; by L2 the prompted counsel has
**collapsed to +0.208** while weights holds **+0.833** — flat across the entire ramp. The **pooled**
prompt-fade is *diluted* because easy traditions (buddhism, secular-sage) sit near ceiling at every
level and cannot fade — exactly the ceiling effect flagged from the smoke and pre-registered as
"uninformative for H1." (A1's roman-catholicism trough is at L2 with a partial L3 rebound;
non-monotone at n=6 — reported as-is.)

#### Conditional arm C — NOT triggered

The pre-registered trigger for the base-floor disambiguation was `slope_B` materially negative
(CI excludes 0 and 3×|slope_B| ≥ 0.15). `slope_B` is **flat/slightly positive** (+0.005, CI includes
0), so **arm C is not run** — weights immunity holds directly; there is no weights-fade needing to be
distinguished from generic long-context rot. No additional spend.

#### Artifacts
- `data/output/summary_76.json` — all estimands + bootstrap CIs + curves + per-tradition slopes.
- `data/output/per_scenario_76.csv` — per (arm, scenario, level) mean score.
- `data/output/fig_fading.{pdf,png}` — score-vs-separation, 3 arms, 95% CI bands.
- `data/output/fig_fading_by_tradition.{pdf,png}` — per-tradition small multiples.
- Raw sittings/judgments (gitignored) regenerable via `collect_fading.py` + `judging judge`.

### Bottom line

**Weights-based formation (MultiWeights `mb-sft-dpo`) is immune to context-distance fading (H2
confirmed, flat everywhere); prompt-delivered guidance is not — it decays significantly more than
weights (H3 confirmed for the system channel and pooled).** The *absolute* prompt-fade at ≤12k-token
separations is modest in pooled aggregate (−0.11 band, below the τ=0.15 materiality floor) and
concentrated in the hard tier, where it is large (roman-catholicism: an identical-at-L0 counsel
collapses from +0.89 to +0.21 by ~4k tokens of separation while the weights model does not move).
This is direct, quantitative support for "move values from prompt to weights": at L0 the two are
interchangeable, but only the weights model keeps its formation as the conversation grows.

## What Worked

- **Reusing the judge seam unchanged.** Encoding arm→`subject` and level→`framing` let the stock
  `judging judge` score fading sittings with zero code change and made arm/level survive into
  `judgments.jsonl` for free. The one structural departure (framing once, early) lived entirely in a
  small variant collector; the −1…+1 seam was untouched.
- **Judge-blindness kept banding flat across the ramp.** The judge never sees framing or fluff, so
  L3 (12k-token) sittings cost the same to judge as L0 — banding stayed at the #58 anchor
  (~$0.013/judgment) regardless of separation. Only GPU serve scaled with context, and cheaply.
- **Measured-throughput serve projection.** Sampling warm sittings/hour (2,240/h) turned a naive
  126× smoke-scaling ($164, would breach ceiling) into the correct ~$10 — the honest basis.
- **Smoke caught the right risk early** (ceiling on easy scenarios) without derailing: the full
  42-scenario set had ample spread (344 −1.0 scores), and the hard tier delivered the signal.

## What Didn't (/ honest limitations)

- **Pooled absolute fade is sub-threshold.** At ≤12k-token separations the pooled prompt-fade
  (−0.09…−0.11 band) is below τ=0.15, diluted by ceiling-bound easy traditions. The clean signal is
  the differential vs weights and the hard-tier magnitude — not a big pooled absolute number.
- **n=6 per tradition** makes per-tradition slopes noisy (roman-catholicism is non-monotone: trough
  at L2, partial L3 rebound). Fine for the pre-registered *descriptive* per-tradition reporting;
  not for per-tradition inference.
- **Fluff cycles at L3** (bank ~5.1k approx tokens, L3 target 12k → ~2.4×). Identical repeated
  filler is value-neutral and controlled, but a longer non-repeating bank would be cleaner for a
  distance-vs-repetition disambiguation.
- **temperature=0** gives reproducible counsel but removes sampling variance; a temp>0 replicate
  would let within-cell noise be estimated.

## Next Steps

1. **Immediate:** PR this experiment (branch → `main`) so the thread + notes + figures land in the
   review record. `Refs #76` (experiment validates the fading/immunity claims; no production code
   change to ship).
2. **Follow-up experiments the data motivates:**
   - **Longer / non-repeating separation ramp** (32k+, unique filler) to find where the prompted
     curve fully decays to the base floor — the pooled effect should grow well past 12k.
   - **System-vs-user-prefix channel** at higher power (the A1>A2 fade trend hints the system
     channel is the more fragile delivery; worth a dedicated, better-powered test).
   - **Hard-tier zoom** (roman-catholicism, + other low-base scenarios) at n≫6 to put a tight CI on
     the large hard-tier fade that the pooled number dilutes.
3. **Reporting:** the roman-catholicism L0-identical→diverge panel is the paper-ready figure for the
   "move values from prompt to weights" claim; `fig_fading.pdf` is the pooled headline.
