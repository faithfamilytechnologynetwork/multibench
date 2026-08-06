# Plan: multibrowser /results leaderboard v2 — jaleesbrowser-style dense table, multi-faith

## Metadata
- **ID**: plan-2026-08-06-multibrowser-results-leaderboard-v2
- **Specification**: [codev/specs/55-multibrowser-results-leaderboa.md](../specs/55-multibrowser-results-leaderboa.md)
- **Status**: draft
- **Created**: 2026-08-06

## Executive Summary

This is a **UI + client-aggregation** rewrite of the `/results` leaderboard presentation (Spec 55,
Approach A). The #49 data tier (`results/<run-id>/` shards + manifest) and the Python exporter are
correct and **unchanged**; the pure aggregation in `lib/leaderboard.ts` is **reused** (its
`computeStandings` core is untouched) with additive helpers and **one structurally-compatible
signature decouple** (Phase 1, see below). Only the presentation and its URL/selection model are
rebuilt into the jaleesbrowser dense-table model, extended with a per-tradition heat strip for the
multi-faith dimension.

**Type-safety gate (consultation-driven).** The porch tests-check runs only `pnpm -C
apps/multibrowser test` (Vitest), and neither Vitest nor `vite build` (esbuild) typechecks — so a
type break would ship green. Every implement phase therefore adds `pnpm -C apps/multibrowser
check-types` (`tsc --noEmit`) to its acceptance as an explicit definition-of-done step. (I do **not**
modify the shared `.codev/checks/test.sh` dispatcher — that is #51-shared infra outside this scope;
the gap is flagged to the architect in Notes as a recommended follow-up.)

The work is confined to the `/results` leaderboard components + client aggregation (architect
constraint, coordinating with in-flight #51's raw-results tier — **no contact with #51's route
family or raw contract**):

- `apps/multibrowser/src/lib/leaderboard.ts` (+ `leaderboard.test.ts`) — additive pure helpers.
- `apps/multibrowser/src/lib/resultsSelection.ts` (+ `resultsSelection.test.ts`) — URL/selection model.
- `apps/multibrowser/src/routes/ResultsPage.tsx` (+ `routes/results.test.tsx`) — the presentation.
- `apps/multibrowser/README.md` + `results/README.md` — docs reconciliation.

Four phases, strict dependency chain: **(1)** pure client aggregation for the dense rows → **(2)**
dense sortable table + URL state (the presentation swap) → **(3)** the multi-faith layer (heat strip
+ drill-down + judge selector + accessibility) → **(4)** docs, #49 supersession, live verify. Each
phase leaves `pnpm -C apps/multibrowser test` green and is a single atomic commit.

**Key design decisions carried from the spec (do not re-litigate):** Gemini-only ranking; Opus is a
badged validation drill-down that never re-ranks; headline = the paper's published first-framing
slice (reconciles at `pressure=all`); Δ = shard **steadfastness** (matched-cell), not Post − Initial;
the heat strip is built from `computeStandings`'s returned `contributions` (so `mean(strip) == Post`
by construction); the whole table is scoped to one pressure (default `all`); no export change.

## Success Metrics
- [ ] All Spec 55 Success Criteria met (dense table; headline reconciles at `all`; Δ = shard
      steadfastness with a fixture distinctness test; framing staircase; heat strip == Post; sort +
      persistent canonical rank; pressure reframes the whole table + rank; drill-down + judge
      selector unchanged; accessibility; deep-linkable incl. stale/invalid-param degradation; no
      export change; additive publish; runtime validation preserved).
- [ ] `pnpm -C apps/multibrowser test` **and** `pnpm -C apps/multibrowser check-types` green, with an
      explicit new test for each new behavior (the package configures no coverage provider —
      suite-green + typecheck + new tests replaces a coverage-% gate; the porch check runs only
      Vitest, which does not typecheck, so `check-types` is a per-phase definition-of-done step).
- [ ] No new on-budget GitHub API calls beyond the existing git-tree poll (fake-fetch call-log).
- [ ] Live `railway up` smoke: the dense board loads, sorts, deep-links, and drills down on the
      deployed static site.
