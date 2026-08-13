# air-90 — multibrowser: /results should list all published datasets

Protocol: AIR (strict). Issue #90.

## Goal
`/results` should list every published dataset in one place: scored benchmark runs
(`results/<id>/`) as today (leaderboard), **plus** raw-only experiment datasets
(`results-raw/<id>/` with no score tier) — each linked to its `/raw/<runId>` explorer landing,
labeled from its catalog.

## What I found
- The discovery seam already existed: `useRawExplorerRunIds` (queries.ts) = `rawRunIds` minus
  `resultsRunIds`, derived from the already-walked SHA-pinned tree → no extra GitHub call, never
  touches `loadResultsManifest` (so no false "manifest not found", the #54 lesson).
- `IndexPage` already renders these as an "Explorers" list via `useRawCatalog(sha, id, null)` for
  the title. I ported the same pattern into `/results` as an **Experiments** section, richer
  (title + description card), fail-soft to the bare run id on a malformed catalog.

## Implementation (as-built)
- `ResultsPage.tsx`: `useRawExplorerRunIds` hook; new `Experiments` `<section>` rendered
  **independently of `manifest`** (shows even with zero scored runs); new module-scope
  `ExperimentRow` component (catalog title/description via `useRawCatalog(..., null)`, links to
  `/raw/$runId`). Empty-state now fires only when BOTH tiers are empty ("No datasets published…").
- `results.test.tsx`: updated the empty-state test; added a describe block covering: experiment
  listed alongside scored runs, experiments-only page (no leaderboard, no empty-state), a run in
  both tiers is scored-not-duplicated, and malformed-catalog falls back to run id without blanking.
- ~30 LOC feature + ~65 LOC tests. Well within AIR scope.

## Verification
- `pnpm exec vitest run` (full multibrowser suite): **355 passed** under node 20.
- `pnpm check-types`: clean. `pnpm build`: clean.
- ⚠️ Node version: this machine defaults to node 26, under which `review.test.tsx` fails 11/11
  (`localStorage` undefined in jsdom — confirmed pre-existing on the clean base, unrelated to my
  change). Repo requires node 20 (`engines.node: 20.x`); `fnm use 20` → all green. Porch's
  test-check must run under node 20.

## Baked decisions honored
- Gemini-only ranking / Opus badges: untouched (no leaderboard-semantics change).
- Raw-only runs never hit the score-tier loader.
- Client-side discovery from the SHA-pinned tree; fail-soft on malformed entries.
- New datasets (e.g. #89 ProtestantBench) appear with zero code change.
