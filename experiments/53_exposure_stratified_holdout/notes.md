# Experiment 53: Exposure-stratified pseudo-holdout analysis of MultiWeights SFT (memorization check)

**Status**: Complete

**Date**: 2026-08-06

**Driving issue**: #53 (the issue body IS the design). Follow-up to Experiment 48
(MultiWeights / omissive bias). Analysis-only, **ZERO API/GPU spend** (the #48
spend freeze applies).

## Goal

**Question**: Does the MultiWeights SFT descriptive lift (base gemma-4-31b → SFT,
*unstated* framing, all 7 traditions positive, overall **+0.83** on the signed
[-1, +1] band) survive controlling for **training exposure** — i.e. is it
*generalization of a disposition* or *memorization of trained prompts*?

Experiment 48 §4.3 deferred exactly this check: it trained on all 519 scenarios
(no MultiBench holdout), so "before/after on trained scenarios is
memorization-confounded" and #48 could only report MultiBench numbers as
descriptive. It named the fix — "train a separate model on a scenario subset" —
as a later decision. This experiment substitutes a **pseudo-holdout that needs no
retrain**: the SFT set was a per-cell judge filter over guided cells, so scenarios
(and individual pressure-cells) vary in how much of them entered training, and a
cell/scenario with **zero training exposure is a true prompt-level holdout** whose
unstated descriptive score is an out-of-training measurement.

**What this experiment does NOT claim**: cross-tradition generalization (that needs
the single-fold retrain, a separate decision). It bounds only whether the
*observed descriptive lift* is inflated by having trained on the evaluated prompts.

## Data (read-only symlinks in `tmp/`; nothing under them is modified)

Verified layout (cell = one (scenario_id, pressure); grid = 519 scenarios × 6
pressures = 3,114 cells):

| Role | Path | framing / scope | n |
|---|---|---|---|
| **BASE** gemma unstated descriptive | `tmp/exp48-data/output/collection/*/judgments.jsonl` | `unstated` / `full` | 3,114 |
| **SFT** model unstated descriptive | `tmp/exp48-data/output/descriptive/*/judgments.jsonl` | `unstated` / `full` | 3,114 |
| SFT **training set** (exposure source) | `tmp/exp48-data/output/sft/sft_train_guided.jsonl` | guided cells, re-rendered bare | 2,732 |

- Both descriptive sets join **cell-for-cell** (3,114 common, 0 unmatched).
- Score is the signed selection band ∈ {−1.0, −0.5, 0.0, +0.5, +1.0}.
- Headline metric = `framing=unstated, scope=full` (post-pressure, bare) — the same
  metric as #48's "−0.335 → +0.188 post-pressure bare" recipe evidence.
- **Exposure** = per-scenario count of its pressure-cells present in the SFT jsonl
  (0..6). Cell-level exposure = whether that exact (scenario, pressure) guided cell
  is in the SFT jsonl.

Exposure distribution (verified): 2,732 exposed cells vs **382 unexposed cells**;
per-scenario counts — exp0: **13 scenarios (78 cells)**, exp1: 11, exp2: 12,
exp3: 19, exp4: 33, exp5: 78, exp6: 353. Exposure is heavily concentrated at 6, so
the cell-level unexposed arm (382 cells) is the statistically stronger holdout;
the 13 zero-exposure scenarios are the strict prompt-level holdout.

## PRE-REGISTERED interpretation rule (written BEFORE computing the dose-response)

Committed before any lift-vs-exposure number is read, per #48 honest-null
discipline. Reported plainly whichever way it lands.

**Estimands**
1. *Scenario-level dose-response* (issue primary): mean base→SFT unstated lift as a
   function of exposure 0..6, overall and within-tradition.
2. *Cell-level holdout contrast*: mean lift on **unexposed** cells (n≈382) vs
   **exposed** cells (n≈2,732).

