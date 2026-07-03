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

Drafted + committed spec (`[Spec 26] Initial specification draft`), ran `porch done 26`.

### Specify — iter 1 consult (Codex + Claude), 2026-07-02
- **Claude APPROVE**; **Codex REQUEST_CHANGES** (both HIGH). All feedback legit &
  applied in `[Spec 26] Specification with multi-agent review`:
  - Security: HTML/SVG-escape all artifact text, never into `<script>` (M9/T6b).
  - Validation table: dup tradition id / cross-metadata mismatch / dup base identity
    → error; dup v2 key last-wins; empty/absent v2+skipped valid; extra files ignored.
  - Fixed output contract: `--out DIR` → report.html + analysis_stats.json + figures/ (M10).
  - §4.8 committed miniature fixture run-dirs (tmp/ is gitignored, JaleesBench external);
    parity self-check runs on fixture, real 20260702 only a local smoke (M11).
  - Resolved IQ3: per-tradition CIs only, no pooled/field-mean CI in v1.
  - Clarified steadfastness formula; refined T6 to asset-loads.

### spec-approval — APPROVED by human (2026-07-03)
- Both IQ defaults accepted: matplotlib = final deferrable phase behind `--figures`;
  spotlights = table, transcripts optional. Architect suggested phasing = my IQ1.

### Plan — started 2026-07-03
- 5 phases (scaffold-first walking skeleton, then architect's 4):
  1. Scaffold + CLI skeleton + dispatcher registry line (walking skeleton).
  2. Loaders + validation + aggregation (cell reducer) + parity self-check (≤1e-9).
  3. Bootstrap stats (shared RESAMPLES, point_and_ci/diff_ci) + analysis_stats.json.
  4. HTML report (colors.py + html_report.py, inline SVG, escaping, CIs shown).
  5. matplotlib figures (figures.py, saveboth PDF+PNG) — LAST, deferrable.
- Deps: numpy hard; matplotlib optional-extra `figures` + in dev group (CI can test,
  lazy import keeps HTML path matplotlib-free). Single-source FRAMINGS/PRESSURES
  from tradition_validator.core (mirror judging/core_imports.py).

### Plan — iter 1 consult (Codex + Claude), 2026-07-03
- **Claude APPROVE** (full coverage table); **Codex REQUEST_CHANGES** (3, HIGH).
  Applied in `[Spec 26] Plan with multi-agent review`:
  - Phase 2 now recomputes+parity-checks `techniques` + `agreement` (M3 lists them),
    not read-through; clarified sittings.jsonl deferred to Phase 4.
  - Phase 3 = stats.py + `stats_to_dict` in-memory; file-write is Phase 4's cli.report.
  - Determinism/byte-stability explicit (stable ordering + rounding, two-run identical
    test); non-default `--fig-format` test added to Phase 5.

Applied plan rebuttal + revision, gate reached.

### plan-approval — APPROVED by human (2026-07-03)
- Implement 1→5, single PR (Closes #26), no self-approve/merge. Local smoke over
  tmp/judging-runs/20260702/* runs in architect's env if worktree lacks artifacts
  (they exist at main-checkout path; worktree tmp/ is gitignored).

### Implement Phase 1 (scaffold) — 2026-07-03
- Created workflows/analysis uv project mirroring judging: pyproject (typer, numpy,
  tradition_validator path; matplotlib as `figures` extra + dev group), __init__/
  __main__/cli.py (report subcommand, all flags, body deferred to Phase 4; added
  `@app.callback()` so `report` stays a NAMED subcommand — single-command Typer
  apps otherwise collapse it), core_imports (FRAMINGS/PRESSURES), README, .gitignore,
  uv.lock. Added dispatcher registry line for workflows/analysis (+1).
- Tests (test_cli_smoke): 5 pass — help lists report, report --help lists all flags,
  no-args exits non-zero, importing cli does NOT import matplotlib, core_imports OK.
- Verified: `python -m analysis --help`, `report --help`, pytest all green.

### Implement Phase 2 (loaders + aggregation + parity) — 2026-07-03
- Read judging/report.py + judge.py + scores.py as ground truth; reproduced the
  EXACT aggregation semantics (cell reducer = mean of present judges; _mean_over =
  unweighted mean of in-scope cells, None never 0; steadfastness = full−turn1;
  score_distribution over per-judge verdicts; agreement exact/within-one on ≥2-judge
  cells; scenario_agreement scoped to unstated/full; techniques rate; by_scenario).
- loaders.py: v2 overlay by _JKEY (subject,scenario,pressure,framing,judge,scope);
  fail-fast validation table (missing artifact/key, off-grid/string score, dup
  tradition id, cross-metadata mismatch, dup base identity); tolerate dup-v2-last-wins,
  empty/absent v2+skipped, extra files. SCORES/TECHNIQUE_IDS owned by analysis (input
  contract, not in tradition_validator).
- aggregate.py: TraditionAggregate + check_parity(≤1e-9) self-check.
- Fixtures: buddhism + taoism, 2 scenarios each, LEAN rows (dropped raw/rationale/
  direction/usage/ts → 77KB each), report.json regenerated via REAL judging
  build_report (genuine cross-check). buddhism BUD-001 has 8 v2 overrides (one flips
  gemini good_cause -0.5→0.0). fixtures/README documents provenance.
- Tests: 42 pass (13 loader/validation + parity/reducer). **SMOKE: 0 parity diffs
  over ALL 5 real 20260702 run-dirs (540 judgments each)** — aggregation is a perfect
  reproduction of judging's report.json.

Next: commit Phase 2, `porch done 26` → 2-way impl consult.
