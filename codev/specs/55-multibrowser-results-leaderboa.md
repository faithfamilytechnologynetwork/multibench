# Specification: multibrowser /results leaderboard v2 — jaleesbrowser-style dense table, multi-faith

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Implementation phases, file paths, and code belong in codev/plans/55-*.md.
-->

## Metadata
- **ID**: spec-2026-08-06-multibrowser-results-leaderboard-v2
- **Status**: draft
- **Created**: 2026-08-06

## Clarifying Questions Asked

No spec file existed at spawn, and the issue (#55) plus the reference design and the committed #49
data tier already fix the key decisions, so no live questions were put to the user. The questions
this spec had to resolve, and how they were resolved from the issue + real reference code + data:

- **Q: What exactly is being replaced — the data or the presentation?**
  A: The **presentation only**. Issue: "Replace the #49 /results leaderboard PRESENTATION … The
  #49 DATA tier + export stay — this is UI + client aggregation only." Verified: the committed
  shards (`results/20260803/`) already carry every slice the new table needs (see Current State),
  so **no export change is required**.
- **Q: What is the jaleesbrowser model, concretely?**
  A: Read `taqwabench/apps/jaleesbrowser/src/{leaderboard.ts,components/Leaderboard.tsx}`. One row
  per subject; headline **Initial / Post / Δ** columns computed on the paper's published slice
  (the first declared breakdown-axis value — here **unstated** — never pooled across framings);
  per-framing breakdown columns alongside; every column click-to-sort; a **canonical Rank column
  that persists while sorted**; nulls last; click a row → subject drill-down.
- **Q: How is "Δ / steadfastness" defined in the headline?**
  A: The issue is explicit: "Steadfastness = the matched-cell Δ definition from #49's export
  (already in the shards)." So the Δ column is the mean of per-tradition **steadfastness** values
  (matched-cell `full − turn1`), **not** (Post − Initial). Those differ because Post and Initial
  are means over possibly-different matched cells (the #49 asymmetric-panel lesson).
- **Q: How does MultiBench's extra tradition dimension (7) get shown "at a glance"?**
  A: This is the new design work the issue asks the spec to explore. Three candidate shapes are
  evaluated in Solution Approaches (expandable rows / tradition-columns toggle / per-tradition heat
  strip); the recommendation is the **heat strip + click-to-expand drill-down** hybrid.
- **Q: What ranking / judge policy carries over from #49?**
  A: Unchanged: **Gemini-only ranking**; **Opus is a badged validation layer that never
  re-ranks**; headline numbers are the paper's published slice (Gemini, mean of per-tradition
  means) and reconcile to displayed precision.
- **Q: Does deep-linkable state still apply?**
  A: Yes, extended: sort column + direction and row-expansion state join the existing URL-encoded
  selection (run / judge / pressure).

## Problem Statement

The #49 `/results` leaderboard presents standings **one metric slice at a time**: four segmented
selectors (Framing, Metric, Pressure, Drill-down judge) pick a single (framing × metric × pressure)
slice, and the table shows just that slice's per-subject score plus a `k/N` traditions count, with
an expandable per-tradition drill-down. To compare a subject's first-response vs post-pressure
score, or to see the framing staircase (unstated → stated → guided), a reader must click through
selector combinations and hold the numbers in their head.

Waleed's judgement (2026-08-06): *"'49 I don't like it. I liked the jaleesbench leaderboard much
more, but we need to upgrade it to multi-faith."* The JaleesBench browser's leaderboard shows the
**whole picture at a glance** — a dense summary table where each subject's Initial / Post / Δ and
its per-framing staircase are all visible in one row, sortable by any column, with a persistent
canonical rank. MultiBench needs that model, **extended** with its extra dimension: 7 traditions.

This is a **UI + client-aggregation** change. The committed results dataset, the Python exporter,
and the pure client aggregation functions from #49 are correct and stay; only the leaderboard
presentation (and the selection/URL model that drives it) is rebuilt.

## Current State

- **Data tier (#49, committed, unchanged):** `results/20260803/` holds `manifest.json` + one shard
  per tradition (7 traditions, 5 subjects, 2 judges: full-grid `gemini-3.6-flash`, sampled
  `claude-opus-4-8`). Each shard carries
  `means[judge][subject][framing][scope∈{turn1,full}][pressure(+"all")] = [mean, n_judged, n_expected]`
  and `steadfastness[judge][subject][framing][pressure(+"all")] = [value, matched_n]`. **Every
  slice the jaleesbrowser headline needs (unstated turn1, unstated full, unstated steadfastness,
  and each framing's full) is already present** — verified against the committed shards.
- **The SPA (`apps/multibrowser/`, Vite 6 / React 19 / TS / Tailwind 4 / HeroUI v3 / TanStack
  Router+Query)** reads GitHub at runtime (SHA-pinned git-trees + `raw`), browsing both the corpus
  and the `results/` datasets. A `/results` route exists.
- **The #49 leaderboard presentation (`routes/ResultsPage.tsx`):** four single-select segmented
  controls (Framing / Metric / Pressure / Drill-down judge) drive a one-slice table (#, Subject,
  Score, Traditions `k/N`) with expandable per-tradition drill-down. This is the presentation being
  replaced.
- **Reusable pure aggregation (`lib/leaderboard.ts`):** `computeStandings`,
  `subjectTraditionValues`, `traditionValue`, `rankingJudgeModel`, `judgeModelForKey` — the SPA's
  only cross-tradition statistic is the equal-weight mean of per-tradition means, which reconciles
  with the paper's `tab_standings` by construction. These functions are correct and are reused.
- **Selection/URL machinery (`lib/resultsSelection.ts`):** parses/serializes a single-select
  selection (run / judge / framing / metric / pressure) to a clean deep-linkable search record.
  Framing and metric currently exist as *selectors*; in the new model they become *columns*.
- **Palette (`lib/scoreColor.ts`):** the numeric −1…+1 `scoreColor` / `scoreTextColor` ramp — used
  as-is; **no band names** anywhere.
- **In-flight sibling #51 (raw-results browser):** a separate route family with its own raw
  per-scenario contract; the #49 score/leaderboard tier stays MultiBench-specific and is not part
  of #51's generic contract. Shared app, different files/routes.

## Desired State

A **dense, at-a-glance leaderboard** at `/results`, one row per subject, replacing the
selector-driven one-slice table:

- **Headline columns — Initial / Post / Δ**, computed on the paper's published slice: the **first
  framing (unstated)** only, at `pressure="all"`, Gemini judge. `Initial` = unstated `turn1`,
  `Post` = unstated `full`, `Δ` = unstated **steadfastness** (matched-cell, read from the shard —
  *not* Post − Initial). Each is the equal-weight mean of the per-tradition means (the #49
  statistic), so `Post` reconciles with the paper's `subj_overall` to displayed precision.
- **Per-framing breakdown columns — Unstated / Stated / Guided**, each the `full` (post-pressure)
  mean-of-per-tradition-means at that framing (the framing staircase), Gemini judge, `pressure="all"`.
- **The multi-faith upgrade — a per-tradition heat strip in each row**: 7 small `scoreColor`-ramped
  cells (one per tradition, manifest order) showing that subject's per-tradition contributions to
  the **Post** headline. The strip's mean *is* the Post column (reconciles by construction) and
  makes tradition spread visible without expanding. Traditions with no coverage render as an empty
  cell, never a 0.
- **Click a row → subject drill-down**: the full per-tradition table for that subject (reusing the
  #49 drill-down data path), showing exact per-tradition values with coverage badges. The
  **drill-down judge selector** (Opus, badged as validation) repoints only the drill-down, exactly
  as in #49 — it never re-ranks or recolors the Gemini-ranked headline/strip.
- **Sortable by any column** (Initial / Post / Δ / each framing), ascending/descending. A
  **canonical Rank column** (rank by the unstated `full` score descending — the paper's published
  ordering) **persists while sorted**, so re-sorting never re-numbers the ranking. **Nulls sort
  last** in every order.
- **Pressure remains a single top-level selector** (default `"all"`) that reframes the whole table
  (headline + framing columns + strip recompute at the chosen pressure). This keeps the pressure
  cross-cut without returning to one-slice-at-a-time browsing. The **Metric selector is removed**
  (metric is now the three headline columns); the **Framing selector is removed** (framing is now
  the three breakdown columns and the fixed unstated headline).
- **Deep-linkable state (URL):** run, pressure, drill-down judge, **sort (column + direction)**, and
  **expanded subject(s)** are all encoded in the search params; defaults are omitted for a clean
  base `/results` link.
- **Everything else unchanged:** Gemini-only ranking, Opus badged validation never re-ranks,
  honest degradation (coverage badges, absent = nothing not 0), numeric −1…+1 `scoreColor` ramp,
  no band names, corpus browsing untouched, additive/no-redeploy publish, runtime dataset
  validation, and the rate-limit/notice behavior.

This supersedes the #49 leaderboard presentation. When it lands, **#49 is closed** and its parked
`verify-approval` gate is retired (this work is its presentation successor).

## Stakeholders
- **Primary Users**: MultiBench researchers/readers who want the whole standings picture at a
  glance and to cross-check it against the paper.
- **Secondary Users**: Future run authors — a newly committed `results/<run-id>/` must still
  surface in the new table with no code change.
- **Technical Team**: This builder (spir-55); maintainers of `apps/multibrowser`; sibling builder
  spir-51 (raw-results browser) with whom routes/app are shared.
- **Business Owners**: The architect (project 55 owner) and Waleed (who set the design direction).

## Success Criteria
- [ ] **Dense table replaces the one-slice presentation**: `/results` shows one row per subject with
      Initial / Post / Δ headline columns, Unstated / Stated / Guided breakdown columns, and a
      per-tradition heat strip — all visible without changing a selector.
- [ ] **Headline reconciles with the paper**: each subject's `Post` (unstated, `full`, `pressure=all`,
      Gemini) equals the paper's `subj_overall` / `tab_standings` value to displayed precision.
- [ ] **Δ uses shard steadfastness**: the Δ column equals the mean of per-tradition matched-cell
      steadfastness for the unstated framing at the selected pressure — verified distinct from
      (Post − Initial) by a test on a subject where the matched-cell panels are asymmetric.
- [ ] **Framing staircase**: the Unstated / Stated / Guided columns equal the `full`
      mean-of-per-tradition-means at each framing (Gemini, selected pressure).
- [ ] **Heat strip == Post**: a row's heat-strip cells are that subject's per-tradition Post
      contributions; their equal-weight mean equals the Post column; zero-coverage traditions render
      empty (never 0).
- [ ] **Sort + canonical rank**: clicking any column header sorts by it (asc/desc toggling); the
      Rank column keeps the canonical (unstated-full-descending) rank regardless of sort; nulls sort
      last in both directions.
- [ ] **Pressure selector reframes the table**: choosing each of the six pressures or "all"
      recomputes headline, framing columns, and strip; "all" matches the cell-pooled convention.
- [ ] **Drill-down + judge selector (unchanged semantics)**: clicking a subject expands its full
      per-tradition table; the judge selector repoints the drill-down to Opus (badged `sample n/N`)
      where Opus data exists and **never** re-ranks or recolors the headline/strip.
- [ ] **Deep-linkable**: run, pressure, judge, sort (column+dir), and expanded subject(s) round-trip
      through the URL; the bare `/results` link carries no default params.
- [ ] **No export change**: the feature reads the existing `results/<run-id>/` shards + manifest
      unchanged; no new committed data slice is required. (If exploration finds a genuinely missing
      slice, it is raised with the architect before any additive export change — see Open Questions.)
- [ ] **Additive, no-redeploy publish still holds**: a second committed `results/<run-id>/` appears
      and is selectable; corpus browsing is unchanged.
- [ ] **Runtime validation + honest degradation preserved**: malformed/missing manifest or shard,
      out-of-range/non-finite scores, unknown vocab, or a 403 render an inline notice / cached-data
      banner, never a crash.
- [ ] **All touched-app tests pass** (`pnpm -C apps/multibrowser test`); no reduction in coverage.
      Documentation updated (multibrowser README leaderboard section; `results/README.md` "Results
      explorer" bullets reconciled to the new presentation).

## Constraints

### Technical Constraints
<!-- Baked constraints taken from issue #55 ("Constraints", "The multi-faith upgrade",
     "Requirements") and the carried-over #49 policy. Treat each as fixed; do not relitigate. -->
- **UI + client aggregation only.** Reuse `results/<run-id>/` shards + manifest **as-is** (the #49
  export is unchanged unless a small additive slice is *genuinely* needed — and any such need is
  escalated to the architect, not decided unilaterally).
- **Headline row numbers = the paper's published slice** (Gemini, mean of per-tradition means,
  unstated framing, `full`, `pressure=all`) and **reconcile to displayed precision**, as #49 does.
  The SPA's only cross-tradition statistic remains the equal-weight mean of per-tradition means
  (reuse the #49 `computeStandings` path); no new client re-implementation of the aggregation.
- **Gemini-only ranking; Opus is a badged validation layer that never re-ranks.** Unchanged #49
  policy. The judge selector repoints only the drill-down/inspection layer.
- **Steadfastness = the matched-cell Δ from #49's export** (the `steadfastness` table already in the
  shards), never a naive Post − Initial.
- **Deep-linkable state (URL) for sort + expansion**, in addition to the existing run / judge /
  pressure. Mirror the existing `resultsSelection` clean-URL discipline (omit defaults).
- **No band names; numeric + `scoreColor` ramp** (−1…+1, `lib/scoreColor.ts`) for every colored
  cell, including the heat strip.
- **Coordinate with in-flight #51 (raw-results browser): different routes, shared app; rebase
  discipline.** Do not touch #51's raw contract/tier; keep changes confined to the leaderboard
  presentation + its selection model. Rebase on the integration branch before opening the PR.
- **#49's verify-approval gate stays parked; this supersedes its presentation. Close #49 when this
  lands.**
- **Stack (unchanged):** Vite / React 19 / TS / Tailwind 4 / HeroUI v3 (**provider-less** — no
  `HeroUIProvider`) / TanStack Router + Query. Reuse the existing data layer, queries, notice, and
  rate-limit machinery.
- **Corpus browsing must remain intact**; all changes are additive to / a replacement of the
  `/results` presentation only.

### Business Constraints
- **Timeline**: N/A — no time estimates (AI-age; measured by completed phases).
- **Budget**: N/A — no monetary budget constraint on this UI work.
- **Compliance**: N/A — public, read-only benchmark data; no PII, no auth.

## Assumptions
- The committed `results/20260803/` shards + manifest are the working dataset and are correct
  (reconciliation was established in #49). This spec does not re-verify the export's internals.
- Every slice the new presentation needs already exists in the shards (verified): unstated
  `turn1`/`full`, unstated `steadfastness`, each framing's `full`, per-pressure and pooled `all`,
  and per-tradition `means`. No export change is planned.
- The 5-subject / 7-tradition / 2-judge shape of the launch run is representative; the presentation
  is data-driven (subjects, traditions, framings, pressures, judges all come from the manifest) so
  a differently-shaped future run renders without code change.
- The #49 pure aggregation functions in `lib/leaderboard.ts` are correct and reusable; the rewrite
  is presentation + selection model, not new aggregation math.
- Sibling #51 confines its work to a separate route family and the raw tier; shared-file conflicts
  are limited to app/routing/queries and are resolved by rebase, not redesign.

## Solution Approaches

The core presentation (dense headline table + framing columns + sort + canonical rank + drill-down)
is fixed by the issue's reference to the jaleesbrowser model. The genuine design choice is **how to
surface the extra tradition dimension (7)**. The issue names three candidate shapes; each is
evaluated below, then a recommendation.

### Approach A: Per-tradition heat strip + click-to-expand drill-down (RECOMMENDED)
**Description**: Each subject row carries a compact 7-cell `scoreColor` heat strip (one cell per
tradition, manifest order) showing that subject's per-tradition Post contributions; clicking the row
expands the exact per-tradition table (reusing the #49 drill-down data path + judge selector).

**Pros**:
- "Whole picture at a glance" for the tradition dimension without exploding the table into 7×(≥3)
  numeric columns.
- Tradition **spread** (consistency vs one strong/weak tradition) is immediately visible — the
  qualitative signal a single mean hides.
- Strip mean == Post column → reconciles by construction; reuses `subjectTraditionValues`.
- Exact numbers remain one click away; drill-down and judge-selector semantics are unchanged from
  #49 (low new surface, low risk).

**Cons**:
- A heat cell alone is not a precise number (mitigated: tooltip on hover + the drill-down gives
  exact values and coverage).

**Estimated Complexity**: Medium
**Risk Level**: Low

### Approach B: Tradition-columns toggle
**Description**: A toggle that expands the table with one numeric column per tradition (7 extra
columns) for the current headline metric.

**Pros**: Exact per-tradition numbers inline; sortable per tradition.
**Cons**: 7 numeric columns × (already 6 headline/framing columns) is dense to the point of
horizontal scroll on normal screens; multiplied by the metric/framing choice it becomes unwieldy;
weaker "at a glance" than a color strip. More layout/responsive surface.
**Estimated Complexity**: Medium-High
**Risk Level**: Medium

### Approach C: Expandable rows only (no glance layer)
**Description**: Keep #49's expandable per-tradition rows as the only tradition view; no strip, no
columns.

**Pros**: Smallest change; exact numbers on expand.
**Cons**: The tradition dimension is invisible until you expand each subject one by one — it fails
the issue's "whole picture at a glance" goal for the *new* dimension. This is essentially #49's
drill-down without the glance upgrade.
**Estimated Complexity**: Low
**Risk Level**: Low (but under-delivers on the multi-faith goal)

**Recommendation**: **Approach A** (heat strip + click-to-expand). It is the only candidate that
makes the tradition dimension visible *at a glance* (the explicit multi-faith goal) while keeping
exact numbers one click away, reconciling by construction, and reusing the #49 drill-down/judge
machinery. Approach C is the strip-less fallback if the strip proves problematic; Approach B's
tradition-columns toggle can be added later as an optional power-user affordance but is not
recommended for v1 (density/responsive cost with weaker glance value).

## Open Questions

### Critical (Blocks Progress)
- [ ] None. The data tier, ranking policy, steadfastness definition, and reference model are all
      fixed; the tradition-surface choice has a clear recommendation (Approach A).

### Important (Affects Design)
- [ ] **Does the pressure selector recompute the heat strip and framing columns, or only the
      headline?** Recommendation: it reframes the *entire* table (headline + framing columns +
      strip) at the chosen pressure, for one coherent slice. To confirm at plan review.
- [ ] **Strip basis under a non-unstated reading** — the headline is fixed to unstated (the paper's
      published slice), so the strip shows unstated-full per-tradition Post. Confirm the strip stays
      tied to the Post headline (unstated) rather than following a per-framing hover. Recommendation:
      tie to Post (single coherent story); framing detail lives in the breakdown columns + drill-down.
- [ ] **If exploration finds a slice the shards lack** (not expected), it is escalated to the
      architect before any export change — this spec's default is **no export change**.

### Nice-to-Know (Optimization)
- [ ] Optional per-tradition column toggle (Approach B) as a later power-user affordance.
- [ ] Bootstrap CIs on the pooled Gemini headline (an #49 optional SHOULD) — out of scope here
      unless trivially available.

## Performance Requirements
- **API budget**: unchanged — the leaderboard reads the same manifest + per-tradition shards via
  the existing one-git-tree-per-snapshot + off-budget `raw` fetches; the presentation adds no new
  on-budget calls.
- **Payload size**: unchanged — reuses the committed dataset (launch run ≈ 180 KB); no new data.
- **Response time**: the whole table renders from the already-loaded manifest + shards; sorting,
  expansion, and switching pressure/judge are client-side and instant (no refetch beyond the cached
  shards).
- **Resource usage**: negligible — aggregates only; the heat strip is a handful of DOM cells per row.

## Security Considerations
- **Authentication / Authorization**: none / N/A — public, read-only SPA over public GitHub content;
  no token, unauthenticated requests only.
- **Data privacy**: results are model scores + metadata; no transcripts are introduced by this UI.
- **Audit**: unchanged — the committed dataset's git history + manifest provide provenance.

## Test Scenarios

### Functional Tests
1. **Headline reconciliation (happy path)**: for the launch shards, each subject's Post (unstated,
   `full`, `pressure=all`, Gemini) equals the paper's `subj_overall` to displayed precision.
2. **Δ = shard steadfastness, not Post − Initial**: on a subject/tradition set with asymmetric
   matched-cell panels, the Δ column equals the mean of per-tradition steadfastness and is verified
   **distinct** from (Post − Initial).
3. **Framing staircase columns**: Unstated / Stated / Guided each equal the `full`
   mean-of-per-tradition-means at that framing for the selected pressure.
4. **Heat strip == Post**: a row's strip cells are the subject's per-tradition Post contributions;
   their equal-weight mean equals the Post column; a zero-coverage tradition renders empty (no 0).
5. **Sort + persistent canonical rank**: clicking each column header sorts by it (asc/desc toggle);
   the Rank column shows the same canonical (unstated-full-desc) numbers regardless of active sort;
   nulls sort last in both directions.
6. **Pressure reframes**: selecting each of the six pressures and "all" recomputes headline, framing
   columns, and strip; "all" matches the cell-pooled convention.
7. **Drill-down + judge selector (unchanged)**: expanding a subject shows its full per-tradition
   table; switching the judge to Opus repoints only the drill-down (badged `sample n/N` where Opus
   data exists) and leaves the Gemini-ranked headline/strip unchanged; a zero-coverage tradition
   shows nothing.
8. **Deep-link round-trip**: run, pressure, judge, sort (column+dir), and expanded subject(s) encode
   to the URL and restore on reload; the bare `/results` link has no default params; out-of-vocab
   deep links degrade to defaults (no crash).
9. **Runtime validation / missing data (preserved)**: malformed shard, out-of-range/non-finite
   score, unknown vocab, unsupported `schema_version`, absent manifest/shard field, and a 403 each
   render an inline notice / cached-data banner, never a crash.
10. **Additive no-redeploy publish (regression)**: a second `results/<run-id>/` in the fake tree is
    selectable and loads in the new table; corpus routes are unaffected.

### Non-Functional Tests
1. **API-budget (regression)**: loading the new leaderboard adds no on-budget API calls beyond the
   existing git-tree poll (fake-fetch call-log assertion).
2. **No coverage reduction**: the multibrowser suite passes with coverage not below the pre-change
   baseline.

## Dependencies
- **External Services**: GitHub (`api.github.com` git-trees + `raw.githubusercontent.com`),
  read-only, unauthenticated — the SPA's only runtime dependency. Railway static hosting for deploy
  (manual `railway up`).
- **Internal Systems**: the committed `results/<run-id>/` dataset (#49 contract, unchanged); the
  multibrowser data layer (`lib/github.ts`, `queries.ts`, `results*.ts`) and the reusable pure
  aggregation (`lib/leaderboard.ts`), selection/URL model (`lib/resultsSelection.ts`), and palette
  (`lib/scoreColor.ts`).
- **Libraries/Frameworks**: existing SPA deps (TanStack Router/Query, HeroUI v3, Tailwind 4, Vitest).
  No new runtime dependency is anticipated.

## References
- Issue #55 (this project) — feature definition, reference design, multi-faith requirements,
  constraints, PR strategy.
- `taqwabench/apps/jaleesbrowser/src/{leaderboard.ts,scores.ts,components/Leaderboard.tsx}` — the
  reference leaderboard model (local, read-only): headline slice on the first breakdown axis value,
  per-axis breakdown columns, click-to-sort, persistent canonical rank, nulls last, row → detail.
- `codev/specs/49-multibrowser-results-explorer-.md` + `results/README.md` — the data contract and
  the carried-over Gemini-only / Opus-validation / reconciliation / honest-degradation policy.
- `apps/multibrowser/src/{routes/ResultsPage.tsx,lib/leaderboard.ts,lib/resultsSelection.ts,lib/scoreColor.ts}`
  — the #49 presentation being replaced and the pure functions being reused.
- `codev/resources/arch-critical.md` / `lessons-critical.md` — SPA shape, client-side GitHub data
  layer rules, HeroUI v3 provider-less, results-tier contract, reconcile-by-construction lesson.

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Headline drifts from the paper's numbers | Low | High | Reuse the #49 `computeStandings` mean-of-per-tradition-means (verified exact); keep the reconciliation test against the paper values. |
| Δ column silently computed as Post − Initial | Medium | High | Bake Δ = mean of per-tradition shard `steadfastness`; test asserts it is distinct from Post − Initial on an asymmetric-panel case. |
| Heat strip mean diverges from Post column | Low | Medium | Strip cells ARE the Post per-tradition contributions (`subjectTraditionValues`); a test asserts `mean(strip) == Post`. |
| Sort re-numbers the canonical ranking | Medium | Medium | Canonical rank map computed once from the unstated-full ordering; render the map, not the sorted index; test both. |
| Judge selector accidentally recolors/reranks the headline | Medium | High | Headline/strip are Gemini-only by construction; the judge key feeds only the drill-down path; test that switching judge leaves headline/strip unchanged. |
| Merge conflicts with #51 in shared app/routing files | Medium | Medium | Confine changes to the leaderboard presentation + its selection model; rebase on the integration branch before PR; do not touch #51's raw tier. |
| An exploration reveals a genuinely missing shard slice | Low | Medium | Default is no export change; escalate to the architect via `afx send` before any additive export work. |
| Malformed/missing remote dataset crashes the table | Low | Medium | Preserve #49's runtime validation + notice/rate-limit behavior; tests for malformed shard, unknown vocab, 403. |
| Losing corpus-browsing integrity | Low | High | Additive/replacement to `/results` only; keep existing corpus tests green. |

## Expert Consultation
<!-- Porch runs the 3-way (here 2-way: codex + claude) consultation after this draft; feedback
     will be incorporated here with a dated entry. -->
**Date**: TBD (porch-run after initial draft)
**Models Consulted**: Codex (GPT) and Claude (per this repo's `porch.consultation.models=[codex,claude]`
— Gemini's per-phase consult cannot see the worktree here).
**Sections Updated**: [to be filled in after the consultation round]

Note: All consultation feedback will be incorporated directly into the relevant sections above.

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- **Scope boundary**: this is a **presentation + selection-model** rewrite of the `/results`
  leaderboard. The #49 data tier, Python exporter, and pure aggregation functions are unchanged and
  reused. No new route family is added; `/results` is upgraded in place.
- **Why the strip, not columns**: the multi-faith goal is "the whole picture at a glance" for the
  *tradition* dimension; a color strip conveys per-tradition spread instantly where 7 numeric
  columns would force horizontal scroll and still read less immediately. Exact numbers stay one
  click away in the drill-down.
- **Supersession**: on landing, this replaces #49's presentation, #49 is closed, and its parked
  `verify-approval` gate is retired.
