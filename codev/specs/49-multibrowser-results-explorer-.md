# Specification: MultiBrowser Results Explorer — Judge & Pressure Selectors + Leaderboard

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
-->

## Metadata
- **ID**: spec-2026-08-05-multibrowser-results-explorer
- **Status**: draft
- **Created**: 2026-08-05

## Clarifying Questions Asked

A spec file did not exist at spawn, so the answers below are drawn from issue #49, the architect's
data-access notes, the real launch data under `tmp/judging-runs/`, and the established repo conventions
(Specs 7, 8, 26; `codev/resources/arch-critical.md`). No live questions were put to the user; the issue
plus reference data already fix the key decisions. The questions the spec had to resolve, and how:

- **Q: Should the SPA compute standings from raw per-cell scores, or read pre-aggregated numbers?**
  A: Read pre-aggregated per-tradition means computed by the *canonical* Python aggregator, and let the
  SPA do only the final equal-weight mean across traditions. This was validated numerically (see
  Desired State) and guarantees the leaderboard reconciles with the paper.
- **Q: What exactly is the "mean of per-tradition means, post-pressure" standings convention?**
  A: For a given (subject, framing, scope): take each tradition's unweighted mean over its in-scope cells,
  then average those seven tradition-means with equal weight. `scope=full` is post-pressure; `scope=turn1`
  is first-response. Verified to equal the paper's `subj_overall` point estimates exactly.
- **Q: How is the dual-judge / Opus alias / sample-coverage problem handled?**
  A: The export alias-normalizes the two Opus judge ids to one, and records per-cell coverage
  (`n_judged / n_expected`) so views can degrade honestly where Opus is sample-only. The SPA never sees
  two Opus judges and never presents a sample mean as if it were full-grid.
- **Q: What granularity keeps the export in single-digit MB with no transcripts?**
  A: Pre-aggregated breakdowns + coverage + score distributions, sharded per tradition. No transcript
  turns and no per-judgment rationale in v1 (see Open Questions for the rationale trade-off).

## Problem Statement

The 20260803 results programme produced a large dual-judged evaluation run (93,420 Gemini judgments across
the full 5-subject × 3-framing × 6-pressure grid for seven traditions, plus two Opus judge layers). Today
those results are reachable only as a 583 MB local, gitignored run directory and a static HTML/PDF paper —
there is no interactive way to browse them alongside the corpus. The `multibrowser` SPA already browses the
tradition corpus live from GitHub but deliberately ships an **inert** results seam (`loadResults` returns
`null`); the judging output was never bound to it.

We need to bring the JaleesBench browser's "explorer" experience — a **leaderboard** with a **judge
selector** and a **pressure selector** — into `multibrowser`, driven by a compact, committed, browsable
results dataset that the SPA reads at runtime exactly the way it reads traditions. The numbers shown must
reconcile with the paper's standings table, the two Opus judge aliases must be collapsed to one, and views
must be honest wherever Opus coverage is only a sample.

## Current State

- **Run data**: `tmp/judging-runs/<run-id>/<tradition>/{sittings,judgments}.jsonl` + per-tradition
  `report.json`/`report.md` + a run-level `analysis-out/` (figures, `analysis_stats.json`, and the report-v2
  `stats_bundle.json`). This is local-only and gitignored (583 MB); the browser cannot read it.
- **The SPA** (`apps/multibrowser/`, Vite 6 / React 19 / TS / Tailwind 4 / HeroUI v3 / TanStack
  Router+Query) browses the corpus by reading GitHub at runtime: it resolves the latest `main` SHA, lists
  files via one git-trees call, and fetches content from `raw.githubusercontent.com` pinned to that SHA
  (raw is off the 60/hr unauthenticated API budget). New/edited traditions appear without a redeploy.
- **Results are stubbed out**: `src/lib/results.ts` (`loadResults → null`), an intentionally empty
  `ScenarioResults` type, and a reserved `ResultsRegion` placeholder — an explicit additive seam awaiting
  the judging output's shape. There is no `/results` route, no leaderboard, and no selectors.
