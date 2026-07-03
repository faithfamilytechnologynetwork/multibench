# spir-26 — workflows/analysis: port JaleesBench report/figure/stats tooling

Builder: spir-26 (strict mode, SPIR). Issue #26.

## Goal
Create `workflows/analysis` — a uv project that turns MultiBench judging-run
output (`report.json` / `judgments.jsonl` / `judgments_v2.jsonl` / `sittings.jsonl`,
one `--results-dir` per tradition) into cross-tradition analysis artifacts:
a self-contained HTML report (inline SVG) + optional matplotlib PNG/PDF figures +
scenario-cluster bootstrap 95% CIs. Port of JaleesBench's html_report.py /
make_figures.py / paper_stats.py / score.py, reframed to compare **traditions**.

## Phase log

### Specify — started 2026-07-02
- Confirmed no prior spec on disk; porch says phase=specify, iter 1.
- Ran three parallel deep-dives (all faithful, quoted source):
  1. **Input schema** (real artifacts in `tmp/judging-runs/20260702/`, main checkout):
     5 traditions × 5 scenarios × 2 subjects (opus-4-8, sonnet-4-6) × 3 framings ×
     6 pressures × 2 scopes. `report.json` already has scorecard/steadfastness/
     by_framing/score_distribution/agreement/techniques/by_scenario/cost. Raw
     `judgments.jsonl` (+v2 overlay by `sitting_key|judge|scope`) needed for CIs.
     Scores are floats in {-1,-0.5,0,0.5,1} — **already on -1..+1, no band names**.
     Cluster unit = `scenario_id` (5/tradition, tradition-specific prefixes).
     Judge panel asymmetric (self-skip → opus-subject judged by gemini only).
  2. **Port sources**: band_color = `BAND_CMAP(NORM(score))`, NORM =
     `TwoSlopeNorm(-1,0,1)`; band_axis draws ref lines at ±0.5 / 0. paper_stats:
     N_BOOT=5000, SEED=12345, **one shared `RESAMPLES` list reused by point_and_ci
     AND diff_ci** (paired draws — the load-bearing fidelity detail). JaleesBench
     unit = 140 probes; here it's 5 scenarios/tradition. JaleesBench ×0.5 rescale
     (bands -2..+2) — **DROP it here, scores already -1..+1** (adaptation #3).
  3. **Reference output + conventions**: `crosstrad-report.html` is hand-built
     inline SVG (no matplotlib, no CDN). §10 caveats explicitly flag "no CIs, n=5".
     uv projects are standalone (no workspace); mirror `workflows/judging` layout
     (cli.py `app`, `__main__.py` shim, `[project.scripts]`, hatchling, pytest).
     **matplotlib is NOT yet a repo dep** — analysis introduces it (isolated).
     `.codev/checks/test.sh` needs +1 registry line for `workflows/analysis`.

- Key fidelity decisions to record in the port ledger:
  - SCORE_SCALE 0.5 → 1.0 (no rescale); band names dropped (numeric-only per #17/#18).
  - Resampling unit = scenario cluster (5/tradition); per-tradition bootstrap.
  - Keep draw-sharing (one RESAMPLES, reused for point + diff CIs).
  - Comparison axis = tradition (subjects within), not 8-subject field.
  - Cell reducer = unweighted mean of present judges (matches report.json),
    a deviation from JaleesBench's raw-judgment count-pooling — document it.
  - HTML = inline SVG (primary, matches pilot); matplotlib PNG/PDF = optional `--figures`.

- Treating the issue's "Adaptations / Port sources / Port-fidelity mandate / CLI /
  Registry / PR strategy" as fixed architect decisions (no literal "Baked Decisions"
  heading, but same force) — captured in Constraints, not relitigated.

Next: draft `codev/specs/26-workflows-analysis-port-jalees.md`, commit, `porch done 26`.