- [ ] Documentation updated (multibrowser README leaderboard section; `results/README.md` "Results
      explorer" bullets reconciled to the v2 presentation).
- [ ] No regression to corpus browsing or the #49 data tier; no contact with #51's raw tier.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Client aggregation for the dense rows (pure lib + tests)"},
    {"id": "phase_2", "title": "Dense sortable table + URL state (presentation swap)"},
    {"id": "phase_3", "title": "Multi-faith layer: heat strip, drill-down, judge selector, a11y"},
    {"id": "phase_4", "title": "Docs, #49 supersession, live verify"}
  ]
}
```

## Phase Breakdown

### Phase 1: Client aggregation for the dense rows (pure lib + tests)
**Dependencies**: None

#### Objectives
- Provide the pure, tested functions the v2 table renders from — a dense per-subject row (Initial /
  Post / Δ headline + per-framing `full` columns + a manifest-aligned per-tradition heat strip), a
  canonical-rank + sort ordering, and a per-tradition dense drill-down row — **reusing** the existing
  `computeStandings` so reconciliation holds by construction.
- Decouple the aggregation-slice type from `ResultsSelection` *now* (before Phase 2 removes fields
  from `ResultsSelection`), so the Phase-2 selection change cannot silently break `leaderboard.ts`.

#### Deliverables
- [ ] **Signature decouple (the only edit to existing code):** introduce
      `interface Slice { framing: string; metric: Metric; pressure: string }` in `leaderboard.ts`
      and change both `computeStandings` (line ~88) and `subjectTraditionValues` (line ~66) from
      `Pick<ResultsSelection, "framing" | "metric" | "pressure">` to `Slice`. This is structurally
      compatible — every existing caller (ResultsPage, tests) still passes a matching object — so
      behavior is unchanged, but `leaderboard.ts` no longer depends on those `ResultsSelection`
      fields that Phase 2 removes.
- [ ] New exports in `apps/multibrowser/src/lib/leaderboard.ts`:
  - `LeaderboardRow` type:
    `{ subject, initial: number|null, post: number|null, delta: number|null,
       byFraming: Record<string, number|null>,   // keyed by framing id (sort/label resolve by id)
       strip: { tradition: string; value: number|null; nJudged: number; nExpected: number }[],  // 1:1 with manifest.traditions, in manifest order
       rank: number }`.
  - `computeLeaderboardRows(shards, manifest, { pressure, judgeModel? })`: one row per subject —
    `initial` = first-framing `turn1`, `post` = first-framing `full`, `delta` = first-framing
    `steadfastness` (metric='steadfastness'); `byFraming[framingId]` = `full` at that framing; `rank`
    = canonical position by `post` desc, nulls last, ties by subject id (computed once, attached to
    every row).
  - `sortRows(rows, sortKey, dir)`: pure sort over the numeric columns (`initial|post|delta|` a
    framing id); nulls last both directions; ties by subject id; leaves `rank` untouched (rank is a
    field, not the display index). `sortKey` for a framing column is the framing **id** (resolved
    against `byFraming`), so no manifest/order threading is needed.
  - `subjectDrilldownRows(shards, manifest, subject, { pressure, judgeModel })`: per included
    tradition, `{ tradition, initial: number|null, post: number|null, delta: number|null,
    byFraming: Record<string, number|null>, nJudged, nExpected }`. **A tradition is included iff it
    has any non-null value across the displayed slices**; nullable numeric fields cover the sampled
    Opus case (e.g. `full` present but `steadfastness` absent); the coverage badge `nJudged/nExpected`
    is sourced from the **Post slice** (first-framing `full`).
- [ ] New/updated tests in `apps/multibrowser/src/lib/leaderboard.test.ts` (fixtures + the committed
      launch shards already imported there). Existing cases updated only for the `Slice` rename if
      referenced.

#### Implementation Details
- Reuse `computeStandings(shards, manifest, Slice, judgeModel)` for every numeric column; the only
  new client math is field assembly and ordering — **no new re-implementation of the aggregation
  convention** (the reconcile-by-construction lesson).
- **Heat strip (manifest-aligned):** take the Post-slice (`framing=framings[0]`, `metric=full`)
  `computeStandings` result's sparse `contributions`, then **left-join against
  `manifest.traditions`** to produce the 1:1 `strip` array — covered traditions carry their value,
  uncovered traditions carry `value: null` (the distinct empty cell the spec requires). `post` is the
  equal-weight mean over the **non-null** strip cells, so `mean(non-null strip) == post` by
  construction (same iteration source, sparse contributions unchanged — the join only *adds* the
  null placeholders for display).
- Δ column: `computeStandings(..., {framing:framings[0], metric:'steadfastness', pressure})`. On the
  complete Gemini grid this equals `full − turn1`; the distinctness from Post − Initial is a
  property of *asymmetric matched panels*, exercised by a fixture (see Test Plan), not launch data.
- All functions are judge-parameterized; the leaderboard body always passes the ranking (full-grid)
  judge, matching the Gemini-only ranking policy. `judgeModel` is threaded only for the drill-down.

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser check-types` is green (the `Slice` decouple + new types typecheck).
- [ ] `computeLeaderboardRows` on the committed launch shards reproduces, for each subject at
      `pressure=all`, `post` == the paper `subj_overall` (first framing) to the existing test's
      precision; the mean over non-null `strip` cells == `post`.
