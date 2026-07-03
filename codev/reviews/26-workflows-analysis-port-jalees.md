# Review: workflows-analysis-port-jalees

## Summary

`workflows/analysis` is a new standalone `uv`/Typer project that turns MultiBench
**judging** output (N `--results-dir`s, one per tradition) into cross-tradition
analysis artifacts — a faithful port of JaleesBench's `html_report.py` /
`make_figures.py` / `paper_stats.py` / `score.py`, reframed so the comparison axis is
the **tradition** (subjects nested). One command from the repo root:

```bash
uv --project workflows/analysis run python -m analysis report <run-dir>... [--figures]
```

It writes a **self-contained HTML report** (`report.html`), a stats side-output
(`analysis_stats.json`), and — under `--figures` — matplotlib PNG/PDF figures. The
load-bearing addition over the hand-built pilot (`crosstrad-report.html`) is
**scenario-cluster bootstrap 95% CIs**. Delivered across 5 git-committed phases in a
single branch (~1,690 LOC across `analysis/`, **79 tests**).

## Spec Compliance

| Criterion | Status |
|---|---|
| **M1** CLI over N run-dirs → self-contained offline HTML | ✅ |
| **M2** All report sections, tradition-axis (scorecard w/ CIs, staircase, steadfastness heatmap, distributions, technique, agreement, cost, caveats) | ✅ |
| **M3** Point estimates reproduce `report.json` ≤1e−9 (headline, by_framing, steadfastness+by_pressure, techniques, agreement) | ✅ parity self-check on fixtures **and** 0 diffs over all 5 real run-dirs |
| **M4** Bootstrap 95% CIs computed **and displayed** (headline whiskers, gap CIs, steadfastness CIs) with shared draws (F2), 5000 resamples, seeded | ✅ |
| **M5** v2 overlay applied; `skipped.jsonl` self-skips treated as expected absences | ✅ (v2 is override-only) |
| **M6** Numeric only; no band names; `TwoSlopeNorm` colormap | ✅ |
| **M7** Fail-fast on missing artifact/key, off-grid/string score, dup tradition id, cross-metadata mismatch, dup base identity | ✅ |
| **M8** `.codev/checks/test.sh` registry line | ✅ |
| **M9** Output-injection safe (all artifact text escaped; no `<script>` context) | ✅ (JS-free static SVG) |
| **M10** Fixed output contract (`--out DIR` → `report.html` + `analysis_stats.json` (+ `figures/`); idempotent overwrite) | ✅ |
| **M11** Fixture-backed CI (no dependence on `tmp/` or external JaleesBench) | ✅ |
| **S1** `--figures` PNG **and** PDF (`saveboth`, dpi 150, house style) | ✅ |
| **S2** Scenario spotlights table (transcripts optional) | ✅ table; transcripts deferred (see below) |
| **S3** `analysis_stats.json` side-output | ✅ |
| **S4** `--out/--n-boot/--seed/--fig-format` flags | ✅ |

All MUST criteria met. Non-functional: deterministic/byte-stable output, self-contained
HTML with light/dark theming + table-view twins, HTML path imports no matplotlib.

## Deviations from Plan

- **S2 transcripts**: scenario spotlights ship as the `by_scenario` table (the MUST);
  verbatim `sittings.jsonl` transcript excerpts were left out (SHOULD, and the plan
  explicitly deferred sittings loading). Not needed for any figure; a natural follow-up.
- **v2 overlay is stricter than the upstream loader**: judging's `load_judgments`
  silently inserts a v2 row with no base; per spec §4.1 ("never adds a vote") and the
  Phase-2 review, `analysis` **rejects** an orphan v2 row. Verified 0 orphans exist
  across all real+fixture data, so parity is unaffected.
- **Bootstrap sparse-slice guard**: `paper_stats.py` never divides-by-zero because it has
  140 dense probes; at 5 scenario clusters a resample can select only zero-cell scenarios,
  so `analysis` skips those draws (Phase-3 review). A refinement over the source, not a
  behavior change on dense data.
- No time was spent on the matplotlib figures being "optional at install": matplotlib is
  a declared extra **and** in the dev group (so CI exercises `--figures`); the isolation
  requirement is at *import* time (lazy), which is honored and tested.

## Architecture Updates

Applied via the `update-arch-docs` skill (hot/cold two-tier discipline):

- **`codev/resources/arch.md`** (COLD): added a **"## The analysis workflow"** section
  (parallel to the judging section) describing the consumer role, the ≤1e−9 parity
  property, the cluster bootstrap + shared draws, numeric-no-band-names, JS-free SVG
  injection-safety, and matplotlib import-isolation; updated **"## Repository layout"** to
  list `workflows/analysis/`.