- **The canonical aggregation** already exists in Python: `workflows/analysis/analysis/aggregate.py`
  faithfully reproduces `judging.report`'s numeric semantics (cell = subject × scenario × pressure × framing
  × scope; cell score = mean of present judges; breakdown = unweighted mean of in-scope cells; headline =
  unstated + full; steadfastness = full − turn1). The report-v2 `stats_bundle.json.subj_overall` holds the
  paper's standings point estimates + bootstrap CIs.
- **The Opus alias split is real**: in `20260803-framings-opus-sample`, Opus judgments appear under both
  `claude-opus-4-8` (batch) and `anthropic/claude-opus-4.8` (OpenRouter tail); the split is per-tradition
  and the sample dir is still being tail-filled (counts moving until the architect seals it).

## Desired State

A **Results Explorer** in `multibrowser`, added as new routes/facets without disturbing corpus browsing:

- A **leaderboard** showing overall standings by subject for the selected framing and scope, computed as
  the **mean of per-tradition means, post-pressure** (the paper's `tab_standings` convention), with a
  **per-tradition drill-down**, a **framing toggle** (unstated / stated / guided), and a **scope toggle**
  (first-response = `turn1` / post-pressure = `full`).
- A **judge selector** that switches whose verdicts drive every view — **Gemini** (full grid) or **Opus**
  (one normalized judge). Opus stated/guided views degrade honestly (badged sample, coverage shown).
- A **pressure selector** that filters every results view by one of the six pressures or "all".
- The whole explorer is fed by a **committed, additive results dataset** the SPA reads at runtime:
  `results/<run-id>/` with a **manifest** (subjects, judges, framings, pressures, scopes, counts, dates,
  per-cell coverage) plus **per-tradition shards** (scores + metadata only — no transcripts). Total per run
  lands in **single-digit MB**, sharded so any single raw fetch is small. A newly exported+committed run
  appears in the browser with **no code change** (same git-trees + raw mechanism as traditions).

**Reconciliation is guaranteed by construction.** The export publishes each tradition's breakdown means
computed by the canonical Python aggregator; the SPA's only client-side statistic for the leaderboard is
the equal-weight mean across the seven tradition-means. This was verified against the launch data:

| framing | mean-of-per-tradition-means (Gemini) | paper `subj_overall[gemini-3.6-flash]` | match |
|---|---|---|---|
| unstated | 0.138790 | 0.138790 | exact |
| stated | 0.555226 | 0.555226 | exact |
| guided | 0.939201 | 0.939201 | exact |

## Stakeholders
- **Primary Users**: MultiBench researchers/readers exploring the 20260803 results interactively and
  cross-checking them against the paper.
- **Secondary Users**: Future run authors who export a new run and expect it to surface without redeploy.
- **Technical Team**: This builder (spir-49); maintainers of `apps/multibrowser` and `workflows/analysis`.
- **Business Owners**: The architect (project 49 owner) and the MultiBench project lead.

## Success Criteria
- [ ] **Leaderboard reconciles with the paper**: overall standings (mean of per-tradition means) for every
      subject × framing at `scope=full`, judge=Gemini, pressure=all, match the paper's standings table to
      the displayed precision.
- [ ] **Judge selector** switches all views between Gemini and a single normalized Opus judge; the SPA never
      exposes two Opus judges.
- [ ] **Pressure selector** filters every results view by each of the six pressures and by "all".
- [ ] **Framing toggle** (unstated/stated/guided) and **scope toggle** (first-response/post-pressure) drive
      the leaderboard and drill-down.
- [ ] **Per-tradition drill-down** shows each tradition's contributing mean for the current selection.
- [ ] **Honest degradation**: where Opus coverage is sample-only (stated/guided), the view is badged as a
      sample and shows coverage (`n_judged / n_expected`); a tradition with zero coverage for the selection
      is shown as excluded, never as 0.
- [ ] **Additive, no-redeploy publish**: a new `results/<run-id>/` exported and committed appears in the
      browser without a code change; corpus browsing is unchanged.
- [ ] **Size budget**: each run's committed dataset is single-digit MB, sharded per tradition.
- [ ] **Alias normalization**: the export collapses `claude-opus-4-8` and `anthropic/claude-opus-4.8` into
      one Opus judge with no double-counting.
- [ ] Judge & pressure selectors work on the live Railway deploy (manual `railway up`).
- [ ] All tests pass (the touched-app suites: `pnpm -C apps/multibrowser test` and, if the export is Python,
      `uv … pytest` for the export module); no reduction in coverage.
- [ ] Documentation updated (a `results/README.md` data contract + the multibrowser README).

## Constraints

### Technical Constraints
<!-- These are fixed architectural constraints taken verbatim from issue #49 ("Constraints (arch-critical)"
     and "What"/"Data access"/"Acceptance"). Treat each as baked; do not relitigate in Solution Approaches. -->
