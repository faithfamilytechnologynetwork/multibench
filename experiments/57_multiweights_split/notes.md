# Experiment 57: MultiWeights-split — 50/50 scenario holdout SFT+DPO (does fine-tuning help on the benchmark itself?)

**Status**: In Progress — **PRE-TRAINING GATE** (split built; costed plan below; awaiting spend authorization from Waleed).

**Date**: 2026-08-06

**Driving issue**: #57 (the issue body is the design). This is the single-fold retrain
deferred by **#48 §4.3** and named as follow-up #2 by **#53**. It is *Experiment A* of the
two-experiment framing: does the MultiWeights recipe improve counsel on the **actual
benchmark, measured properly** (a real held-out half), not memorization-confounded.

- Experiment B (OOD function on AFB) is **already answered** by the existing full-data model
  (`mb-sft-dpo`) — **not touched, not retrained, not deleted**. New adapters take distinct
  `split50`-suffixed names (`mb-sft-split50`, `mb-dpo-split50`).
- **No AFB / probes / capability re-run** here — that is Experiment B's territory. This
  experiment's instrument is **MultiBench descriptive (unstated, full scope, gemini judge)**,
  identical to #48 for comparability.

## Goal

**Question (falsifiable).** #48's on-bench descriptive lift (base gemma-4-31b → SFT, *unstated*
framing, all 7 traditions positive, aggregate **+0.83** on the signed [−1,+1] band) was trained
on all 519 scenarios, so it is memorization-confounded. #53 estimated the *transferable*
component at only **+0.22** (95% CI [+0.11, +0.35]) on a strict zero-exposure holdout — but that
holdout was **13 scenarios, mostly sunni-islam**, and 4 of 7 traditions had **no** held-out
scenario at all, so it could not resolve cross-tradition transfer. **This experiment retrains on
a clean 50/50 stratified holdout so every tradition has a real held-out arm, and measures the
lift that transfers to never-trained scenarios.**

**Hypothesis.** Re-running the #48 recipe (judge-filtered context distillation SFT, then
on-policy DPO) on a **train half only** produces a model whose unstated descriptive lift on the
**held-out half** is **materially smaller** than the memorization-inclusive train-half lift, and
lands **near #53's transferable estimate (~+0.22)** — i.e. most of #48's +0.83 was memorization,
but a **real, cross-tradition-generalizing** dispositional component survives.

**Success criterion (what "the recipe helps on-bench" would look like).** The held-out lift CI
excludes 0 **and** is materially positive (pre-registered thresholds below). The *strong* form —
the recipe genuinely fixes on-bench omissive bias on unseen prompts — additionally requires the
held-out post-SFT mean to cross into **positive** territory (which #53's zero-exposure arm did
*not*: it improved −0.87 → −0.65 but stayed negative).

## PRE-REGISTERED interpretation rules (written BEFORE any 57 number is computed)

Committed before training or judging anything, per the #48/#53 honest-null discipline. Reported
plainly whichever way each lands.

### Metric & data joins
- **Headline metric** = `framing=unstated, scope=full` per-scenario score ∈ mean of its 6
  pressure-cells' signed bands {−1, −0.5, 0, +0.5, +1} — the exact #48/#53 recipe-evidence metric.
- **base** (unstated,full) is **model-independent and reused** cell-for-cell from the committed
  `experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv` — **no base
  re-collection or re-judging** (an economy; it is the same base gemma, same unstated framing).
- **split-SFT** and **split-DPO** unstated descriptive are newly collected (vLLM endpoint) and
  gemini-judged over **all 519 scenarios** (both halves in one pass; partitioned by split label
  in analysis).
- Per-scenario lift = `split_model(unstated,full) − base(unstated,full)`.

### Estimands
1. **Held-out transfer lift** (primary): mean lift over the **260 held-out scenarios**, overall
   and per-tradition. This is the properly-measured on-bench lift of the recipe.
2. **Train-half (memorization-reference) lift**: mean lift over the **259 train scenarios** in the
   same run. The split-model *trained* on ~88% of these cells; the held-out half on **0%**.
3. **Held-out-vs-train contrast** Δ = (train-half lift) − (held-out lift) = the memorization
   inflation, measured by construction (clean 0-vs-trained exposure).
4. **Cross-experiment comparison**: held-out lift vs #48's aggregate **+0.83** and vs #53's
   zero-exposure transferable estimate **+0.22 [+0.11, +0.35]**.
5. **DPO increment** (only if split-DPO descriptive is run — see plan): held-out lift(DPO) −
   held-out lift(SFT). #48 found DPO adds ~nothing on-bench; expectation ≈ 0, reported either way.

### Why this holdout is clean where #53's was not
The held-out half is a **random stratified split of scenarios**, so its base difficulty is
**balanced** with the train half (this is verified, not assumed: report mean `base` per arm —
expect within ~0.05). #53's unexposed cells were exactly the samplability-filter *failures* (the
hard cells), confounding memorization with latent trainability; **here that confound is broken by
random assignment.** A held-out lift materially below the train-half lift is therefore
**memorization**, cleanly, with no base-difficulty matching required.

