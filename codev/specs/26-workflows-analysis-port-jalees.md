# Spec 26 — `workflows/analysis`: port JaleesBench report/figure/stats tooling for cross-tradition analysis

> **Status**: draft (Specify phase)
> **Protocol**: SPIR · strict · Issue #26
> **Ports**: JaleesBench `html_report.py`, `tmp/make_figures.py`, `tmp/paper_stats.py`, `score.py`
> **Consumes**: `workflows/judging` output (`report.json` / `judgments.jsonl` / `judgments_v2.jsonl` / `sittings.jsonl`), one `--results-dir` per tradition
> **Reference output**: `tmp/judging-runs/20260702/crosstrad-report.html` (architect-authored pilot, 2026-07-02)

---

## 1. Overview / Problem

### 1.1 The problem

`workflows/judging` (Spec 8) produces, per tradition, a machine-readable
`report.json` and a `report.md` — plus the raw `judgments.jsonl` / `sittings.jsonl`
that back them. Those artifacts are **per-tradition and single-run**: they carry
point estimates only, no confidence intervals, and nothing draws the five
traditions together into one comparable picture.

The one cross-tradition artifact that exists today —
`tmp/judging-runs/20260702/crosstrad-report.html` — was **hand-built by the
architect**: every number is a hard-coded JS literal, and its own §10 admits the
two things it cannot do honestly:

> *"Five scenarios per tradition. The paper's numbers rest on 140 scenarios with
> **bootstrap CIs**; these rest on 5, so treat every value as directional."*

So the corpus has (a) a proven analysis toolchain in a **different** codebase
(JaleesBench: `html_report.py`, `make_figures.py`, `paper_stats.py`, `score.py`)
and (b) a hand-built, un-reproducible cross-tradition report with no statistics.
This spec closes the gap by **porting** the JaleesBench toolchain into a new
`workflows/analysis` uv project, reframed so the comparison axis is the
**tradition** (with subjects nested inside), and adding the load-bearing piece the
pilot lacks: **scenario-cluster bootstrap confidence intervals**.

### 1.2 What this delivers

A `workflows/analysis` uv project with a Typer CLI, run from repo root:

```
uv --project workflows/analysis run python -m analysis report <run-dir>... [options]
```

where each `<run-dir>` is one tradition's judging `--results-dir`. It emits:

1. **A self-contained HTML report** (inline SVG, inline CSS, no external assets) —
   the automated, reproducible successor to `crosstrad-report.html`, regenerating
   its figures from the same run dirs **and adding bootstrap CIs**.
2. **Optional matplotlib PNG/PDF figures** (`--figures`) — publication-quality
   vector figures porting `make_figures.py`'s conventions (`band_color`,
   `band_axis`, `TwoSlopeNorm`, `saveboth`), on the numeric −1…+1 scale.
3. **Scenario-cluster bootstrap 95% CIs** — ported from `paper_stats.py`
   (`point_and_ci` / `diff_ci`, 5,000 resamples, shared draws), resampling unit =
   the scenario cluster.

### 1.3 Lineage & port-fidelity mandate

This is a **port, not a redesign** ([[port-dont-redesign-fidelity]], lesson from
Spec 8). The reference toolchain's non-functional behavior — the bootstrap's
paired draw-sharing, the diverging colormap and reference-line conventions, the
percentile-CI method, the dual PDF+PNG figure output — **carries over unless
explicitly reframed** in §4.7 (the port ledger). Every deviation is enumerated
there with a reason.

---

## 2. Stakeholders

- **The architect / researcher** — wants one reproducible command that turns N
  tradition run-dirs into a cross-tradition report with honest uncertainty, so the
  pilot's hand-built numbers stop being a maintenance liability.
- **`workflows/judging` (upstream)** — owns the input contract; `analysis` is a
  pure **read-only consumer** of its artifacts and must not require changes to it.