- [ ] The `strip` array is 1:1 with `manifest.traditions` in manifest order; an uncovered tradition
      is a `value: null` cell (not omitted).
- [ ] Δ distinctness holds on a **synthetic asymmetric-panel fixture** (steadfastness set
      independently of full/turn1 via the existing `shard(...)` helper) and a companion assertion
      documents the coincidence on real Gemini data.
- [ ] `sortRows` orders by each numeric key incl. a framing id (desc & asc), nulls last both ways,
      ties by subject id; `rank` is unchanged by sorting.
- [ ] `subjectDrilldownRows` includes a tradition iff any displayed slice is non-null, returns
      nullable per-slice fields (Opus-sample case), and sources `n/N` from the Post slice.
- [ ] All tests pass; existing `leaderboard.test.ts` behavior is preserved (only the `Slice` rename
      touches existing lines).

#### Test Plan
- **Unit Tests**: reconciliation (launch shards); mean(non-null strip)==post (fixture + launch);
  strip 1:1 with manifest incl. a null cell for an uncovered tradition; Δ=steadfastness distinctness
  (fixture) + real-data coincidence; sort ordering by each numeric key incl. a framing id
  (nulls/ties); canonical-rank stability under sort; drill-down inclusion rule + nullable Opus-slice
  fields + Post-slice coverage source.
- **Type check**: `pnpm -C apps/multibrowser check-types` green (the `Slice` decouple).
- **Integration Tests**: none (pure lib).
- **Manual Testing**: none.

#### Rollback Strategy
Revert the single Phase-1 commit; the `Slice` rename is structurally identical to the old `Pick`, and
the new exports are additive, so nothing else depends on them yet.

#### Risks
- **Risk**: strip/post divergence if contributions are re-derived independently.
  - **Mitigation**: strip is the Post `computeStandings().contributions` left-joined to the manifest;
    the mean is over the unchanged non-null cells (join only adds null placeholders).
- **Risk**: the `Slice` rename subtly changes a caller's inferred type.
  - **Mitigation**: `Slice` is structurally identical to the removed `Pick`; `check-types` in this
    phase proves every caller still compiles.

---

### Phase 2: Dense sortable table + URL state (presentation swap)
**Dependencies**: Phase 1

#### Objectives
- Replace the #49 one-slice selector table with the **dense sortable board**: one row per subject
  with Initial / Post / Δ headline columns + one `full` column per framing, a single top-level
  **pressure** selector (default `all`) that reframes the whole table **and** the canonical rank,
  click-to-sort numeric columns, a persistent canonical Rank column, and `k/N` coverage per row.
