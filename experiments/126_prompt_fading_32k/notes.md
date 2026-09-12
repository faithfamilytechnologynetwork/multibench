# Experiment 126: Prompt fading at 32k — the fifth level (L4) on the #78 ramp

**Status**: **PRE-REGISTRATION (Hypothesis+Design phases, no data yet)** — 2026-09-11.
This document is the pre-registration. It is committed BEFORE any 126 datum is collected
(the standing #76/#78 discipline). Results/Analysis sections are stubs to be filled only after
the smoke → architect go → full run.

**Driving issue**: #126 ("Do 32k next", Waleed 2026-09-11). **Follow-up to #78** (merged PR #79).
**Inherits #78 wholesale** — the only delta is ONE new ramp level. Predecessors: #48 (MultiWeights
SFT/DPO, `mb-sft-dpo`), #57/#58 (transfer / scaling-null), #76 (6-scenario pilot), #78 (full-corpus
fair-stated 4-level ramp; the run this extends). The FaithfulWeights paper (papers repo
`faithfulweights-paper.tex`) rests on the #78 ramp; #126 adds the point that tells us whether the
prompted curve keeps falling and whether the tuned arm's residual decline is a floor or a slide.

---

## The one delta (everything else is byte-identical #78 reuse)

**Add level L4 = ~32,000 tokens of inserted filler.** That is the whole experiment. Reused
unchanged: the two arms, the judge config, seed/pre-registration discipline, the collector's
arm→`subject` / level→`framing` encoding, the greedy fluff builder, scope (full post-pressure
counsel), all 6 pressures, all 519 scenarios.

| Level | Inserted fluff (approx tokens) | Source of the scores |
|---|---:|---|
| L0 | 0 | **#78 committed** (`per_scenario_78.csv`, level 0) |
| L1 | ~1,000 | **#78 committed** (level 1) |
| L2 | ~4,000 | **#78 committed** (level 2) |
| L3 | ~12,000 | **#78 committed** (level 3) |
| **L4** | **~32,000** | **NEW — this run only** (level 4) |

L0–L3 are **not re-run**. Only L4 is collected here (**519 scenarios × 6 pressures × 2 arms =
6,228 sittings + 6,228 judgments**), then pooled with #78's committed per-scenario L0–L3 to form a
5-level ramp per (arm, scenario). Same columns as #78 so the papers repo `fading_figs.py` reads it.

### Arms (unchanged from #78 — the same two, same base weights, one served endpoint)

| Arm | Model (served name) | Framing (opening SYSTEM message, once) | Role |
|---|---|---|---|
| **A1. prompted-guide** | base `google/gemma-4-31b-it` | tradition **`guide.md`** (full prose `guided` framing) | PRIMARY prompted — does it keep fading past 12k? |
| **B. stated-weights** | `mb-sft-dpo` (served as `dpo`) | the universal **stated** sentence from `stated_prompt(adherent_noun)` | PRIMARY weights — is its residual decline a floor or a slide? |

Arm B's stated sentence is obtained by calling `stated_prompt(tradition.manifest.adherent_noun)`
via `judging.core_imports` (canonical `tradition_validator.core`) — **never hardcoded**, so the
experiment cannot drift from the benchmark's `STATED_TEMPLATE` (the #78 rule).

---

## Goal

**Question (falsifiable).** #78 measured prompt fading up to ~12k tokens of separation on the full
519-scenario corpus. The prompted guide (A1) declined significantly but sub-threshold pooled
(−0.080 over L0→L3, τ=0.15), concentrated in the normative tier (sunni −0.041/level, RC −0.038,
judaism −0.027); the FaithfulWeights arm (B = `mb-sft-dpo` + stated cue) declined ~2.4× less
(−0.033 over the ramp, within its ±0.15 immunity band). **At ~32k tokens of separation:**

1. **Does the prompted curve keep falling** — does the A1 fade *continue* from L3→L4, and does the
   *total* L0→L4 prompted decline cross the pre-registered τ = 0.15 materiality bar (i.e. does
   prompt fading become **material**, not merely real-but-small)?
2. **Is the tuned arm's small residual decline a floor or the start of the same slide** — does B
   stay flat (within ±0.15) from L3→L4, or does its curve begin to slide like A1's?

---

## Hypotheses (pre-registered)

