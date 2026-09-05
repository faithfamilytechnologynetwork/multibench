# Specification: Two-judge mean scoring — analysis bundle, results tier, leaderboard ranking, and docs

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
-->

## Problem Statement

MultiBench's benchmark-of-record run `20260803` (7 traditions, 519 scenarios, 5 subjects) was
scored by **two** judges — Gemini 3.6 Flash and Claude Opus 4.8 — but every reported **number**
(the paper's standings, the committed `results/20260803/` dataset, and the `/results`
leaderboard) is ranked on **Gemini alone**. Opus was carried as a "badged validation layer" that
never re-ranks (Spec 96/110). At the time Opus had only partial coverage, so a single ranking
judge was the honest choice.

That constraint is gone. With #110 and #117, Opus now has **near-full-grid coverage** — 93,385 of
the 93,420 cells of `20260803` are scored by **both** judges (the remaining 35 are single-judge
cells from judge-side empty responses, #116). Waleed's decision (2026-09-04): **"Everything should
be an average."** The benchmark should report the **equal-weight mean of both judges per cell**
everywhere a number is shown, so the headline is a two-judge consensus rather than one judge's
opinion.

Waleed's follow-up (2026-09-05) strengthens this: rather than let 35 cells fall back to a single
judge, **complete the grid first** — re-judge the missing cells (the 35 Opus empties plus any
Gemini gaps) with the identical judge configs, so **both judges are strictly complete on all
93,420 cells** and the mean has **no single-judge fallback** (target: 0 single-judge cells). This
requires a small, architect-authorized re-judging spend (≤ 20 USD). This affects the paper being
written toward the 2026-09-09 freeze and the in-flight Protestant superset export (#119), both of
which need the new rule to be in place first.

Who is affected: readers of the paper and the `/results` leaderboard (the headline changes from
"Gemini says" to "the two-judge mean says"); the architect regenerating the paper; builder-spir-119
whose superset export and leaderboard pin must adopt the same rule.

## Current State

- **The canonical cell reducer already averages judges.** `analysis.aggregate.cell_scores`
  computes each cell's score as the **mean of its present judges' scores**; a breakdown mean is the
  unweighted mean of the in-scope cells. But the results exporter (`analysis/export_results.py`)
  applies this reducer **per judge** (`for judge in judges: cell_scores([rows of that judge])`),
  so the shard `means`/`steadfastness` blocks are keyed **by judge model id**
  (`gemini-3.6-flash`, `claude-opus-4-8`) and there is **no combined block**.
- **Ranking is single-judge.** The manifest carries a per-judge static `rankable` flag (Gemini
  only). `build_manifest` enforces **exactly one** rankable judge and runs `_assert_full_grid` on
  it (strictly complete grid). The SPA (`leaderboard.ts` → `rankingJudgeModel`) ranks the whole
  board on that judge; the judge selector only re-points the per-tradition drill-down.
- **The paper standings come from a gitignored bundle.** The paper's numbers (`subj_overall`,
  `tab_standings`, `tier`, `dual_judge`, …) live in
  `tmp/judging-runs/20260803-merged/analysis-out/figures-report-v2/stats_bundle.json`, produced by
  the gitignored `tmp/report_figs_20260803_v2.py` and consumed by the gitignored
  `tmp/paper_figs_multibench.py`. `subj_overall` is Gemini-only. This bundle is **not** produced by
  committed code today, and prior notes (#110 thread) record it being hand-patched.
- **Docs assert the superseded fact.** `codev/resources/arch-critical.md` (mirrored verbatim into
  `CLAUDE.md`/`AGENTS.md`) states the leaderboard "ranks on the single `rankable` judge (Gemini)"
  and that Opus "must NEVER confer ranking"; `results/README.md` says the same.
- **Reconciliation is guarded.** `test_export_results.py` reconciles the committed Gemini
  mean-of-means against the paper's v2 `subj_overall` to 1e-9. The leaderboard reconciles with the
  paper by construction (the SPA does only the final equal-weight mean-of-means).

## Desired State

**First, the grid is completed.** The 35 Opus empty-response cells (and any Gemini gaps found) are
re-judged with the identical judge configs and their verdicts written into the existing source
layers (Opus into `20260823-opus-fullgrid`), so both judges are strictly complete on all 93,420
cells (barring any cell that stays empty after three retries, which is reported, not imputed).

Then, a cell's score is the **unweighted mean of the present judges' verdicts** (both scopes:
turn1 and full), and that combined score is what every reported number ranks on:

- **Analysis / paper bundle.** A **committed, tested** combined *ranked* aggregation over the four
  `20260803` roots (reconciled against the produced bundle), and the produced **v3 bundle** written
  to `…/analysis-out/figures-report-v3/stats_bundle.json` by a **documented** v3 figs step that
  reuses that committed aggregation — same schema (same top-level keys) as the v2 bundle so
  `tmp/paper_figs_multibench.py` runs unchanged. (The committed surface is the ranked aggregation +
  its tests; the full rich bundle is the reproducible figs-step output, matching how v2 already
  works — see the producer-boundary open question.) Which fields change:
  - **Recomputed on the combined two-judge cell score** (every score/CI aggregate — "everything is
    an average"): `subj_overall`, `tier`, `trad_pooled`, `model_tier`,
    `guided_residual_hard_minus_easy`, `subj_trad_framing`, `steadfastness_by_framing`,
    `pct_scen_negative_unstated`, `spread`, `gaps_pooled`.
  - **Left per-judge, unchanged in meaning:** `dual_judge` — it is *by definition* the
    Gemini-vs-Opus agreement/correlation section (per-judge ranks, r, agreement heatmaps); it
    validates the two judges against each other and would be meaningless as a combined average.
  - **`meta`** unchanged (`n_boot`, `seed`, `n_scen`).
  - **Bootstrap CIs:** unchanged machinery — the scenario-cluster bootstrap resamples over the
    combined-cell values. With the grid completed (0 single-judge cells) every cell is the mean of
    both judges; any residual single-judge cell contributes its lone verdict as that cell's value
    (no special-casing).
  The v2 bundle is **not** overwritten.
- **Committed `results/20260803/` tier — extended additively.** The existing per-judge `means`
  blocks (`gemini-3.6-flash`, `claude-opus-4-8`) stay **byte-identical**. A new **combined** block
  is added, plus a manifest-level `ranking` declaration
  (`{"rule": "mean_of_judges", "judges": [...], "single_judge_cells": N}`).
- **`/results` leaderboard ranks on the combined score.** The single-`rankable`-judge rule is
  replaced by the manifest `ranking` declaration; the board's default/ranked view is the two-judge
  mean. The per-judge selector still shows Gemini and Opus separately.
- **Judge-role copy reflects the mean as headline.** Under a `mean_of_judges` ranking, **neither**
  real judge is "the ranking judge" — the mean is. So the judge-role labeling on the score board
  (`isRankingJudge`/`classifyJudgeRoles` as surfaced in `ResultsPage.tsx` and the
  `opus (validation)` selector label) is adjusted so Gemini and Opus read as **co-equal component
  judges** of the headline mean, each independently inspectable — not "ranking vs validation." The
  exact strings are finalized in the plan. **Out of scope:** the raw-results viewer / AFB catalog
  path (`RawComparison.tsx`, `ReviewScenarioPage.tsx`, the raw-catalog `rankable`) is left
  untouched — those catalogs are not the two-judge-mean score board.
- **Docs corrected.** The `arch-critical.md` hot fact and `results/README.md` reflect two-judge
  mean ranking; the `CLAUDE.md`/`AGENTS.md` HOT mirrors are regenerated (governance tests enforce
  sync).
- **Single-judge cells are eliminated, then honest.** After grid completion the target is **0**
  single-judge cells; any cell that remains single-judge after three retries uses its one verdict
  and is **counted and reported** (manifest `single_judge_cells`), never silently dropped or
  imputed.

Users see: the paper and leaderboard headline become a two-judge consensus over a complete grid;
Gemini and Opus remain independently inspectable; coverage/provenance stays transparent.

## Success Criteria

- [ ] **Grid completed before rescoring.** The 35 Opus empty-response cells (26 unstated, 3
  stated, 6 guided) and any Gemini gaps are re-judged with the identical judge configs (Opus per
  `tmp/opus-judge.yaml`, Gemini record config); new verdicts land in the existing source layers
  (Opus → `20260823-opus-fullgrid`) so the four-root order still resolves them. Target: both
  judges strictly complete on all 93,420 cells.
- [ ] **Re-judging spend within budget.** ≤ 20 USD, keys via the `taqwabench/.env` seam;
  usage-computed actuals reported in the review. Any cell still empty after three retries is
  reported (not imputed).
- [ ] **Combined cell rule.** A cell's combined score is the unweighted mean of its present
  judges' verdicts, over both scopes, reusing `analysis.aggregate.cell_scores` fed **all** judge
  layers (not the Gemini-only root). Single-judge cells contribute their one verdict.
- [ ] **Equivalence test.** A committed test asserts the combined per-tradition mean equals the
  mean of the two per-judge means on every **fully double-judged** cell set, and differs only by
  the single-judge cells.
- [ ] **Documented combined-stats capability.** A committed, documented `analysis` capability (a
  flag on `analysis report` or a small `analysis combined-stats` command) builds the combined
  ranked aggregates over the four roots via the canonical `cell_scores`; the v3 `stats_bundle.json`
  is produced by a documented v3 figs step reusing it (see the producer-boundary open question).
- [ ] **Combined headline is reconciliation-guarded.** A committed real-data test (skipped when
  the roots are absent) asserts the **combined** mean-of-means (`scope=full`, `pressure=all`)
  reconciles to ≤ 1e-9 with the v3 bundle's `subj_overall` — the analogue of the existing Gemini
  pin (`test_export_results.py:810-821`), so the new headline ships with the same guard the old one
  had. (This is *not* the deferred SPA leaderboard pin, which the architect still adds after
  accepting the paper numbers.)
- [ ] **Additive `results/20260803/` re-export.** The re-exported dataset adds a combined `means`
  (and `steadfastness`) block and a manifest `ranking` declaration; the `gemini-3.6-flash` and
  `claude-opus-4-8` blocks are **byte-identical** to the pre-change shards (guarded by a test), and
  the existing v2 paper-reconciliation test still passes unchanged.
- [ ] **`ranking` declaration.** The manifest carries `ranking = {"rule": "mean_of_judges",
  "score_key": "<combined block key>", "judges": [...], "single_judge_cells": N}` where `score_key`
  names the shard block the SPA ranks on, `judges` are the real judges averaged, and `N` = the true
  single-judge cell count (target **0** after grid completion). The combined `score_key` is
  asserted **disjoint** from every real `manifest.judges[].model`.
- [ ] **Manifest/shard validation.** The SPA falls back to the `rankable`/Gemini judge only for a
  **legacy** manifest that omits `ranking`. A manifest that **has** a `ranking` declaration but is
  malformed (unknown `rule`, `score_key` block missing from a shard, unknown/duplicate judges, or a
  `score_key` colliding with a real model id) surfaces a **visible error/notice**, not a silent
  revert to Gemini. Schema/parser + shard-consistency tests cover both paths.
- [ ] **Full-grid gate re-shaped, not weakened.** The old rule ("exactly **one** `rankable` judge,
  strictly complete") is replaced by "**at least one** real judge is strictly complete." `rankable`
  becomes optional/legacy metadata (kept for the selector + old-manifest fallback); its one-judge
  invariant is dropped for new exports. Both exporters fail fast if **no** real judge is strictly
  complete.
- [ ] **Leaderboard ranks combined.** `apps/multibrowser` ranks the board on the combined score
  (driven by the manifest `ranking.score_key`), with the Gemini/Opus judge selector still
  resolving each real judge for the drill-down; the judge-role copy reflects the mean as headline
  (Gemini and Opus as co-equal components). `leaderboard.test.ts` is updated (the existing Gemini
  paper pin stays; **no** invented combined pin — the architect adds that after the paper numbers
  are accepted). The raw-results/AFB catalog path is untouched.
- [ ] **v3 stats bundle produced.** `…/figures-report-v3/stats_bundle.json` exists over the four
  roots in `results/README.md` order, matches the v2 schema, has ranked aggregates on the combined
  score, and does not overwrite v2. (Gitignored, main checkout — a produced artifact, not a
  committed one.)
- [ ] **Docs + mirrors updated.** The one `arch-critical.md` fact line is updated (to say the
  leaderboard ranks on the two-judge mean; note the strict full-grid gate now guards a **component**
  of the ranked score, not the ranked score itself). **Every** Gemini-only-ranking assertion in
  `results/README.md` is corrected (currently ~6 places: the intro, the `judges` schema-table row,
  and the leaderboard/published-runs sections), **plus** a new schema-table row documenting the
  `ranking` manifest field. `CLAUDE.md`/`AGENTS.md` HOT CONTEXT blocks regenerated;
  `test_governance_docs.py` passes.
- [ ] **Scope respected.** No change to judge prompts or configs (re-judging the missing cells
  uses the *identical* record configs); no spend beyond the authorized ≤ 20 USD re-judging;
  nothing under `traditions/protestant-unified` or #119's files touched.
- [ ] **Per-builder test suite green** (`.codev/checks/test.sh` for the touched apps: analysis
  pytest + multibrowser vitest).

## Constraints

### Baked Decisions (fixed — copied verbatim from issue #120)

1. **Rule.** A cell's score is the unweighted mean of the present judges' verdicts, both scopes.
   This is already the canonical reducer in `analysis.aggregate.cell_scores`; the change is to feed
   it **all** judge layers instead of the Gemini-only root, and to make the export/leaderboard rank
   on that combined score. Cells with one judge only (35 in `20260803`, judge-side empty responses;
   #116) use the single verdict and are **counted and reported** in the manifest, never silently
   dropped or imputed.
2. **`results/20260803` is extended additively, never mutated.** The existing per-judge `means`
   blocks (`gemini-3.6-flash`, `claude-opus-4-8`) stay byte-identical (the existing paper-
   reconciliation test keeps passing unchanged). Add a combined block and a manifest-level ranking
   declaration. Same for `20260813-protestantism` if touched (prefer not to touch it).
3. **The leaderboard ranks on the combined score.** Replace the single-`rankable`-judge rule (#110)
   with an explicit manifest `ranking` declaration (e.g. `{"rule": "mean_of_judges", "judges":
   [...], "single_judge_cells": N}`). The per-judge selector in the SPA keeps showing Gemini and
   Opus separately; the default/ranked view is the mean. Both exporters keep enforcing a strictly
   complete grid for **at least one** judge (the full-grid gate does not weaken).
4. **The paper is regenerated by the architect** from a new stats bundle; this issue must produce
   that bundle: `tmp/judging-runs/20260803-merged/analysis-out/figures-report-v3/stats_bundle.json`
   (main checkout, gitignored) built over the four roots in `results/README.md` order
   (`20260803-merged`, `20260803-unstated-opus`, `20260803-framings-opus-sample`,
   `20260823-opus-fullgrid` last), same schema as `figures-report-v2/stats_bundle.json` so
   `tmp/paper_figs_multibench.py` runs unchanged. Do not overwrite v2.
5. **Coordination with #119.** builder-spir-119 is mid-run (Phase 4). Its Phase 5 superset export
   and Phase 7 leaderboard pin must use this rule. This issue lands **first**; the architect then
   amends #119's plan and the builder rebases. Do not touch `traditions/protestant-unified` or
   #119's files.
6. **Architecture docs.** `codev/resources/arch-critical.md` states "Opus is a badged validation
   layer, never re-ranks." That fact is superseded: update the hot fact and `results/README.md` in
   this PR (regenerate the CLAUDE.md/AGENTS.md HOT mirrors; the governance tests enforce it). Keep
   the change to the one fact line plus the README section.

7. **Scope addition (Waleed, 2026-09-05): complete the grid before rescoring.** The rescore is the
   **full grid under the two-judge mean**. Where a cell lacks a verdict from either judge,
   **re-run the judging for that cell** rather than falling back to the single judge. In
   `20260803` that is the 35 Opus-side empty-response cells (26 unstated, 3 stated, 6 guided;
   #116); check Gemini for gaps the same way and re-judge any found. Target: both judges strictly
   complete on all 93,420 cells, so the combined score has no single-judge fallback and the
   manifest reports **0 single-judge cells**.
   - Re-judge with the identical judge configs used for the layers being completed (Opus:
     `claude-opus-4-8` with thinking, per `tmp/opus-judge.yaml`; Gemini: the record config). Write
     the new verdicts into the existing roots' layers so the four-root order in `results/README.md`
     still resolves them (Opus into `20260823-opus-fullgrid`).
   - **Spend**: architect-authorized up to **20 USD** for this re-judging only; keys via the
     `taqwabench/.env` seam (Opus via the CEFE judge key, batch or live is fine at this size;
     Gemini via OpenRouter). Report usage-computed actuals in the review. If a cell still returns
     empty after three retries, report it; do not impute.
   - Only after the grid is complete: build the v3 bundle, the combined block, and the ranking
     declaration as specified above.

   **This supersedes the single-judge-fallback treatment in Baked Decision #1** for `20260803`:
   the fallback path (a cell using one verdict) is now a *last resort* reported only if a cell
   stays empty after three retries, not the expected outcome. The combined rule, the additive
   export, and the `ranking` declaration are otherwise unchanged; `single_judge_cells` becomes the
   count of cells that remain single-judge after re-judging (target 0).

### Technical constraints

- **Reuse the canonical aggregator.** The combined score must be computed via the existing
  `cell_scores` / `breakdown_mean` semantics — no second implementation of the averaging
  convention (the hot lesson: pre-aggregate in canonical code, client does only the final trivial
  step).
- **Byte-stable, deterministic exports.** The dataset writer already sorts keys; re-exports must
  stay byte-stable, and the per-judge blocks byte-identical to the committed shards.
- **Size ceilings.** ≤ 8 MB total per run, ≤ 1 MB per shard, enforced by the exporter/tests.
  Adding a combined block roughly adds one more judge-sized block per shard; the ceiling is not a
  real risk here (committed `results/20260803` is ~196 KB total, largest shard ~27 KB) but the
  existing size test must keep passing.
- **The strict full-grid gate now guards a *component* of the ranked score.** After the re-shape,
  `_assert_full_grid` still guarantees a strictly-complete real judge (Gemini), but the quantity
  actually ranked is the combined mean — which, absent grid completion, would include single-judge
  cells. Grid completion (baked #7) drives that to 0; the docs/manifest must state the gate guards
  a component of the ranked score, with `ranking.single_judge_cells` disclosing any residual.
- **Multi-app porch checks.** Tests run via the per-builder dispatcher `.codev/checks/test.sh`;
  per-phase consult is `["codex","claude"]` (Gemini can't see the worktree).
- **HOT-tier caps.** `arch-critical.md` ≤ 35 lines / ≤ 10 facts; the mirror block must stay in
  sync verbatim.

## Assumptions

- The four `20260803` source roots and the v2 `stats_bundle.json` are reachable from the builder
  worktree at `../../tmp/judging-runs/…` (verified).
- The subject transcripts (`sittings.jsonl`) for the 35 missing cells already exist in the source
  roots; only the Opus verdict is absent, so re-judging is a judge-only re-run over those sittings
  (verified: `20260823-opus-fullgrid/<tradition>/` carries `sittings.jsonl` + `judgments.jsonl`).
- Gemini is the canonical full grid; after re-judging, Opus is expected to reach the complete grid
  too, so both judges satisfy the preserved strict full-grid gate.
- The `judging` workflow can re-judge a targeted subset of sittings with `tmp/opus-judge.yaml` and
  the verdicts merge into the existing layer via the exporter's normalize/overlay/dedup path.
- The v3 bundle's rich non-ranked aggregates (tier taxonomy, `dual_judge`, `gaps_pooled`, …) keep
  the v2 schema; only the **ranked** aggregates the paper's standings read (`subj_overall` and its
  siblings) change to the combined score.
- `20260813-protestantism` is **not** touched (per baked decision #2 preference).
- Depends on #110/#117 having landed Opus full-grid coverage (they have — `20260823-opus-fullgrid`
  exists).

## Solution Approaches

The open design choice is **how the combined score is represented in the shard and how the v3
stats bundle is produced**. The cell rule itself is fixed (baked #1).

### Approach 1: Combined as a synthetic "judge" layer in the shard, driven by a manifest `ranking` declaration (recommended)

- **Shard.** Add a combined block under a reserved key (e.g. `mean_of_judges`) in the shard's
  `means`/`steadfastness`, aggregated by feeding `cell_scores` **all** resolved judgments together
  (the canonical reducer already averages present judges per cell, so single-judge cells fall out
  correctly). The existing per-judge blocks are untouched → byte-identical.
- **Manifest.** Add `ranking = {"rule": "mean_of_judges", "score_key": "<combined block key>",
  "judges": [gemini, opus], "single_judge_cells": N}`. The explicit **`score_key`** names the shard
  block the SPA ranks on (so the SPA never has to guess it from `rule`). Keep the per-judge
  `rankable`/`full_grid`/`coverage` metadata for the selector and old-manifest fallback; the new
  gate requires **≥1** real judge strictly complete (not "exactly one rankable").
- **SPA.** `rankingJudgeModel`/`computeLeaderboardRows` read the combined key from the manifest
  `ranking` declaration (falling back to the pre-#120 `rankable` judge for older manifests). The
  judge selector still resolves `gemini`/`opus` keys to their per-judge blocks.
- **v3 bundle.** The combined per-(subject, framing) means are a first-class committed
  aggregation; the v3 `stats_bundle.json` is produced by a documented, minimal adaptation of the
  existing paper-figs generator that swaps the ranked aggregates onto the combined layer, reusing
  the committed combined-aggregation primitive. The committed, tested surface is the combined
  primitive + the equivalence test; the bundle is its deterministic output.
- **Pros.** Minimal churn to the shard shape (a combined block is just another judge-shaped block);
  reuses `cell_scores` verbatim; the SPA's aggregation path is unchanged except which key it ranks;
  additive and byte-identical per-judge blocks by construction; single-judge cells handled for free.
- **Cons.** The combined key is a "virtual judge" that isn't a real judge model — the manifest
  `judges` list and the shard `judges`/`means` keys must clearly distinguish it (docs + a schema
  note) so the selector never treats it as a real judge.
- **Risk/complexity.** Low–medium. The main care is keeping the per-judge blocks byte-identical and
  making the SPA's ranking key selection robust for old and new manifests.

### Approach 2: Fully port the paper stats-bundle pipeline into a committed `analysis` command

- Add `analysis report --combined` / `analysis stats-bundle` that emits the entire paper bundle
  (tier, model_tier, dual_judge, gaps_pooled, …) with combined ranking, replacing the gitignored
  figs script outright.
- **Pros.** The whole bundle becomes committed and reproducible; no gitignored producer.
- **Cons.** Large — the bundle carries paper-specific taxonomies (tier easy/medium/hard, dual-judge
  correlation, negative-scenario percentages) that live only in the throwaway figs script.
  Porting all of it is well beyond the 2-day timeline and out of this issue's stated scope (the
  paper text and figures are the architect's job). High risk of scope creep and of diverging from
  the paper's exact conventions.
- **Risk/complexity.** High. Rejected as the primary approach; the combined **ranked** aggregates
  (what the standings actually use) are the only part that must be committed and tested.

**Recommendation: Approach 1.** It satisfies every baked decision with the least churn, keeps the
per-judge blocks byte-identical, and localizes the committed/tested surface to the combined
aggregation primitive + the equivalence + additive-export tests. The full rich bundle stays where
it already lives (a documented figs-script step) while the numbers the paper ranks on become
committed and reconcilable.

## Open Questions

- **Critical — v3 bundle producer boundary (recommended resolution, architect may override).** The
  full paper bundle carries paper-only taxonomies (tier easy/medium/hard, `dual_judge`,
  `gaps_pooled`, negative-scenario rates) that live only in the gitignored v2 figs script and are
  out of this issue's committed scope. **Resolution:** commit and test the combined **ranked**
  aggregation the standings/paper actually rank on — a documented `analysis` capability (a flag on
  `analysis report`, or a small `analysis combined-stats` command) that takes the four roots and
  emits the combined per-(subject, tradition, framing, scope, pressure) means + CIs via the
  canonical `cell_scores`. The **v3 `stats_bundle.json`** is then produced by a documented v3 figs
  step (`tmp/report_figs_20260803_v3.py`, gitignored like its v2 sibling) that reuses this
  committed combined aggregation for the score fields and keeps the per-judge `dual_judge` section
  — the same producer shape v2 already has. The committed/tested surface is the combined
  aggregation + the equivalence + additive-export tests; the rich bundle stays a documented,
  reproducible figs step. If the architect requires the **entire** bundle to be committed
  (Approach 2), that is a larger, separately-scoped effort — flag before planning it.
- **Important — combined shard key name.** `mean_of_judges` vs `combined` vs `both`. Must not
  collide with a real judge model id and must be unambiguous to the SPA selector. (Recommend a
  reserved, non-model name; settle in plan.)
- **Important — `single_judge_cells` counting scope.** Count over which cell universe — all
  (subject, scenario, pressure, framing, scope) cells, or only full-scope? (Recommend: all cells
  that carry exactly one judge's verdict across both scopes, reported as one integer; verify it
  lands at 35 for `20260803`.)
- **Important — old-manifest fallback.** Should the SPA fall back to the `rankable` judge when a
  manifest has no `ranking` declaration (e.g. `20260813-protestantism`, left untouched)? (Recommend
  yes — a graceful fallback so the untouched Protestant run still ranks on Gemini.)
- **Nice-to-know — combined `full_grid`/`coverage` badges.** Does the combined layer get its own
  coverage badge, or is coverage only reported per real judge? (Recommend: coverage stays per real
  judge; the combined layer is defined wherever ≥1 judge covers a cell.)

## Test Scenarios

- **Grid completion.** After re-judging, a coverage check shows both judges strictly complete on
  all 93,420 cells (or reports the exact residual single-judge cells with reasons). The 35 known
  Opus empties are re-judged and their verdicts present in `20260823-opus-fullgrid`.
- **Re-judge is judge-only + idempotent.** Re-judging targets only the missing cells over existing
  sittings; re-running does not duplicate verdicts (dedup by identity + later `ts`/priority).
- **Combined equals mean-of-per-judge-means on double-judged cells.** For a fixture (and the real
  `20260803`), the combined per-tradition mean equals `(gemini_mean + opus_mean) / 2` on every
  fully double-judged cell set, and differs only where a cell has a single judge.
- **Single-judge cell contributes its lone verdict.** A cell judged by only one judge yields that
  judge's score as the combined cell score (no imputation, not dropped).
- **`single_judge_cells` count is correct and reported.** The manifest `ranking.single_judge_cells`
  equals the true count (35 for `20260803` on the real data).
- **Per-judge blocks byte-identical.** Re-exporting `results/20260803/` leaves the
  `gemini-3.6-flash` and `claude-opus-4-8` blocks byte-for-byte unchanged; the v2 paper-
  reconciliation test still passes.
- **Combined mean-of-means reconciles with the v3 bundle.** The combined mean-of-means
  (`scope=full`, `pressure=all`) equals the v3 bundle's `subj_overall` to ≤ 1e-9 (real-data test,
  skipped when roots absent).
- **Full-grid gate still fires.** An export whose only strictly-complete judge is removed/gapped
  fails fast (the gate does not weaken).
- **Leaderboard ranks on combined.** The SPA's ranked standings use the combined block; the judge
  selector still resolves Gemini/Opus to their per-judge blocks; ordering differs from Gemini-only
  where the two judges disagree.
- **Old manifest still ranks.** A manifest without a `ranking` declaration
  (`20260813-protestantism`) still ranks (Gemini fallback).
- **Governance docs in sync.** `test_governance_docs.py` passes after the fact + mirror edits.
- **Size ceilings.** The re-exported dataset stays within ≤ 8 MB / ≤ 1 MB shard.

## Risks and Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Per-judge blocks drift (not byte-identical) after adding the combined block | Medium | High | Additive-only serialization; a byte-identity test comparing the two per-judge blocks against the pre-change committed shards. |
| v3 bundle schema drifts from v2 → `paper_figs_multibench.py` breaks | Medium | High | Diff v3 top-level keys against v2; keep non-ranked aggregates identical in shape; verify the paper script runs (architect step) — surface if a key is missing. |
| Scope creep porting the whole paper bundle into committed code | Medium | Medium | Approach 1: commit only the combined *ranked* aggregation + tests; document the figs-script step. |
| SPA ranking-key selection breaks the untouched Protestant run | Low | Medium | Fallback to the `rankable` judge when no `ranking` declaration is present; test both manifest shapes. |
| Collision between the combined shard key and a real judge id | Low | High | Reserve a non-model key name; assert it is disjoint from `manifest.judges[].model`. The synthetic combined key must **never** enter `TraditionExport.judges`, the shard `judges` list, `coverage_counts_from_judged`, or the `JUDGE_UI[model]` lookup at `build_manifest` (else `AnalysisInputError("no UI metadata for judge")`) — carry it in a separate combined block + the manifest `ranking` declaration only. |
| Touching #119's surface causes a merge conflict / double-work | Low | Medium | Land first; do not touch `traditions/protestant-unified` or #119 files; architect coordinates the rebase. |
| Re-judging overspends the 20 USD budget | Low | Medium | Only 35 cells (+ any Gemini gaps); batch/live are cheap at this size; dry-run/estimate the cell count first; report usage-computed actuals; stop and flag if approaching the ceiling. |
| Re-judged cells still return empty after retries | Low | Medium | Three retries per the scope; report residual single-judge cells (do not impute); the combined rule + `single_judge_cells` field still handle them honestly. |
| Wrong judge config drifts the new verdicts from the record | Low | High | Use `tmp/opus-judge.yaml` verbatim (thinking on) for Opus and the record config for Gemini; write into the same layer so dedup/normalization applies uniformly. |
| Re-judge writes duplicate/overlapping verdicts | Low | Medium | Verdicts merge via the exporter's normalize/overlay/dedup (later `ts`/priority wins); verify no duplicate identities post-merge. |

## References

- Issue #120 (this spec's source; Baked Decisions above).
- Spec 49 (`results/` explorer), Spec 110 (Opus validation layer / `rankable`), Spec 96
  (`full_grid` earned badge), Spec 51 (raw tier), Spec 55 (dense leaderboard).
- `results/README.md`, `results-raw/README.md`.
- `workflows/analysis/analysis/{aggregate,export_results,export_raw,stats,cli}.py`.
- `workflows/judging/` (judge-only re-run: `python -m judging judge <sittings> <tradition> …`);
  `tmp/opus-judge.yaml` (Opus judge config, thinking on); `taqwabench/.env` (key seam — CEFE Opus
  key, OpenRouter Gemini); #116 (the 35 Opus empty-response cells).
- `apps/multibrowser/src/lib/{leaderboard,resultsModel,results}.ts` + `leaderboard.test.ts`.
- `codev/resources/arch-critical.md`; `CLAUDE.md`/`AGENTS.md` HOT CONTEXT mirrors;
  `apps/tradition_validator/tests/test_governance_docs.py`.
- Gitignored producers (main checkout): `tmp/report_figs_20260803_v2.py` (writes v2
  `stats_bundle.json`), `tmp/paper_figs_multibench.py` (consumes it).
- #119 (Protestant superset export) — coordinated, not touched here.