- Move framing/metric out of the selection (they are now columns) and add **sort + expanded** to the
  deep-linkable URL; ignore stale `?metric=`/`?framing=` and invalid sort keys.
- Heat strip + drill-down + judge selector land in Phase 3. This phase's commit is an **intermediate,
  internally-consistent** state (a sortable Gemini board with no per-tradition drill-down); it is not
  user-visible until the PR merges, so the temporary removal of the #49 drill-down/judge is not a
  shipped regression — the multi-faith layer returns in Phase 3 before the PR.

#### Deliverables
- [ ] `apps/multibrowser/src/lib/resultsSelection.ts`: new `ResultsSelection` shape —
      `{ runId, judge, pressure, sort: { key, dir } | null, expanded: string[] }` (drop `framing`,
      `metric`). Update `DEFAULTS`, `parseResultsSelection` (validate `sort.key` against the fixed
      numeric-column set + framing ids from the manifest; unknown/stale keys → null/ignored),
      `selectionToResultsSearch` (omit defaults; encode `sort` as e.g. `sort=post.desc`, `expanded`
      as a comma list), and `resultsSearchSchema` (unchanged fail-soft record). Keep `judge` in the
      shape (used by the Phase-3 drill-down) even though its selector UI returns in Phase 3.
- [ ] `apps/multibrowser/src/lib/resultsSelection.test.ts`: round-trip run/judge/pressure/sort/
      expanded; clean base URL; stale `?metric=`/`?framing=` dropped; invalid sort key → no sort.
- [ ] `apps/multibrowser/src/routes/ResultsPage.tsx`: rewrite the table to render
      `computeLeaderboardRows` → `sortRows` → sortable dense columns (`byFraming` keyed by framing
      id); pressure selector reframes via `update()`; Rank column from `row.rank`; sort state from
      the URL; `k/N` from the count of non-null `strip` cells over `manifest.traditions.length`.
      Keep the run label, notices, rate-limit banner, and runtime-validation paths. **Remove**, as
      one clean unit, the #49 Framing selector, Metric selector, judge selector, drill-down, **and
      the `opus-caption` block (ResultsPage.tsx:195)** — all return (except metric/framing) in
      Phase 3; leaving `opus-caption` pointing at a removed drill-down would be incoherent.
- [ ] `apps/multibrowser/src/routes/results.test.tsx`: rewrite the existing fixture-driven tests to
      the v2 columns (the current 12 tests — standings, run label, metric-change, deep link, framing,
      pressure, steadfastness, malformed-manifest notice, drill-down, judge selector, empty state —
      are re-scoped: metric/framing/drill-down/judge tests move to Phase 3 or become column/sort
      tests here). Add: sort-by-column, persistent-rank, pressure-reframe, stale-param-degradation,
      and a **new** API-budget call-log assertion (Success Metric 3 lands here). Keep the
      malformed-manifest notice and empty-state cases.

#### Implementation Details
- The page becomes a thin driver over Phase-1 pure functions: parse selection → `computeLeaderboardRows`
  → `sortRows` for display → render. Column headers are buttons toggling `sort` in the URL
  (desc→asc), with `aria-sort`.
- Framing column labels come from `manifest.framings` (declared order), not hardcoded — a
  `FRAMING_LABEL` lookup with the id as fallback (matches the data-driven assumption). Note the
  **`Post` headline column and the first-framing (`framings[0]`) breakdown column are the same
  number by definition** (inherited from the reference design) — a visual grouping/caption makes this
  explicit so it does not read as a bug.
- Reuse the existing `Segmented` control for the pressure selector and `ScoreCell`
  (`scoreColor`/`scoreTextColor`) for numeric cells; Δ cells reuse the same ramp (clamps at ±1).
