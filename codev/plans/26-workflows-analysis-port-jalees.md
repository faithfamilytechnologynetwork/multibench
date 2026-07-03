# Plan: `workflows/analysis` — port JaleesBench report/figure/stats tooling

## Metadata
- **ID**: plan-2026-07-03-workflows-analysis-port-jalees
- **Status**: draft
- **Specification**: [codev/specs/26-workflows-analysis-port-jalees.md](../specs/26-workflows-analysis-port-jalees.md)
- **Created**: 2026-07-03

## Executive Summary

Build `workflows/analysis` as a standalone `uv` project (package `analysis`,
Typer CLI, `python -m analysis`), mirroring `workflows/judging`'s layout, that
turns N per-tradition judging run-dirs into a self-contained cross-tradition HTML
report + scenario-cluster bootstrap CIs + optional matplotlib figures — a faithful
port of JaleesBench's `html_report.py` / `make_figures.py` / `paper_stats.py` /
`score.py`, reframed so the comparison axis is the **tradition** (subjects nested).

The implementation is sequenced **data-in → stats → HTML → figures**, prefixed by a
walking-skeleton scaffold so the toolchain (uv build, CLI, porch test dispatcher)
is proven before any logic lands. This matches the architect-approved phasing
(spec IQ1) and keeps every phase small (≤5 files) and independently testable:

1. **Scaffold + CLI skeleton + dispatcher registry** — the walking skeleton.
2. **Loaders + validation + aggregation + parity self-check** — data-in; point
   estimates reproduce upstream `report.json` to ≤1e−9.
3. **Bootstrap statistics** — shared-draw cluster bootstrap; `analysis_stats.json`.
4. **HTML report** — inline-SVG self-contained report with CIs, injection-safe.
5. **matplotlib figures** — `--figures` PNG/PDF, LAST and deferrable.

The port ledger (spec §4.7) — shared bootstrap draws (F2), `TwoSlopeNorm` colormap
(F3), dual PDF+PNG (F5), v2 overlay (F6), cell reducer (F8) — governs each phase.
Deviations (drop ×0.5 rescale D1, no band names D2, scenario-cluster resampling D3,
tradition axis D4) are baked into the relevant phases.

## Success Metrics
- [ ] All specification MUST criteria met (M1–M11)
- [ ] SHOULD criteria met or explicitly deferred (S1–S4)
- [ ] Point estimates reproduce upstream `report.json` to ≤1e−9 (M3/T3)
- [ ] Bootstrap draw-sharing verified (paired-diff variance < independent) (T4)
- [ ] Output is injection-safe and self-contained (M9/T6/T6b)
- [ ] `.codev/checks/test.sh` runs the analysis suite for a builder that touches it (M8/T9)
- [ ] All tests pass via `uv --project workflows/analysis run pytest workflows/analysis`
- [ ] Documentation: `workflows/analysis/README.md` complete

## Phases (Machine Readable)

