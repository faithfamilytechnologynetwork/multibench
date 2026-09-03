# Builder thread — aspir-110

Project 110: Extend the 20260803 Opus validation layer to the full grid (stated+guided) and re-export.
Protocol: ASPIR (strict mode, porch-driven).

## Specify phase

- Read issue #110 + spec deliverables. Explored the export mechanism end-to-end.
- Key context gathered:
  - `analysis export` / `export-raw` take run roots as CLI args. Current `20260803` wiring
    (from results/README.md): roots = `20260803-merged` (Gemini full grid + report.json),
    `20260803-unstated-opus`, `20260803-framings-opus-sample`. Extend by adding
    `20260823-opus-fullgrid` (the new stated+guided full-grid Opus verdicts).
  - Source data verified present in main checkout `tmp/judging-runs/`. `20260823-opus-fullgrid`
    has 7 tradition dirs + an accidental empty dir named with spaces (no judgments.jsonl →
    skipped by read_run_root). To confirm harmless.
- **Design finding that reshaped the spec (#96):** `full_grid` is static in `JUDGE_UI`
  (gemini→true, opus→false). Worse, the SPA `rankingJudgeModel` = `find(j => j.fullGrid)` — and
  `build_manifest` sorts judges so `claude-opus-4-8` < `gemini-3.6-flash`. So naively flipping
  Opus `full_grid:true` would make **Opus** the ranking judge (regression; Opus must never
  re-rank). #96 mandates decoupling: `full_grid` earned from coverage; `rankable` a separate
  static property (Gemini-only). Spec now includes a Phase-A refactor + coordinated SPA change.
- **Load-bearing risk flagged:** full-grid Opus run is 62,267/62,280 (13 short). Earning
  `full_grid:true` needs merged Opus coverage complete for every cell; the sample root is kept
  to back-fill. Must verify empirically in implement; if incomplete, escalate to architect —
  never fake the flag.
- Wrote spec to codev/specs/110-extend-the-20260803-opus-valid.md (canonical template:
  Problem/Current/Desired/Success Criteria + Constraints/Assumptions/Solution/Risks).
- Ran 2-way spec consult (codex + claude) — both REQUEST_CHANGES, high-value:
  - `export_raw.py` also shares `JUDGE_UI` (writes catalog `fullGrid` L534) — was out of scope; now in.
  - 7 SPA `fullGrid` sites, not 2 — incl. `ResultsPage.tsx:221` "(ranking)" label that would brand
    Opus the ranking judge. Ranking-proxy sites → `rankable`; sample-caption sites keep `fullGrid`.
  - `rankable` must be OPTIONAL in zod (20260813-protestantism manifest lacks it) + fallback ranking.
  - results-raw re-export rewrites ~121MB gz shards + Railway baked bundle goes stale (re-bake owner = architect).
  - SC2 byte-identity needs an executable pytest (shards are minified single-line JSON).
  - Stale "Opus stated/guided sample" docstrings; #50 nContributing invariant note.
- **Q1 contradiction (quantified + escalated + RESOLVED):** unstated Opus is 15551/15570 (99.88%) —
  strict per-cell full_grid is UNACHIEVABLE for Opus, but deliverable 3 wants the badge true.
  Architect APPROVED (2026-09-03): tolerant earned full_grid (FULL_GRID_MIN_COVERAGE=0.95, all 3
  framings) + static `rankable` strict-100% for ranking. Add-ons: (1) manifest carries per-judge
  `coverage` fraction; (2) tests both sides of threshold. 79 gaps are judge-side (refusals/parse),
  not collection gaps — for the review doc.
- Revised spec comprehensively (all reviewer points + both architect add-ons), wrote rebuttal,
  advanced to PLAN.

## Plan phase

- Wrote 4-phase plan: (1) exporter refactor [both export_results + export_raw], (2) SPA rewire,
  (3) in-place re-export, (4) paper artifacts + summary. Ordering: SPA `rankable` support lands
  BEFORE re-export so no intermediate commit ranks Opus.
- 2-way plan consult (codex + claude) — both REQUEST_CHANGES, HIGH, excellent. Verified all claims:
  - **Raw-tier mechanism gap:** `iter_tradition_raw` yields RawTraditionExport (no coverage) +
    frees rows per tradition; `_catalog_doc` takes only judge_models. "Import earns_full_grid(exports)"
    is impossible. FIX: coverage contract at the resolved-rows level (`accumulate_coverage`),
    accumulated in the raw write loop; pinned to `_coverage_summary`'s scope=full/pressure=all slicing.
  - **`loadCommitted()` (leaderboard.test.ts:126) drops `rankable`** → after re-export the sealed
    parity test would fall back to fullGrid → select Opus (sorted first). FIX: carry rankable through
    = named Phase 2 deliverable before Phase 3. Full fixture list enumerated.
  - **Dedup:** ts doesn't guarantee full-grid wins. FIX: explicit `(priority, ts)` precedence in
    resolve_judgments (full-grid root last); verify ALL overlapping identities.
  - **--limit** would flip Gemini fullGrid:false in fixtures. FIX: raw coverage over full resolved rows.
  - **Coverage denominator** must pin to _coverage_summary (else two disagreeing numbers).
  - **SC2** pytest → it's a one-time migration gate; durable guardian = reconciliation test. Spec SC2 reworded.
  - **Paper scripts** read frozen stats_bundle → must recompute from merged roots; sibling path from
    worktree is `../../../multibench-papers` (run generators from main checkout).
  - export_afb out of scope (single complete Terra judge, doesn't call _catalog_doc).
- Revised plan + light spec edits; wrote plan rebuttal. Plan approved autonomously → implement.

## Implement phase_1 (exporters) — DONE

- Verified real data: cross-alias Opus collision is WITHIN the sample root; 3 existing roots have
  no cross-root overlap → root-order `(priority, ts)` precedence is safe (existing exports
  byte-identical). fullgrid root passed LAST = highest priority → wins sample overlap.
- `export_results.py`: JUDGE_UI split to `{key, rankable}`; `FULL_GRID_MIN_COVERAGE=0.95`; coverage
  contract (`coverage_counts_from_judged`, `earns_full_grid`, `judge_coverage`) pinned to the
  scope=full/pressure=all slicing; `_coverage_from_exports`; `resolve_judgments(raws, priorities)`
  `(prio, ts)`; `build_corpus_export`/`build_tradition_export` thread root-order priority;
  `build_manifest` emits earned full_grid + static rankable + coverage fraction, asserts exactly
  one rankable, strict `_assert_full_grid` for rankable; counts.coverage now single-sourced from
  the same table; stale docstrings fixed.
- KEY: coverage denominator uses the run's ACTUAL subject universe (distinct subjects across
  judges), NOT hardcoded 5 — else small fixtures break; real 5-subject run unchanged.
- `export_raw.py`: `accumulate_full_scope_judged` folds full resolved rows per tradition
  (limit-independent); `_catalog_doc` takes `coverage` and emits fullGrid/rankable/coverage;
  `build_catalog` + `write_dataset` build coverage; `iter_tradition_raw` passes root-order priorities.
  export_afb untouched (single complete Terra judge, doesn't call _catalog_doc).
- Tests: 8 new (both-sides threshold, judge_coverage, earning-full_grid-≠-rankable, rankable strict
  fail-fast, 0/>1 rankable fail-fast, dedup priority beats ts / ts breaks equal-priority ties,
  raw↔score cross-tier agreement). Updated manifest/catalog shape assertions + regenerated the
  frozen raw_writer golden manifest hash (0fa6ff03…). Full suite: 241 passed, 6 skipped.
  Reconciliation (Gemini) green — no committed results/ data touched (AC2).
- Committed codev artifacts + phase_1 code; dispatcher green; PHASE_COMPLETE.

### phase_1 iteration-1 review (codex REQUEST_CHANGES / claude APPROVE) — all addressed
- codex #1 (REAL BUG): v2 override bypassed priority. The sample root HAS 20 v2 rows overlapping
  fullgrid → sample corrections would beat fullgrid. FIXED: v2 now respects (prio); a v2 applies
  only if prio >= winner prio; equal-prio last-wins preserved. + test.
- codex #3: raw --limit coverage truncated by the outer break. FIXED: removed outer break, coverage
  over all traditions' full resolved rows. + 2-tradition limit test.
- codex #4: coverage denominator used OBSERVED subjects → a wholly-absent subject could spuriously
  earn full_grid. FIXED: pin to report-DECLARED subjects both tiers (TraditionExport.subjects +
  RawTraditionExport.subjects). Real numbers unchanged (all 5 declared). + missing-subject test.
- codex #2 (raw rankable fail-fasts): REBUTTED — would break AFB single-judge + --limit; raw isn't
  the ranking authority (score manifest is); advisory only. Review-doc note instead.
- claude: 6 real-data guardians SKIP in worktree (green-by-skip). FIXED: wired `tmp->../../tmp`
  symlink, re-ran → 250 passed 0 skipped (reconciliation genuinely verified). Symlink removed
  (never commit it; .gitignore `tmp/` doesn't match the symlink). Phase 3 must re-create it for SC2/SC4.
- cosmetic: unknown-judge check before rankable-count. README stale shapes → Phase 3.
- REVIEW-DOC TODO: note raw catalog's `rankable` is advisory (not gated); score manifest is the
  ranking authority.
- Next: commit fixes, porch rebuttal + re-verify (iteration 2).
