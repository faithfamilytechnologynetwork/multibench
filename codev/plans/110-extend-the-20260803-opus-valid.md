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

#### The shared coverage contract (resolves the reviewers' raw-tier mechanism gap)

The score tier has `dict[str, TraditionExport]` with per-cell counts; the raw tier **streams**
(`iter_tradition_raw` yields a `RawTraditionExport` with no coverage aggregates and frees the
resolved rows per tradition). So the shared helper cannot take an `exports` dict. Instead, define
the coverage contract at the **resolved-rows** level, computed with the **exact same slicing
`_coverage_summary` already uses — `scope=="full"`, `pressure==PRESSURE_ALL`, pooled over
subjects+traditions, per (judge, framing)** — so the earned badge, the displayed `coverage`
fraction, and the manifest's existing `counts.coverage` are one number, never two disagreeing ones:

- `accumulate_coverage(counts, resolved_rows, universe)` — folds one tradition's resolved rows
  (using `_scenario_universe` for the denominator) into a running
  `dict[(judge, framing), {n_judged, n_expected}]`. Streaming-safe (tiny counters; per-tradition
  rows freed as before).
- `earns_full_grid(counts, judge, threshold=FULL_GRID_MIN_COVERAGE)` — true iff **all three
  framings** present with per-framing `n_judged/n_expected ≥ threshold`.
- `judge_coverage(counts, judge)` — pooled `Σ n_judged / Σ n_expected` (the displayed fraction).

Score tier feeds `accumulate_coverage` from its exports (or reuses `_coverage_summary`'s output,
which is the same shape); raw tier feeds it incrementally in the write loop. Both exporters
resolve judgments through the identical loaders, so the counts — hence the earned badge and
fraction — match by construction.

**`--limit` rule:** the raw tier accumulates coverage from the **full resolved rows** (the 3rd
`iter_tradition_raw` yield), **not** the written shard subset, so a `--limit` dev fixture reports
true judge coverage and Gemini stays `fullGrid:true`/`rankable:true` in the fixture catalogs
(no fixture-semantics flip). `export_afb.py` is **out of scope**: it builds its catalog directly
via `RawTierWriter` (does **not** call `_catalog_doc`) with a single Terra judge that is complete
by construction; its hardcoded `fullGrid:true` stays, and adding optional `rankable`/`coverage`
to the schema leaves its fixture valid.

#### Dedup precedence (resolves "full-grid must win over the sample")

`resolve_judgments` currently breaks a same-identity collision by **later `ts`** (the architect's
cross-alias rule for the ~1,800 sunni cells). Relying on `ts` to make full-grid outrank the sample
is not guaranteed. Add an explicit **source priority**: thread a per-root priority (root order)
so the winner is chosen by `(priority, ts)` — higher-priority root wins, ties broken by later `ts`
(the existing cross-alias rule is preserved at equal priority). Default priority 0 keeps every
other run's output byte-identical. Place the full-grid Opus root **last** (highest priority) so it
outranks the sample; the sample survives only where full-grid has no verdict (the gap-fill). Phase
3 verifies **every** overlapping identity resolves to the full-grid verdict, not just one cell.

#### Files to Create / Modify