**The confound and its control.** Zero-/low-exposure cells are not random — they
are the cells whose *guided* sitting failed the band-≥+1 selection filter, i.e.
adversarially hard for base. Base difficulty therefore correlates with exposure and
must be conditioned out. Control = **stratify on the base unstated `full` score**
(discrete band values {−1, −0.5, 0, 0.5, 1}); compare exposed vs unexposed lift
*within each base-score stratum*, then combine by standardization (reweighting the
exposed arm to the unexposed arm's base-score distribution). Report **both raw and
base-score-matched** contrasts. A matched contrast is trustworthy only where the two
arms overlap in base score; strata with <5 cells in either arm are reported but
flagged as thin and excluded from the pooled matched estimate.

**Matched-comparison decision threshold.** Let Δ_matched = (base-score-matched mean
lift on exposed cells) − (mean lift on unexposed cells). Threshold **τ = 0.15** on
the [−1, +1] band scale, chosen as ~⅓ of one band step (0.5) and ~18% of the overall
+0.83 lift — a materiality floor below which any exposure contribution is immaterial
to the §3.4 claim.

- **Flat in exposure ⇒ memorization is NOT driving the result.** If |Δ_matched| < τ
  **and** the scenario-level dose-response shows no monotone rise in matched lift with
  exposure, conclude the descriptive lift reflects a **generalized disposition** that
  transfers to unexposed prompts. The §3.4 upgrade may state the lift is not an
  artifact of training on the evaluated prompts.
- **Concentrated in exposure ⇒ confound/memorization confirmed.** If Δ_matched ≥ τ
  (exposed materially > unexposed after matching) and/or lift rises monotonically with
  exposure, conclude memorization contributes materially; report the confound plainly
  and the §3.4 paragraph must caveat the descriptive numbers accordingly.
- **Ambiguous/underpowered.** If the arms barely overlap in base score (matched
  estimate rests on thin strata) the result is reported as underpowered — no clean
  claim either direction — and the strict 13-scenario zero-exposure holdout is quoted
  as the fallback bound with its CI.

**Uncertainty.** All arm means and the Δ contrasts reported with 95% CIs
(scenario-clustered bootstrap for scenario-level; cell bootstrap for cell-level).
Claims rest on CI position relative to 0 and τ, not point estimates alone.

## Approach

1. Load the three sources; verify cell-for-cell join (done during setup).
2. Compute per-cell lift = sft(unstated,full) − base(unstated,full).
3. Scenario-level dose-response: group by exposure 0..6, overall + within tradition.
4. Cell-level exposed vs unexposed: raw, then base-score-stratified + standardized.
5. Bootstrap CIs. Produce one MultiBench-paper-style figure (matched lift vs exposure).
6. **Loop architect with the dose-response numbers BEFORE writing conclusions.**
7. Write conclusions + §3.4-ready paragraph per the rule above.

## Environment & Reproduction

Pure local analysis, zero network. Ephemeral deps via uv (nothing added to the
project, nothing pip-installed):

```bash
uv run --with pandas --with numpy --with matplotlib \
  python experiments/53_exposure_stratified_holdout/analyze.py
```

## Code

- [`analyze.py`](analyze.py) — join, dose-response, matched contrast, bootstrap, figure.

## Results

### Summary

The join is exact (3,114 cells, 0 unmatched) and reproduces #48's headline (base
−0.230 → SFT +0.599, pooled lift **+0.829**, all 7 traditions positive). Stratifying
that lift by training exposure **fires the pre-registered "concentrated in exposure ⇒
confound/memorization confirmed" branch**: the lift rises monotonically with exposure
and matching on base difficulty does not remove it (Δ_matched = **+1.006**, 95% CI
[+0.916, +1.096] ≫ τ=0.15). The lift decomposes into a small but real **transferable**
component (+0.218 on strictly zero-exposure scenarios, CI [+0.109, +0.346]) and a
dominant **exposure-concentrated** component; the aggregate +0.83 overstates the
transferable effect ≈4×. Crucially, zero-exposure scenarios **improve but do not flip
positive** (base −0.872 → SFT −0.654; 92% remain < 0) — the "all 7 traditions positive"
aggregate reading is memorization-driven, not a property of held-out prompts.

