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
- Committed fixes; rebuttal written; iteration-2 consult running.

### Architect correction (2026-09-03, for Phase 3/4 — do NOT assert "79")
- Compute the EXACT Opus residual per framing from the merged four-root export. Architect's direct
  count = **39 cells with no Opus verdict = 13 stated/guided + 26 unstated** (the "79" double-counted
  sample-layer overlap). Report per-framing.
- Cause: empty judge response (no text block → json.loads('') fails after 3 retries); refusal vs
  max_tokens NOT distinguishable in current logs. Cite **#116**, don't guess which.
- Applies to: Phase 3 residual verification + Phase 4 review doc / markdown summary.

### phase_1 iteration 2 review
- codex REQUEST_CHANGES (only raw ranking-integrity), claude APPROVE (independently verified 3-root
  re-export byte-identical + 4-root dry run → Opus {full_grid:true, rankable:false,
  coverage:0.999422}, Gemini unchanged → SC1 will hold).
- FIXED codex #2 properly: my AFB rebuttal reason was WRONG (export_afb doesn't call _catalog_doc —
  both reviewers). Added raw-catalog guards in `_catalog_doc`: >1 rankable → raise; a rankable judge
  that hasn't earned full_grid → raise; ZERO rankable allowed (validation-only/AFB-style). Changed
  the limit test to use opus (non-rankable; Gemini is never partial in reality). +3 tests. 247/253.

### Phase 3/4 notes from claude iter2 (IMPORTANT for later phases)
- **Badge/coverage are FULL-SCOPE ONLY** (denominator 46,710, NOT the 93,420 two-scope grid).
  Opus coverage 0.999422 is over full-scope cells; don't present it as coverage of the 93,420 grid.
  claude's dry run: **27 full-scope Opus gaps (unstated 19 / stated 2 / guided 6)**; architect's 39
  includes **12 turn1 gaps the badge can't see** (39 = 27 full + 12 turn1). Phase 4 must report
  per-framing AND per-scope, not conflate; compute exact from the merged export; cite #116 for cause.
- **Phase 3 byte-identity script must expect** `google/gemini-3.6-flash` added to Gemini's
  `aliases[]` on re-export (permitted under SC2's judges[] allowance). Gemini MEANS unchanged.
- **--limit raw export is now O(full corpus)** (reads all sittings) — document in review doc.
- Plan naming drift: impl uses `coverage_counts_from_judged`/`accumulate_full_scope_judged` (plan
  said `accumulate_coverage`) and kept `_assert_full_grid` (plan said `assert_strict_full_grid`) —
  substance matches; noted for plan readers.
- Next: iter2 rebuttal, commit, porch done → iteration 3 re-verify.

### phase_1 iteration 3 review — CONCEDED codex, claude APPROVE
- codex RC'd 3rd time (raw tier: exactly-one-rankable + strict both-scope). claude APPROVE (re-exported
  real 3-root → byte-identical shards/fingerprint/counts; 253/0 guardians pass).
