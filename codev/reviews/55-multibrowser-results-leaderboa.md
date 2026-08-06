# Review: multibrowser /results leaderboard v2 — jaleesbrowser-style dense table, multi-faith

- **Spec**: [codev/specs/55-multibrowser-results-leaderboa.md](../specs/55-multibrowser-results-leaderboa.md)
- **Plan**: [codev/plans/55-multibrowser-results-leaderboa.md](../plans/55-multibrowser-results-leaderboa.md)
- **Status**: implementation complete (4 phases), PR pending
- **Date**: 2026-08-06

## What was built

A **UI + client-aggregation** rewrite of the `/results` leaderboard presentation, replacing #49's
selector-driven one-slice table with the jaleesbrowser dense-table model, extended with MultiBench's
tradition dimension. The #49 data tier (`results/<run-id>/` shards + manifest), the Python exporter,
and the `computeStandings` core are **unchanged and reused** — no export change.

- **Dense board** (one row per subject): First-response / Post-pressure / Δ (steadfastness) headline
  columns on the paper's published slice (first framing), plus one post-pressure column per framing.
- **Per-tradition heat strip** (the multi-faith upgrade): a `scoreColor` square per tradition whose
  non-null mean *is* the Post column, built from `computeStandings`'s own `contributions` (reconciles
  by construction). Accessible (`role="img"` + label; dashed empty cell for uncovered traditions).
- **Sortable** numeric columns with a **persistent canonical rank**; **pressure** reframes the whole
  table (headline + framing columns + strip + rank); **judge selector** repoints only the drill-down
  to Opus (badged, never re-ranks/recolors); **dense per-tradition drill-down** (`—/N` when a Post
  numerator is absent). Run / pressure / judge / sort / expansion are all deep-linkable.

### Phases
1. **Client aggregation** (pure lib) — `computeLeaderboardRows` / `sortRows` / `subjectDrilldownRows`,
   the `Slice` decouple, subject-id column join, structural Gemini-only ranking.
2. **Dense sortable table + URL state** — new selection model (sort + expanded; framing/metric → columns),
   run selector, retained #49 drill-down via a `Slice` literal.
3. **Multi-faith layer** — heat strip, drill-down upgraded to the dense per-tradition table,
   URL-encoded keyboard expansion, accessibility.
4. **Docs + cleanup + verify** — READMEs reconciled to v2, removed the app-dead `subjectTraditionValues`,
   a11y polish, build + preview smoke.

Final: `pnpm -C apps/multibrowser test` → **179 tests green**; `check-types` clean; production bundle
builds; preview serves `/results`.

## #49 supersession (architect action at merge)

This **supersedes the #49 leaderboard presentation**. When this PR merges:
- **Close #49** — its presentation is replaced by this dense-table v2.
- **Retire #49's parked `verify-approval` gate** — it was held pending this successor.

Both are **architect actions** flagged here (the builder does not close #49 or touch its gate).

## Lessons learned

- **A type break can ship green here.** The porch tests-check runs only Vitest, and neither Vitest nor
  `vite build` (esbuild) typechecks. The Phase-2 selection-shape change would have silently broken
  `leaderboard.ts` via a `Pick<ResultsSelection, …>`. Fix: decouple to a standalone `Slice` type in
  Phase 1 *and* make `pnpm … check-types` a per-phase definition-of-done. **Recommended follow-up for
  the architect (out of scope here):** add `check-types` to the shared `.codev/checks/test.sh`
  multibrowser branch so the porch gate itself typechecks — it would protect #51 and all future
  multibrowser builders.
- **Reconcile by construction, then guard it.** Every numeric column reuses `computeStandings`; the
  heat strip reuses its returned `contributions`. `mean(non-null strip) == post` and `post == paper`
  are then true by construction and pinned by a committed-shard test — no second implementation of the
  aggregation convention to drift.
- **Test fixtures must be able to *fail*.** Two review catches were tests that couldn't discriminate:
  a positional-zip row-assembly bug that a `post`-only test would miss (fixed by joining columns on
  subject id + a crossing-order fixture), and a pressure-reframe test where the second subject had no
  data so rank could never change (fixed with a `false_authority` slice that flips the order).
- **Δ is the shard's matched-cell steadfastness, not post − initial** — identical on the complete
  Gemini grid, so the distinctness the UI must preserve lives on a synthetic asymmetric fixture.
- **Accessibility details matter:** `aria-label` on a role-less `<span>` is ignored (`role=generic`
  prohibits it) — the strip cells needed `role="img"`; and `aria-controls` should reference an id that
  exists (gated on `open`).

## Systematic notes

- Every phase's review feedback was incorporated with a written rebuttal (see
  `codev/projects/55-*/*-rebuttals.md`); no feedback was rejected.
- Scope discipline held: all changes are inside the `/results` leaderboard components + client
  aggregation; no contact with #51's raw-results tier, the `results/` data, or the exporter.

## PR prep

- **Rebase onto `origin/main`** to drop the `docs/paper/*` files inherited from the branch base
  (`d0fa576`, whose content already landed on `origin` as `9a4f735`) — the PR should show only the
  `/results` leaderboard changes.
- **Interactive verification:** the 20-test `results.test.tsx` integration suite exercises every board
  interaction (columns, sort + persistent rank, pressure reframe, run switch, heat strip, dense
  drill-down, keyboard expansion, deep-link restore, judge invariance) against a byte-faithful GitHub
  fetch stand-in; `pnpm build` + `pnpm preview` confirm the bundle builds and serves. A final live
  click-through against the real GitHub runtime happens on the post-merge Railway deploy (per plan,
  production `railway up` is after merge).