- **Client-side only, GitHub-at-runtime**: the SPA reads GitHub at runtime (SHA-pinned git-trees + `raw`
  fetches, unauthenticated 60/hr budget). Results data must be **committed files, additive, no backend, no
  baked data** — a new run appears without redeploy. Results add effectively zero API calls (same one
  git-tree per snapshot; shard content via `raw` is off-budget).
- **Stack**: Vite / React 19 / TS / Tailwind 4 / HeroUI v3 (**provider-less** — no `HeroUIProvider`) /
  TanStack Router + Query. Reuse the existing data layer and filter/deep-link machinery.
- **Corpus browsing must remain intact**; results features are **additive routes/facets**.
- **Scores + metadata only — no full transcripts.** Raw run data is 583 MB; the export must land in
  single-digit MB, **sharded per tradition** so raw fetches stay small. Include a **manifest** (subjects,
  judges, framings, pressures, scopes, counts, dates).
- **Dual-judge with Opus alias normalization**: the run is Gemini 3.6 Flash (full grid) + Claude Opus 4.8
  (unstated full + stated/guided sample). Opus judgments exist under two aliases (`claude-opus-4-8` vs
  `anthropic/claude-opus-4.8`); **the export must alias-normalize** so the SPA sees one Opus judge. Views
  must **degrade honestly** where Opus coverage is sample-only.
- **Leaderboard convention is fixed**: overall standings by framing = **mean of per-tradition means,
  post-pressure**, the same convention as the paper's Table `tab_standings`. Numbers must reconcile with the
  paper's tables. To guarantee this, the export must use the **canonical aggregation semantics** already
  encoded in `workflows/analysis` (cell = mean of present judges; breakdown = unweighted mean of in-scope
  cells; uncovered cells excluded, never 0).
- **Charts, if any, follow the repo's dataviz palette** — the seven-stop diverging score colormap
  (`workflows/analysis/analysis/colors.py`, deep red → grey-beige → deep green, `TwoSlopeNorm(−1,0,1)`
  linear). **No band-name labels** (Burns/Sparks/… are forbidden in any output); the scale is numeric −1…+1.
- **Canonical launch data**: `20260803-merged` (Gemini) + `20260803-unstated-opus` + the (moving)
  `20260803-framings-opus-sample`. The run data is a **read-only symlink** in the worktree
  (`tmp/judging-runs/`); build/test the export against it but **commit only the export OUTPUT**.

### Business Constraints
- **Timeline**: N/A — no time estimates (AI-age; measure by completed phases).
- **Budget**: N/A — no monetary budget constraint on this work.
- **Compliance**: N/A — public, read-only benchmark data; no PII, no auth.

## Assumptions
- The judging output schema is stable for the launch run: `judgments.jsonl` rows carry a numeric top-level
  `score` (∈ {−1, −0.5, 0, 0.5, 1}) and the identity keys `(subject, tradition, scenario_id, pressure,
  framing, judge, scope)`; the export reads the top-level `score`, never the `raw` string.
- The three source run directories together supply Gemini (all framings, full grid) and Opus (unstated full
  + stated/guided sample) for the same seven traditions and five subjects; the export **merges** them into
  per-tradition, per-judge shards.
- The canonical aggregation in `workflows/analysis/analysis/aggregate.py` is the source of truth for cell
  and breakdown semantics; the export reuses it (or re-derives identical numbers verified against
  `report.json` / `stats_bundle.json`).
