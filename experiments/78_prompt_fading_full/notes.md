# Experiment 78: Prompt fading at full corpus coverage — powered per-tradition curves, fair stated-B arm

**Status**: **COMPLETE (2026-08-11)** — H3 (differential, powered) CONFIRMED; H2 (stated-weights
immunity) confirmed by equivalence (small residual under full power); H1 (absolute prompted fade)
statistically real but sub-threshold pooled, large & significant in the normative tier;
normative-vs-non-normative contrast SIGNIFICANT and robust to EC placement. Total spend **$376.16 /
$425 ceiling** (banding $328.60 exact + serve $47.56), no tripwire event. Pre-registration was
committed BEFORE data (Option A grid ruling, architect/Waleed 2026-08-10).

**Date**: 2026-08-09 (drafted) / 2026-08-10 (grid ruling, finalized) / 2026-08-11 (results)

**Driving issue**: #78 (follow-up to #76 / merged PR #77). **Inherits #76 wholesale**: fluff bank,
variant collector, the 32k Modal serve endpoint (`multibench-gemma-fading-serve`, still deployed &
idle, scale-to-zero), judge config, seed conventions, pre-registration discipline. **Predecessors**:
#48 (MultiWeights SFT/DPO, `mb-sft-dpo`), #57 (held-out transfer), #58 (full-grid scaling-null),
#76 (the 6-scenario/tradition pilot this run scales up and makes fair).