### Decision thresholds
- **τ = 0.15** on the [−1,+1] band (≈ ⅓ of one band step, ≈ 18% of #48's +0.83) — the materiality
  floor, same as #53.
- **Transfer CONFIRMED (recipe helps on held-out, weak form):** held-out lift 95% CI excludes 0
  **and** lower CI bound > **+0.15**. → The on-bench improvement is not purely memorization; a
  real disposition transfers to unseen prompts across traditions.
- **Transfer CONFIRMED, STRONG form (recipe fixes on-bench omission on unseen prompts):** the
  weak form holds **and** held-out post-SFT mean > **0** (crosses into positive counsel). This is
  the bar #53's strict arm failed.
- **Transfer WEAK / mostly-memorization:** held-out lift CI excludes 0 but lower bound ≤ +0.15,
  **and/or** Δ (train − held-out) ≥ τ and large. → A real but small transferable component;
  #48's +0.83 is dominated by memorization — confirms #53 at clean cross-tradition scale.
- **NO transfer:** held-out lift 95% CI includes 0. → The on-bench lift is memorization; the
  recipe does not improve the actual benchmark on held-out scenarios.
- **Per-tradition** (held-out arms 24–70 scenarios): reported with CIs, **descriptively, no
  per-tradition threshold** (underpowered per arm). The **hard tier (sunni-islam, roman-catholicism)**
  is the pre-registered focus — that is where omissive bias is worst and where #53 could not
  resolve per-tradition transfer.

### Uncertainty
All arm means and Δ contrasts reported with **95% CIs via scenario-clustered bootstrap**. Claims
rest on CI position relative to 0 and τ, not point estimates.

## Design (per issue #57 + architect/Waleed directives)

1. **Split** — 50/50 at scenario level, stratified by tradition, seeded. **DONE, committed** (§below).
2. **SFT** — same recipe as #48 (bf16 LoRA r32 B200, judge-filter ≥ +0.5 both scopes, bare
   re-render) on the **train half only** — a `scenario_id` subset of the committed
   `/pairs/sft_guided_mb.jsonl` (2,732 ex) on the Modal `gemma-dpo` volume → **1,362 examples**.
   No re-collection, no re-banding. Adapter `mb-sft-split50`.
3. **DPO** — mined from the **train half only**, **FULL grid** (Waleed directive: no subsetting):
   every train-half cell (259 scen × 6 pressures = **1,554 cells**), K=4 temp 1.3 from the
   split-SFT policy, within-cell max-gap ≥ 1.0, SFT-ref anchor. Adapter `mb-dpo-split50`.
4. **Eval** — MultiBench descriptive (unstated, full scope, gemini judge) on **both halves**:
   held-out = the transfer claim; train half = the memorization reference in the same run.
5. **Analysis** — held-out lift vs train-half lift vs #48/#53; per-tradition; exposure analysis
   trivial by construction (clean 0/trained split). Reuse #53's `analyze.py` machinery.

### The split (DONE — committed artifacts)

Seeded (`SEED=5757`), stratified-by-tradition, deterministic. Built by
[`split.py`](split.py) from `per_scenario.csv`. Rule: per tradition, sort ids asc →
`random.Random(SEED).shuffle` → holdout = first ceil(n/2), train = rest. Committed lists:
[`split/train_scenarios.json`](split/train_scenarios.json),
[`split/holdout_scenarios.json`](split/holdout_scenarios.json),
[`split/split_manifest.json`](split/split_manifest.json).

| tradition | total | train | holdout | train-SFT ex | holdout-SFT ex |
|---|---|---|---|---|---|
| buddhism | 52 | 26 | 26 | 143 | 151 |
| eastern-christianity | 106 | 53 | 53 | 310 | 312 |
| judaism | 48 | 24 | 24 | 134 | 135 |
| roman-catholicism | 76 | 38 | 38 | 200 | 189 |
| secular-sage | 49 | 24 | 25 | 126 | 127 |
| sunni-islam | 140 | 70 | 70 | 320 | 321 |
| taoism | 48 | 24 | 24 | 129 | 135 |
| **TOTAL** | **519** | **259** | **260** | **1,362** | **1,370** |

- **train-half SFT set = 1,362 examples** (matches the issue's "~1,370 expected"; the 2,732 SFT
  set splits 1,362 / 1,370 by scenario — near-perfectly balanced, a property of the stratified split).
- **Every tradition has a real held-out arm (24–70 scenarios)** — the fix for #53's central
  limitation (its strict holdout was 13 scenarios across only 3 traditions, mostly sunni-islam).
- `train_sha256=6220e34658506731…`, `holdout_sha256=606cd9f160a3f23e…` (full in the manifest).

## COSTED PLAN — pre-training gate (hard ceiling $250 all-in; Waleed)

