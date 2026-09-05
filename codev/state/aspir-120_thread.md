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

## Status: phase_1 COMPLETE (force-advanced; claude APPROVE all iters, codex points all addressed).

## Phase 2 — DONE (combined block + ranking in both exporters)
- export_results.py: combined block as SEPARATE top-level shard fields (`combined`,
  `combined_steadfastness`) via cell_scores over ALL judgments — NOT inside `means` (preserves
  test:801 + shardConsistencyNotices + results.data.test by construction). Manifest gains
  `ranking={rule:mean_of_judges, score_key:"combined", judges:[...], single_judge_cells:{count,
  cells:[...], attempts?}}`. Gate re-shaped: "exactly one rankable" → "≥1 real judge strictly
  complete"; rankable now legacy selector/fallback metadata. COMBINED_KEY asserted disjoint from
  real judges; never enters judges list/coverage/JUDGE_UI.
- export_raw.py: gate re-shaped same way; emits `ranking={rule,judges}` (no combined per-cell block
  — raw shards are transcripts+verdicts). Golden fixture regenerated (only manifest changed).
- single_judge_attempts threaded through export_dataset/write_dataset/build_manifest + CLI
  `--single-judge-attempts` (provenance not in data).
- Tests: equivalence (combined==mean-of-per-judge on double-judged; diverges + reported on
  single-judge), combined-serialized-separately, ranking shape+disjointness, single_judge recorded,
  gate both directions (both exporters). Old "exactly one rankable" tests repurposed to new gate.
- Real-data smoke (4 roots): ranking ok, single_judge_cells count=2 attempts=3 = the exact 2
  residual cells (three-way lockstep w/ test allowlist holds). 258 passed, 8 skipped.
- NOTE: results/20260803 NOT re-exported yet (that's phase_4). SPA is phase_5.
- phase_2 iter2: BOTH APPROVE.

## Phase 3 — DONE (combined ranked-stats capability + v3 bundle)
- Committed `analysis/combined_stats.py` + CLI `analysis combined-stats`: reuses the export merge
  seam (read_run_root+resolve_judgments) → shim run → aggregate_tradition → compute_tradition_stats,
  feeding ALL judges' rows so cell_scores gives combined cells. Emits combined CIs (analysis_stats
  schema) + subj_overall_point. Deterministic/byte-stable. `export_combined_mean_of_means` helper
  for reconciliation.
- v3 bundle produced (gitignored, main checkout): `tmp/report_figs_20260803_v3.py` = v2 with the
  LOAD swapped to combined cells (build_combined_runs + cell_scores; no 2nd dedup); dual_judge/meta
  unchanged; stops after bundle write. Output:
  `…/analysis-out/figures-report-v3/stats_bundle.json` (v2 NOT overwritten; same top-level keys).
- Reconciliation VERIFIED: export_combined_mean_of_means == v3 subj_overall[0], max diff 2.2e-16.
- Tests: combined_stats reconciles w/ export (fixture), CLI smoke+determinism, real-data v3
  reconciliation (skip-when-absent). 262 passed, 9 skipped.
- Doc: results/COMBINED-STATS.md.
- phase_3 consult: BOTH REQUEST_CHANGES — same real bug: v3 dual_judge built gem_lut from combined
  `merged` → compared combined-vs-Opus (r 0.854→0.956). FIXED: v3 reuses v2's dual_judge verbatim
  (raw Gemini-vs-Opus, incl route_bridge/full_grid). Added guard test (v3/v2 schema + dual_judge
  identical + subj_overall differs). Float == → approx.
- phase_3 iter2: BOTH APPROVE (on reuse-v2). Then ARCHITECT DECIDED: RECOMPUTE dual_judge.full_grid
  on the completed grid.