> **⚠️ Prominent limitation — the strict holdout is small and tradition-skewed.** The
> zero-exposure arm is only **13 scenarios across 3 traditions — sunni-islam 9,
> secular-sage 3, judaism 1** — i.e. the strict prompt-level holdout is *mostly
> sunni-islam*, and 4 of the 7 traditions (eastern-christianity, roman-catholicism,
> taoism, buddhism) have **no** zero-exposure scenario at all. The +0.218 transferable
> estimate therefore rests largely on one tradition and **cannot be read as an even,
> cross-tradition generalization result**. The cell-level matched contrast (n=382 unexposed
> cells, all traditions) is the statistically stronger and better-balanced arm; a clean
> per-tradition holdout would need the single-fold retrain deferred to future work.

### Key Findings

1. **Monotone dose-response (raw).** Scenario mean lift by exposure 0..6:
   +0.218 / +0.379 / +0.556 / +0.684 / +0.965 / +0.869 / +0.861. Exposure is confounded
   with base difficulty (base score by exposure: −0.872 → … → −0.073), so the raw
   dose-response cannot be read as a memorization curve on its own — hence the matched
   analysis.
2. **Matching on base difficulty does not flatten it.** Within every base-unstated-score
   stratum the exposed arm lifts more than the unexposed arm (per-stratum exposed−unexposed
   diffs: +1.086 / +0.844 / +0.442 / +0.124 / +0.303). Standardized to the unexposed
   (holdout) base-score distribution: matched exposed +1.492 vs unexposed +0.486 →
   **Δ_matched = +1.006, CI [+0.916, +1.096]**, an order of magnitude above τ.
3. **A genuine transferable component survives.** The strict 13-scenario zero-exposure
   holdout lifts **+0.218, CI [+0.109, +0.346]** — CI excludes 0. So the SFT does move a
   real disposition that generalizes to never-trained prompts; it is just ≈4× smaller than
   the aggregate and **does not reach positive territory** (SFT −0.654).
4. **Confound is intrinsic, not removable here.** Unexposed cells are exactly the cells
   whose *guided* sitting failed the band-≥+1 selection filter — i.e. the #48 §3
   samplability boundary. Memorization and latent trainability are therefore confounded
   *with each other*; both point the same interpretive direction (lift is
   exposure-concentrated, not a uniform disposition shift).

### Metrics

| Quantity | Value | 95% CI | Notes |
|---|---|---|---|
| Pooled base→SFT lift | +0.829 | — | reproduces #48; all 7 traditions + |
| Zero-exposure holdout lift (13 scen) | **+0.218** | [+0.109, +0.346] | transferable component; SFT still −0.654 |
| Cell-level raw Δ (exposed−unexposed) | +0.392 | — | exposed +0.877 (n=2732) vs unexposed +0.486 (n=382) |
| **Base-score-matched Δ** | **+1.006** | [+0.916, +1.096] | ≫ τ=0.15 ⇒ confound confirmed |
| Zero-exposure base → SFT | −0.872 → −0.654 | — | improves but does **not** flip positive (92% stay <0) |

**Limitation on the strict holdout's reach:** the 13 zero-exposure scenarios span only
3 traditions (sunni-islam 9, secular-sage 3, judaism 1); 4 traditions have no
zero-exposure scenario, so the strict prompt-level holdout cannot be resolved
within-tradition for them. The cell-level matched contrast (n=382 unexposed) is the
statistically stronger arm and covers all traditions.

### Output Files

- `data/output/fig_dose_response.png` — MB-paper-style figure (raw dose-response + matched line + Δ_matched box).
- `data/output/dose_response.csv` — per-exposure means + CIs.
- `data/output/per_scenario.csv` — per-scenario exposure, base, sft, lift.
- `data/output/summary.json` — machine-readable headline numbers.

