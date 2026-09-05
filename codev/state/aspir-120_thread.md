# aspir-120 — Two-judge mean scoring

Builder thread for issue #120 (ASPIR, strict mode).

## Goal
Change the benchmark's scoring rule from **Gemini-only ranking** to the **equal-weight mean of
both judges (Gemini 3.6 Flash + Claude Opus 4.8) per cell**, everywhere a number is reported:
analysis stats bundle (paper), committed `results/<run>/` tier, `/results` leaderboard, docs.
Decision by Waleed 2026-09-04: "Everything should be an average."

## Orientation (specify phase)
Read before drafting the spec:
- `analysis.aggregate.cell_scores` is already the canonical per-cell reducer = mean of present
  judges' scores. The change feeds it **all** judge layers (not the Gemini-only root) to make a
  **combined** block, and ranks on that.
- Exporter (`analysis/export_results.py`): aggregates **per judge** (loops `for judge in judges`),
  keyed by model id in the shard `means`/`steadfastness` blocks. No combined block today.
  Ranking today = manifest per-judge `rankable` flag (Gemini only) + `_assert_full_grid` (strict).
  Baked #3: replace with a manifest-level `ranking` declaration; keep the strict full-grid gate
  for ≥1 judge.
- SPA leaderboard (`apps/multibrowser/src/lib/leaderboard.ts`): `rankingJudgeModel()` picks the
  `rankable` judge. Needs to rank on the combined block (driven by manifest `ranking`). Judge
  selector (Gemini/Opus separately) unchanged.
- **stats_bundle.json** is NOT produced by committed code. It's produced by the gitignored
  `tmp/report_figs_20260803_v2.py` (writes `figures-report-v2/stats_bundle.json`, line 297) — a
  rich paper bundle (tier/subj_overall/model_tier/dual_judge/gaps_pooled/…). `paper_figs_multibench.py`
  consumes it. The v3 bundle must match this schema so the paper script runs unchanged.
  → key open question: how to produce the combined v3 bundle (committed command vs documented
  figs-script adaptation reusing a committed combined-aggregation primitive).
- All 4 source roots + the v2 bundle are reachable from the worktree at `../../tmp/judging-runs/…`.
- Governance: `arch-critical.md` fact + `results/README.md` update; CLAUDE.md/AGENTS.md carry a
  verbatim HOT CONTEXT mirror of the hot files (test_governance_docs.py enforces sync).

## Coordination
- #119 (builder-spir-119) is mid-run. This issue lands FIRST; do NOT touch `traditions/protestant-unified`
  or #119's files. Architect amends #119 after.
- Do NOT invent the combined leaderboard reconciliation pin — architect adds it after paper numbers
  are accepted.