- **Validation coverage note:** malformed/missing-data and 403/rate-limit handling live in the data
  layer (`results.data.test.ts`) and its query path, which are unchanged — so those are *preserved by
  not touching them*, not re-asserted at the page here. The page-level test keeps the
  malformed-manifest **notice-render** case (which already exists in `results.test.tsx`).

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser check-types` green.
- [ ] At `pressure=all`, the page renders each subject's Post at the paper value to **displayed
      precision** — asserted as a formatting test over fixture rows whose Post equals known paper-like
      values (the exhaustive real-shard reconciliation stays in the Phase-1 lib test; the page test
      only proves the correct field is rendered at the right precision, no full-shard fake-fetch
      fixture rebuild).
- [ ] Clicking a numeric header sorts the display; the Rank column keeps canonical numbers; nulls
      last; a stale `?metric=`/`?framing=` or bad `?sort=` renders the default view without error.
- [ ] Selecting each pressure (and `all`) reframes headline + framing columns + rank.
- [ ] Loading the board adds no new on-budget GitHub API call beyond the git-tree poll (fake-fetch
      call-log assertion).
- [ ] Corpus routes and the data-layer notice/rate-limit behavior are unchanged.

#### Test Plan
- **Unit Tests**: `resultsSelection` parse/serialize (sort/expanded/stale/invalid).
- **Integration Tests**: `results.test.tsx` render — v2 columns, sort, persistent rank, pressure
  reframe, display-precision formatting, stale-param degradation, API-budget call-log, malformed-
  manifest notice, empty state.
- **Type check**: `pnpm -C apps/multibrowser check-types`.
- **Manual Testing**: deferred to Phase 4 (live smoke).

#### Rollback Strategy
Revert the Phase-2 commit; Phase-1 exports remain (unused) and the suite returns to the #49 board.

#### Risks
- **Risk**: selection-shape change ripples to the page and both test files in one phase.
  - **Mitigation**: Phase 1 already decoupled `leaderboard.ts` via `Slice`, so the only consumers of
    the removed fields are the page and its tests — which are this phase's deliverables; `check-types`
    proves nothing else breaks.
- **Risk**: sort accidentally re-numbers rank.
  - **Mitigation**: rank is a computed field rendered directly (not the array index); test pins it.
- **Risk**: `opus-caption` left live pointing at a removed drill-down.
  - **Mitigation**: it is removed in the same clean unit as the drill-down/judge selector (deliverable
    above); a test asserts it is absent in Phase 2.

---

### Phase 3: Multi-faith layer — heat strip, drill-down, judge selector, accessibility
**Dependencies**: Phase 2

#### Objectives
- Add the **per-tradition heat strip** (the multi-faith upgrade) to each row, the **click-to-expand
  per-tradition drill-down**, the **drill-down judge selector** (Opus badged, never re-ranks), and
  the full **accessibility** affordances.

#### Deliverables
- [ ] `apps/multibrowser/src/routes/ResultsPage.tsx`:
  - Heat strip column: one `scoreColor` cell per `row.strip` entry (already 1:1 with
    `manifest.traditions`, manifest order), each with a `title`/`aria-label` (tradition + value or
    "no data"); a `value: null` entry renders as the visually distinct neutral empty cell (`scoreColor`
    already returns neutral grey for null).
  - Expandable rows: a keyboard-operable button (`aria-expanded`) toggling `sel.expanded` (URL-encoded)
    that renders `subjectDrilldownRows` as a per-tradition dense sub-table (per-tradition
    Initial/Post/Δ + each framing's `full`, coverage-badged).
  - Re-add the **judge selector** (`Segmented`) — repoints only the drill-down to Opus where data
    exists (badged `sample n/N`); the headline/strip stay on the ranking (Gemini) judge.
  - Wrap the table in a horizontal-scroll container (`overflow-x-auto`) for narrow viewports.
- [ ] `apps/multibrowser/src/routes/results.test.tsx`: heat-strip==Post + labels + empty-cell;
      expand/collapse (keyboard) + URL round-trip of `expanded`; judge selector repoints drill-down
      only (headline/strip unchanged) + `sample n/N` badge + zero-coverage tradition shows nothing;
      scroll-container present.

#### Implementation Details
- The strip reads `row.strip` directly (Phase-1 manifest-aligned; `mean(non-null)==post`); no new
  aggregation in the component.
- The drill-down judge model resolves via `judgeModelForKey(manifest, sel.judge)`; the headline and
  strip always use `rankingJudgeModel(manifest)` regardless of `sel.judge` — a test asserts switching
  the judge leaves headline/strip cells byte-identical.
- Expansion state is a set of subject ids serialized to the URL (`expanded=a,b`); parsing tolerates
  unknown ids (ignored).

#### Acceptance Criteria
- [ ] `pnpm -C apps/multibrowser check-types` green.
- [ ] Strip cells == the `row.strip` values with accessible labels; empty (`null`) cells are
      neutral-distinct and labeled "no data".
- [ ] Expanding a subject (mouse and keyboard) shows the per-tradition dense table and round-trips
      through the URL.
- [ ] Switching the judge repoints only the drill-down (badged), never the headline/strip/rank.
- [ ] Table scrolls horizontally on a narrow viewport (scroll wrapper asserted).

#### Test Plan
- **Unit Tests**: none new (pure math is Phase 1).
- **Integration Tests**: `results.test.tsx` — strip, labels, expand (keyboard), judge repoint,
  sample badge, zero-coverage omission, scroll wrapper.
- **Manual Testing**: deferred to Phase 4.

#### Rollback Strategy
Revert the Phase-3 commit; the Phase-2 sortable board remains fully functional.

#### Risks
- **Risk**: judge selector leaks into the headline/strip.
  - **Mitigation**: headline/strip hardwired to `rankingJudgeModel`; a test asserts invariance.
- **Risk**: color-only strip inaccessible.
  - **Mitigation**: per-cell `title`/`aria-label` + non-color empty state + keyboard expansion.

---

### Phase 4: Docs, #49 supersession, live verify
**Dependencies**: Phase 3

#### Objectives
- Reconcile documentation to the v2 presentation, record the #49 supersession, and verify the real
  user path on the deployed static site.

#### Deliverables
- [ ] `apps/multibrowser/README.md`: leaderboard section describes the dense sortable table + heat
      strip + drill-down + pressure/judge/sort deep-linking.
- [ ] `results/README.md`: the "Results explorer (SPA)" bullets updated from the #49 selector model
      to the v2 dense-table model (framing/metric are columns; pressure is the single reframing
      selector; Gemini-ranked; Opus drill-down; heat strip).
- [ ] Note in the review/PR that this **supersedes the #49 presentation**; **#49 is closed and its
      parked `verify-approval` gate retired** when this lands (architect action — flagged, not done
      unilaterally).
- [ ] Live `railway up` smoke (manual): board loads, sorts, pressure reframes, a row expands, a
      deep-link restores state — on the deployed site.

#### Implementation Details
- Docs-only + manual verify; no code changes expected (any bug found reopens the relevant phase's
  concern as a fix commit).

#### Acceptance Criteria
- [ ] Both READMEs reflect the v2 presentation with no stale #49 selector language.
- [ ] Live smoke passes; screenshots/notes captured in the review.
- [ ] Final `pnpm -C apps/multibrowser test` **and** `pnpm -C apps/multibrowser check-types` green.

#### Test Plan
- **Unit/Integration Tests**: full suite green (regression).
- **Manual Testing**: the live `railway up` smoke above.

#### Rollback Strategy
Docs revert trivially; the live deploy is a static site (redeploy previous bundle if needed).

#### Risks
- **Risk**: live behavior diverges from tests (rate-limit/edge).
  - **Mitigation**: the smoke exercises the real GitHub-at-runtime path; notices/banner already tested.

---

## Dependency Map
```
Phase 1 (pure aggregation)
   └─→ Phase 2 (dense table + URL state)
          └─→ Phase 3 (heat strip + drill-down + judge + a11y)
                 └─→ Phase 4 (docs + supersession + live verify)
