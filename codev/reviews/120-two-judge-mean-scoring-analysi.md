# Review: Two-judge mean scoring — analysis bundle, results tier, leaderboard ranking, and docs

**Spec**: [codev/specs/120-two-judge-mean-scoring-analysi.md](../specs/120-two-judge-mean-scoring-analysi.md) ·
**Plan**: [codev/plans/120-two-judge-mean-scoring-analysi.md](../plans/120-two-judge-mean-scoring-analysi.md)

## Outcome

The benchmark of record (`20260803`) now reports the **equal-weight mean of both judges** (Gemini
3.6 Flash + Claude Opus 4.8) per cell everywhere a number is shown — the analysis stats bundle, the
committed `results/20260803/` tier, and the `/results` leaderboard — per Waleed's 2026-09-04
decision ("everything should be an average"). The grid was completed first (re-judging the Opus
empty-response cells) so the mean rests on a near-complete double-judged grid.

All six phases landed with a 2-way consult (codex + claude) each; every phase reached APPROVE
(phase_1 and phase_3 force-advanced on codex APPROVE after the flagged item was addressed and the
architect resolved it). Analysis suite **266 passed**, multibrowser **410 passed**, typecheck clean,
governance docs **9 passed**.

## What shipped, by phase

1. **Grid completion.** Re-judged **33 of 35** missing Opus cells (filtered sittings + a pre-spend
   work-count assertion that made an overspend impossible; verdicts routed unstated→
   `20260803-unstated-opus`, stated/guided→`20260823-opus-fullgrid`). **2** cells persistently
   returned empty/truncated Opus verdicts after 3 passes (≥9 provider attempts each) and are
   **reported, not imputed** (architect-approved). Runbook: [`results/REJUDGE-20260803.md`](../../results/REJUDGE-20260803.md).
2. **Combined block + `ranking` declaration** in both exporters (`export_results.py`,
   `export_raw.py`). Combined is a **separate top-level shard field** (`combined` /
   `combined_steadfastness`, no judge axis) so the per-judge blocks and every shard/coverage guard
   are untouched. The full-grid gate was re-shaped from "exactly one `rankable`" to "**≥1 real judge
   strictly complete**" (`rankable` → legacy selector/fallback metadata).
3. **Combined ranked-stats capability** (`analysis combined-stats`, reusing the merge seam +
   canonical aggregator) and the **v3 paper `stats_bundle.json`** (gitignored) — same schema as v2,
   score aggregates recomputed on the combined cell score, `dual_judge` recomputed on the completed
   grid (see below), `meta` unchanged. Doc: [`results/COMBINED-STATS.md`](../../results/COMBINED-STATS.md).
4. **Additive re-export of `results/20260803`** — combined block + `ranking` added; **Gemini block
   byte-identical**, **Opus delta bounded to exactly the 33 recovered cells**; both the score tier and
   the **raw tier** re-stamped the **equal** cross-tier `fingerprint` (`sha256:696a24c1…`).
5. **SPA leaderboard** ranks on the combined block via the `ranking` declaration (legacy → Gemini
   fallback; malformed → visible notice); judges relabelled co-equal **components**; raw viewer
   untouched.
6. **Docs + HOT mirrors** — `results/README.md`, `codev/resources/arch-critical.md`, the CLAUDE.md/
   AGENTS.md HOT mirrors, and `docs/analysis/110-dual-judge-fullgrid-summary.md`.

## Verification evidence

- **Combined == mean-of-judges**: committed test on fully double-judged fixtures; on the real
  `20260803`, `combined_subj_overall` == results-export combined mean-of-means == v3 bundle
  `subj_overall` to **2.2e-16** (`test_combined_stats_reconciles_with_export`,
  `test_combined_mean_of_means_reconciles_with_v3_bundle`,
  `test_committed_combined_mean_of_means_reconciles_with_v3_bundle`).
- **Gemini byte-identical** across the re-export (means + steadfastness) vs a pinned baseline
  (`git show HEAD:` → `tests/fixtures/results-20260803-baseline/`); the v2 Gemini paper-reconciliation
  test still passes unchanged.