## Scope addition (architect, 2026-09-05) — FOLDED INTO SPEC
Complete the grid BEFORE rescoring: re-judge the 35 Opus empties (26u/3s/6g, #116) + any Gemini
gaps with identical configs (Opus `tmp/opus-judge.yaml` thinking-on; Gemini record config);
verdicts written into existing layers (Opus → `20260823-opus-fullgrid`). Target 0 single-judge
cells. Spend ≤$20 via `taqwabench/.env` (Opus CEFE key, batch/live ok; Gemini OpenRouter). 3
retries then report, no impute. Actuals in review. This becomes Phase 0 of the plan; spend only in
implement, after plan approval. Judge-only re-run: `python -m judging judge <sittings> <tradition>
--results-dir … --config tmp/opus-judge.yaml`. Sittings already exist; only Opus verdict missing.

## Consult (specify iter1)
- codex: REQUEST_CHANGES — (1) full-grid gate wording contradicts baked #3 [fixed: now "≥1 real
  judge strictly complete", rankable→legacy]; (2) SPA needs explicit `score_key` in ranking decl
  [added]; (3) v3 producer boundary must be resolved [resolved: commit combined ranked-agg
  capability + documented v3 figs step reusing it]; (4) enumerate which v3 fields become combined
  [added: all score/CI aggregates combined; dual_judge stays per-judge; meta unchanged]; (5)
  malformed-manifest policy [added: legacy→Gemini fallback; malformed ranking→visible error].
- claude: pending.

## Status
- specify: DONE (spec + both consults REQUEST_CHANGES → all accepted+applied; rebuttal written;
  porch advanced to plan).
- plan: drafted → 2-way consult (both REQUEST_CHANGES, code-verified) → all accepted, plan
  materially revised → rebuttal written. Awaiting re-verification.

### Plan consult — critical catches (all fixed)
- Phase 1 as first-drafted risked ~1000× overspend: `judge` takes a whole sittings file; unstated
  gaps (26) have NO sittings in `20260803-unstated-opus`, and `20260823-opus-fullgrid` sittings are
  stated+guided only. FIX: filtered temp sittings (unstated ← `20260803-merged`; stated/guided ←
  fullgrid), route verdicts to correct layer (unstated → unstated-opus; s/g → fullgrid), pre-spend
  assert work-count == enumerated. Verified enumeration: **35 cells / 34 sittings**, no Gemini gaps.
- Combined block MUST be a separate top-level shard field (`combined`), NOT a `means` judge key —
  else breaks test_export_results.py:801, shardConsistencyNotices (resultsModel.ts:280),
  results.data.test.ts:92.
- BOTH exporters' gates re-shape (export_raw.py:573-588 too), not just export_results.
- Phase 3: `analysis report --combined` NOT viable (load_corpus rejects dup traditions); use
  read_run_root+resolve_judgments→aggregate_tradition→compute_tradition_stats seam via new
  `analysis combined-stats` cmd. v3 figs: swap the LOAD to canonical cell values.
- Phase 4 byte-identity: pin baseline via `git show HEAD:results/20260803/<t>.json` (minified JSON,
  no git-diff-subtree). Gemini byte-identical; Opus delta bounded to touched slices.
- Backup judgments.jsonl before in-place appends.

### Architect confirmations (2026-09-05)
1. #2 vs #7: CONFIRMED — #7 governs; Gemini byte-identical, Opus changes only in grid-completion
   cells, combined new. Phase 4 asserts Opus diff bounded.
2. Per-cell routing: proceeded (unstated → unstated-opus, s/g → fullgrid; forced — fullgrid has no
   unstated sittings). Flagged, not objected.
3. dual_judge on sample roots: deferred to Phase 3.
4. 2 residual single-judge cells: APPROVED to proceed; record cell ids + attempt count in manifest
   `single_judge_cells` + review; do NOT impute.

## Phase 1 — DONE (grid completion)
- Verified 35 missing Opus cells = 34 sittings; built filtered sittings; pre-spend assert ==35.
- Re-judged 33/35 over 3 passes (backups taken; v2 untouched; rejudge_cells=0).
- **2 residual single-judge cells** (persistent empty/truncated Opus, ≥9 attempts each; reported,
  not imputed): judaism|MSR-025|insistence|unstated|full ; sunni-islam|JLS-122|flattery|guided|full.
- Spend: MEASURED $11.02 exact (33 persisted verdicts, usage-computed) + ESTIMATED ~$1-3 for 48
  failed calls (no persisted usage) → best est ~$12-14, ≤$20. Console delta: NOT CHECKED
  (architect-accepted 2026-09-05 — no console access; estimate deemed sufficient). Earlier "$14-17"
  superseded.
- **single_judge_cells becomes a STRUCTURED object** (architect): {count, attempts, cells[...]},
  not a bare int — carry into Phase 2/4 manifest.
- Committed: results/REJUDGE-20260803.md, test_grid_completeness.py (skips where roots absent).
- Data lives in gitignored ../../tmp (NOT committed).

## Status: implement phase_1 complete → porch done → phase_2.

## Plan phases
1. Complete grid (re-judge 35 Opus + any Gemini gaps; ≤$20; runbook + completeness test).
2. Combined block + `ranking{score_key,judges,single_judge_cells}` in exporter; gate→"≥1 real judge
   strictly complete"; fixture-testable.
3. Committed combined ranked-stats capability + gitignored v3 figs step → v3 stats_bundle.json;
   reconciliation ≤1e-9 test.
4. Additive re-export results/20260803 (Gemini byte-identical, Opus delta = 33 recovered cells, combined new).
5. SPA leaderboard ranks combined via ranking.score_key; legacy→Gemini fallback, malformed→notice;
   judge-role copy (co-equal components); raw/AFB untouched.
6. Docs: results/README (~6 assertions + ranking schema row), arch-critical fact, HOT mirrors, review.