- DONE: v3 dual_judge.full_grid recomputed (raw Gemini vs raw Opus over 93,418 double-judged cells,
  agree() from 110-dualjudge-fullgrid-figs.py): overall n=93,418 r=0.833 bias=-0.031 within 94.0;
  by-framing r 0.854/0.825/0.684 (guided +0.001 vs doc's 0.683 from the 33 recovered cells); guided
  within 95.4. v2's partial block → `full_grid_v2_partial` (n=93,385). Other dual_judge subsections
  reused from v2 verbatim. Dead gem_lut block deleted from v3 script; stale fig PNGs removed.
  Reconciliation fixture strengthened (varied valid scores). Test asserts recompute vs doc ≤0.005.
- ⚠️ FLAGGED: docs/analysis/110-dual-judge-fullgrid-summary.md now stale (residual 35→2, n
  93,385→93,418, guided 0.683→0.684). ARCHITECT ASSIGNED (2026-09-05): update it in MY Phase 6 to
  the completed-grid numbers + a 'supersedes the 93,385-cell figures' note; architect carries into
  paper. Added to plan Phase 6.
- phase_3 re-review (rank fix): codex APPROVE, claude REQUEST_CHANGES — REAL catch: reusing v2's
  dual_judge left `unstated` n STALE (31,114) but Phase 1 grew unstated Opus to 31,139 → would
  HARD-FAIL paper_figs_multibench.py's live `len(pairs)==bundle n` asserts. porch force-advanced to
  phase_4 (codex approve) but I FIXED it (real correctness bug for the paper regen):
  v3 dual_judge is now FULLY recomputed on the completed grid using paper_figs's EXACT load_opus
  (raw-gemini lut; mapped dedupe + v2 overlay). Results: unstated n=31,139, framings_sample n=9,000
  (deduped, r=0.777), unstated_rank/framings_tier recomputed, route_bridge reused (fixed artifact),
  full_grid recomputed n=93,418 (+rank), v2 full_grid → full_grid_v2_partial. Added
  test_v3_dual_judge_n_matches_paper_figs_live_pairing (pins n vs paper_figs's exact pairing).

## Phase 4 — DONE (additive re-export of results/20260803)
- Pinned baseline (git show HEAD:results/20260803/*.json → tests/fixtures/results-20260803-baseline/).
- Re-exported over the 4 completed roots: `analysis export ... --single-judge-attempts 3`.
  Opus 93,385→93,418, Gemini 93,420 unchanged. ranking={mean_of_judges, combined, single_judge_cells
  {count:2, attempts:3, cells:[judaism/MSR-025/insistence/unstated/full,
  sunni-islam/JLS-122/flattery/guided/full]}}.
- VERIFIED: Gemini block byte-identical (all shards); Opus changed ONLY in the 5 recovered
  traditions, n_judged monotonic (cells only added); combined+combined_steadfastness present;
  combined NOT in means (SPA guards safe); sizes OK.
- Tests (run in worktree vs committed+baseline): gemini byte-identical, opus delta bounded,
  combined+ranking, three-way lockstep (manifest single_judge_cells == grid-completeness allowlist).
  266 passed, 11 skipped.
- NOTE: porch force-advanced phase_3 (codex approve) before Claude's stale-n catch; the dual_judge
  fix + phase_4 ride the branch and get reviewed in phase_4's consult.
- phase_4 consult: codex + claude REQUEST_CHANGES. claude BLOCKING catch: the re-export changed the
  score-tier fingerprint but committed results-raw/20260803 still had the old one → Spec 51 cross-tier
  invariant broken (rawData.test.ts:463 red). FIXED: re-exported the RAW tier over the same 4 roots
  (analysis export-raw) → both tiers stamp sha256:696a24c1… (EQUAL); 26 affected-scenario shards +
  manifest changed (deterministic writer; not all 519). rawData.test.ts 35/35 pass. Also
  strengthened: opus-delta test (n_judged-unchanged→byte-identical + total==33 exact), added
  committed↔v3 combined reconciliation test, gemini byte-identity now covers steadfastness block too.
  pnpm install done (node_modules present for phase_5).

## Phase 5 — DONE (SPA leaderboard ranks on combined)
- resultsModel.ts: parse combined/combined_steadfastness shard fields + manifest `ranking`
  declaration (non-strict zod, no schema bump). Validate ranking (rule known, score_key not
  colliding with a real judge, judges⊆manifest, no dups) → visible ERROR notices, never silent
  revert. shardConsistencyNotices flags a combined-ranked manifest whose shard lacks the block.
- leaderboard.ts: COMBINED_SCORE_KEY="combined"; rankingJudgeModel returns ranking.scoreKey first
  (legacy → rankable/gemini). traditionValue reads shard.combined for the combined key (drill-down
  still resolves each real judge from means).
- ResultsPage.tsx: when ranking present, judges labelled "(component)" + a component-caption ("board
  ranks on the two-judge mean"); legacy keeps ranking/validation copy. Header says two-judge mean.
  Raw viewer / RawComparison / raw-catalog rankable UNTOUCHED (scoped out).
- Tests: leaderboard.test (combined ranking, legacy fallback, traditionValue combined), results.data
  (ranking parse + 4 malformed cases + combined shard + shard-missing-combined notice), results.test
  page-level (board ranks combined, component labels/caption). typecheck clean. multibrowser 407,
  analysis 266.
- NO invented combined leaderboard pin (architect adds after paper numbers accepted).
- phase_5 iter2: BOTH APPROVE.

## Phase 6 — DONE (docs + HOT mirrors + review)
- results/README.md: rewrote all Gemini-only-ranking assertions → two-judge mean; added a `ranking`
  schema-table row + a `combined` shard-doc block; noted the gate guards a component; dated #120
  revision note (both tiers re-stamped fingerprint; Railway baked bundle stale until redeploy);
  linked COMBINED-STATS.md.
- arch-critical.md: leaderboard fact → two-judge mean (Spec 49/110/120). Regenerated CLAUDE.md +
  AGENTS.md HOT CONTEXT mirrors verbatim.
- Found + fixed a PRE-EXISTING #110 governance drift: lessons-learned.md "Metadata contracts & paper
  deliverables (#110)" section was missing from the lessons-critical.md map → added it. Governance
  test now 9/9 (was 3 failing: 2 mirror-stale from my arch edit + this pre-existing map drift).
- docs/analysis/110-dual-judge-fullgrid-summary.md: supersedes note w/ completed-grid numbers
  (residual 2, matched 93,418, guided r 0.684, within 94.0) — architect task done.
- codev/reviews/120-*.md written (verification evidence, spend, residual cells, dual_judge recompute,
  deploy note, lessons).
- ALL 6 phases complete + APPROVED (phase_6: codex COMMENT→addressed, claude APPROVE). Final suites
  green: analysis 266, multibrowser 410, governance 9/9, typecheck clean. Branch pushed
  (origin/builder/aspir-120 == HEAD 3e0cc2ab).
- porch gates on `pr_exists`. Opening PR BLOCKED on GitHub API rate limit (transient) — retrying in
  background. PR body drafted at scratchpad/pr-body.md. On success: porch done 120 --pr <N> --branch
  builder/aspir-120, notify architect (PR gate = human approval, WAIT).

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
