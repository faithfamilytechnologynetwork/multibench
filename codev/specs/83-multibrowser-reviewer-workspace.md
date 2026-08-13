# Specification: multibrowser — reviewer workspace (`/review`) for expert tradition validation

> **Retrospective.** This spec was authored *after* the feature landed (PR #83), per the repo's
> "three documents per feature" convention. It records the WHAT and WHY as-built; it does not
> simulate a spec that preceded the code. The PR description is ~80% of it; the two architect
> integration-review comments on PR #83 supplied the remaining required behavior (report length,
> reshuffle confirmation, the aggregation label), completed by a second builder while the author
> (Ben) was out.

## Metadata
- **ID**: spec-2026-08-13-multibrowser-reviewer-workspace
- **Status**: as-built (retrospective)
- **Created**: 2026-08-13
- **PR**: #83 (branch `claude/multibench-scenario-review-2439j1`)
- **Feature surface**: `apps/multibrowser` — three new routes under `/review`

## Problem Statement

MultiBench scores AI assistants on whether their counsel stays faithful to a tradition's guidance.
That measurement only means something if the tradition's own materials — its canonical `source.md`,
its companionship `guide.md`, and each scenario's judge-guidance, pressures, and transcripts — are
*correct*. Those materials are authored with AI assistance and need validation by adherents and
scholars of each tradition (the path toward each tradition's `scholar_review` status).

Before this feature there was no structured way for a domain expert to review a tradition. A
reviewer would have to browse the corpus ad hoc, hold their own notes, and email findings with no
common shape — nothing attributable, nothing aggregatable, nothing linked to the exact reviewed
snapshot. The benchmark's credibility rests on expert sign-off it had no workflow to collect.

## Current State (before PR #83)

`apps/multibrowser` is the team-standard read-only SPA that browses the corpus live from GitHub
(SHA-pinned trees + `raw` content). It has display-first views (`/t/<tradition>`, `/results`,
`/raw/...`) and the query hooks, `RawComparison` transcript/verdict view, and fail-soft Notice
components those views share. There was **no review surface** and no reviewer-intake concept.

## Desired State (as-built)

A guided expert-review workflow living entirely inside the static SPA — no backend added — across
three routes:

- **`/review`** — the front door. States the three review steps (**1** review the scenario source,
  **2** review the guide, **3** review your assigned 10 scenarios, each with four checks), captures
  reviewer identity (name / contact / standing), and lists traditions to pick with per-tradition
  progress.
- **`/review/<tradition>`** — the workspace. `source.md` (step 1) and `guide.md` (step 2) rendered
  inline with an intake control each; then step 3, an assigned **10-scenario sample** (deterministic
  even spread across the corpus; seeded reshuffle with the seed recorded; manual add/remove) with
  per-check status dots; then the submit panel.
- **`/review/<tradition>/<scenario>`** — the four per-scenario checks, each pairing the content
  under review with an intake control: **(a)** the scenario (`turn1.md` + meta), **(b)** the scoring
  guide (`judge-guidance.md`), **(c)** the judges' verdicts (the existing `RawComparison` embedded
  with a **local**, not URL, selection so browsing never leaves the review), **(d)** the six
  pressure points. Prev/next walks the assigned sample.

**Intake posture.** The SPA stays static and read-only. Reviewer intake (a verdict +
free-text notes + an optional suggested revision per check) persists to `localStorage`
(`multibench.review.v1`) through a **tolerant zod loader** — one corrupt subfield degrades to a
default rather than discarding the reviewer's work. Nothing leaves the browser until the reviewer
explicitly submits.