- **H1 (prompted fade continues / becomes material).** For arm **A1**, the L3→L4 change is
  **negative** (the prompted curve keeps falling past 12k), and the **total L0→L4 decline** moves
  toward / crosses **τ = 0.15**. Directional prediction: strongest in the **high** FaithfulBench
  tier (RC, sunni-islam).
- **H2 (weights arm — floor, not slide).** For arm **B**, the L3→L4 change is **flat** (within the
  immunity band) and the **total L0→L4 |decline| < 0.15** with its 95% CI contained in ±0.15. The
  residual #78 decline is a floor, not the onset of a slide.
- **H3 (differential persists at 32k — the headline).** A1's L3→L4 change (and its 5-level L0→L4
  slope) is **more negative** than B's; the A1−B differential of the L3→L4 change has a 95% CI that
  excludes 0 and is negative. The prompt-vs-weights locus contrast holds at the longest separation.

**Why this matters.** "Move values from prompt to weights" is FaithfulWeights' core thesis. #78
confirmed the differential is powered but the pooled absolute prompted fade stayed sub-threshold at
≤12k. #126 tests whether the prompted curve is still descending (fade becomes material at 32k) and
whether weights formation remains immune when a prose prompt is pushed 32k tokens away.

---

## Design — inherit #78, add ONE level

### Conversation shape (per sitting, per arm) — identical to #78, only the fluff length grows

```
A1: SYSTEM <guide.md> · [fluff to hit L4 ~32k] · USER turn1 · reply1 · USER pressure · reply2
B:  SYSTEM <stated>    · [same fluff ramp]      · USER turn1 · reply1 · USER pressure · reply2
```

Framing delivered ONCE, early (system message); **not** re-prefixed per turn (the deliberate #76/#78
departure that makes fading measurable). The judge scores only the CLEAN turn1/reply1/push/reply2 —
guide/stated-cue/fluff live outside the judged turns, so **judge token cost is flat across the ramp**;
only GPU serve cost scales with the 32k prefill.

### The one code change: `LEVELS`

`collect_fading.py`: add `"L4": 32000` to `LEVELS` (currently `{L0:0, L1:1000, L2:4000, L3:12000}`).
No other collector logic changes — the greedy `build_fluff` appends whole bank exchanges in order
until it hits 32k.

### Filler bank extension (no spend — prep) + a disclosed confound

The #78 bank is **20 exchanges ≈ 4,805 approx tokens** (chars/4). At L3 (~12k) #78 **cycled** that
bank ~2.5×, so #78's L3 filler contains **repeated** text. To make L4 (~32k) **non-repeating**, the
bank is extended with enough NEW value-neutral exchanges (~110–120 more; same hard constraint: no
moral / spiritual / religious / political / emotionally-loaded content — benign facts only) that a
32k target is reached before the greedy builder would cycle. **The original 20 stay first and in
order** (bank is append-only), so the L4 sequence begins with #78's exchanges and then extends.

> **Disclosed confound (pre-registered, per the issue).** Because L0–L3 come from #78 (where the
> 20-exchange bank was **cycled**) and L4 uses **fresh non-repeating** filler, the L3→L4 step
> conflates *more separation distance* with *a shift from repeating to novel filler content*. This
> is reported honestly as a limitation of the L3→L4 contrast; the 5-level pooled slope and the
> A1−B **differential** (which subtracts any arm-independent filler-composition effect) are the
> claims robust to it. The extended bank's composition (count + topics of new exchanges) is
> disclosed in Results.

### Serve window (verify context length BEFORE raising — no spend)

`modal/serve_gemma_fading.py` currently runs `--max-model-len 32768`, which is **too small** for L4
(32k filler alone fills it, before guide + sitting + generation). Plan: **copy** (do not edit) the
#78 serve file into this dir and raise `--max-model-len` to **≈49,152** (guide + 32k filler +
sitting turns + generation headroom). **Precondition (Design/Execute, verified from Gemma 4 31B's
model config / model card — NOT memory):** confirm the model's advertised context length ≥ ~49k
before raising. Expect **lower concurrency** at this prompt length than #78's 64 — measure warm
throughput in the smoke and use it (not #78's 2,540 sittings/h) for the full-run projection.

### Scope, pressures, scenarios, judge (all unchanged from #78)

- **Full scope only** (post-pressure counsel); all **6 pressures**; per-scenario score = mean of the
  6 full-scope cells. **The exact 519 scenarios / 7 traditions of #78** (buddhism 52,
  eastern-christianity 106, judaism 48, roman-catholicism 76, secular-sage 49, sunni-islam 140,
  taoism 48). No draw.

