# Plan: Two-judge mean scoring — analysis bundle, results tier, leaderboard ranking, and docs

**Specification**: [codev/specs/120-two-judge-mean-scoring-analysi.md](../specs/120-two-judge-mean-scoring-analysi.md)

## Executive Summary

Implements the spec's **Approach 1** (recommended): the combined two-judge score is a **synthetic
block** in each results shard, aggregated by feeding the canonical `analysis.aggregate.cell_scores`
**all** judge layers at once (it already averages present judges per cell), and the leaderboard /
paper rank on that block via an explicit manifest **`ranking`** declaration. The per-judge blocks
stay additive; the committed/tested surface is the combined aggregation plus its equivalence and
reconciliation guards. The full paper `stats_bundle.json` (v3) is produced by a documented figs
step reusing a committed combined ranked-aggregation capability — the same producer shape v2 has.

Sequencing follows the architect's 2026-09-05 scope addition: **complete the grid first**
(re-judge the 35 Opus empty-response cells, and any Gemini gaps, with identical configs), then
build the combined aggregation, then produce the real artifacts (v3 bundle + re-exported dataset),
then the SPA and docs.

**Baked-decision tension surfaced (see Risks + Phase 4).** Baked #2 says the `claude-opus-4-8`
block stays *byte-identical*; baked #7 (the later scope addition) writes 35 new Opus verdicts into
the layer. These conflict on the Opus block. Resolution taken: the later, dated #7 governs — after
grid completion the **Gemini** block stays byte-identical (it is what the paper-reconciliation
guard protects and Gemini is already complete), while the **Opus** block changes by *exactly* the
grid-completion cells and nothing else. Flagged to the architect for confirmation; non-blocking.

## Phases (Machine Readable)

