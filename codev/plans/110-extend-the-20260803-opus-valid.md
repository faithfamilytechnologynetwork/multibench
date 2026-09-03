# Plan: Extend the 20260803 Opus validation layer to the full grid (stated+guided) and re-export

**Specification**: [codev/specs/110-extend-the-20260803-opus-valid.md](../specs/110-extend-the-20260803-opus-valid.md)

## Executive Summary

The spec's approach is a three-part change — a #96 exporter refactor, a coordinated SPA rewire,
and an in-place data re-export — plus paper artifacts. The **ordering** is the load-bearing
design decision: the exporter refactor and the SPA `rankable` support land **before** the
data re-export, so every intermediate commit keeps **Gemini** as the ranking judge and Opus can
never accidentally re-rank (the highest-severity risk). Concretely:

1. **Exporter refactor (Python)** — earn `full_grid` tolerantly (`FULL_GRID_MIN_COVERAGE=0.95`,
   all three framings), add a static `rankable` flag and a per-judge `coverage` fraction, in
   **both** `export_results.py` and `export_raw.py` (they share `JUDGE_UI`). No committed data
   changes yet, so the SPA is unaffected.
2. **SPA rewire (TypeScript)** — accept optional `rankable`/`coverage`, move every
   ranking-proxy site to `rankable` with a `?? fullGrid ?? gemini` fallback, keep `fullGrid`
   only for sample captions. Committed manifests still lack `rankable`, so the fallback keeps
   Gemini ranking — the SPA is now *ready* for the new manifest without depending on it.
3. **Data re-export** — regenerate `results/20260803` + `results-raw/20260803` from the four
   roots. The committed manifest now carries earned Opus `full_grid:true`, `rankable:false`,
   `coverage≈0.9992`; the SPA (already updated) selects Gemini via `rankable`. Verify Gemini
   byte-identity, cross-tier fingerprint parity, and coverage.
4. **Paper artifacts + summary** — regenerate `tab:djtier`, `fig:dualjudge`, agreement stats
   into `../multibench-papers/{figures,tables}/` (uncommitted there); commit an in-repo markdown
   numbers summary.

