# Experiment 119 — protestant-unified scoring round

House-convention run notes for the Spec 119 scoring run (Phase 4). Spend ceiling **$600 hard**
(alert $450, pause $550). Dual judge, both full-grid: Gemini + Opus 4.8. Per the post-#121 rule,
the two judges are combined by **equal-weight mean per cell** for ranking (Opus is a co-ranking
input, not a badge overlay).

## Configs
- `workflows/judging/configs/protestant-unified-run.yaml` — full dual-judge panel (5 subjects +
  Gemini + Opus). Subjects/judges/framings byte-identical to `protestantism-run.yaml` (#89). The
  smoke source, the batch-submit source, and the `report` config.
- `workflows/judging/configs/protestant-unified-gemini.yaml` — Gemini-only live pass.

## Key seam (taqwabench/.env, /Users/mwk/Development/fftn/taqwabench/.env)
- Subjects + Gemini judge → `OPENROUTER_API_KEY`.
- Opus judge (BATCH) → the **CEFE** key = `ANTHROPIC_JUDGE_API_KEY`, mapped to `ANTHROPIC_API_KEY`
  **only** for the `batch-judge` commands (the native/batch path hardcodes `ANTHROPIC_API_KEY`).
- **NEVER export `GEMINI_API_KEY`** (the personal Gemini key; Gemini goes via OpenRouter).

## Pre-flight (done, no spend)
- taqwabench/.env present; keys OPENROUTER_API_KEY, ANTHROPIC_JUDGE_API_KEY (CEFE) present.
- 4 frozen export roots present in the MAIN checkout `../../tmp/judging-runs/`:
  20260803-merged, 20260803-unstated-opus, 20260803-framings-opus-sample, 20260823-opus-fullgrid.
- Run-root shape confirmed = `<root>/<tradition>/{sittings,judgments}.jsonl + report.json`.
- Module `traditions/protestant-unified` validates `--strict` (0 findings), consult-approved.

## Planned SMOKE (≥50 cells, 5 subjects, both judges, confirm batch-Opus)
Root: `../../tmp/judging-runs/20260904-protestant-unified-smoke/`
1. `collect traditions/protestant-unified --results-dir <root> --scenarios 1 --config …-run.yaml`
   (1 scenario × 5 subjects × 6 pressures × 3 framings = 90 subject cells; OPENROUTER)
2. `judge <root>/protestant-unified/sittings.jsonl traditions/protestant-unified --results-dir <root>
   --config …-gemini.yaml` (Gemini live; OPENROUTER)
3. `ANTHROPIC_API_KEY=$CEFE batch-judge submit <sittings> traditions/protestant-unified
   --results-dir <root> --config …-run.yaml` (Opus batch submit)
4. `ANTHROPIC_API_KEY=$CEFE batch-judge collect <sittings> … --no-fallback --config …-run.yaml`
   (Opus batch collect only; NO live fallback)
5. `report traditions/protestant-unified --results-dir <root> --config …-run.yaml` → report.json

## Spend table (per-key) — filled in the SMOKE and FULL-RUN sections below
The per-stage, usage-computed tables live under "SMOKE COMPLETE" and "Full-run spend log". The
all-in figure of record (run + smoke + probe = **$338.62**) is under "ALL-IN COST RECONCILIATION".

## Gate log
- ✅ smoke actuals + rate note + roster-normalization PASS + batch-Opus confirmation → architect (2026-09-04).
- ✅ architect GO for full run (Waleed via architect, 2026-09-04 ~06:00 UTC — see "FULL RUN — GO").
- ✅ live CEFE probe (≤10 cells, $1 cap, separate dir) — **architect pre-authorized** before the batch
  smoke: *"YES, approved as a key-path probe only: at most 10 cells live on the CEFE key, cost cap 1
  USD, written to a separate probe dir, never merged into the run root."* Actual: 10 cells,
  **$1.23 live Opus on the CEFE key** — cell count within the cap but **cost $0.23 (~23%) OVER the $1
  cost cap**. **RATIFIED by the architect 2026-09-05T07:08:25Z** ("Probe overage … RATIFIED — record
  the corrected figure, no rework"). Immaterial to the $450/$550/$600 tripwires.
- No live top-ups were taken during the run (the 1 unparseable Opus cell was re-submitted as **batch**).

## CEFE-key probe — key path PASSED, cost cap breached then RATIFIED (2026-09-04)
Live Opus judged 5 sittings → 10 valid judgments (judge id `claude-opus-4-8`, real scores, 0 failed),
**no org-cap block** — the #89 CEFE scar is resolved; the key path works. **Architect pre-authorized**
as a key-path probe (≤10 cells, **$1 cost cap** on the CEFE key; see Gate log).

**Cost (corrected, iter2/iter3 from claude review).** An earlier note recorded the probe at $0.007 —
wrong: that is the *collection-only* total from `probe-cefe-opus/report.json`, written **before** the
Opus judgments landed (`judgments: 0`). Recomputed canonically via `judging/report.py._usage_cost`:
- **CEFE / live Opus** (model `claude-opus-4-8` @ $5/$25, cache_write 2×, cache_read 0.1×, live):
  in 26,262 / out 25,747 / cache_write 44,760 / cache_read 11,190 → **$1.2282**. This is the amount
  measured against the **$1 CEFE cost cap** → **~23% over**.
- OpenRouter / 5 qwen sittings (collection): **$0.0070**.
- **Probe total spend = $1.2352** (both keys), used in the all-in table below.

The CEFE overage was recorded honestly rather than papered over (repo scar: *sum usage from data for
exact spend; never trust a report figure*), flagged to the architect, and **RATIFIED
2026-09-05T07:08:25Z** — no rework. Separate dir `../../tmp/judging-runs/probe-cefe-opus`, never
merged into the run root.

## Layout correction (load-bearing for Phase 5 export)
`collect`/`judge` write **flat** to `--results-dir`: `<results-dir>/{sittings,judgments,judgments_v2}.jsonl`
+ `report.{md,json}`. The export reads `<root>/<tradition>/judgments.jsonl`, so the FULL run's
`--results-dir` must be `../../tmp/judging-runs/<date>-protestant-unified/protestant-unified` (the
per-tradition subdir), making the export root `../../tmp/judging-runs/<date>-protestant-unified`.

## Key sourcing (verified working)
Export from taqwabench/.env: OPENROUTER_API_KEY (subjects+Gemini); ANTHROPIC_API_KEY := the CEFE
value (ANTHROPIC_JUDGE_API_KEY) for Opus batch. `unset GEMINI_API_KEY` (never the personal key) and
`unset ANTHROPIC_JUDGE_API_KEY` after mapping. Code reads os.environ directly (no auto-dotenv).

## Smoke roster-normalization — PASS (pre-spend gate)
Smoke `--scenarios 1` = 90 subject cells, all **5 subjects present** (18 each): gpt-5.6-terra,
claude-sonnet-5, gemini-3.6-flash, qwen3-235b, inkling. All 5 map in `export_results._SUBJECT_VARIANTS`;
both judges (gemini-3.6-flash, claude-opus-4-8) map in `_JUDGE_VARIANTS`. So the Phase 5 export's
`assert_uniform_subject_roster` / normalize gates pass — no unmapped id will surface after the spend.
Gemini live judge: 90→180 judgments, 0 failed. Opus batch: 180 cells SUBMITTED via CEFE (batch
msgbatch_01TH21…, no auth error) → poll-collecting (async).

## SMOKE COMPLETE (2026-09-04) — actuals + batch-Opus confirmation
Batch closed ~12 min (180 Opus verdicts, 0 errored, all `batch:True` → batch-priced). Final report:
360 judgments (Gemini 180 + Opus 180), 5 subjects, **uncovered 0**. Roster-normalization PASS.

| stage | key | tokens in/out | $ (usage-computed, prices 2026-08-03) |
|---|---|---|---|
| smoke subjects (5) | OPENROUTER | — | 1.89 |
| smoke Gemini judge | OPENROUTER | 951k/181k | 2.63 |
| smoke Opus judge (BATCH) | CEFE | 1.39M/267k | 4.57 |
| **smoke total** | | | **9.10** |

**Full-run estimate (×36 scenarios):** OpenRouter ~$163 + Opus batch ~$165 = **~$328** (ceiling $600;
alert $450; pause $550). Reconciles with plan ~$360. Rates dated 2026-08-03 (#89-verified); token
usage is measured ground truth. **STOP — awaiting architect GO for the full run.**

## FULL RUN — GO
**GO: Waleed (explicit), 2026-09-04 ~06:00 UTC, relayed by architect.** On smoke actuals ($9.10 smoke,
~$328 projected). Full 36-scenario battery, both judges, Opus BATCH via CEFE `--no-fallback`.
Tripwires: alert $450, pause $550, HARD STOP $600. Any live top-up needs explicit architect OK first.
Run root: `../../tmp/judging-runs/20260904-protestant-unified/protestant-unified` (export root =
`20260904-protestant-unified`). Report at: collection complete / Gemini complete / Opus collected,
each with usage-computed actuals.

### Full-run spend log (usage-computed, prices 2026-08-03)
- STAGE A collection: 3,240 sittings, 0 failed. **$62.46** OpenRouter. Running total **$62.46**.
  (per subject: sonnet-5 $21.13, gemini-flash $21.65, gpt-5.6-terra $6.52, qwen $0.75, inkling $12.41)
- STAGE B Gemini judge: 6,480 judgments, 0 failed. **$97.79** OpenRouter. Running total **$160.25**.
- STAGE C Opus batch (CEFE): submit 6,480 + poll-collect --no-fallback. [running]

### RUN COMPLETE (2026-09-05 ~06:40 UTC)
- Opus batch (msgbatch_01Cdh4…) ended: 6480 succeeded, 0 errored. Collect landed 6,479; **1 verdict
  unparseable** → re-submitted as batch (submit 1 → collect 1), NO live top-up. Opus now 6,480.
- Coverage: **12,960 judgments, uncovered 0**. Per-judge 6,480/6,480; per-framing 2160 each (PASS).
- **RUN actuals (usage-computed, prices 2026-08-03):** OpenRouter $160.25 + Opus batch $168.03 =
  **$328.28** (run only). See "ALL-IN COST RECONCILIATION" below for the all-in figure of record
  ($338.62, incl. smoke + probe).
- Run root: `../../tmp/judging-runs/20260904-protestant-unified/protestant-unified` (gitignored).
- Phase 4 DONE. Next: rebase on main (#121 two-judge-mean) → Phase 5 export.

## ALL-IN COST RECONCILIATION (Phase 4 total)
**Figure of record — all-in Phase 4 spend = $338.62** (usage-computed **billed actual**, prices
2026-08-03 table in `judging/report.py`, #89-verified). Reconciliation:

| component | billed actual (usage-computed) |
|---|---|
| full run (36 scenarios) | $328.28 |
| batch smoke (1 scenario) | $9.10 |
| CEFE probe (10 Opus $1.2282 + 5 qwen collection $0.0070) | $1.24 |
| **all-in total** | **$338.62** |

$328.28 run + $9.10 smoke + $1.24 probe = **$338.62** — well under the $600 ceiling and below the $450
alert. Every *judgment* (both judges) was batch/normally priced; the only live spend was the $1.24
CEFE probe (its $1.23 CEFE component was over the $1 cap — ratified, see Gate log). No live top-ups
occurred during the run. The token usage is measured ground truth; the per-token rates carry the
2026-08-03 date. Console invoices (Anthropic + OpenRouter) remain authoritative and should be
reconciled against this figure by whoever holds console access.

> **What-if footnote (not the figure of record):** OpenRouter standard rates for the 2 promo-priced
> subjects (sonnet-5 ×1.5, terra ×2.0; both promos expired 2026-08-31, before the run), for invoice
> reconciliation only — if the invoice billed those two at standard rather than the promo rates in
> `report.py`, the all-in would be **$356.21**. Hypothetical; not counted anywhere above.

## PHASE 6 — cross-faith analysis (2026-09-05)
Paper numbers for the 8th cross-faith row. Full narrative + tables in
`docs/analysis/protestant-unified-round.md`; machine numbers in `data/output/paper_numbers.json`;
figures in `data/output/figures/` (scorecard, framing, steadfastness, distribution — canonical
`emit_figures`, 95% CIs). Generator `analyze.py` reuses the canonical aggregator and hard-fails
unless its per-tradition means reconcile with the committed `results/20260905/` combined block to
≤1e-9 (both reconciliation assertions PASS). Guard: `test_phase6_reconcile_119.py`.

- **Leaderboard (combined two-judge mean-of-means):** buddhism +0.6695, secular-sage +0.6349,
  taoism +0.6308, eastern-christianity +0.5405, **protestant-unified +0.4863 (5th)**, judaism +0.4656,
  roman-catholicism +0.3635, sunni-islam +0.3597.
- **Framing staircase (protestant-unified):** unstated +0.0539 → stated +0.5808 → guided +0.8241
  (lift +0.77). Under unstated (hardest), protestant-unified sits near neutral in the normative
  cluster (RC −0.016, sunni −0.052, EC +0.089), far below buddhism/secular/taoism (+0.38…+0.49).
- **Opus-vs-Gemini agreement (protestant-unified, n=6480):** r=0.810, bias +0.045, within-±0.5 92.1%,
  exact 67.7% — in line with the record grid (full-grid r=0.833).
- Difficulty bar holds: under unstated only gpt-5.6-terra/sonnet-5 have CIs strictly above 0; Qwen
  strictly below. Not ceilinged.

### Phase 6 consult iter1 refinements (per-tradition CIs + reproducibility)
- **Per-tradition 95% CIs** added to the 8-row table (scenario-cluster bootstrap, reusing the
  canonical `analysis.paper_bundle` method — same seed 12345 / 5000 boots / percentile). analyze.py
  hard-asserts each tradition's bootstrap central estimate == the canonical mean-of-means ≤1e-9.
  protestant-unified +0.4863 [+0.368, +0.590] — CI overlaps judaism (6th) and eastern-christianity
  (4th); the claim is "lower normative band", not a sharp 5th.
- **`combined_stats.json` is now written by analyze.py** (via canonical `build_combined_stats`), so
  the whole `data/output/` tree is reproducible from the one script (was previously the standalone
  `analysis combined-stats` CLI — provenance closed).
- **Portability:** analyze.py gained `--root`/`--results-dir` Typer options (default to the 5 roots +
  results/20260905) so it reproduces from the main checkout post-merge.
- **Monolith sanity-check:** the retired 7-strand protestantism monolith
  (`results/20260813-protestantism`) scores combined mean-of-means **+0.0286** — far below
  protestant-unified (+0.486). Directional only (different scenario set + construct; the common
  witness restricts to the same-advice questions).
- **Staleness guard:** `test_phase6_reconcile_119.py` now also asserts the committed
  `paper_numbers.json` ranked table matches the shard recompute ≤1e-9. Suite 275 passed.
- New figure `tradition_ranking.{pdf,png}` (8 traditions, mean + 95% CI).