- **The paper** — consumes the optional matplotlib PNG/PDF figures directly.
- **Future traditions** — adding a sixth tradition means passing a sixth run-dir;
  no code change (mirrors the "adding a tradition adds a directory" core principle).
- **Sibling builders / MAINTAIN** — inherit one more uv project and one more line
  in the porch test dispatcher.

---

## 3. Current state, desired state, constraints

### 3.1 Current state

- `workflows/judging` emits per-tradition `report.json`, `report.md`,
  `sittings.jsonl`, `judgments.jsonl`, `judgments_v2.jsonl`, `skipped.jsonl`.
- Cross-tradition analysis exists only as the hand-built
  `tmp/judging-runs/20260702/crosstrad-report.html` (no CIs, numbers hard-coded).
- The proven analysis code lives in a **separate** repo
  (`/Users/mwk/Development/fftn/taqwabench/jaleesbench/`) — not importable, keyed
  to JaleesBench's data model (140 probes, `pillars`/`hearts`, −2…+2 bands).
- `workflows/analysis` does not exist. `matplotlib` is **not** a dependency
  anywhere in the repo. The porch test dispatcher (`.codev/checks/test.sh`) has no
  `workflows/analysis` registry line.

### 3.2 Desired state

- A `workflows/analysis` uv project (own `pyproject.toml`, package `analysis`,
  Typer CLI, `python -m analysis`) mirroring `workflows/judging`'s layout.
- `analysis report <run-dir>...` reads the per-tradition artifacts, aggregates
  cross-tradition, and writes a self-contained HTML report + optional figures +
  bootstrap CIs.
- The report regenerates every figure/section of `crosstrad-report.html` from data
  (not literals) and additionally shows CIs on the scorecard and framing gaps.
- `.codev/checks/test.sh` gains one registry line so a builder touching
  `workflows/analysis` runs its pytest suite.

### 3.3 Constraints

- **Read-only consumer.** `analysis` must not modify `workflows/judging` or the run
  dirs; it only reads `report.json` + the `*.jsonl` artifacts.
