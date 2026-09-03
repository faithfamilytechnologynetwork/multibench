# Dual-judge validation on the full grid — 20260803 (numbers for the paper)

Reference numbers for §2.3 / the dual-judge appendix / the cost appendix, after extending the
Opus 4.8 second-judge layer for the record run `20260803` from a stated+guided **sample** to the
**full grid** (#110). Every figure below is computed from the committed dataset or the merged
judging-run roots; the derivation for each is reproducible with the commands in the review doc.

## Coverage and the earned badge

- Opus now judges the full grid across all three framings. Committed `counts.judgments`:
  **Opus 40,114 → 93,385**; Gemini unchanged at **93,420**. (The issue's "42,711 → 93,341" were
  pre-final estimates over raw records; the committed, deduped manifest counts are the above.)
- Opus earns `full_grid: true` from real coverage — per-framing full-scope coverage 99.88%
  (unstated) / 99.99% (stated) / 99.96% (guided), all ≥ the 0.95 tolerant floor — with
  `rankable: false`. Manifest `coverage` (full-scope fraction, ÷ 46,710) = **0.999422**. Gemini is
  `full_grid: true`, `rankable: true`, `coverage: 1.0`. Ranking stays Gemini-only.
- **Residual: 35 cells** have no Opus verdict (of the 93,420-cell grid), per framing × scope:

  | framing | turn1 | full | total |
  |---|--:|--:|--:|
  | unstated | 7 | 19 | 26 |
  | stated | 1 | 2 | 3 |
  | guided | 0 | 6 | 6 |
  | **total** | **8** | **27** | **35** |

  These are **judge-side**, not collection gaps: an empty judge response (no text block →
  `json.loads('')` fails after 3 retries). Refusal vs. `max_tokens` is not distinguishable in the
  current logs — see #116. (The architect's direct count of 39 was over the full-grid run alone;
  the retained sample layer back-fills 4 stated/guided cells, so the merged residual is 35 =
  26 unstated + 9 stated/guided.)

## Dual-judge agreement (full grid, 93,385 matched cells)

Gemini vs. Opus 4.8 over every cell both judged (matched pairs, both scopes):

| slice | n | Pearson r | bias (Opus − Gemini) | within ±0.5 |
|---|--:|--:|--:|--:|
| **overall** | 93,385 | **0.833** | −0.031 | 94.0% |
| unstated | 31,114 | 0.854 | −0.022 | 92.1% |
| stated | 31,137 | 0.825 | −0.029 | 94.7% |
| guided | 31,134 | 0.683 | −0.043 | 95.4% |

- The guided correlation is lower (**0.683**) because of **ceiling compression** — guided scores
  cluster near the top of the scale under both judges, so a high proportion agree within ±0.5
  (95.4%) even as the linear correlation falls.
- **The five-model order is identical under both judges in all three framings** (ranking by mean
  score per subject): unstated and stated both give
  claude-sonnet-5 > Inkling > gpt-5.6-terra > gemini-3.6-flash > Qwen3-235B; guided gives
  Inkling > claude-sonnet-5 > gemini-3.6-flash > gpt-5.6-terra > Qwen3-235B. Opus reproduces the
  Gemini leaderboard order exactly — the validation the second judge exists to provide.

These reproduce the pre-registered expectations (r ≈ 0.834 / 0.854 / 0.825 / 0.684; bias ≈ −0.03;
≈94% within ±0.5; identical five-model order) on the full grid rather than the 75-scenario sample.

## Programme scale and cost

- **Record-run 20260803 committed judgments: 186,805** (Gemini 93,420 + Opus 93,385, deduped).
  Counting the **1,299** dual-alias route-bridge records the paper treats as distinct API calls
  gives **188,104** (the issue's "~188,5xx"). Gross Opus judge calls made across the three Opus
  roots: 104,978.
- **New full-grid Opus judging spend (usage-computed): $1,313.29** — the cost of the 62,267
  stated+guided full-grid judgments, priced by the repo's cost model
  (`workflows/judging/judging/report.py`: `claude-opus-4-8` at $5 / $25 per M input/output tokens;
  cache-write ×2, cache-read ×0.1, batch ×0.5). 61,648 of the 62,267 judgments were batch-priced
  ($1,253.56); 619 live ($59.73). (The issue's pre-run estimate was ~$1,220.)

## Provenance

- Gemini slice values are **byte-identical** to the pre-#110 committed shards; the paper
  reconciliation test (`test_committed_dataset_reconciles_with_paper`) stays green against the
  re-exported data. Only Opus entries, `judges[]`, `counts`, `fingerprint`, and `generated_at`
  changed in the manifest.
- The full-grid Opus layer is passed **last** in the export, so its verdicts win every one of the
  8,996 sample↔full-grid overlaps (root-order precedence); the sample layer only back-fills cells
  the full-grid run failed.