**Submission (the durable store).** Submission produces an explicit Markdown report (reviewer
identity; every verdict/note/suggestion; links to the exact files at the reviewed SHA; the sample +
seed) and opens a **prefilled GitHub issue** labeled `tradition-review` — attributable and
aggregatable via `gh issue list --label tradition-review`, requiring no new infrastructure. A `.md`
download, clipboard copy, and JSON backup/restore serve reviewers without GitHub accounts. If
server-side collection is ever wanted, the submit panel is the single seam to replace (filed as
issue #85).

## Success Criteria

1. A reviewer can complete all three steps for a tradition and submit, with every check linked to
   the exact file at the reviewed snapshot.
2. Intake survives reloads and a corrupt/older payload (tolerant load), and never leaves the
   browser until explicit submission.
3. The default 10-scenario sample is deterministic (every reviewer opening a tradition cold sees
   the same 10) and stable (never re-drawn under a reviewer mid-review); reshuffle is seeded and the
   seed is recorded in the report.
4. **The prefilled-issue path actually renders at the real sample size** — a full 10-scenario
   report fits under the issue-URL length guard, so production reviewers get the prefilled issue,
   not only the copy-report fallback. *(This was the load-bearing gap the integration review found;
   see Constraints → Required fixes.)*
5. The SPA remains static, read-only, and dependency-free of new packages; existing views unchanged.

## Constraints

### Baked decisions (architect — not relitigated)
- **The SPA stays static and read-only.** Reviewer intake is client-side; the durable store is
  GitHub issues, not a new backend. Server-side collection is a future seam (#85), not this PR.
- **GitHub issues labeled `tradition-review`** are the submission channel and aggregation key. The
  label now exists repo-side (created by the architect during integration review).
- **Semantic HeroUI tokens only.** The numbered color shades (`default-500`, `warning-50`,
  `primary`, …) compile to no-ops on the pinned `@heroui/styles` 3.2.1 (the #55 nonexistent-shade
  class of bug); the review feature's functional colors use the semantic tokens that exist. (A
  broader `@theme` shim to fix the numbered shades app-wide is filed as its own issue, not here.)

### Required fixes from the integration review (completed in-PR)
1. **Report length.** At the real sample size (~10 scenarios) the generated report emitted a file
   link for all 42 checks even when unreviewed, pushing the prefilled-issue URL to ~12.5K — past
   the 6.5K `MAX_ISSUE_URL_LENGTH` guard — so reviewers *always* fell back to copy-the-report.
   **Fix:** omit untouched check sections/links from the report; a full 10-scenario report now
   fits. Regression test added at `REVIEW_SAMPLE_SIZE`.
2. **`tradition-review` label** existed only after the architect created it; resolved repo-side. A
   fixture pins the exact label name so a rename can't silently diverge.
3. **Reshuffle confirmation.** "Reshuffle sample" silently stranded completed scenario checks
   (state survives but becomes unreachable and drops from the report) while "Start over" confirmed.
   **Fix:** reshuffle now confirms before discarding completed work (and stays quiet when there is
   none to lose).

### Technical constraints
- Client-side GitHub data layer: unauthenticated, SHA-pinned, fail-soft (rate-limit banner + stale
  content) — the review pages reuse the existing query hooks and Notice/RateLimit components.
- Tests run under Node 20 (repo `engines: node 20.x`); jsdom `localStorage` is unavailable under
  newer Node, so the route tests require the pinned toolchain.

## Solution Approach (as-built)

A `lib/review.ts` intake model (tolerant zod persistence + a `useSyncExternalStore` module store +
pure updaters + deterministic sampling + progress), a `lib/reviewReport.ts` submit seam (pure
report/issue/edit-URL builders), three route components reusing existing corpus queries and
`RawComparison`, plus reviewer-facing docs. No new dependencies; existing pages untouched.

Rejected alternatives: (a) adding a backend to collect intake — violates the static/read-only
posture and adds infrastructure the benchmark doesn't need; (b) URL-carried selection inside the
embedded verdict viewer — would leak review navigation into the address bar and break prev/next.

## Test Scenarios

- **Sampling**: even spread is deterministic and stable; seeded reshuffle is reproducible from the
  seed; add/remove preserves corpus order.
- **Persistence**: tolerant load survives corrupt subfields; updaters are pure; progress counts
  answered vs. total and flagged.
- **Report/issue builders**: identity/date/snapshot/run/sample carried; notes as blockquotes;
  pinned file links; **untouched checks omitted**; **a full 10-scenario report rides the
  prefilled-issue URL**; label pinned to `tradition-review`.
- **Routes** (over the fake-repo harness): landing lists steps/traditions and retains identity;
  workspace assigns an even sample and records verdicts; scenario page walks four checks; prev/next;
  404 on unknown scenario; **reshuffle confirms before dropping completed checks**.

## References
- PR #83 and its two architect integration-review comments (the binding spec for the completion).
- `codev/specs/54-*`, `codev/plans/54-*`, `codev/reviews/48-*` (document-shape references).
- `traditions/README.md` (corpus contract); `results/README.md`, `results-raw/README.md`
  (the tiers the embedded verdict view reads).
- Follow-ups filed: #85 (server-side collection seam), the `@theme` numbered-shade shim.

## Approval
Retrospective — no spec-approval gate. Landed via PR #83 review.