- `framings-opus-sample` counts are still moving; the export is **re-runnable** and the committed dataset is
  regenerated when the architect confirms the sample is sealed. The manifest records the run's coverage as
  of export time.
- The SPA continues to have exactly one git-tree call per snapshot; results shards are additional `raw`
  fetches (off-budget) fetched lazily per tradition/run.

## Solution Approaches

### Approach 1: Pre-aggregated per-tradition shards; SPA does only mean-of-means (RECOMMENDED)
**Description**: A Python export tool (reusing `workflows/analysis` aggregation) reads the merged run +
the two Opus layers, alias-normalizes Opus, and writes `results/<run-id>/manifest.json` plus one shard per
tradition. Each shard carries, per (subject × framing × scope × pressure-including-"all" × judge), the
tradition's breakdown **mean** and **coverage** (`n_judged`, `n_expected`), plus per-subject score
distributions. The SPA reads the shards and computes the leaderboard as the **equal-weight mean across the
seven tradition-means**; the drill-down just lists those tradition-means. Selectors/toggles pick which
precomputed slice to display.

**Pros**:
- Reconciliation is guaranteed — tradition-means come from the canonical aggregator, and mean-of-means was
  verified to equal the paper exactly.
- Tiny: ~a few thousand floats + counts per run → comfortably single-digit MB (likely << 1 MB core).
- Client math is trivial and pressure/framing/scope/judge are a fixed finite slice space, so no TS
  re-implementation of the aggregation convention is needed.
- Honest degradation falls out of the coverage counts already in each slice.

**Cons**:
- The slice space is fixed at export time; a genuinely new cross-cut (e.g. arbitrary per-scenario filtering)
  would need an export change. Mitigated: the issue's required cuts (judge/pressure/framing/scope, per
  tradition) are all covered, and per-scenario is a bounded SHOULD.

**Estimated Complexity**: Medium
**Risk Level**: Low

### Approach 2: Publish compact per-cell scores; SPA aggregates client-side
**Description**: Export a compact per-cell shard (subject, scenario, pressure, framing, scope, judge →
score) per tradition; re-implement the aggregation convention in TypeScript so the SPA computes every
breakdown live.

**Pros**:
- Maximum flexibility for future cross-cuts (per-scenario, custom groupings) with no re-export.

**Cons**:
- Must faithfully re-implement `aggregate.py`'s convention in TS and keep it in sync — direct reconciliation
  risk against the paper (the exact failure the "reconcile to displayed precision" acceptance guards).
- Larger: ~65k+ Gemini cells + Opus across seven traditions; feasible in single-digit MB only with a packed
  columnar layout, pushing complexity onto both writer and reader.

**Estimated Complexity**: High
**Risk Level**: Medium

### Approach 3: Hybrid — Approach 1 core + a bounded per-scenario layer
**Description**: Ship Approach 1 for the leaderboard/drill-down, and additionally emit per-scenario means at
the headline (and optionally per-framing) condition (mirroring `report.json.by_scenario`) for a scenario-level
drill-down, kept small by limiting the per-scenario cross-cut.

**Pros**: Adds scenario-level exploration without the full per-cell cost or the TS-aggregation reconciliation
risk.
**Cons**: More surface than the issue strictly requires; per-scenario across all framing×scope×pressure would
blow the size budget, so the cross-cut must be deliberately limited.
**Estimated Complexity**: Medium-High
**Risk Level**: Low-Medium

**Recommendation**: **Approach 1** for v1 (meets every acceptance criterion with guaranteed reconciliation
and the smallest reconciliation risk), with the **per-scenario layer of Approach 3 as an optional SHOULD**
if it fits the size budget. Approach 2 is not recommended because it puts the paper-reconciliation guarantee
at risk.

## Open Questions

### Critical (Blocks Progress)
- [ ] **Sample sealing**: `20260803-framings-opus-sample` is still tail-filling. The committed launch
      dataset must be regenerated once the architect confirms it is sealed. Do we commit an interim export
      now and refresh, or wait for the seal before the first commit? (Export is re-runnable either way.)