- CONCEDED: my genericity objection was weak (AFB bypasses _catalog_doc → it's MB-specific). Now
  `_catalog_doc` requires exactly-one rankable + STRICT both-scope completeness (pooled ALL-scope
  count == scenarios×subjects×6×3×2; valid because resolved rows are unique-per-cell & in-grid).
  strict_judged accumulated in write_dataset/build_catalog. Tests: accept/zero/multiple/strict-incomplete.
  --limit test now gemini(complete,rankable)+opus(partial). 248/254.
- claude cheap notes done: _assert_full_grid → exp.subjects (declared universe, consistent w/ coverage);
  module docstring fixed; plan Phase 4 "79"→per-framing/scope residual + full-scope caveat.
- REVIEW-DOC TODOs: judge-set asymmetry (score full/all vs raw all-resolved; unreachable turn1-only);
  --limit raw now O(full corpus); raw rankable now strictly gated (updated from earlier "advisory" note).
- phase_1 ADVANCED (porch, at max-iter 3; my iter3 concession is committed → final code is the
  improved version; codex iter3 RC was on pre-concession code).

## Implement phase_2 (SPA: rank by rankable)
- NB: I prematurely ran `porch done` on phase_2 before implementing (porch cycled done→next). Recovery:
  implemented phase_2 fully, committed, THEN run the pending consult so it reviews real code.
- Changes (all backward-compatible; `?? fullGrid` fallback preserves pre-#110 manifests incl. committed
  20260803 which has no rankable until Phase 3):
  - resultsModel.ts + rawModel.ts: optional `rankable?`/`coverage?` in zod schema + type + map.
  - leaderboard.ts: `rankingJudgeModel` → find(rankable) ?? find(fullGrid) ?? gemini; new `isRankingJudge`
    helper = `rankable ?? fullGrid`.
  - Ranking-proxy sites → rankable: ResultsPage highlightJudge + selector label + drill caption
    (reworded, role-based; shows coverage% for full-grid validation); ReviewScenarioPage prose (split
    coverage 'scores every transcript' from ranking 'ranks the leaderboard'); rawSelection defaultJudge;
    RawRunPage default judge. Sample-caption sites keep `!fullGrid` (coverage): RawComparison badge,
    ResultsPage isSample.
  - CRITICAL fix: leaderboard.test.ts `loadCommitted()` now carries rankable/coverage (else the sealed
    parity test would fall back to fullGrid→Opus after Phase 3 re-export).
  - Fixtures: fakeRepo.ts + rawFixture.ts gain rankable/coverage.
  - New tests (SC6): rankingJudgeModel by rankable (Opus-first full-grid → still Gemini); legacy fallback;
    isRankingJudge; schema round-trip + backward-compat parse; rawSelection rankable default; #50/#110
    full-grid-Opus-not-in-standings.
- Verified: `tsc --noEmit` clean; vitest 393 passed (27 files). Reconciliation (committed 20260803, no
  rankable yet) still ranks Gemini via fallback.
- Committed phase_2; ran consult: codex APPROVE, claude REQUEST_CHANGES (3 valid gaps).
  - #50 test was a TAUTOLOGY (computeStandings never reads opus coverage) → replaced with a real
    results.test.tsx UI test: full-grid Opus {rankable:false, coverage:0.999} + partial shard →
    asserts Gemini still ranks, "opus (validation)" label, coverage-% caption (not sample), no
    sample-badge, "opus — validation" drill header.
  - ReviewIndexPage:109 "Opus validation SAMPLE" → "validation LAYER" (goes false after Phase 3).
  - ResultsPage drill header role word: keyed on isSample → now isRankingJudge (full-grid Opus was
    losing "validation"). Added selJudgeMeta/drillJudgeIsRanking.
  - Coverage surfaced in validation caption; ranking judge coverage is definitionally 1.0 → not
    separately surfaced (noted).
  - tsc clean; vitest 393 passed.
- Next: commit fixes, porch done → phase_2 iteration 2.
- iter2: codex RC (ReviewScenarioPage "scores every transcript" false for tolerant-full-grid Opus),
  claude APPROVE. FIXED: role-accurate prose (ranking judge 'every transcript'; full-grid validation
  'at full-grid scale' + coverage%; sample 'a sample') via pure `classifyJudgeRoles` helper + test.
- iter3: BOTH APPROVE → phase_2 ✓ (unanimous).

## Implement phase_3 (re-export 20260803 in place)
- Steps: wire tmp symlink; `analysis export` 4 roots → results/20260803; `analysis export-raw` 4 roots
  → results-raw/20260803 (~121MB); verify Gemini byte-identity, cross-tier fingerprint, Opus
  full_grid:true/rankable:false/coverage; compute residual per framing+scope (cite #116); update READMEs.
- IMPORTANT: implement BEFORE any porch done (phase_2 slip: prematurely done'd, recovered).

### phase_3 re-export DONE + verified
- Score export (4 roots) → results/20260803: Opus {full_grid:true, rankable:false, coverage:0.999422},
  Gemini {full_grid:true, rankable:true, coverage:1.0}. SC1 ✓.
- **Gemini byte-identical** across all 7 shards (re-serialized means+steadfastness subtree vs git HEAD). SC2 ✓.
- Manifest diff confined to: judges, counts, fingerprint, generated_at. SC2 ✓.
- Paper reconciliation test green against new committed data. SC4 ✓.
- Raw export (4 roots) → results-raw/20260803: 519 shards, 137MB. Cross-tier fingerprint MATCH. SC3 ✓.
- Raw catalog opus {fullGrid:true, rankable:false, coverage:0.999422} — passed exactly-one-strict-rankable guard.
- **Dedup exhaustive:** all 8996 sample∩fullgrid overlapping cells → full-grid verdict (0 mismatches).
- SPA vitest 394 pass against NEW committed data (leaderboard reconciliation ranks Gemini via rankable).
- **Opus residual = 35 judge-side cells** (complete grid 93420, Opus 93385):
  unstated turn1 7 / full 19 (=26); stated turn1 1 / full 2 (=3); guided turn1 0 / full 6 (=6).
  → 26 unstated (MATCHES architect) + 9 stated/guided (architect's 13 minus 4 sample-backfilled). Cause #116.
- spaces-dir in fullgrid root: 1 exists, skipped by read_run_root (no judgments.jsonl). OK.
- READMEs updated (4th root + worktree ../../tmp path + Railway re-bake note). Committed (~137MB), symlink removed.
- TODO: message architect re Railway re-bake (Q2). Then porch done → phase_3 consult.
- Architect confirmed (2026-09-03): **Railway re-bake is THEIRS** — they run `railway up --no-gitignore`
  from apps/multibrowser AFTER the PR merges (baked bundle built from main). MUST document the re-bake
  step + the fingerprint-stale window (resolveRawSource fails safe to committed GitHub tier until
  re-bake) in BOTH the review doc AND the PR body. Approved 35-residual/0.9994/byte-identical numbers.
  Proceed to phase_4.
- phase_3: iter1 codex COMMENT / claude RC (README schema tables stale). Fixed both READMEs
  (judges shape earned/static/coverage split; ranks on rankable not full-grid; full-scope coverage
  clarified; size ~132MB). iter2: BOTH APPROVE → phase_3 ✓ (unanimous).
- phase_3 review-doc TODOs (non-blocking): reconciliation skips in-worktree (verified out-of-band via
  symlink); Gemini aliases gained google/gemini-3.6-flash (phase_1 _JUDGE_VARIANTS, value-neutral);
  Railway re-bake = architect at PR time; judges-differed preset repointed by new Opus verdicts.

## Implement phase_4 (paper artifacts + numbers summary)
- Read generators tmp/paper_figs_multibench.py + paper_figs_additions.py (inputs: old Opus roots +
  frozen stats_bundle). Recompute agreement from merged 4-root data (same dedup); regen tab:djtier,
  fig:dualjudge, agreement stats → ../multibench-papers/{figures,tables} (uncommitted, run from MAIN checkout).
- Compute exact matched-cell count, programme total, Opus spend (usage-computed) from data.
- Write markdown numbers summary (committed in-repo). Implement BEFORE porch done.

### phase_4 DONE — numbers computed from the merged data
- Dual-judge agreement (full grid, 93,385 matched cells, canonical resolve_judgments):
  overall r=0.833 bias −0.031 within±0.5 94.0%; unstated 0.854 / stated 0.825 / guided 0.683
  (ceiling compression); IDENTICAL 5-model order under both judges in all 3 framings. Matches the
  pre-registered r≈0.834/0.854/0.825/0.684.
- Opus committed judgments 40,114 → 93,385 (issue est 42,711→93,341 = raw-record/pre-sweep).
- Programme total: record-run committed 186,805 (Gemini 93,420 + Opus 93,385); +1,299 dual-alias
  route-bridge records = 188,104 (≈ issue's ~188,5xx); gross Opus calls 104,978.
- **New full-grid Opus spend (usage-computed): $1,313.29** (repo cost model: opus $5/$25 per M,
  cache_write×2, cache_read×0.1, batch×0.5; 61,648 batch $1,253.56 + 619 live $59.73). Issue est ~$1,220.
- Residual 35 = 26 unstated (7 turn1/19 full) + 3 stated (1/2) + 6 guided (0/6); judge-side (#116).
- Committed: docs/analysis/110-dual-judge-fullgrid-summary.md (numbers summary).
- Regenerated (UNCOMMITTED, papers repo ../../../multibench-papers/): figures/fig_dual_judge.pdf
  (3 full-grid framing heatmaps) + tables/tab_dualjudge_{tier,rank}.tex; patched stats_bundle
  dual_judge.full_grid (main-checkout tmp, backup written). Via scratchpad script (canonical loaders).
- REVIEW-DOC TODOs (for Review phase): all phase non-blocking notes — judges-differed preset repoint,
  reconciliation skips in-worktree (verified out-of-band), Gemini aliases +google/gemini-3.6-flash,
  Railway re-bake=architect post-merge, --limit raw O(full corpus), raw rankable strictly gated,
  badge coverage full-scope-only, RawRunPage default-judge untested-directly, spend/residual/programme deltas vs estimates.
