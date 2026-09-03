# Dual-judge validation on the full grid — 20260803 (numbers for the paper)

Reference numbers for §2.3 / the dual-judge appendix (App D) / the cost appendix, after extending
the Opus 4.8 second-judge layer for the record run `20260803` from a stated+guided **sample** to
the **full grid** (#110). Every figure below is reproducible: run the committed generator
`docs/analysis/110-dualjudge-fullgrid-figs.py` from the main checkout, which computes agreement,
the tier×framing table, and the heatmap over every matched cell via the canonical export loaders
(the same `resolve_judgments` root-order precedence the committed dataset uses) and writes
`tab_dualjudge_tier.tex`, `tab_dualjudge_agree.tex`, and `fig_dual_judge.pdf` into
`../multibench-papers/` (uncommitted; the architect wires them).

## Coverage and the earned badge

- Committed `counts.judgments`: **Opus 40,114 → 93,385** (unstated 31,114 + stated/guided 62,271);
  Gemini unchanged at **93,420**.
- Opus earns `full_grid: true` from real coverage — per-framing full-scope coverage 99.88%
  (unstated) / 99.99% (stated) / 99.96% (guided), all ≥ the 0.95 tolerant floor —
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
  current logs — see #116. The full-grid run alone failed **39** cells (13 stated/guided + 26
  unstated, the architect's direct count); the retained sample layer back-fills 4 of the
  stated/guided cells, so the merged residual is 35 (26 unstated + 9 stated/guided).

## Dual-judge agreement (full grid, 93,385 matched cells)

Gemini vs. Opus 4.8 over every cell both judged (matched pairs, both scopes):

| slice | n | Pearson r | bias (Opus − Gemini) | within ±0.5 | exact |
|---|--:|--:|--:|--:|--:|
| **overall** | 93,385 | **0.833** | −0.031 | 94.0% | 75.9% |
| unstated | 31,114 | 0.854 | −0.022 | 92.1% | 62.8% |
| stated | 31,137 | 0.825 | −0.029 | 94.7% | 78.8% |
| guided | 31,134 | 0.683 | −0.043 | 95.4% | 86.1% |
| stated + guided | 62,271 | 0.781 | −0.036 | 95.0% | 82.4% |

- The guided correlation is lower (**0.683**) because of **ceiling compression** — guided scores
  cluster near the top of the scale under both judges, so a high proportion agree within ±0.5
  (95.4%) even as the linear correlation falls.
- The combined **stated + guided r = 0.781** replaces the sample-era 0.777 (§2.3 / App D).
- **The five-model order is identical under both judges in all three framings** (ranking by mean
  score per subject): unstated and stated give
  Sonnet 5 > Inkling > GPT-5.6 > Gemini 3.6 > Qwen3-235B; guided gives
  Inkling > Sonnet 5 > Gemini 3.6 > GPT-5.6 > Qwen3-235B. **Caveat:** in guided, the 3rd/4th
  places (Gemini 3.6 vs GPT-5.6) are effectively tied under Opus (0.911 vs 0.910); the order
  matches Gemini's but the margin is within 0.001.

## Programme scale and cost (paper convention)

Using the paper's cost-appendix convention (Gemini grid + Opus validation layers **including** the
route bridge + the router pilot):

- **Programme total: 137,931 → 191,202** = 93,420 (Gemini) + **95,982** Opus + 1,800 router pilot,
  where Opus 95,982 = 31,114 unstated + 62,271 full-grid stated+guided + a **2,597-cell route
  bridge** (sample-root cells judged under both Opus aliases — the OpenRouter tail-fill).
- The paper's published **42,711** is not an estimate: it is committed Opus 40,114 + the 2,597
  route bridge (= 31,114 + 9,000 sampled + 2,597 under the old sample layer). Under #110 the 9,000
  sample is superseded by the 62,271 full-grid stated+guided cells.