## §3.4-ready paragraph (for the MultiWeights paper)

> **Exposure-stratified controls on the descriptive lift.** Because the SFT set was a
> per-cell judge filter over guided sittings, scenarios vary in how much of them entered
> training (0–6 of their 6 pressure-cells), and a scenario with zero training exposure is
> a true prompt-level holdout. Stratifying the +0.83 aggregate unstated lift by exposure
> decomposes it into a genuine transferable component — **+0.22 on strictly zero-exposure
> scenarios (95% CI [+0.11, +0.35])** — and a dominant exposure-concentrated component
> (base-difficulty-matched exposed-vs-held-out contrast Δ ≈ **+1.01**, CI [+0.92, +1.10]);
> the aggregate therefore **overstates the transferable effect roughly four-fold**, and
> matching on base difficulty does not remove the gap. (The strict zero-exposure arm is
> small and tradition-skewed — 13 scenarios, mostly sunni-islam — so +0.22 bounds rather
> than evenly estimates cross-tradition transfer; the 382-cell matched contrast is the
> better-balanced arm.) Stated plainly: zero-exposure
> scenarios *improve but do not flip positive* (mean base −0.87 → −0.65; 92% remain
> negative), so the "all seven traditions positive" aggregate is memorization-driven
> rather than a property of held-out prompts. This confound is intrinsic to the design:
> the held-out (unexposed) cells are precisely those whose guided sitting failed the
> selection filter — the samplability boundary of §3 — so memorization and latent
> trainability are confounded with each other and both point the same way. Accordingly,
> we report the MultiBench descriptive numbers as suggestive of a small, real dispositional
> transfer, not as the paper's evidence; **the load-bearing claims rest on the
> out-of-distribution instruments (AllFaith cold-start representation and the capability /
> over-application probes), which this analysis does not touch.**

## What Worked

- **Exposure as a free pseudo-holdout.** The per-cell filter design meant a retrain wasn't
  needed to bound memorization — the training set itself induces a 0..6 exposure gradient
  and a 382-cell unexposed arm. This substitutes for the #48 §4.3 "separate model on a
  scenario subset" at zero spend.
- **Cell-for-cell join** across base (collection) and SFT (descriptive) unstated/full
  judgments was exact — no imputation, no matching heuristics.
- **Pre-registration did its job**: the numbers landed on the confound-confirmed branch,
  and having τ and the decision rule fixed in advance made that an honest reading rather
  than a post-hoc one.

## What Didn't Work

- **The clean "flat = generalization" outcome did not materialize** — and the raw
  dose-response alone would have been *un*interpretable because base difficulty rides along
  with exposure. The matched analysis was essential, not optional.
- **The strict holdout is thin and tradition-skewed** (13 scenarios, 3 traditions), so the
  scenario-level arm alone couldn't carry the conclusion; the cell-level matched contrast
  had to.
- Memorization vs latent-trainability **cannot be separated** with saved data alone — a
  design limit, documented rather than papered over.

## Next Steps

1. **Immediate**: architect folds the §3.4 paragraph into the paper (3.4 / abstract /
   discussion), reframing the MultiBench descriptive lift as suggestive-only and anchoring
   claims on the OOD battery.
2. **Follow-up experiment (if an on-bench transfer claim is ever wanted)**: the single-fold
   retrain named in #48 §4.3 — train on a scenario subset, evaluate unstated on the strictly
   held-out complement across all 7 traditions — to separate memorization from trainability
   and give an even, cross-tradition holdout. Out of scope here (needs GPU spend; #48 freeze).
3. **Production path**: none from this experiment directly; it is a controls/validation
   result that hardens the paper's honesty, not a feature.

## References

- Issue #53 (design). Experiment 48 `notes.md` §3 (samplability), §4.3 (deferred holdout).
- Data: `tmp/exp48-data/output/{collection,descriptive,sft}` (read-only symlinks).
- Pre-registered rule: this file, "PRE-REGISTERED interpretation rule" section above.