- **`codev/resources/arch-critical.md`** (HOT): added one **map** line — "The judging &
  analysis workflows — consult when…" — fixing a pre-existing omission and covering the
  new section. No new HOT *fact* (the sibling judging workflow is cold-only too; kept the
  cap clean).
- **`workflows/README.md`**: added the `analysis` bullet.
- **`workflows/analysis/README.md`**: invocation, output contract, module map, fixtures
  provenance.

## Lessons Learned Updates

Added to `codev/resources/lessons-learned.md` (COLD, "## Porting fidelity") — four durable,
cross-spec engineering lessons (routed COLD, not HOT: the sibling judging workflow is cold-only
too, keeping the hot cap clean):

- **Parity as a real cross-check.** When a consumer must match an upstream aggregator, make the
  parity test compare two independent implementations — regenerate fixtures via the *actual*
  upstream aggregator (then trim), and reuse the upstream's exact reducer rather than re-deriving
  it, or the numbers drift.
- **Re-express a ported statistic so the reference machinery ports verbatim.** The cell-mean
  aggregate is `sum(cell values)/count(cells)`, so JaleesBench's `(sum,count)` cluster-bootstrap
  code ports unchanged — built over cells grouped by scenario (D5). Keep the shared resample-draw
  list for paired diffs; guard the small-N zero-count edge (skip the draw, don't divide by zero).
- **Import-isolate a heavy optional dependency and prove it with a subprocess test.** matplotlib
  is imported only inside the `--figures` branch; a subprocess asserts `import analysis.cli` leaves
  it out of `sys.modules` (an in-process check is polluted by sibling test modules).
- **A JS-free static-SVG report is injection-safe by construction** — no `<script>` context exists,
  so untrusted model-produced strings can't reach one; one `esc()` chokepoint seals the surface.

## Lessons Learned

### What Went Well
- **The port-fidelity mandate paid off.** Reading judging's `report.py` as ground truth
  (not paraphrasing) meant the cell reducer matched exactly — **0 parity diffs across all
  5 real run-dirs**, not just the fixtures. The `crosstrad-report.html` and `paper_stats.py`
  sources gave the exact conventions to carry over.
- **Regenerating fixtures via the real judging aggregator** made the ≤1e−9 self-check a
  genuine two-implementation cross-check rather than a tautology.
- **JS-free static SVG** collapsed the injection surface to nothing (no `<script>` to reach)
  — M9 fell out for free, and the report is trivially self-contained.
- **Scaffold-first phasing** (walking skeleton before logic) meant the toolchain (uv build,
  CLI, porch dispatcher) was proven in Phase 1, so later phases never fought the plumbing.
- **The 2-way review caught real issues every phase** (see Consultation Feedback) — none
  cosmetic: v2-insert semantics, NaN on sparse slices, undisplayed steadfastness CIs.

### Challenges Encountered
- **Matching floats exactly**: preserving judgment order through the v2 overlay so the
  cell-score summation order matched judging's — resolved by mirroring `load_judgments`'s
  dict-overlay exactly (base then v2, insertion order preserved).
- **Small-N bootstrap robustness**: the 5-cluster resample can hit an all-zero-count draw
  that `paper_stats.py` never does — resolved by skipping such draws while keeping shared
  draws intact.
- **Test isolation for the matplotlib import check**: an in-process `sys.modules` assertion
  broke once `test_figures` imported matplotlib during collection — resolved by moving the
  check into a subprocess.
- **A porch-flow misstep**: I hardcoded a `--context` path for a re-review consult from a
  previous phase's pattern; that iteration's command had **no** `--context` flag, so the
  run produced no output. Fixed by always taking the exact command from `porch next`.

### What Would Be Done Differently
- Take the consult command verbatim from `porch next` every time instead of reconstructing
  it — the flag set varies by iteration.
- Consider generating the committed fixtures with a small checked-in helper (documented in
  `tests/fixtures/README.md`) rather than a scratch script, so regeneration is one command.

### Methodology Improvements
- **SPIR worked well here.** The per-phase 2-way review with a rebuttal loop is the right
  granularity for a fidelity-critical port — each phase's load-bearing invariant (parity,
  paired-draw CIs, injection-safety, import-isolation) got its own adversarial pass.
- Minor porch UX: the iter-2 "Fix issues from iteration 1 → build → done → consult" loop can
  read as circular after a rebuttal; documenting that `porch done` (post-fix) advances to
  the re-review consult would save a beat.

