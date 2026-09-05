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

That constraint is gone. With #110 and #117, Opus now has **full-grid coverage** — 93,385 of the
93,420 cells of `20260803` are scored by **both** judges (the remaining 35 are single-judge cells
from judge-side empty responses, #116). Waleed's decision (2026-09-04): **"Everything should be an
average."** The benchmark should report the **equal-weight mean of both judges per cell**
everywhere a number is shown, so the headline is a two-judge consensus rather than one judge's
opinion. This affects the paper being written toward the 2026-09-09 freeze and the in-flight
Protestant superset export (#119), both of which need the new rule to be in place first.

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

A cell's score is the **unweighted mean of the present judges' verdicts** (both scopes: turn1 and
full), and that combined score is what every reported number ranks on:

- **Analysis / paper bundle.** A documented, committed way to build a **combined** stats bundle
  over the four `20260803` roots, and the produced **v3 bundle** written to
  `…/analysis-out/figures-report-v3/stats_bundle.json` — same schema as the v2 bundle so
  `tmp/paper_figs_multibench.py` runs unchanged, but with the ranked aggregates (`subj_overall`
  and the standings the paper reads) computed on the combined two-judge score. The v2 bundle is
  **not** overwritten.
- **Committed `results/20260803/` tier — extended additively.** The existing per-judge `means`
  blocks (`gemini-3.6-flash`, `claude-opus-4-8`) stay **byte-identical**. A new **combined** block
  is added, plus a manifest-level `ranking` declaration
  (`{"rule": "mean_of_judges", "judges": [...], "single_judge_cells": N}`).
- **`/results` leaderboard ranks on the combined score.** The single-`rankable`-judge rule is
  replaced by the manifest `ranking` declaration; the board's default/ranked view is the two-judge
  mean. The per-judge selector still shows Gemini and Opus separately.
- **Docs corrected.** The `arch-critical.md` hot fact and `results/README.md` reflect two-judge
  mean ranking; the `CLAUDE.md`/`AGENTS.md` HOT mirrors are regenerated (governance tests enforce
  sync).
- **Single-judge cells are honest.** The 35 single-judge cells use their one verdict, are
  **counted and reported** (manifest `single_judge_cells`), and are never silently dropped or
  imputed.

Users see: the paper and leaderboard headline become a two-judge consensus; Gemini and Opus remain
independently inspectable; coverage/provenance stays transparent.

## Success Criteria

- [ ] **Combined cell rule.** A cell's combined score is the unweighted mean of its present
  judges' verdicts, over both scopes, reusing `analysis.aggregate.cell_scores` fed **all** judge
  layers (not the Gemini-only root). Single-judge cells contribute their one verdict.
- [ ] **Equivalence test.** A committed test asserts the combined per-tradition mean equals the
  mean of the two per-judge means on every **fully double-judged** cell set, and differs only by
  the single-judge cells.
- [ ] **Additive `results/20260803/` re-export.** The re-exported dataset adds a combined `means`
  (and `steadfastness`) block and a manifest `ranking` declaration; the `gemini-3.6-flash` and
  `claude-opus-4-8` blocks are **byte-identical** to the pre-change shards (guarded by a test), and
  the existing v2 paper-reconciliation test still passes unchanged.
- [ ] **`ranking` declaration.** The manifest carries
  `ranking = {"rule": "mean_of_judges", "judges": [...], "single_judge_cells": N}` with `N` = the
  true single-judge cell count for the run.
- [ ] **Full-grid gate preserved.** Both exporters still require a **strictly complete grid for at
  least one judge**; the gate does not weaken.
- [ ] **Leaderboard ranks combined.** `apps/multibrowser` ranks the board on the combined score
  (driven by the manifest `ranking` declaration), with the Gemini/Opus judge selector unchanged;
  `leaderboard.test.ts` is updated (the existing Gemini paper pin stays; **no** invented combined
  pin — the architect adds that after the paper numbers are accepted).
- [ ] **v3 stats bundle produced.** `…/figures-report-v3/stats_bundle.json` exists over the four
  roots in `results/README.md` order, matches the v2 schema, has ranked aggregates on the combined
  score, and does not overwrite v2. (Gitignored, main checkout — a produced artifact, not a
  committed one.)
- [ ] **Docs + mirrors updated.** The one `arch-critical.md` fact line and the `results/README.md`
  ranking section are updated; `CLAUDE.md`/`AGENTS.md` HOT CONTEXT blocks regenerated;
  `test_governance_docs.py` passes.
- [ ] **Scope respected.** No change to judging, prompts, or verdicts; no new spend; nothing under
  `traditions/protestant-unified` or #119's files touched.
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

### Technical constraints

- **Reuse the canonical aggregator.** The combined score must be computed via the existing
  `cell_scores` / `breakdown_mean` semantics — no second implementation of the averaging
  convention (the hot lesson: pre-aggregate in canonical code, client does only the final trivial
  step).
- **Byte-stable, deterministic exports.** The dataset writer already sorts keys; re-exports must
  stay byte-stable, and the per-judge blocks byte-identical to the committed shards.
- **Size ceilings.** ≤ 8 MB total per run, ≤ 1 MB per shard, enforced by the exporter/tests.
  Adding a combined block roughly adds one more judge-sized block per shard — must stay under the
  ceilings.
- **Multi-app porch checks.** Tests run via the per-builder dispatcher `.codev/checks/test.sh`;
  per-phase consult is `["codex","claude"]` (Gemini can't see the worktree).
- **HOT-tier caps.** `arch-critical.md` ≤ 35 lines / ≤ 10 facts; the mirror block must stay in
  sync verbatim.

## Assumptions

- The four `20260803` source roots and the v2 `stats_bundle.json` are reachable from the builder
  worktree at `../../tmp/judging-runs/…` (verified).
- Opus's `20260803` grid is complete enough that Gemini remains the strictly-complete judge
  satisfying the preserved full-grid gate (Gemini is the canonical full grid; Opus's residual gaps
  are the 35 single-judge cells).
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
- **Manifest.** Add `ranking = {"rule": "mean_of_judges", "judges": [gemini, opus],
  "single_judge_cells": N}`. Keep the per-judge `rankable`/`full_grid`/`coverage` metadata for the
  selector and the preserved strict full-grid gate (still exactly-one strictly-complete judge).
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

- **Critical — v3 bundle producer boundary.** Does "a documented way … to build the combined stats
  bundle" mean a fully committed `analysis` command, or a committed combined-aggregation primitive
  plus a documented adaptation of the gitignored figs script? (Recommendation: the latter — commit
  and test the combined *ranked* aggregation the standings read; produce the full bundle via the
  documented figs step. To be settled in the plan; flag to the architect if a fully committed
  command is required.)
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
| Collision between the combined shard key and a real judge id | Low | High | Reserve a non-model key name; assert it is disjoint from `manifest.judges[].model`. |
| Touching #119's surface causes a merge conflict / double-work | Low | Medium | Land first; do not touch `traditions/protestant-unified` or #119 files; architect coordinates the rebase. |
| Single-judge count ≠ 35 (miscount) reported | Low | Medium | Compute from resolved rows on the real data; assert against the expected 35 in a real-data test (skip when data absent). |

## References

- Issue #120 (this spec's source; Baked Decisions above).
- Spec 49 (`results/` explorer), Spec 110 (Opus validation layer / `rankable`), Spec 96
  (`full_grid` earned badge), Spec 51 (raw tier), Spec 55 (dense leaderboard).
- `results/README.md`, `results-raw/README.md`.
- `workflows/analysis/analysis/{aggregate,export_results,export_raw,stats,cli}.py`.
- `apps/multibrowser/src/lib/{leaderboard,resultsModel,results}.ts` + `leaderboard.test.ts`.
- `codev/resources/arch-critical.md`; `CLAUDE.md`/`AGENTS.md` HOT CONTEXT mirrors;
  `apps/tradition_validator/tests/test_governance_docs.py`.
- Gitignored producers (main checkout): `tmp/report_figs_20260803_v2.py` (writes v2
  `stats_bundle.json`), `tmp/paper_figs_multibench.py` (consumes it).
- #119 (Protestant superset export) — coordinated, not touched here.