<!-- REQUIRED: porch uses this JSON to track phase progress. Update this when adding/removing phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Scaffold, CLI skeleton & test dispatcher"},
    {"id": "phase_2", "title": "Loaders, validation, aggregation & parity self-check"},
    {"id": "phase_3", "title": "Scenario-cluster bootstrap statistics"},
    {"id": "phase_4", "title": "Self-contained HTML report"},
    {"id": "phase_5", "title": "Optional matplotlib figures"}
  ]
}
```

## Phase Breakdown

### Phase 1: Scaffold, CLI skeleton & test dispatcher
**Dependencies**: None

#### Objectives
- Stand up `workflows/analysis` as a buildable standalone `uv` project with a
  working Typer CLI skeleton and wire it into porch's test dispatcher — the
  walking skeleton that proves toolchain end-to-end before any logic.

#### Deliverables
- [ ] `workflows/analysis/pyproject.toml` — package `analysis`, hatchling, deps
      `typer>=0.12`, `numpy>=1.26`, `tradition_validator` (path source);
      `[project.optional-dependencies] figures = ["matplotlib>=3.8"]`;
      `[dependency-groups] dev = ["pytest>=8", "matplotlib>=3.8"]`;
      `[project.scripts] analysis = "analysis.cli:app"`; `[tool.pytest.ini_options]
      testpaths = ["tests"]`.
- [ ] `workflows/analysis/analysis/__init__.py`, `__main__.py`
      (`from analysis.cli import app`), `cli.py`
      (`app = typer.Typer(name="analysis", no_args_is_help=True, add_completion=False)`
      with a `report` command signature per spec §4.6 whose body raises a clear
      "not implemented in this phase" until Phase 4 wires it — or a minimal stub
      that validates args), `core_imports.py` (re-export `FRAMINGS`, `PRESSURES`
      from `tradition_validator.core`, mirroring judging).
- [ ] `.codev/checks/test.sh` — add one registry line:
      `workflows/analysis) echo "uv --project workflows/analysis run pytest workflows/analysis" ;;`
- [ ] `workflows/analysis/README.md` — invocation + module map (initial).
- [ ] `workflows/analysis/tests/conftest.py` (repo-root via `parents[3]`),
      `tests/test_cli_smoke.py`.

#### Implementation Details
- Mirror `workflows/judging` structure exactly (verified conventions: hatchling
  wheel `packages = ["analysis"]`; `[tool.uv.sources] tradition_validator =
  { path = "../../apps/tradition_validator", editable = true }`).
- `numpy` is a hard dep (bootstrap core). `matplotlib` is declared as an optional
  extra AND in the dev group so CI can exercise `--figures` (Phase 5) while base
  installs stay light; all matplotlib imports are **deferred inside the `--figures`
  branch** so `--help`/HTML never import it.
- `cli.py` commands defer heavy imports inside the function body (judging idiom).

#### Acceptance Criteria
- [ ] `uv --project workflows/analysis run python -m analysis --help` exits 0.
- [ ] `uv --project workflows/analysis run python -m analysis report --help` exits
      0 and lists `--out/--figures/--n-boot/--seed/--fig-format`.
- [ ] `uv --project workflows/analysis run pytest workflows/analysis` collects &
      passes the smoke test.
- [ ] Running `.codev/checks/test.sh` with `workflows/analysis` in the diff
      dispatches to the analysis pytest command.

#### Test Plan
- **Unit**: `test_cli_smoke.py` — `--help` and `report --help` exit 0; importing
  `analysis.cli` does not import `matplotlib` (assert `"matplotlib" not in
  sys.modules` after import). (T8)
- **Integration**: dispatcher line resolves (T9) — verify via a small assertion or
  documented manual check that `test_cmd_for workflows/analysis` is non-empty.
- **Manual**: `uv --project workflows/analysis run python -m analysis --help`.

#### Rollback Strategy
Revert the phase commit; `workflows/analysis/` is additive and the single
dispatcher line is isolated — no other project is affected.

#### Risks
- **Risk**: `tradition_validator` path source misconfigured → uv resolve fails.
  - **Mitigation**: copy judging's `[tool.uv.sources]` block verbatim (path depth
    `../../apps/tradition_validator`); `core_imports` import is exercised by the
    smoke test.

---

### Phase 2: Loaders, validation, aggregation & parity self-check
**Dependencies**: Phase 1

#### Objectives
- Read N run-dirs (fail-fast validation + v2 overlay), reduce to cells, and compute
  the cross-tradition aggregates — proving correctness by reproducing each
  `report.json`'s point estimates to ≤1e−9.

#### Deliverables
- [ ] `analysis/loaders.py` — load `report.json` + `judgments.jsonl` +
      `judgments_v2.jsonl` (overlay by `(sitting_key,judge,scope)`) +
      `skipped.jsonl`; apply the §4.1 validation table (fail-fast on missing
      artifact/key, off-grid score, duplicate tradition id, cross-metadata
      mismatch, duplicate base identity; tolerate dup-v2-last-wins, empty/absent
      v2+skipped, extra files).
- [ ] `analysis/aggregate.py` — cell reducer (mean over present judges per
      `(subject,scenario_id,pressure,framing,scope)`) and cross-tradition
      aggregates: headline, by_framing, steadfastness (+by_pressure), technique
      rates, agreement (from `report.json`), score_distribution, by_scenario.
- [ ] `workflows/analysis/tests/fixtures/` — ≥2 committed miniature run-dirs
      (real-shaped `report.json`+`judgments.jsonl`+`judgments_v2.jsonl`+
      `skipped.jsonl`, ~2 scenarios × both subjects × a couple framings/pressures;
      `report.json` produced by the real judging aggregator then trimmed) + a few
      malformed fixtures for fail-fast tests.
- [ ] `tests/test_loaders.py`, `tests/test_aggregate.py`.

#### Implementation Details
- Parse the **top-level `score` float** (never the `raw` string); validate ∈
  {−1,−0.5,0,0.5,1}.
- Cell reducer averages **present** judges only (D5) — do not count uncovered
  cells as 0; self-skips (from `skipped.jsonl`) are expected absences.
- Aggregates use the unweighted mean of in-scope cell values (F8). Steadfastness =
  `mean(unstated,full) − mean(unstated,turn1)`.
- `agreement`/`scenario_agreement`/`techniques`/`score_distribution` can be read
  straight from `report.json` for display; the **recomputed** headline/by_framing/
  steadfastness are what the ≤1e−9 self-check compares against `report.json`.

#### Acceptance Criteria
- [ ] Over each fixture run-dir, recomputed headline/by_framing/steadfastness/
      steadfastness_by_pressure match its `report.json` to ≤1e−9 (M3/T3).
- [ ] Every §4.1 fail-fast condition raises a clear, file-naming error; tolerated
      conditions (dup-v2, empty/absent v2+skipped, extra files, self-skips) do not
      (M5/M7/T1).
- [ ] A v2 override yields the v2 score with vote count unchanged (T2).

#### Test Plan
- **Unit**: T1 (each validation branch), T2 (v2 overlay).
- **Integration**: T3 (parity over committed fixtures; optional local smoke over
  the five real `20260702` run-dirs when present).
- **Manual**: run loaders over `tmp/judging-runs/20260702/*` locally, eyeball
  recomputed vs `report.json`.

#### Rollback Strategy
Revert the phase commit; Phase 1 skeleton remains functional.

#### Risks
- **Risk**: fixture `report.json` not internally consistent with its judgments →
  false parity failures.
  - **Mitigation**: generate the fixture via the real judging aggregator over a
    tiny judged set, then trim; document provenance in a fixture README.
- **Risk**: asymmetric-panel mis-weighting.
  - **Mitigation**: a fixture with an opus (1-judge) and sonnet (2-judge) cell;
    assert the cell mean averages present judges only.

---

### Phase 3: Scenario-cluster bootstrap statistics
**Dependencies**: Phase 2

#### Objectives
- Port `paper_stats.py`'s bootstrap to the scenario cluster: per-tradition 95% CIs
  on headline, recognition/instruction gaps, and steadfastness, with **shared draws**
  so paired differences use identical resamples — plus an `analysis_stats.json`
  side-output.

#### Deliverables
- [ ] `analysis/stats.py` — per-tradition `RESAMPLES` (one shared list of resample
      index arrays generated once, `rng = np.random.default_rng(seed)`, `N_BOOT`
      default 5000, `SEED` default 12345); `point_and_ci(cells)` and
      `diff_ci(cells_a, cells_b)` returning `[point, lo, hi]` via
      `np.percentile(boots, [2.5, 97.5])`; cluster resampling over the tradition's
      `scenario_id` set.
- [ ] Wire the stats into the aggregate result object; emit `analysis_stats.json`
      (the `paper_stats.json` analogue) — the point+CI values (S3).
- [ ] `tests/test_stats.py`.

#### Implementation Details
- **Resampling unit = scenario cluster** (D3): one draw = resample the tradition's
  scenario_ids with replacement; a resampled quantity gathers all cells of the
  chosen scenarios and applies the cell reducer / aggregate (F8) — internal
  representation is per-scenario cell values, not JaleesBench's (sum,count) arrays
  (D5), but the point/CI math and paired reuse match `paper_stats.py`.
- **Shared draws (F2)**: build one `RESAMPLES` list per tradition and reuse it for
  every `point_and_ci`/`diff_ci` of that tradition so gaps (stated−unstated,
  guided−stated) and steadfastness (full−turn1) are paired per draw.
- **CIs are per-(tradition, subject)** only; no pooled/cross-tradition CI (IQ3
  resolved, spec §4.3).
- Determinism: same inputs + `--seed` → identical stats.

#### Acceptance Criteria
- [ ] `diff_ci(a,b)` point == `point_and_ci(a)[0] − point_and_ci(b)[0]` (paired).
- [ ] Paired (shared-`RESAMPLES`) diff variance < independent-draw diff variance on
      a fixture (F2 verified) (T4).
- [ ] 95% CI = `[2.5, 97.5]` percentile of the 5000-value bootstrap; reproducible
      under a fixed seed (T4).
- [ ] `analysis_stats.json` written with per-tradition-per-subject point+CI values.

#### Test Plan
- **Unit**: T4 (paired-point identity; paired vs independent variance; percentile
  bounds; seed reproducibility).
- **Integration**: run stats over a fixture; assert CI ordering `lo ≤ point ≤ hi`
  and that n=5 CIs are wide (sanity, not brittle threshold).

#### Rollback Strategy
Revert the phase commit; Phases 1–2 remain functional (aggregates without CIs).

#### Risks
- **Risk**: draw-sharing accidentally lost (fresh draws per estimate) → wrong diff
  CIs. **Mitigation**: T4's paired-identity + variance test is the explicit guard.
- **Risk**: RNG-order sensitivity across estimates. **Mitigation**: pre-generate
  `RESAMPLES` once per tradition before any estimate (mirror `paper_stats.py`).

---

### Phase 4: Self-contained HTML report
**Dependencies**: Phase 3

#### Objectives
- Render the self-contained, injection-safe HTML report (inline CSS + inline SVG)
  that regenerates the pilot's figures **from data**, adds CI whiskers, and wires
  the `report` CLI command to the fixed output contract.

#### Deliverables
- [ ] `analysis/colors.py` — `score_color(v)` (matplotlib-free interpolation over
      the 7 diverging stops with `TwoSlopeNorm(-1,0,1)` semantics) and
      `score_axis` reference-line positions (±0.5, 0); numeric scale, **no band
      names** (D1/D2).
- [ ] `analysis/html_report.py` — assemble a single self-contained HTML doc
      (inline `<style>` with light/dark `@media`); sections reframed to the
      tradition axis: cross-tradition scorecard (CI whiskers), framing-staircase
      small-multiples (+ recognition/instruction gap table w/ CIs), steadfastness
      heatmap (tradition×subject rows × 6 pressures + pooled), score-distribution
      stacked bars, technique profile (meter bars), judge agreement, scenario
      spotlights (table from `by_scenario`; transcripts optional), cost, caveats
      (n=5, judge asymmetry, scenario-mix). Each figure has a `<details>` table
      twin. **All artifact text HTML-escaped; never into `<script>`** (M9).
- [ ] Wire `cli.report` → write `<out>/report.html` + `<out>/analysis_stats.json`
      (fixed output contract §4.6; idempotent overwrite; `--out` default
      `./analysis-out`).
- [ ] `tests/test_html_report.py`, `tests/test_colors.py`.

#### Implementation Details
- Chart marks are hand-built inline SVG via string assembly (pilot house style);
  numeric chart data may enter an inline `<script>` only as JSON of
  numeric/whitelisted values with `<`/`&`/`</script` neutralized — free text goes
  only into escaped HTML text nodes.
- `score_color` endpoints: −1 → deep red, 0 → grey-beige, +1 → deep green (same 7
  stops as `make_figures.py`'s `BAND_CMAP`), so Phase 5 matplotlib matches.
- Caveats ported from `crosstrad-report.html` §10.

#### Acceptance Criteria
- [ ] `analysis report <fixture-dirs> --out DIR` writes a self-contained
      `report.html` (no external `src=/href=` asset loads; opens offline) (M1/M2/
      M10/T6).
- [ ] An injection payload (`</script>`, `<img onerror>`, `&<>`) in a fixture's
      `rationale`/scenario id renders as escaped literal text, never live markup
      (M9/T6b).
- [ ] No band-name string appears in output; `score_color(-1|0|1)` returns the
      expected red/grey/green endpoints (M6/T5).
- [ ] Report shows CI whiskers on the scorecard and CI columns on the gap table.

#### Test Plan
- **Unit**: T5 (numeric-only + color endpoints), T6 (self-contained asset check),
  T6b (injection escaping).
- **Integration**: render over committed fixtures; assert required sections present
  and CI values wired from Phase 3.
- **Manual**: open the generated `report.html` in a browser; compare figures to
  `tmp/judging-runs/20260702/crosstrad-report.html` when available.

#### Rollback Strategy
Revert the phase commit; Phases 1–3 deliver loaders/aggregates/stats + JSON.

#### Risks
- **Risk**: injection escaping missed on one field. **Mitigation**: a single
  `esc()` chokepoint for all text nodes + T6b payload test.
- **Risk**: SVG scorecard drifts from pilot conventions. **Mitigation**: port axis
  range/label and mark styles from the pilot; table-twin cross-checks numbers.

---

### Phase 5: Optional matplotlib figures
**Dependencies**: Phase 4

#### Objectives
- Port `make_figures.py`'s publication figures behind `--figures` (off by default),
  reusing the Phase 2–3 computed quantities and Phase 4 color stops. Deferrable:
  if dropped, Phases 1–4 still deliver the full HTML report.

#### Deliverables
- [ ] `analysis/figures.py` — matplotlib `band_color`/`band_axis` (built from the
      same 7 stops + `TwoSlopeNorm`), `saveboth(fig, name)` writing both `.pdf` and
      `.png` (`dpi=150`), serif house style; figures: scorecard (dot plot + CI
      bars), framing staircase small-multiples, steadfastness heatmap
      (`TwoSlopeNorm(-vmax,0,vmax)`, `vmax=|M|.max()`), score-distribution bars.
- [ ] Wire `--figures` in `cli.report` → `<out>/figures/<name>.<ext>` per
      `--fig-format` (default `pdf,png`); **matplotlib imported lazily inside this
      branch only**.
- [ ] `tests/test_figures.py` (skip-if-matplotlib-absent).

#### Implementation Details
- Fidelity F3/F4/F5: `BAND_CMAP` 7 stops; heatmap norm auto-scaled to `|M|.max()`;
  dual PDF (vector) + PNG (dpi 150); serif fonts; `band_axis` ref lines at ±0.5/0.
- Numeric scale (D1): no `×0.5` rescale, no band-name labels; axis reads
  "Score (−1…+1; 0 = neutral)".
- Import isolation (D7/§7.3): the HTML-only path must never import matplotlib —
  guarded by the Phase 1 smoke assertion.

#### Acceptance Criteria
- [ ] `analysis report <dirs> --figures --out DIR` writes both `.pdf` and `.png`
      for each figure under `<out>/figures/` (S1/T7).
- [ ] With matplotlib absent, the figures test skips cleanly and the HTML path
      still works (T7).
- [ ] No band-name label in any figure; colormap endpoints match `score_color`.

#### Test Plan
- **Unit**: T7 (figures written; skip-if-absent).
- **Integration**: `--figures` over a fixture; assert file existence + non-empty.
- **Manual**: eyeball a rendered PNG against the pilot/paper conventions.

#### Rollback Strategy
Revert the phase commit; the `--figures` flag and `figures.py` are additive and
isolated — the default HTML path is untouched.

#### Risks
- **Risk**: matplotlib leaks into the default path (import at module top).
  - **Mitigation**: lazy import inside the `--figures` branch; Phase 1 smoke test
    asserts `matplotlib` not imported by `analysis.cli`.

---

## Dependency Map
```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5 (optional/deferrable)
(scaffold)  (data-in)   (stats)     (HTML)       (matplotlib figures)
```

## Resource Requirements
### Development Resources
- **Environment**: repo-root `uv`; Python ≥3.11; `tradition_validator` present at
  `apps/tradition_validator` (path dep). No network, no credentials (offline tool).
### Infrastructure
- None. No DB, no services, no config beyond the one `.codev/checks/test.sh` line.

## Integration Points
### Internal Systems
- **`workflows/judging` outputs** — read-only consumer of `report.json` +
  `*.jsonl` in each run-dir; **Phase 2**; no fallback needed (fail-fast on missing).
- **`tradition_validator.core`** — single-source `FRAMINGS`/`PRESSURES` ordering;
  **Phase 1** (path dep); fallback: none (hard dep, mirrors judging).
- **porch test dispatcher** (`.codev/checks/test.sh`) — one registry line;
  **Phase 1**.
### External Systems
- None (offline; no live model calls).

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Port estimates drift from `report.json` | M | H | ≤1e−9 parity self-check on committed fixtures (T3) |
| Draw-sharing lost → wrong diff CIs | M | H | Paired-identity + variance test (T4) |
| Injection via judge strings in HTML | M | M | Single `esc()` chokepoint + payload test (T6b) |
| matplotlib leaks into default path | L | M | Lazy import + Phase 1 `sys.modules` assertion |
| Fixture `report.json` inconsistent with its judgments | M | M | Generate via real judging aggregator, then trim; document provenance |
| n=5 CIs look "broken" | H | L | Framed as intended; caveats state n=5 explicitly |

### Schedule Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Phase 5 (figures) scope creep | M | L | Explicitly deferrable/last; Phases 1–4 ship the full HTML report without it |

## Validation Checkpoints
1. **After Phase 1**: CLI `--help` works; dispatcher runs the suite; no matplotlib import.
2. **After Phase 2**: parity ≤1e−9 on fixtures; all fail-fast branches covered.
3. **After Phase 3**: paired-draw CI properties hold; `analysis_stats.json` emitted.
4. **After Phase 4**: self-contained, injection-safe HTML with CIs; numeric-only.
5. **Before PR**: full suite green via the dispatcher; README complete; optional
   local smoke over the real `20260702` run-dirs.

## Documentation Updates Required
- [ ] `workflows/analysis/README.md` (invocation, module map, output contract, fixtures)
- [ ] Root `workflows/README.md` — add an `analysis` line (if it enumerates workflows)
- [ ] Arch/lessons docs: routed in the Review phase via the `update-arch-docs` skill
      (candidate lesson: matplotlib introduced but import-isolated; scenario-cluster
      bootstrap draw-sharing) — not a plan deliverable, noted for Review.

## Post-Implementation Tasks
- [ ] Optional local smoke: regenerate the pilot's figures from the five real
      `20260702` run-dirs and eyeball against `crosstrad-report.html`.
- [ ] Review phase: lessons learned + PR.

## Expert Review
**Date**: (pending — porch runs 2-way plan consultation next)
**Model(s)**: codex, claude (per `porch.consultation.models`)
**Key Feedback**: _to be recorded here after consultation._
**Plan Adjustments**: _to be recorded here._

## Approval
- [ ] Expert AI Consultation Complete (codex + claude)
- [ ] Human plan-approval gate

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-07-03 | Initial implementation plan | Spec 26 approved; architect phasing | spir-26 |

## Notes
- **PR strategy** (spec §3.4.8): all five phases ship as git commits within a
  **single** PR, opened during/after Phase 5 (or after Phase 4 if the architect
  elects to defer figures), unless the architect requests an earlier/mid PR.
- **Phase commits** use `[Spec 26][Phase: <name>] type: description`.
- **Deferrability**: Phase 5 is the only optional phase; the plan is valuable and
  shippable at the end of Phase 4 (full HTML report + CIs) if figures are deferred.