- **Self-contained HTML.** No external CSS/JS/CDN/`<img>`; inline `<style>` + inline
  SVG + optional inline `<script>` only (matches the pilot's house style). The HTML
  report must open offline as a single file.
- **Fail fast, no fallbacks** (global rule). If a run-dir is missing a required
  artifact, or a `judgments.jsonl` row lacks a required key, or a numeric score is
  off the five-value grid, **fail loudly** with a clear error naming the file —
  never silently substitute a default or a zero. Absent `(subject, judge)` pairs
  that are explained by `skipped.jsonl` (self-judge) are **not** errors.
- **Numeric scores, no band names** (per #17/#18). Output surfaces bare numbers on
  the −1…+1 scale; the ported `band_color` keeps its diverging colormap but **no
  band-name label** (Burns/Sparks/Inert/Scent/Perfume) may appear in any output.
- **Standalone uv project** (no root workspace exists). Cross-project deps, if any,
  are wired point-to-point via `[tool.uv.sources] { path = "…", editable = true }`,
  as `judging` pulls in `tradition_validator`.
- **Python `uv`, Typer CLI, `python -m analysis`, run from repo root** — mirror the
  judging invocation exactly.
- **Determinism.** Bootstrap RNG is explicitly seeded (default `SEED = 12345`, from
  the port source; overridable via `--seed`); the same inputs + seed produce
  byte-identical statistics.

### 3.4 Baked decisions (architect, recorded from Issue #26)

The issue is effectively a baked-decisions block. Recorded verbatim in force; not
relitigated in §4:

1. **Data source** is MultiBench judging output (multiple `--results-dir`s, one per
   tradition), NOT JaleesBench's results format. Derive schemas from the **real
   artifacts** in `tmp/judging-runs/20260702/`, not from docs
   ([[testing-llm-pipelines-mock-boundary]] / "derive format from real data").
2. **Comparison axis is the tradition** (subjects within), not an 8-subject field.
   Figures: cross-tradition scorecard, framing-staircase small-multiples,
   steadfastness-by-pressure heatmap (tradition × subject rows), score
   distributions, technique profile, judge agreement.
3. **Numeric scores, no band names** — port `band_color` to the numeric scale.
4. **Bootstrap CIs must cross over** — the load-bearing statistics piece the pilot
   lacks (5 scenarios/tradition, no CIs). Resampling unit = scenario cluster.
5. **CLI** via Typer, run from repo root:
   `uv --project workflows/analysis run python -m analysis report <run-dir>...`.
   Outputs a self-contained HTML report + optional matplotlib PNG/PDF figures.
6. **Port-fidelity mandate** — port, don't redesign; carry non-functional behavior
   (bootstrap draw-sharing, figure conventions) unless reframed above; document
   every deviation (§4.7).
7. **Registry** — add `workflows/analysis` to `.codev/checks/test.sh` (+1 line).
8. **PR strategy** — plan phases ship as git commits within a **single** PR (not
   per-phase PRs); PR opened during/after the final implement phase unless the
   architect requests earlier.

---

## 4. Solution exploration

### 4.1 The input contract (derived from the real artifacts)

Each `<run-dir>` is one tradition's judging `--results-dir`. The relevant files:

| File | Unit of a row / object | Used for |
|---|---|---|
| `report.json` | one object | pre-computed aggregates (point estimates) |
| `judgments.jsonl` | one judge's verdict on one cell | **re-aggregation for CIs** |
| `judgments_v2.jsonl` | re-judge override, same keys | overlay onto base judgments |
| `sittings.jsonl` | one 4-turn transcript | scenario spotlights (optional) |
| `skipped.jsonl` | one self-judge skip (no score) | explains absent judge verdicts |

**`report.json` top-level keys** (identical order across traditions):
`tradition, subjects, judges, counts, scorecard, score_distribution, agreement,
taxonomies, techniques, by_scenario, scenario_agreement, cost`.

Load-bearing sub-structures (real values):

- `scorecard[subject]` = `{ headline, steadfastness, steadfastness_by_pressure{6},
  by_framing{unstated,stated,guided} }` — all floats; `steadfastness*` may be
  negative.
- `score_distribution[subject]` = counts keyed by **stringified** score:
  `{"-1.0","-0.5","0.0","0.5","1.0"}` → int.
- `agreement` = `{cells, exact_pct, within_one_pct, worst_scenario,
  worst_scenario_exact_pct}`.
- `techniques[subject]` = seven fixed rates: `reads_person, engages_reason,
  gentleness, gradualism, exit_ramp, proportion, open_door`.
- `by_scenario[scenario_id][subject]` = float; `scenario_agreement[scenario_id]` =
  float; `cost = {rows[{stage,model,tokens_in,tokens_out,usd}], total_usd,
  fully_priced, prices_dated}`.
- `taxonomies` is an **open, per-tradition map** (buddhism has 5 families,
  sunni-islam only 2; `register` is not universal). **Not surfaced** in the
  cross-tradition report (the reference report standardizes on the seven universal
  `techniques` instead) — treat as out of scope for v1 (§9.4).

**`judgments.jsonl` row** — 15 keys; identity =
`(sitting_key, subject, tradition, scenario_id, pressure, framing, judge, scope)`
plus `score` (float ∈ {−1,−0.5,0,0.5,1}), `direction`, `rationale`,
`techniques_used`, and optional `raw`, `usage`, `ts`. `sitting_key =
"subject|scenario_id|pressure|framing"`. `scope ∈ {turn1, full}`. **Parse the
top-level `score` (float), never the `raw` string.**

**`judgments_v2.jsonl`** — identical key set; **overrides** base judgments by
`(sitting_key, judge, scope)` (v2 wins, never adds a vote). The analysis tool must
apply this overlay before aggregating, exactly as the judging report does.

Structural facts the parser must respect:
- **Asymmetric judge panel.** A judge never scores its own subject (self-skip in
  `skipped.jsonl`), so opus-subject cells are judged by one judge, sonnet-subject
  cells by two. Iterate over judges **present** per cell; absence explained by
  `skipped.jsonl` is expected, not an error.
- **Universal core.** framings = `{unstated, stated, guided}`; pressures = the six
  above; both identical across traditions.
- **Cluster unit.** `scenario_id` (5 per tradition; tradition-specific prefixes
  `BUD-/BZ-/MSR-/JLS-/TAO-`). No dedicated `cluster` field exists.

### 4.2 The cell reducer & aggregation (matching `report.json`)

To keep the port's point estimates **numerically identical** to the upstream
`report.json` (so the report is trustworthy), aggregation follows the judging
spec's cell reducer (§5.9 of Spec 8), not JaleesBench's raw-judgment pooling:

1. **Overlay** `judgments_v2` onto `judgments` by `(sitting_key, judge, scope)`.
2. **Cell** = `(subject, scenario_id, pressure, framing, scope)`; **cell value** =
   unweighted mean of present judges' `score`.
3. **Aggregate** (headline, by_framing, steadfastness, …) = unweighted mean of the
   in-scope **cell** values; uncovered cells are excluded, never counted as 0.
   - `headline` = mean cell score at `framing=unstated, scope=full`.
   - `by_framing[f]` = mean cell score at `framing=f, scope=full`.
   - `steadfastness` = headline(full) − mean(unstated, turn1).
   - `steadfastness_by_pressure[p]` = mean(unstated, p, full) − mean(unstated, p, turn1).

This is a **deliberate deviation** from `paper_stats.py`'s count-weighted pooling
of raw bands, forced by the asymmetric panel (raw pooling would double-weight
sonnet's two-judge cells). Recorded in §4.7. Where `report.json` already provides a
point estimate, the port SHOULD reproduce it to ≤1e−9 as a self-check.

### 4.3 The bootstrap (the load-bearing statistics piece)

Ported from `paper_stats.py`, reframed to the scenario cluster:

- **Resampling unit = the scenario cluster.** Within a tradition there are 5
  `scenario_id` values; one bootstrap draw resamples 5 scenario indices **with
  replacement** and pulls all of each chosen scenario's cells together (cluster
  bootstrap). Cross-tradition quantities resample within each tradition's own
  cluster set (traditions are not pooled into one cluster pool — each tradition
  keeps its 5).
- **`N_BOOT = 5000`, `SEED = 12345`** (port defaults; `--n-boot`, `--seed`
  overridable).
- **Shared draws (fidelity requirement).** Generate **one** list of resample index
  arrays per tradition **once** and reuse it for every point estimate and every
  difference of that tradition, so paired quantities (e.g. recognition gap =
  stated−unstated) are computed on the **same** resampled scenarios per draw. This
  is `paper_stats.py`'s `RESAMPLES` mechanism (not the unused `draws()` generator);
  it must be carried over verbatim in spirit.
- **CI method = percentile.** 95% CI = `np.percentile(boots, [2.5, 97.5])`; every
  output is `[point, lo, hi]`.
- **`point_and_ci(cells)`** and **`diff_ci(cells_a, cells_b)`** — ported
  signatures. Because the MultiBench cell reducer differs from JaleesBench's
  (sum,count) pooling, the internal representation resampled per draw is the set of
  **per-scenario cell values** (not per-probe sum/count arrays); the point/CI math
  and the paired-draw reuse are otherwise identical.

Quantities that get CIs (minimum): per-tradition-per-subject **headline**;
**recognition gap** (stated−unstated) and **instruction gap** (guided−stated) via
`diff_ci`; **steadfastness** (pooled and per-pressure) via `diff_ci`.

**Accepted limitation (n = 5).** A cluster bootstrap over 5 units yields wide CIs
that will routinely cross zero — that is the honest point of adaptation #4, not a
bug. The report frames every value as directional (mirrors the pilot's §10) and
the caveats section states the n=5 limitation explicitly.

### 4.4 The colormap & numeric-scale reframe

Port `band_color` / `band_axis` from `make_figures.py`, adapted to numeric scores:

- Keep the **diverging colormap** (7 stops, deep-red → grey-beige → deep-green) and
  the **`TwoSlopeNorm(vmin=−1, vcenter=0, vmax=1)`** mechanism verbatim — 0 pins to
  the grey center, negatives red, positives green.
- **Drop the `× SCORE_SCALE (0.5)` rescale.** JaleesBench bands are −2…+2 and
  halved at report time; **MultiBench scores are already −1…+1**, so the port's
  `SCORE_SCALE = 1.0` (no rescale). This is the concrete meaning of "port
  `band_color` to the numeric scale."
- **No band names.** Rename the function to `score_color` (or keep `band_color` but
  strip all band-name labels); the colormap's internal id may stay, but no output —
  legend, tooltip, axis label, caption — may use a band name. Axis labels read
  e.g. *"Score (−1…+1; 0 = neutral)"*.
- `band_axis` reference lines (dashed grey at ±0.5, solid grey at 0) carry over;
  heatmaps auto-scale contrast with a fresh `TwoSlopeNorm(−vmax, 0, vmax)`,
  `vmax = |M|.max()`, exactly as the source.

### 4.5 Two rendering paths (both wanted)

The two port sources render figures two different ways, and the issue asks for
both — so the port keeps both, with a shared numeric aggregation/stats core
feeding each:

- **HTML report = inline SVG** (primary, MUST). Mirrors
  `crosstrad-report.html`'s house style: hand-built SVG marks via string assembly,
  inline CSS with light/dark `@media`, a "Table view" `<details>` twin per figure
  for accessibility, self-contained. This is the automated successor to the pilot.
- **matplotlib PNG/PDF = `make_figures.py` port** (optional, SHOULD, behind
  `--figures`). Publication figures; `saveboth` writes both `.pdf` (vector, for
  LaTeX) and `.png` (`dpi=150`); serif house style; `band_color`/`band_axis`
  conventions. **Introduces `matplotlib` as a new dependency, isolated to this uv
  project** (§4.7 deviation). `--figures` is off by default so the common
  HTML-only path needs no matplotlib import.

Figures/sections to (re)produce, reframed to tradition axis (from
`crosstrad-report.html` §1–§10 + `make_figures.py`):

1. **Cross-tradition scorecard** — dot plot, headline by tradition (both subjects),
   −1…+1 axis, **with bootstrap CI whiskers** (the pilot's Figure 1 + CIs).
2. **Framing staircase** — small-multiples, one panel per tradition
   (unstated→stated→guided), both subjects; table twin shows recognition (S−U) and
   instruction (G−S) gaps **with CIs**.
3. **Steadfastness heatmap** — diverging heatmap, rows = tradition × subject,
   columns = six pressures + pooled column; `TwoSlopeNorm` auto-scaled.
4. **Score distributions** — stacked horizontal bars across the five score values
   per tradition/subject, with n counts.
5. **Technique profile** — the seven universal techniques, pooled per subject
   (meter bars in HTML).
6. **Judge agreement** — exact-% / within-one-% / lowest-agreement scenario per
   tradition (from `agreement` + `scenario_agreement`).
7. **Scenario spotlights** (SHOULD) — per-scenario `by_scenario` table; transcript
   excerpts from `sittings.jsonl` optional.
8. **Cost & throughput** + **caveats** (n=5, judge asymmetry, scenario-mix) —
   summed across traditions; caveats ported from the pilot §10.

### 4.6 Module & CLI layout (mirror `workflows/judging`)

```
workflows/analysis/
  pyproject.toml            # package "analysis"; hatchling; [project.scripts] analysis = "analysis.cli:app"
  README.md
  analysis/
    __init__.py
    __main__.py             # from analysis.cli import app; app()
    cli.py                  # app = typer.Typer(name="analysis", no_args_is_help=True)
    loaders.py              # read run-dir artifacts; v2 overlay; validation (fail-fast)
    aggregate.py            # cell reducer + cross-tradition aggregates (§4.2)
    stats.py                # bootstrap: RESAMPLES, point_and_ci, diff_ci (§4.3)
    colors.py               # score_color, score_axis, TwoSlopeNorm (§4.4)
    html_report.py          # inline-SVG self-contained report (§4.5)
    figures.py              # optional matplotlib PNG/PDF (imported only under --figures)
  tests/
    conftest.py             # parents[3] repo-root; fixtures pointing at a tiny sample run
    test_*.py               # one per module
```

`report` command signature (Typer):
```
analysis report RUN_DIR... [--out PATH] [--figures/--no-figures]
                           [--n-boot 5000] [--seed 12345] [--fig-format pdf,png]
```
Heavy imports (matplotlib) deferred inside the command body so `--help` and the
HTML path stay import-light (judging's convention).

### 4.7 JaleesBench fidelity — the port ledger

**What must cross over (unchanged):**

| # | Behavior | Source |
|---|---|---|
| F1 | Bootstrap = 5,000 resamples, percentile 95% CI `[2.5, 97.5]`, seeded | `paper_stats.py` |
| F2 | **One shared `RESAMPLES` list per bootstrap pass, reused for point + diff** so paired quantities use identical draws (paired CIs on differences) | `paper_stats.py` `RESAMPLES` |
| F3 | Diverging colormap (7 stops) + `TwoSlopeNorm` centered at 0; ref lines at ±0.5 / 0 | `make_figures.py` `band_color`/`band_axis` |
| F4 | Heatmap auto-contrast: fresh `TwoSlopeNorm(−vmax,0,vmax)`, `vmax=|M|.max()` | `make_figures.py` |
| F5 | matplotlib figures saved as **both** `.pdf` and `.png` (`dpi=150`), serif house style | `make_figures.py` `saveboth` |
| F6 | v2 re-judge overlay applied before aggregating (v2 wins by identity key) | `score.py` `load_judgments` |
| F7 | Self-contained HTML: inline CSS + inline SVG, no external assets, table-view twins | `html_report.py` / `crosstrad-report.html` |
| F8 | Cell = mean over present judges; aggregate = unweighted mean of cells | judging Spec 8 §5.9 |

**Deliberate deviations (with reason):**

| # | Deviation | Reason |
|---|---|---|
| D1 | `SCORE_SCALE 0.5 → 1.0` (drop the ×0.5 rescale) | MultiBench scores are already on −1…+1; JaleesBench bands were −2…+2 (adaptation #3) |
| D2 | **No band names** anywhere in output; `band_color`→`score_color` | #17/#18: numbers everywhere, no band-name labels |
| D3 | Resampling unit = **scenario cluster (5/tradition)**, per-tradition, not 140 probes pooled | MultiBench data model (adaptation #1) |
| D4 | Comparison axis = **tradition** (subjects nested), not an 8-subject field | adaptation #2 |
| D5 | Bootstrap resamples **per-scenario cell values**, not per-probe (sum,count) arrays; aggregate via the cell reducer (F8) | asymmetric judge panel — raw-judgment pooling would double-weight two-judge cells |
| D6 | Input = judging `report.json` + `*.jsonl`, not JaleesBench `collect.jsonl`/`probes.json`/`citations_turn1.jsonl` | adaptation #1 |
| D7 | **matplotlib introduced** as a dependency (isolated to this uv project, deferred import) | issue asks for optional PNG/PDF figures; repo had none |
| D8 | Drop JaleesBench-specific sections: scripture/citation classes (`clean`/`leaky`/`intrinsic`), Ansari case study, reasoning-mode, pillars/hearts breakdowns | MultiBench-general; per-tradition `taxonomies` are non-uniform (§9.4 out of scope) |

---

## 5. Open questions

### Critical (blocks progress) — none
All architect decisions are baked (§3.4). If the two-rendering-path scope (§4.5)
should shrink to HTML-only for v1, the architect can say so; the plan will phase
matplotlib last so it is trivially deferrable.

### Important (affects design)
- **IQ1 — matplotlib figures in v1 or deferred?** The plan will implement the HTML
  report + CIs first and the matplotlib figures as the **final** phase, so if the
  architect wants v1 to ship HTML-only, that phase is dropped without disturbing
  the rest. Default: include, behind `--figures` (off by default).
- **IQ2 — scenario spotlight transcripts.** Reading `sittings.jsonl` for verbatim
  excerpts is SHOULD, not MUST; the `by_scenario` table (from `report.json`) is the
  MUST. Default: table in v1, transcript excerpts optional.
- **IQ3 — cross-tradition CI on pooled quantities.** Some numbers (e.g. a
  "field-mean" row) pool across traditions; the resampling then draws within each
  tradition's own 5-scenario cluster set and combines. Default per §4.3; flagged
  for review since it is the one place the cluster design must be stated precisely.

### Nice-to-know
- **NQ1** — a `--json` side-output of the computed stats (the analogue of
  `paper_stats.json`) for downstream tooling. Default: emit
  `analysis_stats.json` alongside the HTML (cheap, aids testing).
- **NQ2** — should the HTML be browsable by `apps/multibrowser`? Out of scope; the
  report is a standalone file.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Point estimates drift from upstream `report.json` (port bug) | Self-check: recompute each `report.json` point estimate via the cell reducer and assert ≤1e−9 match in tests (§9.5) |
| Silent mis-parse (wrong key, `raw` string vs float, off-grid score) | Fail-fast validation in `loaders.py`; a unit test asserts a malformed row raises, not defaults |
| Draw-sharing lost in the port → differences get independent draws → wrong CIs | F2 is an explicit test: `diff_ci(a,b)` point must equal `point_a − point_b`, and paired-draw variance < independent-draw variance on a fixture |
| CIs so wide they look broken (n=5) | Framed as intended (§4.3); caveats section states n=5 explicitly; not hidden |
| matplotlib import bloats the HTML-only path or CI | Deferred import inside `--figures` branch; HTML path never imports matplotlib; figures test marked to skip if matplotlib absent |
| Judge-panel asymmetry mis-weighted | Cell reducer (F8/D5) averages present judges per cell before aggregating; test on the real sonnet(2-judge)/opus(1-judge) fixture |
| `taxonomies` non-uniformity crashes a generic loader | Out of scope for v1 (§9.4); loader ignores `taxonomies` |

---

## 7. Success criteria

### 7.1 Functional (MUST)

- **M1** — `uv --project workflows/analysis run python -m analysis report <dir>...`
  runs from repo root over the five `20260702` run-dirs and writes a **single
  self-contained HTML file** that opens offline with no external requests.
- **M2** — The HTML report contains, reframed to the tradition axis: cross-tradition
  scorecard (with CI whiskers), framing-staircase small-multiples, steadfastness
  heatmap (tradition × subject rows × 6 pressures + pooled), score-distribution
  stacked bars, technique profile, judge agreement, cost, caveats — i.e.
  regenerates `crosstrad-report.html`'s figures **from data**.
- **M3** — Point estimates reproduce the upstream `report.json` values (headline,
  by_framing, steadfastness, steadfastness_by_pressure, techniques, agreement) to
  ≤1e−9.
- **M4** — Bootstrap 95% CIs are computed and displayed for per-tradition-per-subject
  headline and for recognition/instruction gaps and steadfastness, via ported
  `point_and_ci` / `diff_ci` with **shared draws** (F2), 5,000 resamples, seeded.
- **M5** — `judgments_v2.jsonl` is overlaid before aggregating (F6); `skipped.jsonl`
  self-skips are treated as expected absences, not errors.
- **M6** — Scores are numeric only; **no band name** appears in any output. The
  colormap maps numeric −1…+1 via `TwoSlopeNorm` (F3, D1/D2).
- **M7** — Fail-fast: a missing required artifact, a missing required judgment key,
  or an off-grid score raises a clear error naming the file; no silent default.
- **M8** — `.codev/checks/test.sh` gains the `workflows/analysis` registry line so
  the dispatcher runs its pytest suite for a builder that touches it.

### 7.2 Functional (SHOULD)

- **S1** — `--figures` emits matplotlib PNG **and** PDF figures (`saveboth`, dpi 150,
  serif house style, `band_color`/`band_axis`) porting `make_figures.py`.
- **S2** — Scenario spotlights table from `by_scenario`; transcript excerpts from
  `sittings.jsonl` optional.
- **S3** — `analysis_stats.json` side-output of computed point+CI values (the
  `paper_stats.json` analogue), for testing/downstream use.
- **S4** — `--out`, `--n-boot`, `--seed`, `--fig-format` flags behave as in §4.6.

### 7.3 Non-functional

- Determinism: same inputs + seed → byte-identical statistics and HTML.
- Self-contained HTML; light/dark via CSS `@media`; table-view twins for
  accessibility.
- New tradition = new run-dir argument, no code change.
- HTML-only path imports no matplotlib.

### 7.4 Out of scope (v1)

- Per-tradition `taxonomies` breakdown heatmaps (pillars/hearts/virtues analogues)
  — the families are non-uniform across traditions; the report standardizes on the
  seven universal techniques (D8).
- JaleesBench-specific sections: scripture-citation classes, Ansari case study,
  reasoning-mode comparison (D8).
- Any change to `workflows/judging` or the run artifacts.
- Integration into `apps/multibrowser`.
- Live model calls (analysis is purely offline over existing artifacts).

### 7.5 Test scenarios

- **T1 (parse + validate)** — a tiny fixture run-dir (1–2 scenarios, both subjects,
  a couple framings/pressures) loads; a malformed row (missing key / off-grid
  score / `raw`-only) raises; a `skipped.jsonl` self-skip does not.
- **T2 (v2 overlay)** — a base judgment overridden by a v2 row yields the v2 score,
  vote count unchanged.
- **T3 (cell reducer / point-estimate parity)** — over a real `20260702` run-dir,
  recomputed headline/by_framing/steadfastness/techniques/agreement match
  `report.json` to ≤1e−9 (M3).
- **T4 (bootstrap correctness)** — `diff_ci(a,b)` point == `point_a − point_b`;
  paired draws (shared `RESAMPLES`) give smaller diff variance than independent
  draws on a fixture; CI is `[2.5,97.5]` percentile; reproducible under fixed seed.
- **T5 (numeric-only)** — rendered HTML/text contains no band-name string
  (Burns/Sparks/Inert/Scent/Perfume); `score_color(-1|0|1)` returns the expected
  red/grey/green endpoints.
- **T6 (self-contained HTML)** — output HTML has no `http(s)://` asset refs, no
  `<img src>`, no `<script src>`; opens as one file.
- **T7 (figures, sk-if-absent)** — with matplotlib available, `--figures` writes
  both `.pdf` and `.png`; test skips cleanly if matplotlib is not installed.
- **T8 (CLI smoke)** — `analysis --help` and `analysis report --help` exit 0 without
  importing matplotlib.
- **T9 (dispatcher)** — `.codev/checks/test.sh` maps `workflows/analysis` to its
  pytest command.

---

## 8. Consultation Log

### Iteration 1 — pre-draft research (2026-07-02)
Three parallel deep-dives established the input schema (real `20260702`
artifacts), the port-source algorithms (`band_color`/`band_axis`,
`RESAMPLES`/`point_and_ci`/`diff_ci`, `saveboth`), and the reference output
(`crosstrad-report.html` is hand-built inline SVG; no matplotlib in repo; uv
projects standalone). Findings drove §4 and the port ledger §4.7.

_(Porch will run 3-way spec consultation next; feedback recorded here.)_
