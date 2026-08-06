# Review: MultiBrowser Results Explorer — Judge & Pressure Selectors + Leaderboard

## Summary

Brought the 20260803 results programme into the multibrowser SPA: a Python export tool that turns
local judging runs into a compact, committed `results/<run-id>/` dataset, and an additive `/results`
explorer (Gemini-ranked leaderboard + framing/metric/pressure/judge selectors + per-tradition
drill-down) that reads it at runtime. Six implementation phases; the leaderboard reconciles with the
paper's standings to displayed precision, verified against the real committed shards.

## Spec Compliance

- [x] AC: **Leaderboard reconciles with the paper** — mean-of-per-tradition-means == `subj_overall` at
  1e-9 for every subject×framing; asserted in both the Python export tests and a TS test over the
  committed shards (Phases 1, 4).
- [x] AC: **Judge selector** — switches the inspection/drill-down to a single normalized Opus judge;
  the SPA never sees two Opus judges (Phases 1, 5).
- [x] AC: **Pressure selector** — every view filterable by the six pressures + "all" (Phases 4, 5).
- [x] AC: **Leaderboard** by framing, per-tradition drill-down, framing toggle, scope toggle
  (first-response/post-pressure) + **steadfastness** metric (architect add) (Phases 4, 5).
- [x] AC: **Gemini-only ranking** — structurally guaranteed (`computeStandings` always uses the
  full-grid judge); Opus never re-ranks (Phases 4, 5).
- [x] AC: **Honest degradation** — Opus stated/guided badged `sample n/N`; zero-coverage traditions
  omitted, never 0; full-grid coverage denominators (Phases 1–5).
- [x] AC: **Additive, no-redeploy publish** — a new `results/<run-id>/` appears via the same git-trees
  + `raw` path, incl. under a truncated tree; corpus browsing intact (Phase 3).
- [x] AC: **Size** — committed dataset 174 KB (≤ 8 MB total, ≤ 1 MB/shard; **test-asserted** via the
  porch dispatcher / local suite — no GitHub Actions job runs the JS/Python suites yet) (Phase 2).
- [x] AC: **Alias normalization** — Opus `claude-opus-4-8` + `anthropic/claude-opus-4.8` collapse to
  one, deduped; subject-id aliases normalized to five canonical (Phase 1).
- [ ] AC: **Live Railway deploy** (`railway up`, judge/pressure selectors live) — deferred to the
  Verify phase (manual, human-run); build passes and integration tests cover the behavior.

## Deviations from Plan

- **Steadfastness scoped in (not out).** The plan initially scoped steadfastness out of v1; the
  architect's conditional plan-approval brought it back as a matched-cell metric. Implemented as a
  third leaderboard metric — which also re-aligned the plan with the spec's Test Scenario 5.
- **Phase 3 force-advanced.** Porch hit its iter-3 review safety ceiling on Phase 3 and advanced with
  Codex's final verdict still REQUEST_CHANGES; every raised point was addressed and committed before
  the ceiling (the final PR CMAP re-reviews the full diff).
- **`deploy.test.ts` hardening** (not in the original plan) added after a leaked `serve` from a
  defunct worktree blocked the dispatcher — architect-requested: detached spawn + process-group reap
  + port pre-flight.

## Key Metrics

- **Commits**: ~70 on the branch (17 `[Phase]` feature/data commits + spec/plan/thread/porch/review;
  count keeps growing through the review consult rounds).
- **Tests**: 264 passing (Python 112 = 81 existing + ~31 new; JS 152 = ~97 existing + ~55 new).
- **Files created**: `workflows/analysis/analysis/export_results.py` (+ test + `tests/fixtures/export/`);
  `results/20260803/**` (dataset) + `results/README.md`;
  `apps/multibrowser/src/lib/{resultsModel,resultsSelection,leaderboard,scoreColor}.ts` (+ tests);
  `src/routes/ResultsPage.tsx` (+ `results.test.tsx`); `src/lib/results.data.test.ts`.
- **Files modified**: `analysis/{aggregate,cli}.py`; `apps/multibrowser/src/lib/{github,queries}.ts`;
  `src/router.tsx`, `src/routes/RootLayout.tsx`, `src/test/fakeRepo.ts`, `src/deploy.test.ts`,
  `apps/multibrowser/README.md`; the four governance docs.
