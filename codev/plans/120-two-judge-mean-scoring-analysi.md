# Plan: Two-judge mean scoring — analysis bundle, results tier, leaderboard ranking, and docs

**Specification**: [codev/specs/120-two-judge-mean-scoring-analysi.md](../specs/120-two-judge-mean-scoring-analysi.md)

## Executive Summary

Implements the spec's **Approach 1**: the combined two-judge score is produced by feeding the
canonical `analysis.aggregate.cell_scores` **all** judge layers at once (it already averages
present judges per cell), and the leaderboard / paper rank on it via an explicit manifest
**`ranking`** declaration. Two code-verified corrections from the plan review are baked in:

- **The combined block is a *separate top-level shard field* (`combined` / `combined_steadfastness`),
  never a judge key inside `means`.** Putting it in `means` would break
  `test_export_results.py:801` (`set(shard["means"]) <= manifest_models`), trip
  `shardConsistencyNotices` (`resultsModel.ts:280`) into an "unknown judge" runtime notice on every
  shard, and fail `results.data.test.ts:92`. A separate field preserves all per-judge guards by
  construction and sidesteps the `_coverage_from_exports` judge-set leak (it reads `means` keys).
- **Phase 1 re-judging uses a *filtered* sittings file + a pre-spend work-count assertion.**
  `judging judge` takes a whole `sittings.jsonl` with no cell targeting; handing it a full merged
  sittings file would judge ~21,840 cells (Opus-with-thinking, hundreds of USD) against the 20 USD
  ceiling with **no error**. The mechanism is spelled out per-cell in Phase 1.

Sequencing follows the architect's 2026-09-05 scope addition: **complete the grid first**, then
build the combined aggregation, then the real artifacts, the SPA, and the docs.

### ⚠️ Blocking dependency — architect confirmation before Phase 1 spend

Two items must be confirmed by the architect **before** Phase 1 spends anything (both raised by the
plan reviewers; a message is already sent):

1. **Baked #2 vs #7 conflict.** #2 says the `claude-opus-4-8` block stays *byte-identical*; #7
   adds 35 Opus verdicts that change it. These conflict on the Opus block. This plan does **not**
   autonomously declare a winner. Recommended reading (for confirmation): #7 (later, dated) governs
   — Gemini stays byte-identical (already complete; the paper-reconciliation-guarded value), the
   Opus block changes by *exactly* the grid-completion cells, combined is new.
2. **Per-cell verdict routing.** #7 says "write into `20260823-opus-fullgrid`", but that root holds
   only **stated + guided** sittings; the **26 unstated** gaps have no sitting there (their
   transcripts live in `20260803-merged`, and their Opus verdict layer is `20260803-unstated-opus`).
   So unstated verdicts must land in `20260803-unstated-opus` and stated/guided in
   `20260823-opus-fullgrid`. Confirm this routing.
3. (Minor) `dual_judge` in the v3 bundle stays computed on the sample Opus roots; it reads oddly
   once Opus is a complete grid. Confirm leaving it as-is vs recomputing on the full grid.

Grid enumeration is verified now (read-only, no spend): **35 missing Opus cells = 34 distinct
sittings** — judaism 14 (11u/2g/1s), roman-catholicism 6 (5u/1s), secular-sage 5 (5u),
sunni-islam 6 (1u/1s/4g), taoism 4 (4u); buddhism + eastern-christianity complete; **no Gemini
gaps**.

## Phases (Machine Readable)