<!-- REQUIRED: porch parses this JSON to track phase progress. Keep in sync; at least two phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Complete the two-judge grid (re-judge missing cells)"},
    {"id": "phase_2", "title": "Combined block + ranking declaration in the exporter"},
    {"id": "phase_3", "title": "Combined ranked-stats capability + v3 stats bundle"},
    {"id": "phase_4", "title": "Additive re-export of results/20260803"},
    {"id": "phase_5", "title": "Leaderboard ranks on the combined score (SPA)"},
    {"id": "phase_6", "title": "Docs + HOT mirrors"}
  ]
}
```

## Phase Breakdown

### Phase 1: Complete the two-judge grid (re-judge missing cells)

**Dependencies**: None

#### Objective

Re-judge every cell missing a verdict from either judge so both judges are strictly complete on
all 93,420 cells of `20260803`, eliminating single-judge fallback before any rescoring. Delivers
the completed source grid the downstream artifacts rank on, plus a committed, reproducible runbook
and a coverage-verification test.

#### Files to Create / Modify

- Source data (gitignored, main checkout via `../../tmp/judging-runs/`): new Opus verdicts appended
  into `20260823-opus-fullgrid/<tradition>/` (and Gemini into the record layer only if gaps exist).
- `results/REJUDGE-20260803.md` (committed runbook): the exact enumeration method, the
  `python -m judging judge … --config tmp/opus-judge.yaml` commands, retry policy, and the
  usage-computed spend actuals.
- `workflows/analysis/tests/test_grid_completeness.py` (committed): a real-data test (skipped when
  roots absent) asserting both judges reach the complete grid over the four roots — or documenting
  the exact residual single-judge cells.
- `codev/state/aspir-120_thread.md`.

#### Deliverables

- [ ] Missing-cell enumeration: the set of `(subject, scenario, pressure, framing, scope)` cells
  lacking an Opus verdict (expected 35: 26 unstated, 3 stated, 6 guided) and any lacking Gemini.
- [ ] Re-judge those cells over their existing sittings with the identical configs (Opus:
  `tmp/opus-judge.yaml`, thinking on; Gemini: record config), writing verdicts into the existing
  layers; up to 3 retries per cell; residual empties reported, not imputed.
- [ ] Spend ≤ 20 USD via the `taqwabench/.env` seam (Opus CEFE key; Gemini OpenRouter); usage
  actuals captured for the review.
- [ ] Committed runbook + grid-completeness test.

#### Acceptance Criteria

- [ ] Both judges strictly complete on all 93,420 cells (or the exact residual single-judge cells
  are enumerated with reasons); no duplicate verdicts introduced (dedup by identity + `ts`/priority).
- [ ] Spend within budget; actuals recorded.
- [ ] Grid-completeness test passes (real data) / skips cleanly (fixtures-only CI).

#### Test Plan

- Real-data: `test_grid_completeness` compares Gemini vs Opus resolved cell sets over the four
  roots and asserts the symmetric difference is empty (or the documented residual).
- Idempotency: re-running the re-judge does not add duplicate identities (verify via
  `resolve_judgments` dedup).
- Manual: dry-run the enumeration + a cost estimate before spending; stop and flag if approaching
  the ceiling.

### Phase 2: Combined block + ranking declaration in the exporter

**Dependencies**: None (fixture-testable; does not need Phase 1 data)

#### Objective

Teach the results exporter to emit a **combined** two-judge block per shard and a manifest
**`ranking`** declaration, additively, while re-shaping the full-grid gate — without disturbing the
per-judge blocks.

#### Files to Create / Modify

- `workflows/analysis/analysis/export_results.py`:
  - Add a reserved combined key (e.g. `COMBINED_KEY = "mean_of_judges"`); assert it is disjoint
    from every real `manifest.judges[].model`.
  - Build the combined `means`/`steadfastness` by feeding `cell_scores` **all** resolved judgments
    (not per-judge), reusing `breakdown_mean` / `_matched_steadfastness`; write it into the shard
    under the combined key alongside — never inside — the per-judge blocks.
  - Add `build_manifest` → `ranking = {"rule": "mean_of_judges", "score_key": COMBINED_KEY,
    "judges": [<real judges>], "single_judge_cells": N}`, where `N` = cells carrying exactly one
    judge's verdict (both scopes).
  - Re-shape the gate: replace the "exactly one `rankable`" invariant with "**≥1 real judge
    strictly complete**" (`_assert_full_grid` on at least one real judge); keep `rankable`/
    `full_grid`/`coverage` per-judge metadata for the selector + legacy fallback.
  - Guard: the combined key must never enter `TraditionExport.judges`, the shard `judges` list,
    `coverage_counts_from_judged`, or the `JUDGE_UI[model]` lookup.
- `workflows/analysis/tests/test_export_results.py`: new tests (below).

#### Deliverables

- [ ] Combined block in shards; `ranking` declaration in the manifest with `score_key`,
  real-judge list, and `single_judge_cells`.
- [ ] Re-shaped gate + preserved per-judge metadata.
- [ ] Tests.

#### Acceptance Criteria

- [ ] **Equivalence**: on fixtures, the combined per-tradition mean equals the mean of the two
  per-judge means on fully double-judged cell sets, differing only by single-judge cells.
- [ ] **Additive/byte-identical**: per-judge blocks in a fixture export are byte-identical
  before/after adding the combined block.
- [ ] **`ranking` shape**: `score_key` present and disjoint from real model ids; `single_judge_cells`
  correct on a fixture with a deliberate single-judge cell.
- [ ] **Gate**: an export with **no** strictly-complete real judge fails fast; an export with ≥1
  strictly-complete judge succeeds even without a `rankable`-flagged judge.
- [ ] analysis pytest green.

#### Test Plan

- Unit: equivalence, single-judge contribution, `single_judge_cells` count, combined-key
  disjointness, gate re-shape (both directions), combined key absent from `judges`/coverage.
- Regression: existing per-judge/coverage/full_grid tests still pass unchanged.

### Phase 3: Combined ranked-stats capability + v3 stats bundle

**Dependencies**: Phase 1 (completed grid), Phase 2 (combined aggregation)

#### Objective

Provide a committed, tested way to compute the combined **ranked** aggregates over multiple roots,
and produce the v3 `stats_bundle.json` the architect regenerates the paper from — same schema as
v2, ranked on the combined score, without overwriting v2.

#### Files to Create / Modify

- `workflows/analysis/analysis/` — a committed combined ranked-aggregation capability: either a
  `--combined` flag on `analysis report` or a small `analysis combined-stats` command that takes
  the four roots and emits the combined per-(subject, tradition, framing, scope, pressure) means
  (+ CIs) via `cell_scores`. Reuse `aggregate`/`stats`; add CLI wiring in `cli.py`.
- `workflows/analysis/tests/test_*` — reconciliation + capability tests.
- Gitignored (main checkout): `tmp/report_figs_20260803_v3.py` (documented adaptation of
  `report_figs_20260803_v2.py`: score fields recomputed on the combined cells per the spec's
  enumeration; `dual_judge`/`meta` unchanged), writing
  `…/analysis-out/figures-report-v3/stats_bundle.json`.
- `results/REJUDGE-20260803.md` or `results/README.md` — document the v3-bundle build command.

#### Deliverables

- [ ] Committed combined ranked-aggregation capability (documented invocation).
- [ ] v3 `stats_bundle.json` produced over the four roots (results/README order), v2 not touched.
- [ ] Reconciliation test.

#### Acceptance Criteria

- [ ] The v3 bundle exists, matches v2's top-level keys, and its score fields differ from v2 where
  the two judges differ; `dual_judge`/`meta` unchanged in shape.
- [ ] **Reconciliation**: a real-data test (skipped when roots absent) asserts the combined
  mean-of-means (`scope=full`, `pressure=all`) equals the v3 bundle's `subj_overall` to ≤ 1e-9.
- [ ] analysis pytest green.

#### Test Plan

- Real-data reconciliation (skipped without roots); the committed capability's output is
  deterministic/byte-stable on a fixture.
- Manual: run the v3 figs step; confirm `tmp/paper_figs_multibench.py` consumes it unchanged
  (spot-check keys) — the paper render itself is the architect's step.

### Phase 4: Additive re-export of results/20260803

**Dependencies**: Phase 1, 2, 3

#### Objective

Regenerate the committed `results/20260803/` dataset over the completed four-root grid so it
carries the combined block + `ranking` declaration, with the Gemini block byte-identical and the
Opus block changed only by the grid-completion cells.

#### Files to Create / Modify

- `results/20260803/manifest.json` + `results/20260803/*.json` (re-exported via `analysis export`).
- `workflows/analysis/tests/test_export_results.py` — byte-identity + reconciliation assertions on
  the committed artifact.

#### Deliverables

- [ ] Re-exported dataset: combined block present, `ranking.single_judge_cells` = residual (target
  0), Gemini block byte-identical, Opus block delta = exactly the grid-completion cells.
- [ ] Tests over the committed artifact.

#### Acceptance Criteria

- [ ] **Gemini byte-identical** vs the pre-change shards; existing v2 Gemini paper-reconciliation
  test still passes unchanged.
- [ ] **Opus block** differs from the pre-change shards *only* at the grid-completion cells
  (diff is the 35 cells + their affected slice means), documented in the review.
- [ ] Combined mean-of-means on the committed artifact reconciles with the v3 bundle (≤ 1e-9).
- [ ] Size ceilings still satisfied; size/consistency tests pass.

#### Test Plan

- Committed-artifact tests: Gemini byte-identity (git diff scoped to the Gemini sub-tree of each
  shard), Opus delta bounded to the grid-completion cells, combined block present, `ranking` fields
  correct, sizes within ceilings, v2 + v3 reconciliation.

### Phase 5: Leaderboard ranks on the combined score (SPA)

**Dependencies**: Phase 2 (manifest/shard shape); Phase 4 (real dataset, for a real-data test)

#### Objective

Make the `/results` leaderboard rank on the combined score via the manifest `ranking` declaration,
keep the Gemini/Opus drill-down selector, adjust the judge-role copy so the mean reads as the
headline, and handle legacy/malformed manifests correctly — leaving the raw/AFB catalog untouched.

#### Files to Create / Modify

- `apps/multibrowser/src/lib/resultsModel.ts`: parse the `ranking` declaration (zod, non-strict —
  no schema-version bump); expose `score_key`/`rule`/`judges`/`single_judge_cells`.
- `apps/multibrowser/src/lib/leaderboard.ts`: rank on `ranking.score_key` when present; fall back
  to `rankable`/Gemini only for a **legacy** manifest (no `ranking`); a malformed `ranking`
  surfaces a visible notice (not a silent revert). Keep the drill-down selector resolving each real
  judge.
- `apps/multibrowser/src/routes/ResultsPage.tsx` (+ judge-role labels): Gemini/Opus as co-equal
  component judges of the headline mean; drop the "ranking vs validation" framing on the score
  board. **Do not** touch `RawComparison.tsx` / `ReviewScenarioPage.tsx` / raw-catalog `rankable`.
- `apps/multibrowser/src/lib/leaderboard.test.ts` (+ any results tests): updated pins.

#### Deliverables

- [ ] Leaderboard ranks on the combined block; selector unchanged in function; judge-role copy
  updated; legacy + malformed manifest paths handled.
- [ ] Tests.

#### Acceptance Criteria

- [ ] Ranked standings use the combined block; ordering differs from Gemini-only where the judges
  disagree (fixture).
- [ ] Legacy manifest (no `ranking`) still ranks (Gemini fallback); malformed `ranking` shows a
  visible notice.
- [ ] Existing Gemini paper pin retained; **no** invented combined pin (architect adds later).
- [ ] multibrowser vitest green; raw/AFB catalog tests unchanged and passing.

#### Test Plan

- Unit (vitest): combined ranking on a fixture manifest+shards; legacy fallback; malformed →
  notice; selector resolves each real judge; raw catalog untouched.

### Phase 6: Docs + HOT mirrors

**Dependencies**: Phase 2, 4, 5 (final contract)

#### Objective

Update the governance/docs to describe two-judge-mean ranking and keep the HOT mirrors in sync.

#### Files to Create / Modify

- `results/README.md`: correct **every** Gemini-only-ranking assertion (intro, `judges`
  schema-table row, leaderboard + published-runs sections); add a schema-table row for the new
  `ranking` field; note the strict full-grid gate now guards a **component** of the ranked score.
- `codev/resources/arch-critical.md`: update the one leaderboard fact line (ranks on the two-judge
  mean; gate guards a component).
- `CLAUDE.md`, `AGENTS.md`: regenerate the `BEGIN…END CODEV HOT CONTEXT` blocks verbatim from the
  hot files.
- `codev/reviews/120-two-judge-mean-scoring-analysi.md`: the review (verification evidence, spend
  actuals, the byte-identity/Opus-delta note, lessons).

#### Deliverables

- [ ] README + arch-critical fact + regenerated mirrors; review doc.

#### Acceptance Criteria

- [ ] `apps/tradition_validator/tests/test_governance_docs.py` passes (mirror in sync, caps
  respected, map accurate).
- [ ] No stale Gemini-only-ranking assertion remains in `results/README.md`.

#### Test Plan

- `test_governance_docs.py`; a grep audit for residual "Gemini-only"/"rankable"-ranking language in
  `results/README.md`.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Baked #2 (Opus byte-identical) vs baked #7 (add Opus verdicts) conflict | High | Medium | Resolution: #7 (later, dated) governs the Opus block; Gemini stays byte-identical (the guarded value). Flagged to architect; Phase 4 bounds the Opus diff to exactly the grid-completion cells. |
| Re-judging overspends / cells stay empty | Low | Medium | Only ~35 cells; estimate first; 3 retries then report (no impute); stop + flag near ceiling; report actuals. |
| Wrong judge config drifts new verdicts | Low | High | Use `tmp/opus-judge.yaml` verbatim (thinking on) / record Gemini config; write into the same layer so normalize/overlay/dedup applies. |
| Combined key collides with / leaks into the real judges list | Low | High | Reserved non-model key; assert disjoint; keep it out of `judges`/coverage/`JUDGE_UI` (Phase 2 guard + test). |
| v3 bundle schema drifts from v2 → paper script breaks | Medium | High | Recompute only the enumerated score fields; keep `dual_judge`/`meta` shape; diff v3 vs v2 top-level keys; spot-check paper-script consumption. |
| SPA silently reverts to Gemini on a malformed new manifest | Low | Medium | Legacy (no `ranking`) → fallback; malformed `ranking` → visible notice; tests both paths. |
| Touching #119's surface | Low | Medium | Land first; do not touch `traditions/protestant-unified` or #119 files; architect coordinates the rebase. |

## Documentation Updates

- `results/README.md` (ranking assertions + `ranking` schema row), `results/REJUDGE-20260803.md`
  (re-judge runbook + spend actuals), `codev/resources/arch-critical.md` (one fact),
  `CLAUDE.md`/`AGENTS.md` (regenerated HOT mirrors), and the review doc. No change to
  `results-raw/README.md` or the raw/AFB catalog docs.
