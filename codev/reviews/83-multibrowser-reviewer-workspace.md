# Review — multibrowser reviewer workspace (`/review`), PR #83

> **Retrospective.** Started from the architect's integration-review findings on PR #83 and the
> completion work that resolved them (done by a second builder while the author, Ben, was out).
> Lessons will be appended at close.

## Metadata
- **Spec**: `codev/specs/83-multibrowser-reviewer-workspace.md`
- **Plan**: `codev/plans/83-multibrowser-reviewer-workspace.md`
- **PR**: #83 · branch `claude/multibench-scenario-review-2439j1`
- **Feature author**: Ben (commit `47cf0d5`). **Completion**: second builder (integration-review
  fixes + governance docs), same branch/PR.

## 1. Integration-review findings (architect, single-model, medium risk)

The architecture was assessed as exactly right: reuses the query hooks / `RawComparison` /
fail-soft components, no new deps, static + read-only preserved, and the submit-panel seam for
future server-side collection was appreciated (now issue #85). Docs excellent. Three things blocked
merge, all fixable:

1. **The prefilled-issue path never rendered at real sample size.** A 10-scenario report is ~9.2K
   chars body → ~12.5K URL vs the 6.5K `MAX_ISSUE_URL_LENGTH` guard — even with zero answers filled
   — so production reviewers always got the copy-report fallback. Existing tests missed it because
   the fixture was 2 scenarios.
2. **`tradition-review` label** didn't exist, so the `?labels=` param was silently dropped and
   `gh issue list --label tradition-review` aggregation came back empty. The architect created it →
   resolved repo-side; a fixture asserting the name was optional.
3. **"Reshuffle sample" was destructive without confirmation** — it dropped completed checks from
   the generated report (state survives but is unreachable) while "Start over" confirmed.

Non-blocking, worth doing: a privacy note by the Contact field (destination issue is public →
prefer a GitHub handle); cold deep-link sample materialization (deferred as a follow-up);
`ReviewIndexPage` hardcodes judge names in prose while `RawComparison` reads them from the catalog
(will drift); a `@theme` numbered-shade shim (own issue).

## 2. What the completion changed, and why

| # | Change | Why |
|---|--------|-----|
| Req 1 | `checkSection` returns `string | null`; untouched checks (and their file links) are omitted from the report — a fully-untouched scenario is listed compactly as `### <id> — _not reviewed_`; source/guide fall back to `_Not reviewed._` | Cuts the report from ~12.5K URL to well under the 6.5K guard so the **prefilled-issue path actually renders** at 10 scenarios. Untouched checks carried no reviewer signal anyway — only cost. |
| Req 1 (test) | New `reviewReport.test.ts` case at `REVIEW_SAMPLE_SIZE`: a zero-answer **and** a realistic partially-filled 10-scenario report both ride the prefilled URL | Locks the real-sample-size regression the 2-scenario fixture missed. |
| Req 2 | Fixture pinning `REVIEW_ISSUE_LABEL === "tradition-review"` + both URL builders carry `labels=tradition-review` | A rename here can't silently diverge from the repo label the aggregation depends on. |
| Req 3 | `answeredScenarioChecks` gates a `window.confirm` on reshuffle; silent when nothing is at risk | Mirrors "Start over" — stops silent loss of completed work — without nagging on a fresh sample. New route test covers decline (sample untouched) and accept (reshuffles). |
| Non-blocking | One-line privacy note under the Contact field | The destination issue is public; nudge reviewers toward a GitHub handle over an email. |

**Deliberately deferred** (documented, not silently dropped): catalog-driven judge names on the
landing page (adds a results-run dependency + fallback to a traditions-only page — a follow-up, not
a completion-PR change; the names are universal-core stable), cold deep-link materialization (filed
follow-up), the `@theme` shim (own issue), server-side collection (#85).

## 3. Verification evidence

- **Tests**: `pnpm -C apps/multibrowser test` → **350 passed / 350** under Node 20 (was 347; +3 new
  cases, 1 rewritten). Baseline was re-confirmed green *before* any change.
- **Typecheck**: `tsc --noEmit` clean.
- **Build**: `pnpm build` clean (exit 0).
- The Req 1 fix is proven by construction: the new test builds an actual 10-scenario report and
  asserts `prefilledIssueUrl(...)` is non-null — not a hand-estimated length.

## 4. Toolchain note (cost me time — recorded so it doesn't cost the next builder)

The repo pins `engines: node 20.x`. Under Node **26** (a common default), `pnpm test` fails 10
`review.test.tsx` cases with `localStorage` undefined — jsdom does not expose `localStorage` there —
which looks like a real regression but is purely an environment mismatch. Under Node **20** (`fnm
use 20`) the suite is green. **Always run this app's tests under Node 20.** No CI workflow currently
runs the multibrowser suite (only `validate.yml` for the Python validator), so the Node-20
expectation lives only in `package.json` `engines` and the porch per-builder `.codev/checks/test.sh`
dispatcher.

## 5. Deviations from a strict "mirror Start over" reading

The architect said "mirror the confirmation." A literal mirror would confirm on *every* reshuffle.
Instead the confirm is **conditional** on there being completed scenario work to lose — a fresh
reshuffle (the common first action) proceeds without a prompt. This is strictly better UX and still
closes the data-loss hole; it also keeps the pre-existing "reshuffle draws a seeded sample" test
passing unchanged (that test does zero checks, so no prompt fires). Flagged here in case the
architect prefers an unconditional confirm.

## 6. Lessons
- **Test at the real operating size, not a convenient fixture.** A 2-scenario fixture made a
  URL-length guard look satisfied when the 10-scenario production path always overflowed it. When a
  guard is a function of N, put a test at the real N.
- **A "static, read-only SPA" can still have a durable write path** — here GitHub issues as the
  attributable, aggregatable store — as long as the write is an explicit, user-initiated hand-off
  and the only replaceable seam is isolated (the submit panel, #85).
- **Omission is a length lever.** Carrying a link for every possible check is honest but expensive;
  omitting the untouched ones both shortens the artifact and sharpens its signal (only what the
  reviewer actually said).
- **Pin the toolchain expectation loudly.** A Node-version mismatch presents as a fake test
  regression; the engines pin and this note are the only guards until CI runs the suite.