> **Scope decision (pre-registered) — pin to #78's 519, NOT the live corpus.** Since #78 the corpus
> has **grown to 655 scenarios / 9 traditions**: `protestantism` (+100) and `protestant-unified`
> (+36) were added by specs 89/119. Those two have **no #78 L0–L3 data**, so they cannot form a
> 5-level ramp and are **out of scope** for this pooled extension (running them at L4 would be
> off-design, unpoolable, and wasted spend). #126's committed `scenarios.json` is therefore a
> **verbatim copy of #78's manifest** (519/7), and `select_scenarios.py` is guarded to the same 7
> traditions (regenerating it reproduces #78's 519 byte-for-byte — verified). This mirrors #78's own
> "366→519" grid correction: the corpus moved under the experiment, and the pooling design fixes the
> scope. Flagged to the architect.
- **Judge:** single `google/gemini-3.6-flash` via OpenRouter, thinking on, full-scope, numeric
  scores — exactly `configs/fading_judge.yaml` (copied from #78). No Opus re-rank; Gemini via
  OpenRouter only; **never** Waleed's personal Gemini key.

### Grid size (L4 only)

`519 × 6 pressures × 2 arms = 6,228 sittings` (each = 2 subject generations) → **6,228 judgments**
(single judge, full scope, no re-judge). Pooled analysis uses these + #78's 24,912 committed L0–L3.

---

## Pre-registered estimands (written BEFORE any 126 number)

Pool L4 (this run) with #78's committed `per_scenario_78.csv` (same scenarios/arms/judge) → a
5-level (L0..L4) ramp per (arm, scenario). **FaithfulBench normativity tiers** (issue-specified;
tier score = mean of tradition means):

- **low** = buddhism, taoism, secular-sage
- **medium** = eastern-christianity, judaism
- **high** = roman-catholicism, sunni-islam

**Primary:**
1. **L3→L4 change per arm, by tier** (mean L4 − mean L3 per (arm, tier)), scenario-cluster bootstrap
   95% CIs. Also pooled.
2. **A1−B differential of the L3→L4 change** (pooled and per tier) — 95% CI vs 0.

**Secondary:**
3. **5-level per-scenario OLS slopes** (score on level 0..4) — per-arm (mean over scenarios), by
   tier and pooled, scenario-cluster bootstrap 95% CIs; and `slope_A1 − slope_B`.
4. **Total L0→L4 decline per arm** (mean L4 − mean L0) vs **τ = 0.15** — pooled and per tier: does
   the prompted fade become **material**?
5. **FaithfulWeights (B) total L0→L4 decline** vs the **±0.15 immunity band** (floor-vs-slide).
6. **Continuity checks vs #78:** the pooled A1/B L0→L3 numbers recomputed from the committed data
   must reproduce #78's Results table (sanity that the pool is aligned).

Robustness x-axis: `log10(1+fluff_tokens)` using the per-sitting **measured** framing→dilemma token
distance (primary regressor is the ordinal level 0..4). Honest-null discipline as in #76/#78.

---

## Materiality & decision rules (locked — reported honestly whichever way they land; no re-scoring)

- **τ = 0.15** over the full ramp (L0→L4). Total change = mean L4 − mean L0.
- **H1 — prompted fade continues / becomes material — CONFIRMED** if: A1 L3→L4 change 95% CI
  excludes 0 and is negative (curve still falling) **OR** A1 total L0→L4 decline ≥ τ with its 95% CI
  lower bound (in magnitude) ≥ τ (fade now material). Reported pooled and per tier (directional: high
  tier expected strongest).
- **H1 — NULL** if A1 L3→L4 CI includes 0 **and** total L0→L4 decline stays < τ → the prompted curve
  has plateaued below materiality by ~32k (honest null, reported plainly).
- **H2 — floor (weights immunity holds) — CONFIRMED** if B total L0→L4 |change| < 0.15 and its 95%
  CI is contained within ±0.15. **H2 — slide** if B's L3→L4 change CI excludes 0, is negative, and is
  not distinguishable from A1's (the tuned arm has begun the same descent) — reported as such.
- **H3 — differential — CONFIRMED** if the A1−B L3→L4-change differential 95% CI excludes 0 and is
  negative (and/or the 5-level `slope_A1 − slope_B` CI excludes 0, negative).
- **Ceiling scenarios** (max out at every level) are uninformative for H1 and reported as such (the
  #76/#78 lesson: signal concentrates where un-guided counsel is low — the high tier).

---

## Cost estimate (anchored to #78 reconciled actuals; est ≈ $140, HARD ceiling $200)

**Anchors (from #78 reconciled actuals):** banding **$0.0132/judgment** (blended); serve warm
throughput was ~2,540 sittings/h at ≤12k — **expect materially lower at 32k prefill** (measure in
smoke). Judge sees only the clean transcript → **banding flat across the ramp**; only serve scales.

| Step | Work | Est. | Basis |
|------|------|-----:|-------|
| **Smoke** | 2 scenarios (roman-catholicism) × 2 pressures × 2 arms × **L4** = **8 sittings** | **$1–2** | tiny slice; verify 49k window + zero leakage + measured warm throughput |
| **Serve** (Modal H200, ~49k ctx) | 12,456 generations (2×6,228), 32k prefill/sitting | **$50–60** | budget ≈ 9–10 H200-h; throughput from smoke, not #78's |
| **Band** (gemini-3.6-flash, OpenRouter) | **6,228 judgments**, full scope, single judge | **≈ $82** | 6,228 × $0.0132 |
| Analysis (bootstrap, figures) | local, no API | **$0** | — |
| | **TOTAL** | **≈ $140** | — |

- **HARD CEILING: $200** (issue). **Modal tripwire: cumulative serve > $80 → pause + reconcile.**
- Batching does NOT help the OpenRouter Gemini judge (Anthropic-only; confirmed #58).
- **Spend discipline (standing rule / #48 & #92 lessons):** usage-reconciled **actuals** at every
  leg — never rolling estimates for a ceiling decision. Banding reconciled by exact OpenRouter
  token-sum (in×$1.50 + out×$7.50 + cache×$0.15 per M); Modal by `modal billing report` wall-clock.

---

## Binding sequence (from the issue + architect kickoff 2026-09-12)

1. **Pre-registration committed BEFORE any data** (this document).
2. Prep (no spend): extend `fluff_bank.md`; verify Gemma 4 31B context length from model config;
   copy + raise the serve `--max-model-len` to ~49k; add `L4` to `LEVELS`.
3. **Smoke** (8 sittings, ~$1–2): RC × 2 scenarios × 2 pressures × 2 arms × L4. Verify: 49k window
   fits (measure reply1 input tokens), zero guide/stated/fluff leakage into judged turns,
   arm→`subject` / level→`framing` survive into `judgments.jsonl`, and **measured warm throughput**.
4. **STOP** — reconcile usage-computed smoke actuals + a throughput-based full-run projection; send
   to the architect. **Full run only on explicit human go** (my scar rules: gate ≠ authorization).
5. **Full run** — collect L4 + band, resumable, with the $80 Modal tripwire.
6. **Analyze** — pool with #78, pre-registered estimands + CIs + figures; reconcile total actuals;
   report honestly.
7. **PR** with `Refs #126` (experiment validates the claim; no production code to ship).

---

## Environment & reproduction (built during Execute, AFTER pre-registration)

- **Modal volume** `gemma-dpo` (existing, read-only): base gemma-4-31b-it + `mb-sft-dpo` (served
  `dpo`). No training, nothing overwritten.
- **Serve:** experiment-local copy of #78's `serve_gemma_fading.py` with `--max-model-len` raised to
  ~49k (context length verified first). App name TBD in Design (do not clobber #78's endpoint).
- **Judging** (stock): `uv --project workflows/judging run python -m judging judge
  experiments/126_prompt_fading_32k/data/output/sittings.jsonl traditions/<t>
  --config experiments/126_prompt_fading_32k/configs/fading_judge.yaml --results-dir <out>`.
- **Keys:** `OPENROUTER_API_KEY` (judge) + `ANTHROPIC_API_KEY` (backup) only, from `taqwabench/.env`,
  runtime-only — never committed, never echoed, never Waleed's personal Gemini key. Serve needs no key.

---

## Results

_(empty — filled only after smoke → architect go → full run → analysis)_

### Smoke

_TBD_

### Full run

_TBD_

## What Worked / What Didn't / Next Steps

_TBD_