- **Opus spend, usage-computed** (repo cost model, `workflows/judging/judging/report.py`:
  `claude-opus-4-8` $5 / $25 per M in/out; cache-write ×2, cache-read ×0.1, batch ×0.5):
  - **New full-grid stated+guided judging: $1,313.29** (62,267 records; 61,648 batch $1,253.56 +
    619 live $59.73) — the incremental cost of #110.
  - **Total Opus validation (all layers): $2,381.98** (unstated $772.77 + sample $295.92 —
    including the sample's 20 `judgments_v2.jsonl` re-judgments — + full-grid $1,313.29). This
    replaces the cost appendix's approximate ≈$1,310 line for the validation layers; the all-in
    programme Total (`tab:cost`, currently ≈$3,700) rises to ≈$4,800.

## Paper edits the architect must wire (this pass regenerated the inputs, not the prose)

Line numbers are for `multibench-paper.tex` at the time of writing.

- **`tab:djtier`** (`tab_dualjudge_tier.tex`, `:1207-1222`): now the full stated+guided **grid**,
  not a sample — update the caption (`:1209` "matched stated+guided sample" → "full stated+guided
  grid") and the n-cell column (now 4,470–6,479). Same 6-column shape, same sign/U+2212 convention.
- **`tab:djtier` commentary** (`:1166-1171`): the guided low-/medium-normativity deflation is still
  ≈0.05–0.06 (−0.06 / −0.05), but the high-normativity tier now moves **−0.01 (guided) / +0.00
  (stated)** (was +0.01 stated), and the guided high-normativity Opus mean is **+0.70 vs +0.85
  medium** (was +0.61 vs +0.87).
- **Sign-flip statistic** (`:1160`): "1.8% of sampled framing cells are a Gemini +1 that Opus
  scores −1" → **1.5%** on the full framing grid.
- **New agreement table** (`tab_dualjudge_agree.tex`): per-framing r / bias / within-±0.5 over the
  full grid — add a `\begin{tabular}{@{}lrrrr@{}}` wrapper (Slice, n, r, bias, within ±0.5).
- **`fig_dual_judge.pdf`** (caption `:1175-1176`): now **3 panels** (Unstated / Stated / Guided
  full grid) — replace "Left: full unstated grid. Right: stated+guided sample."
- **§2.3 / App-D prose**: the sample-era "r = 0.777, bias −0.034, 94.1%, 82.1% exact" (`:1156`,
  `:618`) → full-grid stated+guided "r = 0.781, bias −0.036, 95.0%, 82.4% exact"; unstated stays
  0.854. **Sample methodology** (`:1143-1147`, `:614-618`): "hash-stratified 75-scenario
  stated+guided sample … all 9,000 designed judgments" no longer describes the layer — it is now
  the full stated+guided grid (the sample is retained only as a gap-filler).
- **Counts everywhere**: `137,931 → 191,202` (`:193`, `:378-380`, `app:cost`); "stratified sample
  (42,711 judgments)" (`:377`) → the full-grid 95,982 (31,114 unstated + 62,271 stated+guided +
  2,597 route bridge). All-in cost ≈$3,700 → ≈$4,800 (`:380`, `tab:cost` Total); the Opus
  validation cost line (`:1274`) "42,711 … ≈ $1,310" → 95,982 / $2,381.98.
- **Disclosures** (`:1238-1243`): the sample's two-route collection + the 2,597-cell route bridge
  (r=0.949) still hold (the sample layer is retained). But wherever the Opus alias/overlap dedup is
  described as "the later verdict / later `ts` is the one counted," it is superseded by **root-order
  `(priority, ts)` precedence** — the full-grid layer wins any overlap regardless of `ts`.
- **`tmp/paper_figs_multibench.py`** still reads the sample-era `framings_sample` / `framings_tier`
  bundle keys and emits the 2-panel sample figure with asserts pinned to the sample n — a standard
  re-run would **revert** the dual-judge artifacts. Its dual-judge table/figure/asserts should be
  removed or pointed at `docs/analysis/110-dualjudge-fullgrid-figs.py`, the canonical generator for
  the dual-judge artifacts after #110. (`refresh_dualjudge_stats.py` still refreshes the other,
  non-full-grid `dual_judge` sub-keys; this script only adds `dual_judge.full_grid` and snapshots
  the bundle to `.bak` on its first run.)

## Provenance

- Gemini slice values are **byte-identical** to the pre-#110 committed shards; the paper
  reconciliation test stays green against the re-exported data. Only Opus entries, `judges[]`,
  `counts`, `fingerprint`, and `generated_at` changed in the manifest.
- The full-grid Opus layer is passed **last** in the export, so its verdicts win every one of the
  8,996 sample↔full-grid overlaps (root-order precedence); the sample layer only back-fills cells
  the full-grid run failed.