## Technical Debt
- Scenario-spotlight transcript excerpts (S2) not implemented — table only.
- `analysis` owns its copy of the score grid / seven technique ids (input contract, spec
  §4.1); if judging's output contract ever changes these, `analysis` must track it (they
  are not in the shared `tradition_validator.core`). Low risk — the scale is a settled
  contract (#17/#18).
- No pooled/cross-tradition CI (IQ3 deliberately scoped out); a later spec could add it.

## Consultation Feedback

Per-phase consult set is `["codex", "claude"]` (Gemini's impl/review sandbox can't see the
worktree here). Full outputs in `codev/projects/26-workflows-analysis-port-jalees/`.

### Specify (Round 1) — Codex REQUEST_CHANGES, Claude APPROVE
Codex: fixture/source availability (tmp/ gitignored, JaleesBench external); HTML/SVG escaping
requirement; precise `--out` contract; validation edge cases; resolve pooled-CI (IQ3). All
five addressed in-spec (§4.8 fixtures, §3.3 escaping, §4.6 contract, §4.1 validation table,
§4.3 IQ3 resolved). Claude: minor batch_state.json/T6/empty-v2 notes — all folded in.

### Plan (Round 1) — Codex REQUEST_CHANGES, Claude APPROVE
Codex: Phase-2 parity must cover `techniques`+`agreement` (not read-through); sharpen the
Phase-3/4 `analysis_stats.json` emission boundary; make determinism + a non-default
`--fig-format` test explicit. All applied. Claude: full coverage table, APPROVE.

### Phase 1 — scaffold (Round 1): Codex APPROVE, Claude APPROVE. No issues.

### Phase 2 — loaders/aggregate (Round 1): Codex REQUEST_CHANGES, Claude APPROVE → (Round 2) both APPROVE
Codex: v2 must be override-only (was inserting); load `skipped.jsonl` (was ignored); add tests
for both. Fixed (v2 orphan → error, verified 0 orphans; `run.skips` loaded; +2 tests). Claude
minors (dead `.get()` fallback; parity-check `worst_scenario`) applied.

### Phase 3 — bootstrap stats (Round 1): Codex REQUEST_CHANGES, Claude APPROVE → (Round 2) both APPROVE
Codex: divide-by-zero → NaN when a draw selects only zero-cell scenarios; add a sparse-slice
regression test. Fixed (skip empty draws, F2 pairing preserved, never NaN; +3 tests).

### Phase 4 — HTML report (Round 1): Codex REQUEST_CHANGES, Claude APPROVE → (Round 2) both APPROVE
Both: steadfastness CIs computed but not **displayed** (M4). Fixed (heatmap table twin shows
`point [lo,hi]` per-pressure + pooled; SVG cell hover carries CI). Claude minors: full HTML5
document with `<meta charset>` (fixes non-ASCII `−`/`…`); column-alignment (global subjects for
header+body). All applied; +2 tests.

### Phase 5 — matplotlib figures (Round 1): Codex APPROVE, Claude APPROVE. No issues.

### Review / PR (Round 1) — Codex APPROVE, Claude APPROVE. No issues.

### Integration CMAP (architect, 3-way at the PR gate) — Gemini APPROVE, Claude APPROVE, Codex REQUEST_CHANGES (1 confirmed)
**Finding (confirmed):** `aggregate.py` derived the scenario cluster set from *judgments
only*, so on a **partial run** a collected-but-zero-judgment scenario silently vanished from
the bootstrap cluster set — no uncovered signal, resampling over N−1 clusters, **understated
CIs**. Upstream derives the scenario universe from sittings.
**Fix:** derive `scenario_ids` from `report.json`'s `by_scenario` keys (upstream keys them by
judgments ∪ sittings — the full expected coverage) unioned with judged scenarios; a
zero-judgment scenario now stays in the cluster set (carries no cells → correctly *widens*
resamples). Added `test_partial_run_uncovered_scenario_stays_in_cluster_set`. Full runs are
unaffected (by_scenario keys == judged scenarios): the 5 real run-dirs still show N=5 and 0
parity diffs. Re-ran the 2-way delta consult (Codex + Claude) — both APPROVE.

## Flaky Tests
No flaky tests encountered. No tests were skipped as flaky. (`test_figures.py` uses
`pytest.importorskip("matplotlib")` — a deliberate skip-if-extra-absent, not a flaky skip.)

## Follow-up Items
- Scenario-spotlight transcript excerpts from `sittings.jsonl` (S2).
- Optional pooled/cross-tradition CI (deferred per IQ3).
- Consider surfacing the report through `apps/multibrowser` (out of scope here).