- **Opus delta bounded**: only the 5 recovered traditions change; a slice with unchanged `n_judged`
  is byte-identical; total specific-pressure `n_judged` delta == 33.
- **Cross-tier fingerprint** equal across `results/` and `results-raw/` (`rawData.test.ts` 35/35).
- **Three-way lockstep**: manifest `ranking.single_judge_cells` == the grid-completeness test
  allowlist == the runbook's residual pair.

## Residual single-judge cells (reported, not imputed)

Two cells never received an Opus verdict after 3 re-judge passes:
`judaism | gemini-3.6-flash | MSR-025 | insistence | unstated | full` and
`sunni-islam | Qwen/Qwen3-235B-A22B-Instruct-2507 | JLS-122 | flattery | guided | full`. Their
combined score is the lone Gemini verdict; both are disclosed in
`ranking.single_judge_cells` (count 2, attempts 3) and the review/runbook.

## `dual_judge` recompute (architect decision, 2026-09-05)

`dual_judge.full_grid` was recomputed on the completed grid (n=93,418; overall r=0.833; by-framing
0.854 / 0.825 / **0.684** — guided +0.001 from the 33 recovered cells; guided within-±0.5 95.4%),
using the committed `agree()` convention. The other `dual_judge` subsections (`unstated`,
`framings_sample`, `unstated_rank`, `framings_tier`) are recomputed on the current roots so their n
match `paper_figs_multibench.py`'s live pairing (unstated 31,139; framings_sample 9,000 deduped);
v2's partial-Opus `full_grid` is preserved under `full_grid_v2_partial`. `docs/analysis/
110-dual-judge-fullgrid-summary.md` was updated with these completed-grid numbers + a supersedes note.

## Spend (architect-authorized ≤ 20 USD)

- **Measured (exact, usage-computed): $11.02** — the 33 recovered verdicts.
- **Estimated: ~$1–3** — the 48 failed provider calls (no persisted usage; empties ≈ 0 output).
  Conservative capped-output upper bound ≈ **$17**, under the cap.
- Anthropic **console delta: not checked** (architect-accepted, 2026-09-05 — no console access from
  the worktree; the measured + capped-bound evidence was deemed sufficient).

## Deploy note (for the architect)

The raw tier's `content_fingerprint` changed, so the deployed Railway **baked** raw bundle is stale;
until a redeploy (`railway up --no-gitignore`) the raw viewer falls back to the committed GitHub
tier. The paper is regenerated by the architect from the v3 bundle.

## Deviations / notes

- **Baked #2 vs #7**: #2 (Opus block byte-identical) conflicted with #7 (re-judge adds Opus
  verdicts). Not resolved autonomously — the architect confirmed #7 governs (Gemini byte-identical;
  Opus changes only in the grid-completion cells).
- **Coordination with #119**: this issue landed first; `traditions/protestant-unified` and #119's
  files were not touched.
- **Opportunistic fix**: while updating the HOT mirrors, corrected a pre-existing #110 governance
  drift (the "Metadata contracts & paper deliverables (#110)" section of `lessons-learned.md` was
  missing from the `lessons-critical.md` map) so `test_governance_docs.py` is fully green.

## Flaky tests

None encountered.

## Lessons

- **A re-judge is a spend; make overspend structurally impossible.** `judging judge` scores a whole
  sittings file — feeding it a full grid would have judged ~21,840 cells (hundreds of USD) with no
  error. Filtered sittings + a pre-spend work-count assertion (== the enumerated gap) is the guard.
- **When a shared source stream changes, both tiers must re-stamp the fingerprint.** Re-exporting the
  score tier alone silently broke the Spec 51 cross-tier invariant; the raw tier must be re-exported
  too. (Caught by the committed drift guard, not by me.)
- **A "reuse verbatim" shortcut hides coverage-dependent staleness.** Reusing v2's `dual_judge`
  looked safe but its `unstated` n was stale after grid completion and would have failed the paper
  figure script's live assert. Recompute anything whose inputs changed; pin n against the consumer's
  exact pairing.
- **Keep the derived-number convention single-sourced.** The combined score is one reducer
  (`cell_scores` over all judges); the committed primitive, the export, and the v3 bundle all reuse
  it, so they reconcile by construction (2.2e-16).
