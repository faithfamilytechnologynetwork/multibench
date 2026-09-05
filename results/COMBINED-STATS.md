# Combined two-judge stats + the v3 paper bundle (issue #120)

Since #120 the paper and the `/results` leaderboard rank on the **combined** two-judge mean (Gemini
3.6 Flash + Claude Opus 4.8), not on Gemini alone. This documents how the combined numbers are
produced and how they reconcile.

## Committed primitive — `analysis combined-stats`

The combined ranked aggregates (per-(tradition, subject) scenario-cluster CIs, same schema as
`analysis_stats.json`, plus a combined `subj_overall` point) are produced by a committed, tested
command that reuses the results-export merge seam and the canonical aggregator — feeding **all**
judges' resolved rows so `cell_scores` averages the present judges per cell:

```bash
uv --project workflows/analysis run python -m analysis combined-stats \
  ../../tmp/judging-runs/20260803-merged \
  ../../tmp/judging-runs/20260803-unstated-opus \
  ../../tmp/judging-runs/20260803-framings-opus-sample \
  ../../tmp/judging-runs/20260823-opus-fullgrid \
  --out ../../tmp/combined-stats-20260803.json
```

(The roots are the four in [`README.md`](README.md) order; from the main checkout drop the
`../../`.) It is deterministic (fixed bootstrap seed, sorted keys) → byte-stable. `subj_overall`
reconciles **by construction** with the results-tier combined block (both are the mean over
traditions of `breakdown_mean(cell_scores(all judges), …, scope=full)`), guarded by
`test_combined_stats_reconciles_with_export`.

## The v3 paper `stats_bundle.json` — committed generator `analysis paper-bundle`

The full paper bundle (`tier`, `trad_pooled`, `subj_overall`, `model_tier`,
`guided_residual_hard_minus_easy`, `subj_trad_framing`, `steadfastness_by_framing`,
`pct_scen_negative_unstated`, `spread`, `gaps_pooled`, `dual_judge`) is produced by the **committed**
`analysis paper-bundle` command (`workflows/analysis/analysis/paper_bundle.py`) — a clean checkout
with the four roots regenerates it, **no gitignored throwaway script in the loop**:

```bash
uv --project workflows/analysis run python -m analysis paper-bundle \
  ../../tmp/judging-runs/20260803-merged \
  ../../tmp/judging-runs/20260803-unstated-opus \
  ../../tmp/judging-runs/20260803-framings-opus-sample \
  ../../tmp/judging-runs/20260823-opus-fullgrid \
  --out ../../tmp/judging-runs/20260803-merged/analysis-out/figures-report-v3/stats_bundle.json
```

Every **score aggregate** is over the canonical **combined cell value** (`build_combined_runs` +
`cell_scores` — no second dedup/averaging). **`dual_judge`** is a RAW Gemini-vs-Opus validation
section the combined rule does **not** touch (it compares the judges against each other, never
against their mean), recomputed on the CURRENT roots using `paper_figs_multibench.py`'s exact
`load_opus` (raw-Gemini lut; mapped dedupe + `judgments_v2` overlay) so every n matches its live
asserts by construction: `unstated` n=31,139, `framings_sample` n=9,000 (deduped). `route_bridge` is
computed from the raw two-alias sample rows; **`full_grid`** is the combined-grid agreement over
every double-judged cell (n=93,418; overall r=0.833; by-framing 0.854/0.825/0.684; guided within-0.5
95.4%), with its `rank` subsection. The taxonomy is parameterized so a small fixture drives the whole
pipeline in CI. Guarded by `test_paper_bundle.py` (fixture, CI-runnable — the generator's
`subj_overall` reconciles with the export combined mean-of-means),
`test_v3_bundle_schema_and_dual_judge_recompute`, and
`test_v3_dual_judge_n_matches_paper_figs_live_pairing`.

`tmp/paper_figs_multibench.py` renders the paper figures from this bundle unchanged.

The v2 bundle is **not** overwritten (v3 is a sibling directory). The prior gitignored
`tmp/report_figs_20260803_v3.py` is superseded by this committed command.

## Reconciliation guard

The combined headline ships with the same guard the Gemini headline had: the results-export combined
mean-of-means (`scope=full`, `pressure=all`) equals the v3 bundle's `subj_overall` point to ≤1e-9
(`test_combined_mean_of_means_reconciles_with_v3_bundle`, real-data, skipped when the roots/bundle
are absent). At production time the max deviation was **2.2e-16**.