- **Files deleted**: none.
- **Net LOC impact**: ~+2,600 lines (code + tests + the committed dataset + docs).

## Timelog

All times local, 2026-08-05 evening.

| Time | Event |
|------|-------|
| ~19:5x | Spec drafted + 2-way consult (both REQUEST_CHANGES → addressed) |
| 19:59 | **GATE: spec-approval** requested |
| 20:32 | spec-approval approved (architect, with Gemini-only + steadfastness decisions) |
| 20:35–20:56 | Plan drafted + consult + steadfastness-in amendment |
| 20:56 | **GATE: plan-approval** approved |
| 20:57 | Implementation begins (Phase 1) |
| 21:06–21:25 | Phase 1 (export core), 3 iters → unanimous |
| 21:25–21:44 | Phase 2 (writer/manifest/CLI + committed dataset; architect eyeballed) |
| 21:44–22:20 | Phase 3 (SPA data layer); zombie-serve blocker resolved; force-advanced at iter 3 |
| 22:20–22:40 | Phase 4 (leaderboard + selectors), 2 iters → unanimous |
| 22:40–22:47 | Phase 5 (drill-down + judge selector), 1 iter → unanimous |
| 22:47–22:57 | Phase 6 (docs), 2 iters → unanimous |
| 22:57 | All phases complete → review |

### Autonomous Operation

| Period | Duration | Activity |
|--------|----------|----------|
| Spec + Plan | ~1h | drafting + 2 consult rounds each + 2 human gates |
| Human gate waits | ~35m | idle — spec-approval wait |
| Implementation → PR | ~2h | 6 phases, ~13 consultation rounds |

**Total wall clock** (spec gate → review): **~3h**
**Context window resets**: 0 (single continuous session)

## Consultation Iteration Summary

~30 consultation files (13 rounds × 2 models + spec/plan). Verdicts trended APPROVE; Codex was the
consistent first-round blocker on validation completeness and test coverage.

| Phase | Iters | Who Blocked | What They Caught |
|-------|-------|-------------|------------------|
| Specify | 1 | Codex + Claude | subject-id split, tiny-Opus-coverage weighting, truncation fallback |
| Plan | 1 | Codex + Claude | report-less Opus ingestion, v2 overlay, full-grid coverage denominator |
| Phase 1 | 3 | Codex | v2-orphan/dup-base rejection, file-order v2 precedence, disjoint-alias test |
| Phase 2 | 2 | Codex | coverage summary, validate-before-write + stale prune, committed-artifact tests |
| Phase 3 | 3 | Codex | shard↔manifest cross-validation, instant date sort, manifest-vocab validation |
| Phase 4 | 2 | Codex + Claude | surfacing data notices, real-number reconciliation, steadfastness coverage |
| Phase 5 | 1 | — | both APPROVE first round |
| Phase 6 | 2 | Claude | doc↔implementation contradictions (run selection, stale bullet, score ranges) |
| Review (PR) | 1+ | Codex | exclude contract-breaking shards, coverage sanity, all-5×3 reconciliation, doc/metadata accuracy |

**Most frequent blocker**: Codex — first-round REQUEST_CHANGES on most phases, focused on validation
completeness (reject bad input; cross-check against the contract) and exhaustive test coverage.

### Avoidable Iterations

1. **Validate against the contract, not just the shape.** Several Codex rounds (Phases 1–3) asked for
   rejecting/flagging out-of-contract input (orphan v2, duplicate identities, unknown vocab, manifest's
   own vocab). Building the full fail-fast/notice matrix up front would have collapsed ~3 iterations.
2. **Surface every notice in the UI the first time.** Phase 4 shipped a page that computed correctly
   but hid data-layer notices — the "display-first" rule should have been applied to the new page from
   the start, not retrofitted.
3. **Write the reconciliation-against-the-real-artifact test with the feature.** Both the Python and TS
   reconciliation tests were asked for by reviewers; they should have been part of the first cut.

## Consultation Feedback