```

## Resource Requirements
### Development Resources
- **Engineers**: this builder (spir-55); familiarity with the multibrowser SPA + #49 results tier.
- **Environment**: existing pnpm/Vitest toolchain; Railway for the manual deploy smoke.

### Infrastructure
- N/A — no database, service, or config changes; reuses the committed `results/` data and the
  existing static-site deploy.

## Integration Points
### External Systems
- **GitHub (git-trees + `raw`)**: read-only, unauthenticated — unchanged; the leaderboard adds no
  on-budget calls. **Phase**: all (runtime data). **Fallback**: cached data + rate-limit banner
  (already implemented).
- **Railway static hosting**: **Phase**: 4 (manual `railway up` smoke). **Fallback**: redeploy prior
  bundle.

### Internal Systems
- **`lib/leaderboard.ts` / `computeStandings`**: reused as the aggregation source (Phase 1 builds on it).
- **`lib/resultsSelection.ts`**: extended for sort/expanded (Phase 2).
- **`results/<run-id>/` data tier (#49)**: consumed unchanged; **no export change**.
- **#51 raw-results tier**: **no contact** — different route family/contract; rebase discipline at PR.

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Headline drifts from the paper | Low | High | Reuse `computeStandings`; keep reconciliation test at `all` | spir-55 |
| Δ computed as Post − Initial | Med | High | Δ = shard steadfastness; fixture distinctness test | spir-55 |
| Strip mean ≠ Post | Low | Med | Strip = Post `contributions` (single source); test `mean(strip)==post` | spir-55 |
| Sort re-numbers rank | Med | Med | Rank is a computed field, rendered directly; test | spir-55 |
| Judge selector recolors/reranks headline | Med | High | Headline/strip hardwired to ranking judge; invariance test | spir-55 |
| Color-only strip inaccessible | Med | Med | Per-cell aria/title + non-color empty + keyboard expand + scroll wrapper | spir-55 |
| Merge conflict with #51 in shared app files | Med | Med | Scope to `/results` leaderboard + selection; rebase on integration branch at PR | spir-55 |
| A needed shard slice turns out missing | Low | Med | Default no export change; escalate to architect before any export work | spir-55 |

### Schedule Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| N/A — no time estimates (AI-age; measured by completed phases) | — | — | — | — |

## Validation Checkpoints
1. **After Phase 1**: pure functions reconcile + strip==Post + Δ fixture + sort/rank — all green.
2. **After Phase 2**: dense sortable board renders, sorts, reframes by pressure, deep-links; stale
   params degrade; corpus untouched.
3. **After Phase 3**: heat strip + drill-down + judge selector + accessibility all behave per spec.
4. **Before "done" (Phase 4)**: docs reconciled; live `railway up` smoke passes; full suite green.

## Monitoring and Observability
### Metrics to Track
- N/A — client-only read-only SPA; no server metrics. (The existing rate-limit banner is the only
  runtime health signal, unchanged.)
### Logging Requirements
- N/A — no new logging; runtime data problems surface as inline notices (existing behavior).
### Alerting
- N/A.

## Documentation Updates Required
- [ ] `apps/multibrowser/README.md` — v2 leaderboard section.
- [ ] `results/README.md` — "Results explorer (SPA)" bullets reconciled.
- [ ] Review doc (`codev/reviews/55-*.md`) — lessons + #49 supersession note.
- [ ] N/A: API docs, architecture diagrams, runbooks, config guides (none apply to this UI change).

## Post-Implementation Tasks
- [ ] Live `railway up` smoke (Phase 4).
- [ ] Flag #49 closure + `verify-approval` retirement to the architect (their action).
- [ ] N/A: security audit, load testing (public read-only client feature; no new attack surface).

## Expert Review
**Date**: 2026-08-06
**Model**: Codex + Claude (2-way; Gemini's per-phase consult can't see the worktree here).

**Plan iteration 1 (both REQUEST_CHANGES, HIGH — all incorporated):**
- **Type-coupling break** (both, verified): `leaderboard.ts:66,88` use `Pick<ResultsSelection,
  "framing"|"metric"|"pressure">`, which Phase 2's field removal breaks — and neither the porch check
  (Vitest-only) nor `vite build` typechecks, so it ships silently. → Phase 1 now decouples to a
  `Slice` interface *before* Phase 2, and every phase adds `pnpm … check-types`. Flagged the
  dispatcher gap to the architect (Notes).
- **`byFraming` positional array can't resolve `framing:<id>` sort** (Codex): → changed to an
  id-keyed `Record<string, number|null>`; `sortRows` resolves a framing column by id.
- **Heat-strip shape self-contradiction** (Claude): sparse `contributions` can't yield the required
  empty cell for an uncovered tradition. → Phase 1 now emits a manifest-aligned `strip` (1:1 with
  `manifest.traditions`, `value: null` for uncovered); mean over non-null == post.
- **`subjectDrilldownRows` underspecified for the Opus sample path** (Claude): → nullable per-slice
  fields; inclusion = any non-null across displayed slices; coverage from the Post slice.
- **Test-plan cited non-existent "kept" tests** (Claude): additive-publish and 403/rate-limit page
  tests don't exist (validation lives in `results.data.test.ts`). → Phase 2 no longer "keeps" them;
  page reconciliation reduced to a display-precision formatting test (exhaustive reconciliation stays
  in the Phase-1 lib test); the API-budget call-log assertion is now explicitly owned by Phase 2.
- **Mid-branch removal of drill-down/judge with `opus-caption` left live** (Claude): → Phase 2 removes
  the `opus-caption` block in the same clean unit; the phase commit is framed as an intermediate,
  non-shipped state (nothing user-visible until the PR merges); drill-down/judge return in Phase 3.
- **`Post` == `framings[0]` column identity** (Claude): → noted as a visual grouping/caption so it
  doesn't read as a bug.

**Plan Adjustments**: phases ordered so the pure aggregation (with the reconciliation/Δ/strip
guarantees + the `Slice` decouple) lands first and is verified before any UI consumes it; the
multi-faith + accessibility layer is isolated in Phase 3 so it can be reviewed as the distinct "new
design work."

## Approval
- [ ] Technical Lead Review
- [ ] Engineering Manager Approval
- [ ] Resource Allocation Confirmed
- [ ] Expert AI Consultation Complete

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-08-06 | Initial implementation plan | Spec 55 approved | spir-55 |
| 2026-08-06 | Plan iter-1 review incorporated (Slice decouple + check-types gate; id-keyed byFraming; manifest-aligned strip; nullable drill-down; test-plan corrections; opus-caption removal) | Codex + Claude REQUEST_CHANGES | spir-55 |

## Notes
- **Recommended follow-up for the architect (out of scope for #55):** the porch tests-check
  (`.codev/checks/test.sh`) runs only `pnpm -C apps/multibrowser test` (Vitest), which does not
  typecheck, and neither does `vite build` (esbuild). A pure-type break therefore passes the porch
  gate silently. This plan defends against it *within* #55 by (a) decoupling `leaderboard.ts` from the
  changing `ResultsSelection` fields in Phase 1 and (b) making `check-types` a per-phase
  definition-of-done. A durable fix — adding `check-types` to the multibrowser branch of the shared
  dispatcher — would benefit #51 and all future multibrowser builders, but it is #51-shared infra
  outside this project's scope; flagged here for the architect to decide.
- **Phase-2 file count**: the selection-shape change and the page rewrite ship in one phase because a
  TS type change forces its consumer update — splitting them would leave an intermediate red suite.
  It is still one coherent unit (the presentation swap), 4 files, within the "single atomic commit"
  intent. Phase 1's `Slice` decouple ensures the *only* consumers of the removed fields are the page
  and its tests (both Phase-2 deliverables).
- **Scope discipline**: every change is inside the `/results` leaderboard components + client
  aggregation. No touching of `results/` data/export, the `traditions/` corpus browser, or #51's raw
  tier — rebase on the integration branch before opening the PR (architect reminder, 2026-08-06).
- **Supersession**: on landing, this replaces #49's presentation; #49 is closed and its parked
  `verify-approval` gate retired (architect action, flagged in Phase 4).
