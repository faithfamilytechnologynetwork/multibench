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
- specify: spec drafted + scope-addition folded + codex feedback integrated; awaiting claude
  consult, then commit "with review".