### Important (Affects Design)
- [ ] **Rationale/verdict text**: v1 excludes per-judgment `direction`/`rationale` to hold the size budget.
      Is a scenario-level verdict view (with rationale, lazily fetched from a separate layout) wanted later,
      or is aggregates-only acceptable indefinitely?
- [ ] **Run discovery UX**: default to the most recent run by manifest date, or expose a run selector across
      all `results/*/`? (Acceptance only requires that a new run *appears*; a selector is a SHOULD.)
- [ ] **Pressure="all" vs per-pressure means**: confirm the pooled "all" column is the cell-pooled mean
      (all pressures pooled within a tradition before the mean), matching the paper — not a mean of the six
      per-pressure means. (Export emits the pooled slice directly so the SPA never pools cells.)
- [ ] **Opus stated/guided in the leaderboard**: when judge=Opus and framing∈{stated,guided}, should those
      subjects still rank (badged sample) or be shown as "sample — not ranked"? Affects how the leaderboard
      presents partially-covered selections.

### Nice-to-Know (Optimization)
- [ ] Whether to also surface bootstrap CIs (from `stats_bundle.json`) in the UI, or only point estimates.
      CIs cannot be recomputed client-side cheaply; if wanted, the export would carry them for the pooled
      standings only.
- [ ] Whether to wire the per-scenario `ResultsRegion` seam on the scenario page as part of this work or
      leave it inert.

## Performance Requirements
- **API budget**: no material increase to the unauthenticated 60/hr GitHub budget — results reuse the one
  per-snapshot git-tree call; all shard/manifest content is fetched via `raw` (off-budget).
- **Payload size**: each run's committed dataset **single-digit MB total**, sharded per tradition so any one
  shard fetch is small (target: largest tradition shard well under ~1 MB).
- **Response time**: leaderboard renders from a small number of `raw` fetches (manifest + the needed shards)
  within interactive latency; switching selectors/toggles is client-side and instant (no refetch beyond the
  already-cached shards).
- **Resource usage**: negligible client memory (aggregates only, no transcripts).

## Security Considerations
- **Authentication**: none — public, read-only SPA reading public GitHub content; a client app holds no
  token (unauthenticated requests only).
- **Authorization**: N/A — all data is public benchmark output.
- **Data privacy**: results are model scores and metadata; **no transcripts** are published, so no risk of
  leaking scenario transcript content through the results layer.
- **Audit**: the committed dataset is versioned in git (the run-id + manifest date provide provenance).

## Test Scenarios

### Functional Tests
1. **Leaderboard reconciliation (happy path)**: given the launch shards, the leaderboard for each subject ×
   framing at scope=full / judge=Gemini / pressure=all equals the paper's standings to displayed precision.
2. **Judge switch**: selecting Opus recomputes every view from the normalized Opus judge; the alias split
   never surfaces as two judges; alias-normalized Opus counts equal the sum of the two source aliases with
   no double-count.
3. **Pressure filter**: selecting each of the six pressures (and "all") changes the standings/drill-down to
   the corresponding precomputed slice; "all" matches the cell-pooled convention.
4. **Framing & scope toggles**: unstated/stated/guided and turn1/full each select the correct slice;
   first-response vs post-pressure differ as expected (steadfastness = full − turn1 holds).
5. **Honest degradation (Opus sample)**: judge=Opus, framing=stated/guided shows the sample badge and
   coverage; a zero-coverage tradition is excluded from the mean-of-means, not counted as 0.
6. **Additive no-redeploy publish**: with a second `results/<run-id>/` present in the fake repo tree, the
   explorer lists/loads it without any code change; the corpus routes are unaffected.
7. **Missing/partial data**: a shard or manifest field absent renders an inline notice (display-first), not
   a crash; a 403 serves cached data + the rate-limit banner.

### Non-Functional Tests
1. **Size check**: the exported launch dataset is single-digit MB and each tradition shard is under the size
   target (a test/CI assertion on the committed output).
2. **Export parity**: the export's tradition-means match `report.json` / `stats_bundle.json` within numeric
   tolerance (self-check against the canonical aggregator).