- `workflows/analysis/analysis/export_results.py` — split `JUDGE_UI` to `{key, rankable}`; add
  `FULL_GRID_MIN_COVERAGE = 0.95` and the shared `accumulate_coverage`/`earns_full_grid`/
  `judge_coverage` helpers (pinned to `_coverage_summary`'s slicing); keep `assert_strict_full_grid`
  (the existing strict all-cells walk) for **rankable** judges; add the `(priority, ts)` precedence
  to `resolve_judgments` (backward-compatible default); `build_manifest` emits per judge
  `{key, model, aliases, full_grid (earned), rankable (static), coverage (fraction)}`; assert
  exactly one rankable judge; rankable ⇒ `assert_strict_full_grid` or fail-fast; fix stale
  docstring/comment (L504-511, L558-559).
- `workflows/analysis/analysis/export_raw.py` — accumulate coverage in the `write_dataset` loop
  via the shared helper; thread earned `full_grid`/`rankable`/`coverage` into `_catalog_doc`
  (new judge-metadata argument); keep `JUDGE_UI[...]["key"]`; carry the same `(priority, ts)`
  precedence.
- `workflows/analysis/tests/test_export_results.py`, `test_export_raw.py`, `test_export_afb.py` —
  update the catalog/manifest shape assertions; add the new coverage/rankable/precedence tests.

#### Deliverables

- [ ] `full_grid` earned via the tolerant predicate; `rankable` static; `coverage` fraction present.
- [ ] `export_raw.py` catalog carries the same earned `full_grid`/`rankable`/`coverage`.
- [ ] Stale "Opus stated/guided sample" docstring/comment corrected.
- [ ] `resolve_judgments` gains `(priority, ts)` precedence (backward-compatible default 0).
- [ ] Tests: (a) 14.5%-sample framing does NOT earn `full_grid`; 99.9% state DOES (both sides of
      threshold); (b) `rankable` static & coverage-independent (earning `full_grid` never makes a
      judge rankable); (c) rankable + strict-incomplete ⇒ fail-fast; (d) 0 or >1 rankable ⇒
      fail-fast; (e) `coverage` == pooled `n_judged/n_expected` at `_coverage_summary`'s slicing,
      and equals what `counts.coverage` implies; (f) on a sample↔full-grid identity collision the
      higher-priority (full-grid) verdict wins regardless of `ts`; (g) raw + score tiers emit
      identical earned `full_grid`/`coverage` for the same roots.

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
- **Critical test-mapper fix (reviewer HIGH):** `apps/multibrowser/src/lib/leaderboard.test.ts:126`
  `loadCommitted()` maps the real committed manifest through an **explicit field list**
  (`{key, model, aliases, full_grid→fullGrid}`) and **drops `rankable`**. After Phase 3 the real
  `results/20260803` manifest carries Opus `{full_grid:true, rankable:false}`; with `rankable`
  stripped, `rankingJudgeModel`'s fallback `find(j=>j.fullGrid)` selects **Opus** (sorted first) —
  inside the very sealed-launch parity test that pins Gemini (SC4). **Carrying `rankable`
  (and `coverage`) through `loadCommitted()` is a named Phase 2 deliverable**, and must land
  before Phase 3 or SC4 cannot be green.
- Full test/fixture list (each reads `fullGrid`/judge metadata and needs `rankable`/`coverage`):
  `leaderboard.test.ts`, `results.data.test.ts`, `results.test.tsx`, `fakeRepo.ts`,
  `rawData.test.ts`, `rawSelection.test.ts` (`:15` "fullGrid judge preferred over opus" → becomes
  a `rankable` assertion), `rawFixture.ts`, `rawResults.test.tsx`, `rawRun.test.tsx`,
  `RawComparison.test.tsx` — add `rankable`/`coverage`; assertions per SC6.
- **#50 invariant vitest:** add a leaderboard/drill-down test with a **non-rankable,
  full_grid-earned, sub-100%-coverage** judge (mirrors Opus at 99.88%) to confirm the
  `nContributing` / earned-full_grid invariant documented at `ResultsPage.tsx:497-501` still holds
  when coverage is earned-but-not-strict (not just a review-doc note).

#### Deliverables

- [ ] Optional `rankable`/`coverage` in both schemas; ranking-proxy sites use `rankable`.
- [ ] `loadCommitted()` carries `rankable`/`coverage` through (so SC4 stays green post-Phase-3).
- [ ] Legacy manifest (no `rankable`) still ranks Gemini via fallback.
- [ ] Selector labels Opus `(validation)`, Gemini `(ranking)`; `coverage` shown when present.
- [ ] #50 invariant vitest passes with a non-rankable, earned-full_grid, sub-100% judge.

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

- **Gemini byte-identity — one-time migration gate (scripted):** for each tradition, extract the
  `means`/`steadfastness` Gemini sub-tree from `git show HEAD:results/20260803/<t>.json` and from
  the re-exported file, re-serialize both with the canonical dumper, assert equal; assert the
  manifest diff touches only Opus judge entries, `judges[]`, `counts`, `fingerprint`,
  `generated_at`. This is inherently a **pre-vs-post migration** check (the "pre" state ceases to
  exist after merge), so it runs during Phase 3 rather than living as a permanent test — a
  deviation from spec SC2's "add a pytest" wording, made explicit here.
- **Durable Gemini guardian (post-merge):** `test_committed_dataset_reconciles_with_paper`
  (+ sealed-launch parity) already pins every Gemini slice mean to the paper `stats_bundle` values
  committed in `leaderboard.test.ts` — it stays green iff Gemini bytes are stable, so it is the
  permanent guarantee SC2 asks for. (Spec SC2 wording updated to reflect migration-gate +
  reconciliation-guardian.)
- **Fingerprint parity:** compare the two manifests' `fingerprint`.
- **Dedup/overlap — exhaustive:** enumerate **every** identity present in both the sample and the
  full-grid Opus roots and assert the merged winner is the full-grid verdict (the `(priority, ts)`
  precedence from Phase 1), not just one cell.
- Regression: reconciliation test green.

### Phase 4: Dual-judge paper artifacts + numbers summary

**Dependencies**: Phase 3

#### Objective

Regenerate the dual-judge paper artifacts from the new data and deliver the markdown numbers
summary for the paper.

#### Paper regeneration mechanics (resolves the reviewers' "scripts read the frozen bundle" gap)

The generators currently read the **old** Opus roots and a **frozen** `stats_bundle.json`, so
running them as-is reproduces the old statistics. Phase 4 must therefore:
1. **Read the generators first** to identify their exact inputs (which Opus roots / which stats
   bundle / whether they compute agreement from judging runs directly).
2. **Recompute the agreement inputs from the merged four-root data** using the **same dedup**
   (`(priority, ts)` precedence) as the export, so the paper's agreement bundle reflects the
   full-grid Opus layer — either by regenerating the upstream `stats_bundle.json` from the new
   roots or by pointing the generators at the new root. Do not hand-edit numbers.
3. Regenerate `tab:djtier`, `fig:dualjudge`, and the agreement stats from that recomputed input.

**Paths (run from the MAIN checkout, not the worktree):** the generators and their `tmp/` inputs
and the sibling papers repo resolve relative to the main checkout
`/Users/mwk/Development/faithfamilytechnologynetwork/multibench`. From **this worktree** the papers
repo is `../../../multibench-papers` (not `../multibench-papers`); running the generators from the
main checkout keeps their internal `tmp/…` and `../multibench-papers/…` relative paths correct.

#### Files to Create / Modify

- `/Users/mwk/Development/faithfamilytechnologynetwork/multibench-papers/figures/fig_dual_judge.pdf`
  and `.../multibench-papers/tables/` (dual-judge table `tab:djtier` + agreement stats) —
  regenerated via the main-checkout `tmp/paper_figs_multibench.py` / `paper_figs_additions.py`.
  **Not committed** in the papers repo (architect wires them).
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
| Overlap dedup keeps sample instead of full-grid | Med | Med | Explicit `(priority, ts)` source precedence in `resolve_judgments` (full-grid root last/highest); Phase 3 verifies **every** overlapping identity, not one cell. |
| Real-manifest test mapper flips ranking to Opus at Phase 3 | Med | High | `loadCommitted()` carries `rankable` through (named Phase 2 deliverable, lands before Phase 3). |
| Raw-tier "shared helper" has no data in the streaming path | Med | High | Coverage contract defined at the **resolved-rows** level (`accumulate_coverage`), fed incrementally in the raw write loop; both tiers use identical loaders → counts match. |
| `--limit` fixtures flip Gemini `fullGrid:false` | Med | Med | Raw coverage computed over **full resolved rows**, not the written subset; fixtures unaffected. |
| Two disagreeing coverage numbers in one manifest | Med | Med | `coverage` + earned-`full_grid` pinned to `_coverage_summary`'s (scope=full, pressure=all) slicing — same number as `counts.coverage`. |
| Raw-tier ~121 MB rewrite + stale Railway baked bundle | High | Low/Med | Stated consequence; re-bake owner confirmed with architect at PR time; `resolveRawSource` fails safe to GitHub. |
| `#50` nContributing invariant strained at ~99.9% Opus | Low | Med | Phase 2 vitest with a non-rankable earned-full_grid sub-100% judge; also noted in review. |
| Paper scripts reproduce old stats from the frozen bundle | Med | High | Phase 4 recomputes the agreement inputs from the merged four-root data (same dedup) before regenerating table/figure; run from the main checkout so paths resolve. |

## Documentation Updates

- `results/README.md`, `results-raw/README.md` — add the `20260823-opus-fullgrid` root to the
  example export commands (Phase 3).
- New in-repo markdown numbers summary for the paper (Phase 4).
- Review doc: dedup rule, the judge-side-failures note, the `#50` invariant check, and the
  Railway re-bake handoff.
- No arch/lessons hot-tier change anticipated (this rides existing Spec 49/51 contracts); if the
  earned-`full_grid` semantics warrant a lessons line, route via the review's Lessons Updates.