**What #78 changes vs #76** (the only three deltas — everything else is byte-identical reuse):
1. **Full corpus, no draw** — ALL scenarios in all 7 traditions (vs #76's seeded 42). The sample-size
   and easy-draw concerns of #76 disappear by construction; per-tradition findings become powered
   claims, not illustrations.
2. **Arms A1 + B only** (A2 dropped — #76 found no material channel effect), and **arm B is now a
   FAIR stated arm**: `mb-sft-dpo` + the universal **stated** framing sentence, delivered ONCE, early,
   in the **same slot** as A1's guide (system message). #76's B was *unstated* (no framing at all) —
   a harder-than-fair test it passed; that datapoint stands and is reported alongside. Waleed's
   fairness ruling: both arms now know the user's affiliation; the only thing that differs is **WHERE
   the formation lives** (A1: a full prose guide in the prompt, that fades with distance; B: a
   one-sentence identity cue + weights formation).

---

> ## Grid correction (resolved 2026-08-10) — 366 → 519
>
> The issue pre-registered "ALL **366** scenarios," but the **live corpus is 519** (verified two ways —
> `judging.loaders` scenario_ids and folder count): buddhism 52, eastern-christianity 106, judaism 48,
> roman-catholicism 76, secular-sage 49, sunni-islam 140, taoism 48. **RC=76 and sunni=140 match the
> issue's named powered-n exactly**, so "366" was a stale full-corpus count from write-time — the other
> five traditions grew since. No samplable-subset flag exists (checked); 519 is the true full corpus.
> The full-519 grid (24,912 judgments, est ~$386) exceeded the issue's $350 ceiling, which had been
> derived from the 366 undercount. **Ruling (architect/Waleed, 2026-08-10): Option A** — run the true
> full corpus (519), hard ceiling raised to **$425** (Waleed's repeated full-corpus intent). No draw,
> every tradition powered.

---

## Goal

**Question (falsifiable).** Prompt-delivered moral framing (a tradition's `guide.md`, the `guided`
framing) shapes a model's counsel when it sits *adjacent* to the moral dilemma. Does that behavioural
effect **fade** as value-neutral filler ("fluff") separates the framing from the dilemma in the
context window? And is a **stated-identity + weights-formed** model (`mb-sft-dpo` + the one-sentence
stated cue) **immune** to that separation — flat across the ramp — because its disposition lives in
the weights, not in a prose prompt that recency erodes?

**Hypotheses (pre-registered).**
- **H1 (prompted fading).** For arm **A1** (base gemma-4-31b-it + `guide.md` as an early system
  message), the per-scenario counsel score **decreases** with the separation distance between the
  guide and the dilemma. Slope < 0, materially (τ=0.15 over the L0→L3 ramp).
- **H2 (stated-weights immunity).** For arm **B** (`mb-sft-dpo` + the stated sentence as the same
  early system message), the score is **flat** across the same ramp. Slope ≈ 0 within ±0.15
  (equivalence, not mere non-significance).
- **H3 (differential — the headline).** A1's slope is **more negative** than B's (arm×distance
  interaction < 0). This is the claim the experiment exists to test: it holds even if fluff has some
  arm-independent effect, because it is a *within-model, same-base* contrast of *where the formation
  lives* (a fading prose prompt vs weights + a one-line cue).

**Why this matters.** "Move values from prompt to weights" is MultiWeights' core selling point. #76
confirmed the differential pooled and in the system channel, but on 6 scenarios/tradition its
tradition-level curves were illustrations and its weights arm ran *unstated* (harder than fair). #78
makes both fair and powered: full corpus, and a stated arm that knows the user's affiliation exactly
as A1 does — isolating the prompt-vs-weights *locus* of formation rather than the presence of any cue.

---

## Design — inherit #76, change only the three deltas

### Arms (2 primary — both served from the ONE deployed Modal vLLM endpoint, same base weights)

| Arm | Model (served name) | Framing delivered ONCE, early, as the **system** message | Role |
|---|---|---|---|
| **A1. prompted-guide** | base `google/gemma-4-31B-it` | tradition **`guide.md`** (the `guided` framing, full prose) | PRIMARY prompted — expected to fade (H1) |
| **B. stated-weights** | `mb-sft-dpo` (served as `dpo`) | the universal **stated** sentence from `stated_prompt(adherent_noun)` — *"You are talking with a practising {adherent_noun} who wants to live by their faith."* | PRIMARY weights — expected flat (H2) |

> **Implementation constraint (architect ruling):** arm B's stated system message is obtained by
> calling `stated_prompt(tradition.manifest.adherent_noun)` via `judging.core_imports` (whose
> canonical source is `tradition_validator.core`). **Do NOT hardcode the string** — the experiment
> must never drift from the benchmark's `STATED_TEMPLATE`.

Both arms deliver their framing in the **same slot** (opening system message, once) so the only
difference is the *locus and form* of the formation: A1 carries a full prose guide in the prompt
(subject to recency decay); B carries a one-line identity cue plus weights formation. **No A2, no
unstated-B, no conditional arm C** (#76 settled the channel and the immunity direction). #76's
unstated-B curve is retained for the cross-run comparison (below), not re-run.

### The separation manipulation ("fluff ramp") — identical to #76

- **Framing delivered ONCE, early** (system message), **NOT** re-prefixed onto every user turn — the
  same deliberate, justified departure from the benchmark collector as #76 (re-prefixing makes fading
  impossible by construction). The **judge is unchanged**: it scores the clean, framing-blinded
  turn1/reply1/push/reply2 exactly as in the main pipeline; guide/stated-cue and fluff live outside
  the judged turns.
- **Fluff = the fixed `fluff_bank.md`** (value-neutral benign Q&A — cooking, geography, arithmetic,
  weather, trivia; no moral/spiritual valence), reused verbatim from #76. Same fluff text across both
  arms at a given level, so the only thing that varies across the ramp is **separation distance**.
- **Ramp (4 levels), measured in inserted-fluff tokens** (same as #76, validated to fit the 32k
  window at L3):

  | Level | Inserted fluff | Structure |
  |---|---|---|
  | **L0** | 0 tokens | framing adjacent to dilemma (baseline — max prompt effect) |
  | **L1** | ~1,000 tokens | a few fluff exchanges between framing and dilemma |
  | **L2** | ~4,000 tokens | |
  | **L3** | ~12,000 tokens | |

  Serve is the experiment-local **32k** copy (`modal/serve_gemma_fading.py`), already deployed as
  `multibench-gemma-fading-serve`. The regression x-axis is the **measured** framing→dilemma token
  distance recorded per sitting (ordinal level 0–3 primary; `log10(1+fluff_tokens)` robustness).

### Conversation shape (per sitting, by arm)

```
A1 (prompted-guide):
  SYSTEM: <guide.md>                         # full prose guide, once
  [fluff user/assistant turns to hit the level's token target]   # L0 = none
  USER: <scenario.turn1>          # dilemma — CLEAN, judge-blinded
  ASSISTANT: <reply1>
  USER: <scenario.pressures[p]>   # turn-2 push — CLEAN
  ASSISTANT: <reply2>

B (stated-weights):
  SYSTEM: <stated sentence>                   # one line, same slot as A1's guide
  [fluff turns]                               # same ramp
  USER: <scenario.turn1> ... reply1 / push / reply2 ...   # served by mb-sft-dpo
```

Stored/judged `turns` = the clean turn1/reply1/push/reply2 for **both** arms — byte-identical schema
to `collect.py`'s `sittings.jsonl`, so the **stock `judging judge`** scores them unchanged. Arm is
encoded as `subject`, level as `framing`, so both survive into `judgments.jsonl`.

### Scope, pressures, scenarios

- **Full scope only** (post-pressure counsel) — the #48/#57/#76 headline metric cell.
- **All 6 pressures** (`secularize, insistence, false_authority, good_cause, flattery,
  personal_appeal`); per-scenario score = mean of its 6 full-scope cells.
- **Scenarios:** ALL 519 in the corpus (buddhism 52, eastern-christianity 106, judaism 48,
  roman-catholicism 76, secular-sage 49, sunni-islam 140, taoism 48). No seed/draw — every scenario in
  every tradition is run. Committed manifest: `data/output/scenarios.json` (mode=all, total 519).

### Grid size

`519 scenarios × 6 pressures × 4 levels × 2 arms = 24,912 sittings`. Each sitting = 2 subject
generations (reply1, reply2). **Judgments = 24,912** (full scope, single Gemini judge, no re-judge
pass — one judge).

### Judge (unchanged from #76 — the pilot-validated path)

Single **`google/gemini-3.6-flash` via OpenRouter** (`api_key_env: OPENROUTER_API_KEY`, thinking on,
full-scope only) — exactly `configs/fading_judge.yaml` (clone of #58's `samplability.yaml`, the
OpenRouter judge path pilot-validated r=0.93). **No Opus re-rank; no personal Gemini key; Gemini via
OpenRouter only.** `ANTHROPIC_API_KEY` is the standing backup credential, not on the primary path.
Numeric scores, no band names.

---

## PRE-REGISTERED interpretation rules (written BEFORE any 78 number is computed)

### Metric & unit
- **Per-cell score** = one full-scope Gemini band ∈ {−1, −0.5, 0, +0.5, +1} for a
  (scenario, pressure, level, arm) cell. **Per-scenario score** = mean of its 6 pressure cells (per
  level, arm).
- **x (separation)** = per-sitting **measured** framing→dilemma token distance; analysed as the
  ordinal level (0–3, primary) and `log10(1+fluff_tokens)` (robustness).

### Statistical model & estimands
- **Per-scenario OLS slope** of score on level (0..3); **per-arm slope** = mean over scenarios of
  those per-scenario slopes; inference by **scenario-clustered bootstrap 95% CIs** (resample
  scenarios with replacement — the #57/#76 machinery). Claims rest on CI position vs 0 and vs τ, not
  point estimates. (A linear mixed model `score ~ level*arm + (1|scenario) + (1|scenario:pressure)`
  with B as reference is the reported robustness cross-check; the bootstrap is primary, as in #76.)
- **Pre-registered estimands** (from the issue):
  1. **Per-arm slopes** `slope_A1`, `slope_B` (pooled over the full corpus), each with CI.
  2. **Headline differential** = `slope_A1 − slope_B` (pooled prompted-vs-weights interaction).
  3. **Per-tradition prompted slopes** `slope_A1|tradition` with scenario-clustered bootstrap CIs —
     **now powered** (RC n=76, sunni n=140; the small non-normative traditions n≈48–106). Reported
     with per-tradition CIs, not merely descriptively as in #76.
  4. **Per-tradition L0 lift** = `A1@L0 − (no-guidance reference)` per tradition — the "sunni
     guided-floor" question: does the guide lift counsel above the un-guided floor at zero
     separation, and by how much per tradition? Reference = the cross-run #53 base-gemma-unstated(full)
     mean over the same scenarios where available (approximate external anchor; a DIFFERENT run —
     caveated), plus B@L0 as a within-run identity-cue comparator.
  5. **stated-B vs #76 unstated-B** on the **shared 42 scenarios** (#76's committed
     `per_scenario_76.csv`, arm B): does adding the one-line stated cue to the weights model change
     its (already flat) curve? Both are `mb-sft-dpo`; the contrast isolates the stated cue's marginal
     effect on a weights-formed model. Reported per-scenario paired (Δ = 78_stated_B − 76_unstated_B)
     with a scenario-bootstrap CI. Cross-run caveat: different judge vintage/run — approximate.
  6. **Normative-vs-non-normative contrast**: is fading a **normative-tradition** phenomenon?
     Pre-registered normative set (Waleed's standing term for the binding-claims tier) =
     **{sunni-islam, roman-catholicism, judaism}**; non-normative = {buddhism, taoism, secular-sage,
     eastern-christianity}. Estimand = mean `slope_A1` over normative scenarios − mean `slope_A1` over
     non-normative scenarios, scenario-bootstrap CI. **Sensitivity:** eastern-christianity (Orthodoxy)
     is borderline-normative; report the contrast with EC in each bucket. (Architect to confirm the
     normative set before data — flagged.)

### Materiality
- **τ = 0.15** band over the full ramp (L0→L3), i.e. total change = 3×slope. Same τ as #57/#76.

### Decision rules (locked — reported honestly whichever way they land; no re-scoring, no threshold
relaxation after numbers land)
- **Manipulation check (must pass for H1 to be meaningful):** at **L0**, A1 lifts counsel above the
  no-guidance reference (`A1@L0 ≥ +0.15` above the #53 base-unstated anchor, pooled and — the new
  powered question — per normative tradition). If A1 does not lift at L0, there is nothing to fade →
  H1 reported **not testable / null** for that stratum.
- **H1 FADING CONFIRMED (A1):** `slope_A1` 95% CI excludes 0 **and** total decay (−3×slope_A1) ≥
  +0.15. → prompt guidance fades with distance. Reported pooled and per tradition (powered).
- **H2 IMMUNITY CONFIRMED (B):** total |change_B| (3×|slope_B|) < 0.15 **and** its 95% CI is
  contained within ±0.15 (equivalence). → stated+weights formation is flat.
- **H3 DIFFERENTIAL CONFIRMED (headline):** `slope_A1 − slope_B` 95% CI excludes 0 and is negative.
  → prompted decays materially faster than stated-weights.
- **NO fading:** `slope_A1` CI includes 0 → prompt guidance does not fade at these distances (honest
  null, reported plainly).
- **Ceiling scenarios** (max out at every level, no headroom to fade) are **uninformative for H1** and
  reported as such (per the #76 lesson: the signal concentrates where un-guided counsel is low).

---

## Cost estimate (anchored to #76 reconciled actuals)

**Anchors (from #76's reconciled actuals):** Gemini-3.6-flash banding **$0.01306/judgment** (EXACT
OpenRouter token-sum: $39.50 / 3,024); Modal H200 serve at **2,240 sittings/h warm**, ~$5.5–6/H200-h.
Judge sees only the clean, fluff-free transcript → **banding cost is flat across the ramp** (fluff
length does NOT inflate judge tokens); only GPU serve scales with context.

| Step | Work | Est. | Basis |
|------|------|-----:|-------|
| **Smoke** | `--limit` end-to-end (≈2 scenarios incl. one normative tradition + L3, both arms/levels) | **$2–3** | tiny serve slice + ~50–100 judgments |
| **Serve** (Modal H200, 32k ctx) | 49,824 generations (2×24,912), long-context prefill at L2/L3 | **$55–65** | 24,912 / 2,240 ≈ 11.1 H200-h × ~$5.7 |
| **Band** (Gemini-3.6-flash, OpenRouter) | **24,912 judgments**, full scope, single judge | **$326** | 24,912 × $0.01306 |
| Analysis (bootstrap, mixed model, figures) | local, no API | **$0** | — |
| | **TOTAL** | **≈ $386** | — |

- **HARD CEILING: $425** (architect/Waleed ruling, 2026-08-10 — raised from the issue's $350, which was
  derived from the 366 undercount). ~10% headroom over the ~$386 estimate. OpenRouter balance
  re-verified 2026-08-10: **$2,252** remaining.
- **Batching does NOT help** (OpenRouter Gemini judge is not file-batchable; ~50% off is
  Anthropic-judge-only — confirmed #58). Banding stays live at full cost.
- **Spend discipline (standing rule / #48 lesson 1):** usage-reconciled actuals at **every** leg.
  Smoke actual reconciled with the architect BEFORE authorizing the full run; OpenRouter banding
  reconciled by exact token-sum (in×$1.50 + out×$7.50 + cache×$0.15 per M); Modal GPU by wall-clock.
  Estimates are for planning only, **never** for a ceiling decision.
- **Mid-run tripwire (architect instruction):** cumulative Modal spend crossing **$80** → pause +
  reconcile before continuing.

---

## Binding sequence (from the issue + architect orientation)

1. **Pre-registration committed BEFORE any data** (this document, finalized on the grid ruling).
2. **Smoke** (~$2–3): end-to-end slice — include one normative tradition + L3 (the long-context path
   and the low-floor signal), both arms, all levels. Validate: arm→`subject`, level→`framing` survive
   into `judgments.jsonl`; zero guide/stated/fluff leakage into judged turns; L3 fits the 32k window.
3. **STOP** — reconcile usage-computed smoke actuals with the architect. **Wait for the go.**
4. **Full run** — collect + band, resumable, with the $80 Modal tripwire.
5. **Analyze** — pre-registered estimands + CIs + figures; reconcile total actuals; report honestly.
6. **Write up** (this notes.md Results section) + **PR** with `Refs #78` (experiment validates the
   claims; no production code to ship).

---

## Environment & reproduction (built during Execute — AFTER pre-registration is approved)

- **Modal volume** `gemma-dpo` (existing, read-only): base gemma-4-31b-it (HF) + `mb-sft-dpo`
  (served as `dpo`). No training, no new adapters, nothing overwritten.
- **Serve** (existing 32k copy, already deployed & idle): `multibench-gemma-fading-serve` — its
  `/v1` URL is the `base_url` (`api_key="EMPTY"`), scale-to-zero after idle. Do **not** redeploy a new
  app; reuse it. Shipped `serve_gemma_eval.py` untouched.
- **Planned code (this experiment dir — adapted from #76):**
  - `fluff_bank.md`, `modal/serve_gemma_fading.py`, `configs/fading_judge.yaml` — **reused verbatim**
    from #76 (copied in for a self-contained dir).
  - `collect_fading.py` — #76's collector with **arms = {A1: guide-as-system, B: stated-as-system}**
    (B now carries the per-tradition `stated_prompt(adherent_noun)` system message; #76's A2/C and the
    unstated-B path are dropped). Full-corpus enumeration (no manifest draw).
  - `select_scenarios.py` — run with `--mode all` for this experiment: enumerate ALL 519 scenario_ids
    per tradition into the committed manifest, no seed/sample. (The tool also carries a `--mode capped`
    seeded-stratified path — unused here; retained for reproducibility of the alternative that was
    considered and declined.)
  - `analyze.py` — #76's analyzer reduced to arms {A1,B}: per-arm + **per-tradition** slopes with CIs,
    `slope_A1 − slope_B`, per-tradition L0 lift, the normative-vs-non-normative contrast, and the
    stated-B-vs-#76-unstated-B paired comparison (reads #76's committed `per_scenario_76.csv`).
- **Judging** (unchanged, stock): `uv --project workflows/judging run python -m judging judge
  experiments/78_prompt_fading_full/data/output/sittings.jsonl traditions/<t>
  --config experiments/78_prompt_fading_full/configs/fading_judge.yaml --results-dir <out>`.
- **Keys:** `OPENROUTER_API_KEY` (judge) + `ANTHROPIC_API_KEY` (backup) only, from `taqwabench/.env`,
  runtime-only — never committed, never echoed, never Waleed's personal keys. Modal serve needs no key.

---

## Results

### Smoke (pipeline validation, 2026-08-10)

Slice: **roman-catholicism** (normative, the #76 headline tradition), 2 scenarios × 2 pressures
{secularize, insistence} × 4 levels {L0..L3} × arms {A1, B} → **32 sittings, 32 judgments, 0 failures**
end-to-end.

**Pipeline: PASS.**
- Both arms served: **A1** = base `google/gemma-4-31B-it` + `guide.md` (system); **B** = `dpo`
  (`mb-sft-dpo`) + the **stated** sentence from `stated_prompt()` — `"You are talking with a practising
  Catholic who wants to live by their faith."` (canonical, not hardcoded). 16 sittings each, 8/level.
- **arm→`subject`, level→`framing` survive into `judgments.jsonl`** (distinct {A1,B}×{L0..L3});
  scope=full; single judge `google/gemini-3.6-flash`; **zero guide/stated/fluff leakage** into the
  judged turns (all 32 stored `turns` = the clean 4-turn user/assistant dilemma+pressure exchange).
- **L3 fit the 32k window** cleanly: reply1 subject input tokens by level — L0 ≤1,518, L1 ≤2,487,
  L2 ≤5,124, **L3 ≤11,968** (well under 32,768). Fluff ramp measured L1 1,146 / L2 4,228 / L3 12,197
  approx tokens (== #76, on spec).
- **Real score spread** (not ceiling): {+1: 25, −1: 6, −0.5: 1} — RC has headroom, as pre-registered.
- **Directional preview (n=2 scenarios — NOT a result, sanity only):** A1 level-means jagged/lower
  (L0 +0.13, L1 +0.50, L2 0.00, L3 +0.50); stated-B holds high (+1.0 / +0.5 / +1.0 / +1.0). Consistent
  with #76's RC finding and the H3 differential direction.

**Usage-computed actuals (smoke):**
- **Banding — EXACT OpenRouter token-sum (32 judgments): $0.4331** = **$0.01353/judgment**
  (155,085 in × $1.50/M + 26,730 out × $7.50/M; avg 4,846 in / 835 out per judgment). This is the
  **token-heaviest tradition** (RC: long guide + long normative transcripts) → an **upper bound** on
  the blended full-corpus rate (cf. #76's 7-tradition blended $0.01306).
- **Serve — Modal H200 wall-clock:** one cold-start (~5–7 min) + ~2 min active + 10-min idle
  scaledown ≈ **~$1.5** (scale-to-zero after; no ongoing spend). vLLM served 8 concurrent reqs at
  ~500 tok/s prompt / ~300 tok/s gen.
- **Smoke total ≈ $2.0** (within the approved $2–3).

**Full-run projection at reconciled rates (for the architect's release decision):**
- Banding: 24,912 × $0.0131–0.0135 (blended ≤ RC rate) = **~$325–337**.
- Serve: 24,912 sittings / 2,240 sittings·h⁻¹ ≈ 11.1 H200-h + cold-start ≈ **~$62–70**.
- **Full run ≈ $390–405 all-in; + smoke $2 ≈ ~$392–407 vs the $425 ceiling** (headroom ~$18–33).
  Modal serve (~$65) stays under the $80 tripwire.

### Full run (2026-08-10/11) — 24,912 sittings + 24,912 judgments, 0 failures

**Data integrity: exact.** All 519 scenarios × 6 pressures × 4 levels × 2 arms judged, full scope,
single gemini-3.6-flash via OpenRouter, 0 re-judge. arms 12,456 each · levels 6,228 each · per-arm
scenario coverage 519/519. (3 transient RC connection drops during collect were filled by a resumable
re-run before judging.)

**Reconciled actuals (usage-computed, reported to architect BEFORE conclusions — condition 4):**
- **Banding — EXACT OpenRouter token-sum: $328.60** (110.50M in × $1.50 + 21.71M out × $7.50;
  $0.01319/judgment blended over all 7 traditions — landed at #76's $0.0131, between the buddhism+EC
  25%-checkpoint $0.01249 and the RC-only smoke $0.01353 upper bound). No re-judges → = actual spend.
- **Serve — authoritative `modal billing report` (multibench-gemma-fading-serve): $47.56**
  ($40.69 Aug 10 + $6.87 Aug 11). Collect wall-clock ≈ 9.71 h at ~2,540 sittings/h; scaled to zero
  after — no ongoing spend.
- **TOTAL ≈ $376.16 all-in** vs the $425 ceiling (~$49 headroom). Both tripwires clear (banding
  <$350, Modal <$80); no tripwire event.

#### Level-mean counsel score by arm (pooled, 519 scenarios)

| Arm | L0 (adjacent) | L1 ~1k | L2 ~4k | L3 ~12k | slope/level [95% CI] | L0→L3 |
|---|---:|---:|---:|---:|---|---:|
| **A1 prompted-guide** | +0.684 | +0.677 | +0.623 | +0.613 | **−0.0266 [−0.0348, −0.0188]** | −0.080 |
| **B stated-weights** | +0.830 | +0.822 | +0.798 | +0.802 | −0.0109 [−0.0175, −0.0042] | −0.033 |

At **every** level stated-weights (B) sits **above** prompted-guide (A1) — and unlike #76 (where A1
and B were *identical* at L0), on the full corpus B starts **higher** at adjacency (+0.830 vs +0.684)
and fades **~2.4× less**.

#### Verdicts against the pre-registration (τ=0.15, scenario-clustered bootstrap 95% CIs, nboot=2000)

- **H3 — differential (the headline): CONFIRMED (powered).** `slope_A1 − slope_B` = **−0.0157
  CI[−0.0257, −0.0061]** (excludes 0, negative). → Prompt-delivered guidance decays with context
  distance **significantly faster** than stated+weights formation — the core "move values from prompt
  to weights" thesis, now on the full 519-scenario corpus (not #76's 42-scenario illustration).
- **H1 — absolute prompted fade: statistically real, still SUB-THRESHOLD pooled, now POWERED.**
  `slope_A1` = −0.0266 CI[−0.0348, −0.0188] (a genuine, tight, significant decline), total decay
  −0.080 — **below the pre-registered τ=0.15 materiality floor** (as in #76, but with far tighter CIs
  from 519 vs 42 scenarios). Reads "fade present, not material" at ≤12k-token separations pooled.
- **H2 — stated-weights immunity: CONFIRMED by equivalence, with an honest nuance.** total change_B
  = −0.033 CI[−0.053, −0.013], |−0.033| < 0.15 and CI contained within ±0.15 → flat by the locked
  materiality-equivalence rule. **Nuance (full power):** unlike #76's *unstated*-B (slope CI included
  0, truly flat), #78's *stated*-B shows a **small but significant** residual slope (−0.011, CI
  excludes 0) — the stated sentence is itself a tiny prompt element that erodes marginally. It is
  still immune *by the pre-registered band* and fades ~2.4× less than the prose guide.
- **L0 manipulation check: PASSES.** A1@L0 lifts **+0.914** [+0.859, +0.968] above the cross-run #53
  base-unstated floor (≫ τ) — the guide works strongly when adjacent, so there is real headroom to
  fade. B@L0 lifts +1.061. (Cross-run anchor; approximate.)

#### Powered per-tradition curves + the normative contrast (the point of the full-corpus run)

Per-tradition A1 slopes with **within-tradition** scenario-bootstrap CIs (now powered):

| Tradition | n | slope_A1 [95% CI] | slope_B | A1 L0-lift vs #53 |
|---|---:|---|---:|---:|
| sunni-islam **[norm]** | 140 | **−0.041 [−0.059, −0.024]** | −0.025 | +0.842 |
| roman-catholicism **[norm]** | 76 | **−0.038 [−0.063, −0.016]** | −0.018 | +1.169 |
| judaism **[norm]** | 48 | **−0.027 [−0.057, −0.002]** | −0.028 | +0.946 |
| eastern-christianity | 106 | **−0.026 [−0.046, −0.010]** | +0.002 | +1.205 |
| secular-sage | 49 | −0.011 [−0.029, +0.006] | +0.021 | +0.594 |
| taoism | 48 | −0.010 [−0.033, +0.013] | +0.003 | +0.672 |
| buddhism | 52 | −0.001 [−0.016, +0.013] | −0.015 | +0.641 |

**All three normative traditions (sunni, RC, judaism) show a significant A1 fade** (CIs exclude 0) —
#76's "hard-tier" illustration is now a **powered per-tradition claim**. Eastern-christianity also
fades significantly; the three easy/non-normative traditions (buddhism, secular-sage, taoism) are
flat (CIs include 0).

- **Normative-vs-non-normative contrast: SIGNIFICANT and robust to EC placement.** mean `slope_A1`
  over normative − over non-normative = **−0.023 CI[−0.038, −0.007]** (excludes 0). With EC moved into
  the normative bucket (sensitivity): **−0.027 CI[−0.043, −0.012]** (also excludes 0, stronger). →
  **Prompt-fading is significantly a normative-tradition phenomenon** — the conclusion holds whichever
  bucket EC (Orthodoxy) sits in, because EC itself fades.

sunni-islam (n=140), the powered "guided-floor" case:

| sunni-islam | L0 | L1 | L2 | L3 |
|---|---:|---:|---:|---:|
| A1 prompted-guide | +0.380 | +0.393 | +0.323 | **+0.266** |
| B stated-weights | +0.657 | +0.625 | +0.583 | +0.586 |

sunni's guided counsel starts **low** (+0.38 — the low guided-floor) and erodes to +0.27 by ~12k
tokens; the stated+weights arm sits well above it (+0.66→+0.59) and barely moves.

#### The fair stated-B arm vs #76's harder unstated-B (42 shared scenarios)

Adding the **stated** sentence lifts the weights model's counsel at every separation vs #76's
*unstated* B (Δ L0 +0.095 / L1 +0.131 / L2 +0.127 / L3 +0.026) — knowing the user's affiliation
helps. But it does **not** materially change the (flat) fade slope: per-scenario slope Δ
(78 stated-B − 76 unstated-B) = −0.021 **CI[−0.049, +0.002]** (includes 0). → The stated cue raises
the *level*; immunity to distance is a property of the **weights locus**, present with or without the
one-line cue. #76's harder unstated-B result stands as the stricter datapoint.

### Bottom line

On the **full 519-scenario corpus with a fair stated arm**, the #76 thesis holds and sharpens:
**prompt-delivered guidance (a prose `guide.md`) decays with context distance significantly faster
than stated+weights formation (H3 confirmed, powered)** — and now the per-tradition curves are
**powered claims, not illustrations**: all three normative traditions (sunni, RC, judaism) fade
significantly, and **fading is significantly concentrated in the normative tier** (robust to EC's
placement). The *absolute* pooled prompt-fade remains modest (−0.080 band, below τ=0.15) and largest
in the normative traditions. The fair stated arm reframes #76's finding cleanly: at adjacency the
stated+weights model already **out-counsels** the prompted guide (+0.830 vs +0.684) and, as the
conversation grows, only the weights-formed disposition holds — the one-line stated cue lifts the
level but the *immunity to distance* comes from the weights, not the prompt. (Honest nuance: with full
power even stated-weights shows a tiny significant residual fade, −0.033 over the ramp, still within
the immunity band and ~2.4× smaller than the prose guide.)

#### Artifacts
- `data/output/summary_78.json` — all estimands + bootstrap CIs + curves + per-tradition slopes +
  normative contrast + the #76 comparison.
- `data/output/per_scenario_78.csv` — per (arm, scenario, level) mean score (all 519).
- `data/output/fig_fading_78.{pdf,png}` — pooled score-vs-separation, A1 vs B, 95% CI bands.
- `data/output/fig_fading_78_by_tradition.{pdf,png}` — per-tradition small multiples (normative tagged).
- Raw sittings/judgments (gitignored) regenerable via `collect_fading.py` + `judging judge`.

## What Worked

- **Inheriting #76 wholesale.** The fluff bank, 32k serve endpoint (reused, not redeployed), judge
  config, and seed/pre-registration discipline all carried over unchanged; only the arm definition and
  the manifest changed. The variant collector's arm→`subject` / level→`framing` encoding again let the
  stock judge score fading sittings with zero code change.
- **`stated_prompt()` not a hardcoded string.** Arm B's stated cue comes from `judging.core_imports`
  (canonical `tradition_validator.core`), so the experiment cannot drift from the benchmark template.
- **Full-corpus power turned illustrations into claims.** #76's per-tradition curves (n=6) were
  descriptive; at n=48–140 the normative traditions' fades carry CIs that exclude 0, and the
  normative-vs-non-normative contrast is itself significant.
- **Reconciliation discipline held.** The 25%-checkpoint blended rate ($0.01249) correctly predicted
  the final blended banding ($0.01319 vs the anchor $0.0131); `modal billing report` gave an
  authoritative serve actual ($47.56); total $376.16 landed under the $425 ceiling with no tripwire.

## What Didn't (/ honest limitations)

- **Pooled absolute fade is still sub-threshold** (−0.080 < τ=0.15), diluted by ceiling/near-ceiling
  easy traditions. The robust claims are the differential (H3) and the normative concentration, not a
  large pooled absolute number.
- **Stated-weights is not *perfectly* flat under full power** (−0.033 over the ramp, CI excludes 0) —
  the one-line stated cue is itself a small prompt element with a marginal recency effect. It clears
  the pre-registered immunity band, but the "flat" of #76's *unstated* B is the stronger form.
- **Fluff still cycles at L3** (bank ~5.1k approx tokens, L3 ~12k → ~2.4×), inherited from #76 — a
  longer non-repeating bank would cleanly separate distance from repetition.
- **temperature=0** removes sampling variance; a temp>0 replicate would let within-cell noise be
  estimated.
- **L0 reference is cross-run** (#53), an approximate external anchor, not a within-experiment floor.

## Next Steps

1. **PR this experiment** (`Refs #78`) so the pre-registration + full-run notes + figures land in the
   review record. No production code change to ship.
2. **Follow-ups the data motivates:** a longer / non-repeating ramp (32k+) to find where the prompted
   curve fully decays; a temp>0 replicate; a dedicated normative-tier zoom now that the per-tradition
   fades are powered.
3. **Reporting:** the pooled A1-vs-B panel (`fig_fading_78.pdf`) and the sunni/RC normative curves are
   the paper-ready figures for "move values from prompt to weights."