3. **API-budget**: loading the explorer adds no new on-budget API calls beyond the existing git-tree poll
   (verified via the fake-fetch harness call log).

## Dependencies
- **External Services**: GitHub (`api.github.com` git-trees + `raw.githubusercontent.com`), read-only,
  unauthenticated — already the SPA's only dependency. Railway static hosting for deploy (manual `railway up`).
- **Internal Systems**: `workflows/analysis/analysis/aggregate.py` (+ `colors.py` palette) as the canonical
  aggregation/palette source; `workflows/judging` output schema (Spec 8) as the input contract; the
  `multibrowser` data layer (`src/lib/github.ts`, `queries.ts`, `filtering.ts`, `searchParams.ts`) and the
  reserved results seam (`results.ts`, `ScenarioResults`, `ResultsRegion`).
- **Libraries/Frameworks**: existing SPA deps (TanStack Router/Query, HeroUI v3, Tailwind 4, Vitest); Python
  `uv` toolchain for the export (consistent with `workflows/analysis` and the validator).

## References
- Issue #49 (this project) — feature definition, constraints, acceptance, PR strategy.
- `codev/specs/7-jaleesbrowser-browse-explore-m.md` + review — the corpus browser and the reserved,
  deferred results seam (§4.1).
- `codev/specs/26-workflows-analysis-port-jalees.md` — the analysis port: cell/breakdown/scope/steadfastness
  definitions, the `report.json` contract, numeric-only "no band names" rule, asymmetric-panel handling.
- `codev/resources/arch-critical.md` / `lessons-critical.md` — SPA shape, client-side GitHub data-layer
  rules, HeroUI v3 provider-less, multi-app porch checks.
- `workflows/analysis/analysis/aggregate.py`, `colors.py`; run-level `analysis-out/figures-report-v2/stats_bundle.json`
  (`subj_overall` = paper standings point estimates + CIs).
- External JaleesBench (`github.com/iaser-ai/jaleesbench`) — the explorer-feature reference the issue cites
  (not readable from this worktree; the standings convention was reconstructed and verified from launch data).

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Leaderboard drifts from the paper's numbers | Medium | High | Publish canonical tradition-means from `workflows/analysis`; SPA does only mean-of-means (verified exact); add an export-parity test against `report.json`/`stats_bundle.json`. |
| Export exceeds single-digit MB | Low | Medium | Aggregates-only, no transcripts/rationale in v1; per-tradition shards; a size assertion in CI; per-scenario layer gated on fitting the budget. |
| Opus alias double-counting | Medium | High | Normalize both aliases to one judge in the export; test that normalized counts == sum of source aliases; the SPA never sees two Opus judges. |
| Opus sample-only coverage presented as authoritative | Medium | High | Carry per-cell coverage in every slice; badge sample views, show `n_judged/n_expected`, exclude zero-coverage traditions (never 0). |
| `framings-opus-sample` still moving at export | High | Medium | Re-runnable export; regenerate the committed dataset once the architect seals the sample; manifest records coverage-as-of-export. |
| Breaking corpus browsing | Low | High | Additive routes/facets only; reuse existing data layer; keep existing tests green; new tests via `fakeFetch`/`renderApp`. |

## Expert Consultation
**Date**: (pending)
**Models Consulted**: (porch will run the 3-way spec consultation — Codex, Claude; Gemini per repo policy)
**Sections Updated**:
- (to be filled after consultation)

Note: All consultation feedback will be incorporated directly into the relevant sections above.

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- **Scope boundary**: the leaderboard/drill-down is a new top-level `/results` route family (with
  deep-linkable judge/pressure/framing/scope selectors, mirroring the corpus filter machinery). Wiring the
  per-scenario `ResultsRegion` seam on the scenario page is optional (Open Question) and not required for
  acceptance.
- **Why not per-cell in the SPA**: the paper-reconciliation acceptance is safest when the ranking statistic
  is computed by the canonical Python and the SPA does only an equal-weight mean — hence pre-aggregated
  shards rather than a TS re-implementation of the aggregation convention.
