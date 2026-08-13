# Plan: multibrowser — reviewer workspace (`/review`)

> **Retrospective.** Authored after PR #83 landed. This is the HOW **as-built** — the shape the
> code actually took, not a forward plan. Phases below are the natural layers of the diff
> (lib → routes → submit builders → docs), not porch-driven plan phases.

## Metadata
- **ID**: plan-2026-08-13-multibrowser-reviewer-workspace
- **Spec**: `codev/specs/83-multibrowser-reviewer-workspace.md`
- **PR**: #83 · branch `claude/multibench-scenario-review-2439j1`

## Executive Summary

Three review routes added to the existing static SPA, backed by two pure library modules
(`lib/review.ts` intake state + sampling + progress; `lib/reviewReport.ts` the submit seam) and
reusing the corpus query hooks, `RawComparison` verdict view, and fail-soft Notice/RateLimit
components. Intake persists to `localStorage` through a tolerant zod loader; submission is an
explicit Markdown report handed to maintainers via a prefilled `tradition-review` GitHub issue
(with copy / `.md` download / JSON backup fallbacks). No new dependencies; no existing page changed.

## Success Metrics
- Full suite green under Node 20 (`pnpm -C apps/multibrowser test`), `tsc --noEmit` clean, `vite
  build` clean.
- A full 10-scenario report submits via the prefilled issue path (the real-sample-size regression).

## Phase Breakdown (as-built layers)

### Layer 1 — `lib/review.ts`: intake model, persistence, sampling, progress
- `ReviewState` = version + `ReviewerInfo` + per-tradition `TraditionReview` (two tradition-level
  checks `source`/`guide` + a materialized `sampleIds` with `sampleSeed` + per-scenario
  `ScenarioChecks`). `CheckReview` = `{ status, notes, suggestion }`.
- **Tolerant zod schema**: every field `.catch`es to a default independently, so a corrupt subfield
  never discards the rest. `parseReviewState` never throws.
- **Module store** via `useSyncExternalStore` (one shared snapshot across pages; persists on every
  update; cross-tab `storage` event re-reads). Pure updaters: `withReviewer`, `withSample`,
  `withTraditionCheck`, `withScenarioCheck`, `withoutTradition`.
- **Sampling**: `evenSample` (deterministic even spread, always includes the first — the default
  assignment); `seededSample` (FNV-1a → mulberry32 shuffle, reproducible from the recorded seed;
  empty seed falls back to even spread). Picks keep corpus order.
- **Progress**: `traditionProgress` counts answered / total / flagged across source + guide + 4×
  each sampled scenario.

### Layer 2 — routes
- **`ReviewIndexPage`** (`/review`): the three-step explainer, reviewer identity form (name /
  contact / background), tradition grid with progress. Reuses `useTraditions`, fail-soft on
  rate-limit.
- **`ReviewTraditionPage`** (`/review/<tradition>`): materializes the even-spread sample **once**
  per tradition in an effect (never re-drawn automatically — the sample must not shift under a
  reviewer); renders `source.md` / `guide.md` in `Collapsible` + `Markdown` with a
  `ReviewCheckControl` each; the sample list with per-check `CheckStatusDot`, remove, and the
  reshuffle / add-scenario controls; and the `SubmitPanel`.
- **`ReviewScenarioPage`** (`/review/<tradition>/<scenario>`): the four checks with content inline;
  check (c) embeds `RawComparison` with a **local** selection (not URL-carried); honest empty state
  when no results run is published; prev/next across the assigned sample.
- **Components**: `ReviewCheckControl` (verdict toggle + notes + suggestion + "propose an edit"
  link), `CheckStatusDot`, `ReviewProgressBar`. Router entries + a RootLayout nav link.

### Layer 3 — `lib/reviewReport.ts`: the submit seam (pure)
- `buildReviewReport` → the Markdown report; `prefilledIssueUrl` (length-guarded by
  `MAX_ISSUE_URL_LENGTH`, returns `null` when too long → caller offers copy + `blankIssueUrl`);
  `issueTitle`; `editFileUrl` (writable ref, GitHub auto-forks) and `blobUrl` (pinned read link);
  `REVIEW_ISSUE_LABEL = "tradition-review"`.

### Layer 4 — docs
- `docs/analysis/tradition-reviewer-guide.md` (reviewer reference + maintainer aggregation
  section), indexed in the analysis README and linked from `/review`; a README section.

## Completion work in this PR (second builder, integration-review fixes)

1. **Report length (Required 1).** `checkSection` now returns `string | null` — untouched checks
   (unreviewed status, empty notes, empty suggestion) return `null` and are omitted, taking their
   file link with them. A fully-untouched scenario is listed compactly as `### <id> — _not
   reviewed_` (still enumerated against the sample, but spending no file links). Source/guide fall
   back to `_Not reviewed._`. **Effect:** a full 10-scenario report drops from ~12.5K URL to well
   under the 6.5K guard, so the prefilled-issue path renders in production.
2. **Label fixture (Required 2).** A test pins `REVIEW_ISSUE_LABEL === "tradition-review"` and
   asserts both issue-URL builders carry `labels=tradition-review`.
3. **Reshuffle confirmation (Required 3).** `ReviewTraditionPage` computes `answeredScenarioChecks`
   (completed scenario checks in the current sample); the reshuffle button `window.confirm`s before
   discarding them, and stays silent when there are none — mirroring "Start over" without nagging on
   a fresh sample.
4. **Privacy note (non-blocking).** A one-line hint under the Contact field: submitted issues are
   public, prefer a GitHub handle over an email.

## Test strategy
- **Lib tests** (`review.test.ts`, `reviewReport.test.ts`): sampling determinism, tolerant load,
  updaters, progress, report/issue builders — plus the new **`REVIEW_SAMPLE_SIZE` URL-budget
  regression**, the **untouched-checks-omitted** assertions, and the **label fixture**.
- **Route tests** (`review.test.tsx`) over the fake-repo harness: landing, workspace sampling +
  verdicts, scenario walk, prev/next, 404 — plus the new **reshuffle-confirmation** test (declining
  leaves the sample untouched; accepting reshuffles).
- Verified: full suite green (350 tests) under Node 20, `tsc --noEmit` clean, `pnpm build` clean.

## Deliberate non-goals (deferred as follow-ups)
- **Catalog-driven judge names on `ReviewIndexPage`** — the landing prose names Gemini (ranking
  judge) / Opus (validation sample) in static text where `RawComparison` reads them from the
  catalog. Reading them from the catalog on the landing page adds a results-run data dependency to a
  page that otherwise only loads traditions, and needs a fallback when no run is published; left as
  a follow-up rather than grown in a completion PR. (The names are universal-core stable.)
- **Cold deep-link sample materialization** (entering `/review/<t>/<s>` before the tradition page
  drew the sample) — filed as a follow-up by the architect; explicitly out of scope here to avoid
  scope creep.
- **`@theme` numbered-shade shim** (fix the no-op numbered HeroUI shades app-wide) — its own issue.
- **Server-side intake collection** — issue #85.

## Change Log
- 2026-08-13 — Ben: reviewer workspace feature (commit `47cf0d5`).
- 2026-08-13 — completion builder: Required 1–3 + privacy note + governance docs (this PR).