<!-- REQUIRED: porch parses this JSON to track phase progress. Keep in sync; at least two phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Complete the two-judge grid (re-judge missing cells)"},
    {"id": "phase_2", "title": "Combined block + ranking declaration in both exporters"},
    {"id": "phase_3", "title": "Combined ranked-stats capability + v3 stats bundle"},
    {"id": "phase_4", "title": "Additive re-export of results/20260803"},
    {"id": "phase_5", "title": "Leaderboard ranks on the combined score (SPA)"},
    {"id": "phase_6", "title": "Docs + HOT mirrors"}
  ]
}
```

## Phase Breakdown

### Phase 1: Complete the two-judge grid (re-judge missing cells)

**Dependencies**: None — **but Phase 1 execution (spend) waits on the architect confirmation above.**

#### Objective

Re-judge the 34 sittings behind the 35 missing Opus cells (and any Gemini gaps — none found) so
both judges are strictly complete on all 93,420 cells, with a mechanism that cannot overspend.

#### Files to Create / Modify

- Source data (gitignored, main checkout via `../../tmp/judging-runs/`): new Opus verdicts appended
  into `20260803-unstated-opus/<t>/judgments.jsonl` (the 26 unstated) and
  `20260823-opus-fullgrid/<t>/judgments.jsonl` (the 9 stated/guided). Backups taken first.
- `results/REJUDGE-20260803.md` (committed runbook): enumeration method, exact commands, filtered
  sittings construction, the pre-spend assertion, retry policy, and usage-computed spend actuals.
- `workflows/analysis/tests/test_grid_completeness.py` (committed): a real-data test (skipped when
  roots absent) that, **per judge**, compares its resolved cell set against the canonical
  93,420-cell universe (both scopes) and asserts none missing — or reports the exact residual.
- `codev/state/aspir-120_thread.md`.

#### Deliverables

- [ ] **Enumerate** the missing cells → the 34 distinct sittings `(tradition, subject, scenario,
  pressure, framing)`, grouped by the layer that must receive the verdict (unstated →
  `20260803-unstated-opus`; stated/guided → `20260823-opus-fullgrid`).
- [ ] For each group, **build a filtered temp `sittings.jsonl`** containing ONLY those sittings,
  sourced from the root that holds the transcript (unstated ← `20260803-merged/<t>/sittings.jsonl`;
  stated/guided ← `20260823-opus-fullgrid/<t>/sittings.jsonl`).
- [ ] **Back up** each target `judgments.jsonl` (timestamped copy) before appending.
- [ ] **Pre-spend guard**: run the judge's own resume/work-count computation (or a dry count) and
  **assert the work-item count equals the enumerated sitting count** for that group; abort on any
  mismatch (catches both the over-judge and the silent under-judge failure modes).
- [ ] Re-judge with the identical configs — Opus `tmp/opus-judge.yaml` (thinking on), results-dir
  at the target root — up to 3 retries per still-empty cell; residual empties reported, not imputed.
- [ ] Assert `judgments_v2.jsonl` gains **0** rows (no unbudgeted disagreement overrides).
- [ ] Spend ≤ 20 USD via `taqwabench/.env` (Opus CEFE key); usage actuals captured.

#### Acceptance Criteria

- [ ] Both judges strictly complete on all 93,420 cells (or exact residual enumerated with reasons).
- [ ] Work-count assertion held before every spend; total spend ≤ 20 USD, actuals recorded.
- [ ] No duplicate identities and no new `judgments_v2.jsonl` rows post-merge.
- [ ] `test_grid_completeness` passes (real data) / skips cleanly (fixtures-only CI).

#### Test Plan

- Real-data completeness vs the canonical universe (per judge, both scopes).
- Idempotency: re-running the re-judge adds 0 new identities (via `resolve_judgments` dedup).
- Manual pre-flight: enumerate + assert work count == sitting count, and a cost estimate, before
  authorizing spend; stop + flag if approaching the ceiling.

### Phase 2: Combined block + ranking declaration in both exporters

**Dependencies**: None (fixture-testable; does not need Phase 1 data)

#### Objective

Emit a combined two-judge block per shard (separate top-level field) and a manifest `ranking`
declaration, additively, and re-shape the full-grid gate in **both** exporters — without disturbing
the per-judge blocks or any existing guard.

#### Files to Create / Modify

- `workflows/analysis/analysis/export_results.py`:
  - `COMBINED_KEY = "combined"`; assert disjoint from every real `manifest.judges[].model`.
  - Build combined `means`/`steadfastness` by feeding `cell_scores`/`breakdown_mean`/
    `_matched_steadfastness` **all** resolved judgments (not per-judge); carry them on
    `TraditionExport` as separate fields.
  - `serialize_tradition`: write top-level `"combined"` and `"combined_steadfastness"` fields
    (NOT inside `means`); `means`/`judges` unchanged.
  - `build_manifest`: add `ranking = {"rule": "mean_of_judges", "score_key": COMBINED_KEY,
    "judges": [<real judges>], "single_judge_cells": N}` (N = cells with exactly one judge, both
    scopes). Re-shape the gate: replace "exactly one `rankable`" with "**≥1 real judge strictly
    complete**" (`_assert_full_grid` on ≥1 real judge); keep `rankable`/`full_grid`/`coverage`
    per-judge metadata. The combined key never enters `TraditionExport.judges`, the shard `judges`
    list, `_coverage_from_exports`, or `JUDGE_UI[...]`.
- `workflows/analysis/analysis/export_raw.py`: re-shape its ranking-integrity guard
  (`export_raw.py:573-588`) from "exactly one rankable, strictly complete" to "**≥1 real judge
  strictly complete**", and emit the same `ranking` declaration in the raw manifest. **No** combined
  per-cell block in raw shards (they carry transcripts + per-judge verdicts); raw viewer UI
  untouched (scoped out in the spec).
- `workflows/analysis/tests/test_export_results.py`, `test_export_raw*.py`: new tests.

#### Deliverables

- [ ] Top-level `combined`/`combined_steadfastness` shard fields; manifest `ranking` declaration
  (both exporters where the catalog declares ranking).
- [ ] Re-shaped gate in both exporters; per-judge metadata preserved.
- [ ] Tests.

#### Acceptance Criteria

- [ ] **Equivalence** (fixture): combined per-tradition mean == mean of the two per-judge means on
  fully double-judged cell sets, differing only by single-judge cells.
- [ ] **Additive**: per-judge `means`/`judges` byte-identical before/after adding combined;
  `test_export_results.py:801` and `shardConsistencyNotices` clean (combined lives outside `means`).
- [ ] **`ranking`**: `score_key` present + disjoint from real model ids; `single_judge_cells`
  correct on a fixture with a deliberate single-judge cell.
- [ ] **Gate (both exporters)**: no strictly-complete real judge → fail fast; ≥1 strictly-complete
  real judge → success even without a `rankable`-flagged judge.
- [ ] analysis pytest green (incl. existing per-judge/coverage/full_grid/raw tests unchanged).

#### Test Plan

- Unit: equivalence, single-judge contribution, `single_judge_cells`, combined-key disjointness +
  absence from `judges`/coverage, gate re-shape both directions, both exporters.
- Regression: full existing analysis + raw suites.

### Phase 3: Combined ranked-stats capability + v3 stats bundle

**Dependencies**: Phase 1 (completed grid), Phase 2 (combined aggregation)

#### Objective

A committed, tested way to compute the combined **ranked** aggregates over the four roots, and the
produced v3 `stats_bundle.json` — same schema as v2, ranked on the combined score, v2 not touched.

#### Files to Create / Modify

- `workflows/analysis/analysis/combined_stats.py` (new) + `cli.py` wiring: an
  **`analysis combined-stats`** command (NOT a `report` flag — `load_corpus` requires `report.json`
  per dir and rejects a duplicate tradition across roots, so it structurally cannot ingest the four
  roots). Seam: `read_run_root` + `resolve_judgments` (multi-root, priority-ordered) → a shim run
  object exposing `.judgments`/`.subjects`/`.report` → `aggregate_tradition` (duck-typed) →
  `compute_tradition_stats`. Feeding all judges' rows makes the aggregate the combined cell score.
  Deterministic, byte-stable JSON output.
- Gitignored (main checkout): `tmp/report_figs_20260803_v3.py` — a v3 of
  `report_figs_20260803_v2.py` whose **load step is swapped** so its `acc`/`acc1` accumulators
  receive canonical **cell** values (mean over present judges, computed by `cell_scores` /
  imported merge from `analysis.export_results`) instead of raw Gemini judgments — then every
  bundle field (`subj_overall`, `tier`, …) becomes combined automatically. It does **not** append
  both judges' raw rows (that pools per-judgment and diverges on single-judge cells).
  `dual_judge`/`meta` unchanged. Writes `…/analysis-out/figures-report-v3/stats_bundle.json`.
- `results/README.md` (or the runbook): document the v3-bundle build command.
- `workflows/analysis/tests/`: reconciliation + capability tests.

#### Deliverables

- [ ] Committed `analysis combined-stats` capability (documented invocation).
- [ ] v3 `stats_bundle.json` over the four roots (results/README order); v2 untouched.
- [ ] Reconciliation test.

#### Acceptance Criteria

- [ ] v3 bundle exists, matches v2 top-level keys, score fields combined, `dual_judge`/`meta`
  unchanged in shape.
- [ ] **Reconciliation** (real-data, skipped when roots absent): combined mean-of-means
  (`scope=full`, `pressure=all`) == v3 `subj_overall` to ≤ 1e-9.
- [ ] Capability output byte-stable on a fixture; analysis pytest green.

#### Test Plan

- Real-data reconciliation (skip without roots); fixture determinism of `combined-stats`.
- Manual: run the v3 figs step; spot-check keys so `tmp/paper_figs_multibench.py` consumes it
  unchanged (paper render is the architect's step).

### Phase 4: Additive re-export of results/20260803

**Dependencies**: Phase 1, 2, 3

#### Objective

Regenerate the committed `results/20260803/` dataset over the completed grid: combined block +
`ranking` declaration, Gemini block byte-identical, Opus block changed only by grid-completion cells.

#### Files to Create / Modify

- `results/20260803/manifest.json` + `results/20260803/*.json` (re-exported via `analysis export`).
- `workflows/analysis/tests/fixtures/results-20260803-baseline/` (committed golden): the
  **pre-change** per-judge blocks, captured via `git show HEAD:results/20260803/<t>.json` into a
  pinned baseline (shards are single-line minified JSON — a runtime "git diff" is impossible, so
  the baseline must be pinned).
- `workflows/analysis/tests/test_export_results.py`: structural byte-identity + delta-bounding +
  reconciliation assertions on the committed artifact.

#### Deliverables

- [ ] Re-exported dataset: `combined` block present, `ranking.single_judge_cells` = residual
  (target 0), Gemini per-judge block structurally byte-identical, Opus per-judge block delta bounded.
- [ ] Pinned baseline fixture + tests.

#### Acceptance Criteria

- [ ] **Gemini byte-identical**: each re-exported shard's `means["gemini-3.6-flash"]` sub-tree
  equals the pinned baseline exactly; the existing v2 Gemini paper-reconciliation test passes
  unchanged.
- [ ] **Opus delta bounded**: Opus differs from the baseline only at slices whose `(subject,
  framing, scope, pressure)` contain a grid-completion cell (their `n_judged` rises by exactly the
  added cells); every untouched Opus slice equals the baseline. Documented in the review.
- [ ] Combined mean-of-means on the committed artifact reconciles with the v3 bundle (≤ 1e-9).
- [ ] Size ceilings satisfied; size/consistency tests pass.

#### Test Plan

- Committed-artifact tests: Gemini sub-tree equality vs pinned baseline; Opus delta bounded to
  touched slices; combined block + `ranking` present/correct; sizes; v2 + v3 reconciliation.

### Phase 5: Leaderboard ranks on the combined score (SPA)

**Dependencies**: Phase 2 (manifest/shard shape); Phase 4 (real dataset)

#### Objective

Rank the `/results` leaderboard on the combined block via the manifest `ranking` declaration, keep
the Gemini/Opus drill-down selector, adjust judge-role copy so the mean reads as headline, and
handle legacy/malformed manifests — leaving the raw/AFB catalog untouched.

#### Files to Create / Modify

- `apps/multibrowser/src/lib/resultsModel.ts`: parse the new top-level `combined`/
  `combined_steadfastness` shard fields and the manifest `ranking` declaration (zod, non-strict —
  no schema-version bump). `shardConsistencyNotices` needs no change (combined is outside `means`),
  but add a check that a declared `ranking.score_key` block is present in each shard.
- `apps/multibrowser/src/lib/leaderboard.ts`: rank on `ranking.score_key` → `shard.combined` when
  present; fall back to `rankable`/Gemini only for a **legacy** manifest (no `ranking`); a malformed
  `ranking` surfaces a visible notice, not a silent revert. Drill-down selector still resolves each
  real judge from `means`.
- `apps/multibrowser/src/routes/ResultsPage.tsx` + judge-role labels: Gemini/Opus as co-equal
  component judges of the headline mean; drop "ranking vs validation" framing on the score board.
  **Do not** touch `RawComparison.tsx` / `ReviewScenarioPage.tsx` / raw-catalog `rankable`.
- `apps/multibrowser/src/lib/leaderboard.test.ts` (+ results tests): updated pins.

#### Deliverables

- [ ] Leaderboard ranks on the combined block; selector unchanged in function; judge-role copy
  updated; legacy + each malformed case handled.
- [ ] Tests.

#### Acceptance Criteria

- [ ] Ranked standings use the combined block; ordering differs from Gemini-only where judges
  disagree (fixture).
- [ ] Legacy manifest (no `ranking`) still ranks (Gemini fallback).
- [ ] **Each** malformed case shows a visible notice: unknown `rule`, missing `score_key` shard
  block, unknown/duplicate `judges`, `score_key` colliding with a real model id.
- [ ] Existing Gemini paper pin retained; **no** invented combined pin.
- [ ] multibrowser vitest green; raw/AFB catalog tests unchanged and passing.

#### Test Plan

- vitest: combined ranking on a fixture; legacy fallback; the four malformed cases individually;
  selector resolves each real judge; raw catalog untouched.

### Phase 6: Docs + HOT mirrors

**Dependencies**: Phase 2, 4, 5 (final contract)

#### Objective

Update governance/docs to describe two-judge-mean ranking and keep the HOT mirrors in sync.

#### Files to Create / Modify

- `results/README.md`: correct **every** Gemini-only-ranking assertion (intro, `judges`
  schema-table row, leaderboard + published-runs sections); add a schema-table row for `ranking`;
  note the strict full-grid gate now guards a **component** of the ranked score.
- `codev/resources/arch-critical.md`: update the one leaderboard fact line (ranks on the two-judge
  mean; gate guards a component).
- `CLAUDE.md`, `AGENTS.md`: regenerate the `BEGIN…END CODEV HOT CONTEXT` blocks verbatim.
- `codev/reviews/120-two-judge-mean-scoring-analysi.md`: the review (verification evidence, spend
  actuals, the Gemini-byte-identity + Opus-delta note, lessons).

#### Deliverables

- [ ] README + arch-critical fact + regenerated mirrors; review doc.

#### Acceptance Criteria

- [ ] `apps/tradition_validator/tests/test_governance_docs.py` passes (mirror in sync, caps, map).
- [ ] No stale Gemini-only-ranking assertion remains in `results/README.md`.

#### Test Plan

- `test_governance_docs.py`; a grep audit for residual "Gemini-only"/"rankable"-ranking language.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Baked #2 (Opus byte-identical) vs #7 (add Opus verdicts) conflict | High | Medium | **Not resolved autonomously** — architect confirmation gates Phase 1 spend + Phase 4 Opus handling; recommended reading documented above. |
| Re-judge silently over-judges (~21,840 cells) → massive overspend | Medium | High | Filtered temp sittings (only the 34 missing) + **pre-spend work-count assertion** == enumerated count; abort on mismatch. |
| 26 unstated cells unreachable via `20260823-opus-fullgrid` | High | High | Route unstated sittings from `20260803-merged`, verdicts into `20260803-unstated-opus`; per-cell routing confirmed with architect. |
| Combined key trips shard guards / runtime notices | Medium | High | Combined lives in a **separate top-level field**, never in `means`; per-judge guards pass by construction. |
| In-place append corrupts a gitignored source layer (no rollback) | Low | High | Timestamped backup of each `judgments.jsonl` before appending; assert `v2` gains 0 rows. |
| v3 figs step diverges from the cell rule | Medium | High | Swap the **load** to canonical cell values (import merge from `export_results`); never append both judges' raw rows. |
| Byte-identity test not implementable on minified shards | Medium | Medium | Pin a baseline via `git show HEAD:results/20260803/<t>.json`; structural sub-tree comparison. |
| Wrong judge config drifts new verdicts | Low | High | `tmp/opus-judge.yaml` verbatim (thinking on); write into the correct layer so normalize/overlay/dedup applies. |
| SPA silently reverts to Gemini on a malformed new manifest | Low | Medium | Legacy (no `ranking`) → fallback; each malformed case → visible notice; tests all cases. |
| Touching #119's surface | Low | Medium | Land first; do not touch `traditions/protestant-unified` or #119 files. |

## Documentation Updates

`results/README.md` (ranking assertions + `ranking` schema row), `results/REJUDGE-20260803.md`
(re-judge runbook + spend actuals), `codev/resources/arch-critical.md` (one fact),
`CLAUDE.md`/`AGENTS.md` (regenerated HOT mirrors), and the review doc. No change to
`results-raw/README.md` or the raw/AFB catalog docs / raw viewer UI.
