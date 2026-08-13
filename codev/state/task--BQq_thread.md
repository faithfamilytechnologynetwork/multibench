# task--BQq — completing Ben's PR #83 (reviewer workspace /review)

Ben is out; I'm finishing HIS branch `claude/multibench-scenario-review-2439j1` in place (no new PR).

## Environment gotcha
- `pnpm test` FAILS 10 tests (review.test.tsx, localStorage undefined) under node **26** (my default).
  Under node **20** (`fnm use 20`; repo pins engines node 20.x) the full suite is **347/347 green**.
  Always run tests under node 20. Baseline confirmed green before any change.

## The four required items (from the two architect PR comments = the spec)
1. Prefilled-issue URL exceeds MAX_ISSUE_URL_LENGTH (6.5K) at real sample size (10 scenarios) →
   reviewers always hit copy fallback. Fix: omit unreviewed check sections/links from the report;
   add a test at REVIEW_SAMPLE_SIZE.
2. `tradition-review` label already created repo-side. Optional: fixture asserting the label name.
3. "Reshuffle sample" silently drops completed checks → mirror the "Start over" confirm.
4. Governance docs (spec/plan/review, marked Retrospective) in this same PR.

Non-blocking small: privacy note by Contact field (public issue → prefer GitHub handle).
Skipping (not genuinely small): catalog-driven judge names on ReviewIndexPage; cold deep-link
sample materialization (filed as follow-up per architect).

## Progress — DONE (ready for re-review)
- Req 1: `reviewReport.ts` omits untouched checks/links; `### <id> — _not reviewed_` for empty
  scenarios; source/guide → `_Not reviewed._`. New test at REVIEW_SAMPLE_SIZE proves a full
  10-scenario report (zero-answer AND partially-filled) rides the prefilled-issue URL.
- Req 2: fixture pins `REVIEW_ISSUE_LABEL === "tradition-review"` + both URL builders.
- Req 3: reshuffle `window.confirm`s when `answeredScenarioChecks > 0` (mirrors Start over, quiet
  on fresh sample). Route test covers decline (untouched) + accept (reshuffles).
- Non-blocking: one-line privacy note under Contact field (public issue → prefer GitHub handle).
- Governance docs authored (specs/plans/reviews 83-*, marked Retrospective).
- SKIPPED w/ rationale in plan+review: catalog-driven judge names on ReviewIndexPage (adds a
  results-run dep + fallback to a traditions-only page — follow-up), cold deep-link materialization
  (architect follow-up), @theme shade shim (own issue).

## Verification
- `pnpm -C apps/multibrowser test` → 350/350 under Node 20 (was 347; +3 new, 1 rewritten).
- `tsc --noEmit` clean; `pnpm build` clean (exit 0). No eslint configured.

Next: commit (code fixes, then docs), push to origin so PR #83 updates in place, comment on PR,
notify architect. Do NOT merge.