Per-phase consult here was `["codex","claude"]` (Gemini can't see the worktree). Every blocking point
was verified against the real data/code before being incorporated.

### Specify (Round 1)
#### Codex — **Addressed**: exact size ceilings, runtime validation, alias-collision semantics, `n_expected` definition.
#### Claude — **Addressed**: subject-id alias split (Qwen `-Instruct`), tiny-Opus-coverage weighting, truncation-fallback gap, judge/subject disambiguation.

### Plan (Round 1)
#### Codex — **Addressed**: real ingestion adapter (report-less Opus runs), public breakdown helper, fixture/skipif test strategy.
#### Claude — **Addressed**: `load_run_dir` can't ingest Opus runs → purpose-built reader; `judgments_v2` overlay ordering; full-grid coverage denominator; steadfastness matched-cell.

### Phase 1 (Rounds 1–3)
#### Codex — **Addressed**: v2 rejects orphans, same-file dup base identities rejected, v2 file-order-last-wins, disjoint-alias `count==sum` test, committed fixtures.
#### Claude — APPROVE (with tightening suggestions, all adopted).

### Phase 2 (Rounds 1–2)
#### Codex — **Addressed**: manifest coverage summary, validate-before-write + stale-prune, committed-artifact + total-size tests; **Round 2 COMMENT**: CLI counts output + command test (adopted).
#### Claude — APPROVE.

### Phase 3 (Rounds 1–3)
#### Codex — **Addressed**: shard↔manifest cross-validation, instant-based run ordering, `shard.judges[]` validation, manifest's-own-vocab validation, absent-counts degradation. (Force-advanced at iter 3 with the final round's points already committed.)
#### Claude — APPROVE.

### Phase 4 (Rounds 1–2)
#### Codex + Claude — **Addressed**: surface all data-layer notices (no blank page), validate `?run=`, real-number reconciliation test, steadfastness coverage denominator, selector UI coverage.

### Phase 5 (Round 1)
#### Codex + Claude — No concerns raised (both APPROVE); only cosmetic suggestions.

### Phase 6 (Rounds 1–2)
#### Claude — **Addressed**: document run selection, replace stale "no results UI" bullet, byte-stable caveat, means-vs-steadfastness ranges, sorted judges example.
#### Codex — APPROVE.

### Review / PR (Rounds 1–3, porch 2-way)
#### Claude — APPROVE (reconciliation/reproducibility/size/coverage independently verified).
#### Codex — **Addressed** (r1): contract-breaking (tradition-mismatch) shards now **excluded** from standings, not just flagged; coverage sanity (`n_judged>n_expected` / wrong denominator) flagged; committed-artifact reconciliation extended to **all 5 subjects × 3 framings**; plan `Status`, commit count, and the "CI" wording corrected; `.claude/hooks/` gitignored. (r2, Claude) export **path-traversal guard** on run-id/tradition; notice dedup; manifest-sourced denominator. (r3) fail-fast on **unknown framing/pressure/scope** at ingest. **Deferred**: GitHub Actions job for the suites → Technical Debt.

### Architect Integration Review (3-way CMAP: Gemini APPROVE · Claude APPROVE · Codex REQUEST_CHANGES)
Three required items — all **Addressed**:
- **Full-grid invariant earned, not asserted**: `build_manifest` now validates complete Gemini coverage (every tradition × subject × framing × scope × pressure) before writing `full_grid: true`, failing fast otherwise (+ regression test with incomplete Gemini input). The UI ranking trusts that flag.
- **Ephemeral deploy-smoke port**: `deploy.test.ts` now acquires an OS-assigned free port (bind 0) instead of a hardcoded 4199 (which would collide under concurrent builders); keeps the detached spawn + process-group reap; the fixed-port pre-flight is gone.
- **Cleanups**: finished the `aggregate._mean_over` → `breakdown_mean` promotion (six call sites renamed, alias dropped); mirrored the exporter's path-segment guard on the SPA (`isSafePathSegment` rejects a hostile manifest-declared `entry.shard` before it reaches the raw URL) + test.

The committed dataset is byte-identical after these changes (verified via re-export diff). Non-blocking follow-ups noted by the CMAP (palette-parity check, steadfastness ±2 vs the ±1 color clamp, CI jobs) are recorded as Technical Debt / Verify-phase items.

## Lessons Learned

### What Went Well
- **Pre-aggregate-in-Python + trivial client math** made the paper-reconciliation criterion hold by
  construction — the SPA's only statistic is a mean-of-means, verified 1e-9 against the committed shards.
- **Verifying every reviewer claim against the real data first** caught that my own initial
  diagnoses (e.g. the node-26/PORT deploy failure) were wrong, and confirmed the load-bearing ones
  (subject split, live alias collision) before acting.
- **The reserved SPA seam + existing data-layer patterns** made the explorer genuinely additive.

### Challenges Encountered
- **A leaked `serve` from a defunct worktree** blocked the dispatcher and produced a misleading
  failure; the architect root-caused it (shared host port namespace). Cost ~1 investigation cycle +
  a hardening commit.
- **Report-less Opus runs** broke the canonical loader's assumptions — Phase 1 needed a purpose-built
  reader and a public breakdown helper (verified against the existing suite).
- **Codex's escalating validation bar** drove Phases 1–3 to their iteration ceilings; each round's
  ask was legitimate (reject bad input, cross-check the contract).

### What Would Be Done Differently
- Build the full input-validation / notice matrix up front (contract-level, not shape-level).
- Ship the real-artifact reconciliation test and UI notice surfacing with the first cut of each phase.

### Methodology Improvements
- SPIR/porch: the iter-3 force-advance is reasonable, but a builder should explicitly flag a
  force-advanced phase for the PR CMAP (done here in the thread + this review).
- Tooling: a shared-port guard/cleanup for builder worktrees would prevent the zombie-serve class of
  failure entirely.

## Architecture Updates

- Routed: **hot** (`arch-critical.md`) — added one fact: `results/<run-id>/` is a drop-in committed
  data tier the SPA reads at runtime like traditions (manifest + per-tradition shards, scores+metadata
  only), produced by `analysis export`; the `/results` leaderboard ranks Gemini-only and Opus is a
  badged validation layer that never re-ranks. Contract pointer: Spec 49 / `results/README.md`. (7→8
  facts, under cap; no demotion needed.) Full data contract lives in the new `results/README.md`.

## Lessons Learned Updates

- Routed: **hot** (`lessons-critical.md`) — the pre-aggregate-in-canonical-code + trivial-client-math
  reconciliation pattern (9→10 lessons, at cap).
- Routed: **cold** (`lessons-learned.md` § Toolchain & protocol) — porch force-advances a phase at its
  iter-3 safety ceiling even on a REQUEST_CHANGES.
- Routed: **cold** (`lessons-learned.md` § Verification discipline) — builder worktrees share the host
  port namespace; real-server tests must reap the process group + pre-flight the port.

## Technical Debt

- **No GitHub Actions job runs the JS/Python suites.** `.github/workflows/validate.yml` only validates
  traditions. The size ceilings, reconciliation, and all new tests are enforced by the **porch
  per-builder dispatcher** (`.codev/checks/test.sh`) at `porch done` and locally — not by GitHub CI on
  the PR. Adding CI jobs for `workflows/analysis` (pytest) and `apps/multibrowser` (vitest) is worthwhile
  follow-up so these guarantees hold on every push, not just at the porch gate. (Repo-wide gap, surfaced
  by this PR's review; the spec's "CI-checked" wording means this automated test gate.)
- Live Railway `railway up` verification is deferred to the Verify phase (manual, human-run).
- The `/results` bundle grows the main chunk (Vite's >500 KB warning, pre-existing); code-splitting the
  results route is a future optimization, not required for this feature.
- Bootstrap CIs (optional SHOULD, pooled-Gemini only) were not shipped — deliberate v1 exclusion.

## Notes

- The committed launch dataset (`results/20260803/`) was architect-eyeballed before commit (size +
  manifest) and independently re-verified (105 by-framing means + 35 steadfastness == `report.json`;
  counts reconcile 93,420 = 46,710×2, 40,114 = 31,114 + 9,000).
- The Opus framings-sample was sealed mid-implementation; the alias collision (~1,800 sunni-islam
  cells under both aliases) is a *tested* real code path, not theoretical.