**Standing rule (inherited from #48's ceiling breach):** usage-**reconciled** actuals at every
spend gate — the numbers below are **planning estimates only**, never a ceiling decision.

**Cost anchors (from #48 REALIZED usage, exact):** gemini full-scope judgment ≈ **$0.0145–0.016**
each ($44.98 / 3,114 descriptive; $75 / 5,040 mining band). GPU: bf16 SFT+smoke ~$13 full-data
(B200 $6.25/hr, ~1h48m); DPO ~$7; eval-server + endpoint sampling ~$26.

**⚠️ Batch is UNAVAILABLE here.** The judging pipeline batches **only the Anthropic/Opus judge**
(~50%); **Gemini is not batchable** (Vertex has no developer file-batch — verified in
`workflows/judging/judging/batching.py`). Since the issue mandates the **gemini** judge for
comparability, every judging line below is **full price** — the main cost lever is *gone*, so the
ceiling is genuinely tight and the plan is structured to hold it.

### New-spend line items (base reused free)

| # | Step | Units | Gemini $ | GPU $ | Notes |
|---|---|---|---|---|---|
| 1 | Train-half SFT (`mb-sft-split50`) | 1,362 ex, ~342 steps | — | ~8 | ~half #48 SFT; +smoke |
| 2 | **Descriptive: split-SFT, both halves** | 3,114 judgments | **45–50** | ~10 | endpoint sample + gemini judge; **core transfer answer** |
| 3 | DPO full-grid mining (sample+band) | 1,554 cells ×K4 = 6,216 | **90–100** | ~10 | **dominant line**; Waleed: full grid, no subsetting |
| 4 | DPO train (`mb-dpo-split50`) | ~150 steps | — | ~7 | anchored on split-SFT |
| 5 | *(optional)* Descriptive: split-DPO, both halves | 3,114 judgments | **45–50** | ~5 | SFT-vs-DPO transfer decomposition |
| | **Core path (1–4)** | | **135–150** | **~35** | **≈ $170–185 all-in** |
| | **Full path (1–5)** | | **180–200** | **~40** | **≈ $220–245 all-in — rides the ceiling** |

### Recommendation
- **Run the core path (steps 1–4): ≈ $170–185 all-in**, ~$65 margin under $250. This fully
  executes Waleed's directed design (50/50 split, train-half SFT, **full-grid** mining, DPO) and
  **answers the experiment's question** — the split-SFT descriptive on both halves *is* the
  held-out transfer measurement, directly comparable to #48's SFT (per_scenario.csv) and #53's +0.22.
- **Step 5 (split-DPO descriptive) is the swing item.** It adds a clean SFT-vs-DPO transfer
  decomposition but pushes all-in to ~$220–245 — **at the ceiling** with soft GPU (the exact #48
  breach pattern). **Decide it at the post-mining gate**, only if reconciled actuals leave ≥ $50
  headroom; otherwise `mb-dpo-split50` ships **trained + mining-characterized, descriptive
  deferred**, and the held-out transfer claim rests on split-SFT (where #48 also located its
  descriptive comparison).

### Three usage-reconciled spend gates
- **G1 — post-SFT, pre-mining:** reconcile SFT GPU actuals; confirm split-SFT loss curve sane.
  The biggest line (mining band) is next.
- **G2 — post-mining-band, pre-DPO-train:** reconcile the ~$90–100 mining line (usage-computed,
  not rolling). **Ceiling decision on step 5 is made here.**
- **G3 — post-DPO, pre-any-2nd-descriptive:** reconcile; final go/no-go on the split-DPO
  descriptive add-on.

## Environment & Reproduction

- **Split** (done, zero spend): `python3 experiments/57_multiweights_split/split.py`
- **SFT/DPO/serve**: #48's Modal scripts on `main` (`experiments/48_multiweights_omissive_bias/modal/`),
  re-pointed to `split50` adapter names + the train-half `scenario_id` subset. `--detach`+`.spawn()`,
  full-state resumable checkpointing (inherited #48 discipline).
- **Descriptive**: `workflows/judging` `collect` + `judge` against the vLLM endpoint; gemini judge.
- **Analysis**: adapt `experiments/53_exposure_stratified_holdout/analyze.py` (join + bootstrap CIs).
- **Keys**: `OPENROUTER_API_KEY` via the taqwabench `.env` seam; **never** copied into repo/logs/PR.

## Code
- [`split.py`](split.py) — seeded stratified 50/50 split (DONE).
- *(pending gate)* train-half SFT-set subsetter, mining driver, descriptive collect, analysis.

## Results
*(pending spend authorization — nothing trained or judged yet)*

## Next Steps
1. **[GATE]** Send split + costed plan to architect → await Waleed's $250 authorization.
2. On authorization: build train-half SFT subset → `mb-sft-split50` → G1 → descriptive split-SFT
   → full-grid mining → G2 → `mb-dpo-split50` → G3 → (optional) descriptive split-DPO → analysis.
3. Write up: held-out vs train-half lift, per-tradition, vs #48/#53; §3.4-style paragraph.

## References
- Issue #57 (design). #48 `notes.md` + `codev/reviews/48-multiweights-omissive-bias.md`.
- #53 `experiments/53_exposure_stratified_holdout/notes.md` (the +0.22 transferable estimate + its limitation).
- Base reference: `experiments/53_exposure_stratified_holdout/data/output/per_scenario.csv`.
