# experiment-53 — exposure-stratified pseudo-holdout (MultiWeights memorization check)

Soft-mode EXPERIMENT builder. Driving issue #53. Analysis-only, **zero API/GPU spend**
(#48 freeze applies). Follow-up to Experiment 48 (MultiWeights / omissive bias).

## 2026-08-06 — orientation & data mapping

- Read issue #53 (it IS the design) + architect brief + exp48 spec/notes.
- Architect brief: read-only symlinks in `tmp/` (`exp48-data`, `judging-runs`); do NOT
  modify anything under them; pure pandas/matplotlib; pre-register interpretation rule
  BEFORE computing; loop architect at analyze step with dose-response numbers before
  writing conclusions; deliverables = writeup + one MB-paper figure + §3.4 paragraph.
- **Data mapped from real files** (not docs): headline metric = `unstated`/`full` band
  score ∈ {−1,−0.5,0,0.5,1}. BASE = `output/collection/*/judgments.jsonl` (gemma,
  unstated+full, 3114). SFT = `output/descriptive/*/judgments.jsonl` (unstated+full,
  3114). Both join cell-for-cell (3114 common, 0 unmatched). Exposure source =
  `output/sft/sft_train_guided.jsonl` (2732 examples, has scenario_id+pressure).
- **Sanity check reproduced #48 headline**: base −0.230 → sft +0.599, overall lift
  **+0.829**, all 7 traditions positive. Good — data is the right data.
- **Exposure distribution**: 2732 exposed cells vs **382 unexposed**; zero-exposure =
  **13 scenarios / 78 cells**. Concentration at exp=6 (353 scenarios). ⇒ cell-level
  unexposed arm (382) is the stronger holdout; 13-scenario arm is the strict fallback.

## Design decisions

- Pre-registered interpretation rule written into notes.md BEFORE computing dose-response.
- Confound: low-exposure cells failed the guided band filter ⇒ adversarially hard ⇒ base
  score correlates with exposure. Control = stratify on BASE unstated-full score, compare
  exposed vs unexposed within stratum, standardize. Report raw AND matched.
- Threshold τ = 0.15 (⅓ band step, ~18% of +0.83). |Δ_matched|<τ & flat ⇒ generalization
  (memorization not driving); Δ_matched≥τ or monotone rise ⇒ confound confirmed.
- Toolchain: `uv run --with pandas --with numpy --with matplotlib` (ephemeral, nothing
  added to project, no raw pip — per Waleed prefs).

## 2026-08-06 — analyze step: numbers in (pre-conclusion check-in gate)

Ran `analyze.py` (uv ephemeral env). Join exact (3114 cells, 0 unmatched); #48 headline
reproduced (base −0.230 → sft +0.599, +0.829). **Finding is the OPPOSITE of the placeholder
"flat" hope — lift is strongly exposure-dependent:**

- Scenario dose-response (raw lift): exp0 **+0.218** [.11,.35] → exp1 +0.38 → exp2 +0.56 →
  exp3 +0.68 → exp4 +0.97 → exp5 +0.87 → exp6 **+0.861**. Monotone rise. Base score also
  rises with exposure (exp0 base −0.872 → exp6 −0.073) — confound is real & large.
- Cell-level raw: exposed (n2732) +0.877 vs unexposed (n382) +0.486; raw Δ +0.392.
- **Base-score-matched** (standardize exposed→unexposed dist, all 5 strata included, 100%
  unexposed mass): matched exposed **+1.492** vs unexposed +0.486, **Δ_matched = +1.006,
  95% CI [+0.916, +1.096]** — ≫ τ=0.15. Within EVERY base stratum exposed lifts more
  (diffs +1.09/+0.84/+0.44/+0.12/+0.30). Matching does NOT flatten it.
- Strict 13-scenario zero-exposure holdout: **+0.218 [+0.109, +0.346]** — small but
  CI-excludes-0 ⇒ some genuine generalization survives.

**Pre-registered verdict: "concentrated in exposure ⇒ confound/memorization confirmed."**
Nuance: not PURE memorization — held-out lift is +0.22 (real), but the +0.83 headline
overstates the *transferable* effect ~4×. Fixed the figure title ("flat"→"rises"); the
matched line tracks raw (matching doesn't remove it).

Caveat to flag: matched contrast conflates memorization with samplability-driven
trainability (unexposed = cells that failed the guided band filter = the #48 §3
samplability boundary). Both imply the lift is exposure-concentrated, not a uniform
disposition — same bottom line for §3.4.

**GATE: messaged architect with these numbers; HOLDING conclusions + §3.4 paragraph
until they respond (per brief item 5).**

## 2026-08-06 — architect approved; conclusions written; experiment COMPLETE

Architect (09:51Z): write conclusions on this read; lead §3.4 with the DECOMPOSITION
(transferable +0.22 vs exposure-concentrated matched Δ +1.01, aggregate overstates ~4×);
state PLAINLY that zero-exposure scenarios improve but do NOT flip positive
(base −0.87 → **−0.65**, 92% stay <0 — corrects the "all 7 flip" aggregate reading);
include samplability-conflation caveat verbatim; close by locating load-bearing claims on
the OOD instruments (AFB cold + probes) which this analysis doesn't touch.

Wrote all of that into `notes.md` (Results, Key Findings, Metrics table, §3.4 paragraph,
What Worked/Didn't, Next Steps). Verified exact numbers: zero-exposure SFT −0.654, 8% flip,
3 traditions only (sunni-islam 9 / secular-sage 3 / judaism 1) — noted the tradition-skew
limitation. Figure title corrected (rises, not flat); matched line annotated "does not
flatten." Status → Complete.

Deliverables (all committed): `experiments/53_exposure_stratified_holdout/`
{notes.md, analyze.py, data/output/{fig_dose_response.png, dose_response.csv,
per_scenario.csv, summary.json}} + this thread. Zero API/GPU spend; `tmp/` symlinks
gitignored (never staged). Architect is revising paper 3.4/abstract/discussion from the
§3.4 paragraph.

## 2026-08-06 — architect requested PR; opened #56

Architect (09:53Z): open a small additive PR so §3.4's citation resolves (readers find
analyze.py + the pre-registered rule), plus two asks: (1) vector PDF alongside PNG, (2)
holdout-composition limitation prominent (13 scen / 3 traditions, mostly sunni-islam).
Both done: added `fig_dose_response.pdf` (vector, PDF 1.4), promoted the limitation to a
⚠️ callout under Results Summary + a qualifier in the §3.4 paragraph. Committed e04b04f,
pushed, opened **PR #56** (Closes #53). Additive-only (experiments/53_.../ + this thread);
touches no app suite so the per-builder test dispatcher has nothing to run. Awaiting the
quick low-risk review.