Each phase is one atomic commit; all four land in a single PR (builder PR strategy).

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Earn full_grid + rankable + coverage in both exporters"},
    {"id": "phase_2", "title": "SPA: rank by rankable, keep fullGrid for sample captions"},
    {"id": "phase_3", "title": "Re-export results/ and results-raw/ for 20260803 in place"},
    {"id": "phase_4", "title": "Dual-judge paper artifacts + numbers summary"}
  ]
}
```

## Phase Breakdown

### Phase 1: Earn full_grid + rankable + coverage in both exporters

**Dependencies**: None

#### Objective

Close #96 in the Python layer: `full_grid` becomes earned-from-coverage (tolerant), ranking
eligibility becomes a separate static `rankable`, and each judge gains a real `coverage`
fraction — consistently across `export_results.py` (score manifest) and `export_raw.py` (raw
catalog), which share `JUDGE_UI`. Delivers the corrected metadata contract with **no** change to
committed datasets or the SPA yet.

#### Files to Create / Modify

- `workflows/analysis/analysis/export_results.py` — split `JUDGE_UI` to `{key, rankable}`; add
  `FULL_GRID_MIN_COVERAGE = 0.95`, `coverage_ratio(...)`/`judge_coverage(...)` and
  `earns_full_grid(...)`; refactor the strict walk to `assert_strict_full_grid(...)` (reused for
  rankable judges); `build_manifest` emits per judge `{key, model, aliases, full_grid (earned),
  rankable (static), coverage (fraction)}`; assert exactly one rankable judge; rankable ⇒ strict
  complete or fail-fast; fix stale docstring/comment (L504-511, L558-559).
- `workflows/analysis/analysis/export_raw.py` — source the catalog judges' `fullGrid`/`rankable`/
  `coverage` from a **shared** earned helper (no static `full_grid` key read at L534); keep
  `JUDGE_UI[...]["key"]`.
- Extract the shared coverage/earn/rankable logic to a single home (e.g. a small helper block in
  `export_results.py`) imported by `export_raw.py`, so the two tiers cannot disagree.
- `workflows/analysis/tests/test_export_results.py`, `test_export_raw.py`, `test_export_afb.py` —
  update the catalog/manifest shape assertions; add the new coverage/rankable tests.

#### Deliverables

- [ ] `full_grid` earned via the tolerant predicate; `rankable` static; `coverage` fraction present.
- [ ] `export_raw.py` catalog carries the same earned `full_grid`/`rankable`/`coverage`.
- [ ] Stale "Opus stated/guided sample" docstring/comment corrected.
- [ ] Tests: (a) 14.5%-sample framing does NOT earn `full_grid`; 99.9% state DOES (both sides of
      threshold); (b) `rankable` static & coverage-independent (earning `full_grid` never makes a
      judge rankable); (c) rankable + strict-incomplete ⇒ fail-fast; (d) 0 or >1 rankable ⇒
      fail-fast; (e) `coverage` == actual `n_judged/n_expected`.

#### Acceptance Criteria

- [ ] `uv --project workflows/analysis run pytest workflows/analysis` passes, incl. the existing
      `test_committed_dataset_reconciles_with_paper` + sealed-launch parity (Gemini unchanged).
- [ ] No committed `results/`/`results-raw/` file changes in this phase.

#### Test Plan

Unit: fixture-based tests for `earns_full_grid`, `judge_coverage`, `assert_strict_full_grid`, the
one-rankable invariant, and both exporters' judge-metadata shape. Regression: full existing suite
green (reconciliation is the Gemini-drift guard).

### Phase 2: SPA — rank by rankable, keep fullGrid for sample captions

**Dependencies**: None (independent of Phase 1; both are prerequisites for Phase 3)

#### Objective

Make the multibrowser SPA select the ranking judge by `rankable` (not `fullGrid`), while keeping
`fullGrid` strictly as a *coverage/sample-caption* signal — backward-compatible with manifests
that lack `rankable`/`coverage`. Delivers a SPA that ranks Gemini correctly under **both** the old
committed manifests (via fallback) and the new one (Phase 3), so no intermediate state ever ranks
Opus.

#### Files to Create / Modify

- `apps/multibrowser/src/lib/resultsModel.ts` — add optional `rankable?: boolean` +
  `coverage?: number` to the manifest judge zod schema + type + `map`.
- `apps/multibrowser/src/lib/rawModel.ts` — same optional fields on the raw catalog judge shape.
- `apps/multibrowser/src/lib/leaderboard.ts` — `rankingJudgeModel` ⇒
  `find(j=>j.rankable) ?? find(j=>j.fullGrid) ?? "gemini-3.6-flash"`.
- `apps/multibrowser/src/lib/rawSelection.ts` (`:61`) and `src/routes/RawRunPage.tsx` (`:91`) and
  `src/routes/ResultsPage.tsx` (`:120`) — default/highlight judge via `rankable` (same fallback).
- `apps/multibrowser/src/routes/ResultsPage.tsx` (`:221`) — judge-selector label keys off
  `rankable` (`(ranking)` vs `(validation)`); (`:226,470`) `isSample` keeps `fullGrid` but its
  caption copy is reworded so it stays true when Opus is full-grid-but-not-ranking; surface
  `coverage` when present.
- `apps/multibrowser/src/routes/ReviewScenarioPage.tsx` (`:265-273`) — "ranking judge" prose keys
  off `rankable`; `fullGrid` framing for "scores every transcript" stays coverage-only.
- `apps/multibrowser/src/components/RawComparison.tsx` (`:31`) — sample caption keeps `fullGrid`;
  reword if needed.
- Tests/fixtures: `leaderboard.test.ts`, `results.data.test.ts`, `fakeRepo.ts`, `rawData.test.ts`
  and any snapshot fixtures — add `rankable`/`coverage`; new assertions per SC6.

#### Deliverables

- [ ] Optional `rankable`/`coverage` in both schemas; ranking-proxy sites use `rankable`.
- [ ] Legacy manifest (no `rankable`) still ranks Gemini via fallback.
- [ ] Selector labels Opus `(validation)`, Gemini `(ranking)`; `coverage` shown when present.

#### Acceptance Criteria

- [ ] `pnpm -C apps/multibrowser test` passes.
- [ ] `rankingJudgeModel` returns Gemini when Opus is `{full_grid:true, rankable:false}` AND when
      the manifest omits `rankable` (fallback).

#### Test Plan

Unit (vitest): `rankingJudgeModel` with (a) new manifest Opus-full-grid-not-ranking, (b) legacy
manifest without `rankable`; schema round-trips optional fields; selector label; sample-caption
gate still triggers only on `!fullGrid`.

### Phase 3: Re-export results/ and results-raw/ for 20260803 in place

**Dependencies**: Phase 1, Phase 2

#### Objective

Fold the new full-grid Opus root into the committed datasets. After this phase the manifest badges
Opus `full_grid:true`/`rankable:false`/`coverage≈0.9992`, Gemini values are byte-identical, and
both tiers share one fingerprint.

#### Files to Create / Modify

- `results/20260803/manifest.json` + `results/20260803/<tradition>.json` (re-exported).
- `results-raw/20260803/manifest.json` + per-scenario gz shards (re-exported).
- `results/README.md`, `results-raw/README.md` — add the `20260823-opus-fullgrid` root to the
  example commands; note the worktree `../../tmp/...` path vs. the repo-root path.
- (No new committed test file; verification is scripted — see Test Plan.)

Commands (run from the worktree; source roots live in the gitignored main-checkout `tmp/`):

```bash
uv --project workflows/analysis run python -m analysis export \
  ../../tmp/judging-runs/20260803-merged \
  ../../tmp/judging-runs/20260803-unstated-opus \
  ../../tmp/judging-runs/20260803-framings-opus-sample \
  ../../tmp/judging-runs/20260823-opus-fullgrid \
  --run-id 20260803 --out results

