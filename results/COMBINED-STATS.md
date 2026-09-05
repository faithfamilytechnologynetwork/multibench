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

## The v3 paper `stats_bundle.json` (gitignored)

The full paper bundle (`tier`, `trad_pooled`, `subj_overall`, `model_tier`,
`guided_residual_hard_minus_easy`, `subj_trad_framing`, `steadfastness_by_framing`,
`pct_scen_negative_unstated`, `spread`, `gaps_pooled`, `dual_judge`) is produced by the gitignored
`tmp/report_figs_20260803_v3.py`, adapted from its v2 sibling by **swapping only the load step** so
the accumulators receive canonical **combined cell values** (`build_combined_runs` + `cell_scores`,
imported from `analysis` — no second dedup/averaging). Every score aggregate becomes combined
automatically. **`dual_judge`** is a RAW Gemini-vs-Opus validation section that the combined rule
does **not** touch, so v3 **reuses v2's `dual_judge` block verbatim** (including the
`route_bridge`/`full_grid` subsections added by `refresh_dualjudge_stats.py`) rather than
recomputing it from the combined grid — otherwise the Gemini side of the agreement would be polluted
by the combined mean (inflating the inter-judge `r`). `meta` is unchanged too, so the bundle keeps
the exact v2 schema and `tmp/paper_figs_multibench.py` runs unchanged. Guarded by
`test_v3_bundle_matches_v2_schema_and_dual_judge`.

```bash
uv --project workflows/analysis run python ../../tmp/report_figs_20260803_v3.py
# -> ../../tmp/judging-runs/20260803-merged/analysis-out/figures-report-v3/stats_bundle.json
```

The v2 bundle is **not** overwritten (v3 is a sibling directory). The v3 script stops after writing
the bundle (its own fig1–5 rendering assumes discrete per-judge scores and is not the deliverable —
the paper figures are rendered separately from the bundle by `paper_figs_multibench.py`).

## Reconciliation guard

The combined headline ships with the same guard the Gemini headline had: the results-export combined
mean-of-means (`scope=full`, `pressure=all`) equals the v3 bundle's `subj_overall` point to ≤1e-9
(`test_combined_mean_of_means_reconciles_with_v3_bundle`, real-data, skipped when the roots/bundle
are absent). At production time the max deviation was **2.2e-16**.