uv --project workflows/analysis run python -m analysis export-raw \
  ../../tmp/judging-runs/20260803-merged \
  ../../tmp/judging-runs/20260803-unstated-opus \
  ../../tmp/judging-runs/20260803-framings-opus-sample \
  ../../tmp/judging-runs/20260823-opus-fullgrid \
  --run-id 20260803 --out results-raw
```

#### Deliverables

- [ ] `results/20260803/manifest.json`: Opus `{full_grid:true, rankable:false, coverage≈0.9992}`,
      Gemini `{full_grid:true, rankable:true, coverage:1.0}`.
- [ ] Gemini slice values byte-identical to the pre-change committed shards.
- [ ] `results-raw/20260803/manifest.json` `fingerprint` == `results/20260803` `fingerprint`.
- [ ] Overlap dedup keeps the full-grid verdict (verified); spaces-dir skipped.
- [ ] READMEs updated.

#### Acceptance Criteria

- [ ] Gemini byte-identity holds (scripted check below).
- [ ] Cross-tier fingerprint equality holds.
- [ ] `test_committed_dataset_reconciles_with_paper` still green against the re-exported data.
- [ ] Coverage counts match expectation (Opus ~93,341/93,420; Gemini 93,420/93,420).

#### Test Plan

- **Gemini byte-identity (scripted):** for each tradition, extract the `means`/`steadfastness`
  Gemini sub-tree from `git show HEAD:results/20260803/<t>.json` and from the re-exported file,
  re-serialize both with the canonical dumper, assert equal; assert the manifest diff touches only
  Opus judge entries, `judges[]`, `counts`, `fingerprint`, `generated_at`.
- **Fingerprint parity:** compare the two manifests' `fingerprint`.
- **Dedup/overlap:** confirm on a known overlapping cell the retained verdict is the full-grid one
  (later `ts`); if `ts` ordering is not guaranteed, make full-grid preference explicit in
  `resolve_judgments` root order and re-verify (note in review).
- Regression: reconciliation test green.

### Phase 4: Dual-judge paper artifacts + numbers summary

**Dependencies**: Phase 3

#### Objective

Regenerate the dual-judge paper artifacts from the new data and deliver the markdown numbers
summary for the paper.

#### Files to Create / Modify

- `../multibench-papers/figures/fig_dual_judge.pdf`, `../multibench-papers/tables/` (dual-judge
  table `tab:djtier` + agreement stats) — regenerated via `../../tmp/paper_figs_multibench.py` /
  `paper_figs_additions.py`. **Not committed** in the papers repo (architect wires them).
- A committed in-repo markdown summary (e.g. `docs/analysis/110-dual-judge-fullgrid-summary.md`).

#### Deliverables

- [ ] `tab:djtier`, `fig:dualjudge`, agreement stats regenerated from the new data; numbers match
      the spec's expected values within tolerance (r≈0.834/0.854/0.825/0.684; bias≈−0.03; ≈94%
      within ±0.5; identical 5-model order under both judges in all framings).
- [ ] Markdown summary: Opus judgments 42,711 → exact new total; programme total (exact); Opus
      spend +$1,220 **usage-computed** (exact from data); the agreement r/bias/within-±0.5 and
      model-order statements; a line noting the 79 gaps are **judge-side** (refusals/parse), not
      collection gaps.

#### Acceptance Criteria

- [ ] Figures/tables written to `../multibench-papers/{figures,tables}/` (uncommitted there).
- [ ] Exact matched-cell count, programme total, and Opus spend computed **from data** (no rolling
      estimates) and reconciled before the summary is written.

#### Test Plan

Manual: open the regenerated figure/table; sanity-check the agreement numbers against the spec's
expected values; verify the model order is identical under both judges. No automated test (paper
artifacts live outside the repo).

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Opus accidentally becomes the ranking judge | Low | Critical | Static `rankable`; SPA ranks by `rankable` (Phase 2) before any re-export (Phase 3); SC5b/SC6 regression tests; phase order keeps every intermediate commit Gemini-ranking. |
| Under-scoped refactor misses `export_raw.py` / raw SPA sites | Med | High | Both exporters + all 7 SPA sites enumerated; raw catalog shares the earned helper. |
| Backward-compat break on untouched `20260813-protestantism` | Med | High | `rankable`/`coverage` optional in zod; ranking fallback; that dataset untouched. |
| Silent Gemini drift on re-export | Low | High | Scripted Gemini byte-identity check + reconciliation test. |
| Tier fingerprint divergence | Low | Med | Re-export both tiers from the identical four-root set; assert equality. |
| Overlap dedup keeps sample instead of full-grid | Low | Med | Verify `ts` ordering; make full-grid preference explicit if not guaranteed; note in review. |
| Raw-tier ~121 MB rewrite + stale Railway baked bundle | High | Low/Med | Stated consequence; re-bake owner confirmed with architect at PR time; `resolveRawSource` fails safe to GitHub. |
| `#50` nContributing invariant strained at ~99.9% Opus | Low | Med | Verify leaderboard/drill-down behaviour; note interaction in review. |

## Documentation Updates

- `results/README.md`, `results-raw/README.md` — add the `20260823-opus-fullgrid` root to the
  example export commands (Phase 3).
- New in-repo markdown numbers summary for the paper (Phase 4).
- Review doc: dedup rule, the judge-side-failures note, the `#50` invariant check, and the
  Railway re-bake handoff.
- No arch/lessons hot-tier change anticipated (this rides existing Spec 49/51 contracts); if the
  earned-`full_grid` semantics warrant a lessons line, route via the review's Lessons Updates.
