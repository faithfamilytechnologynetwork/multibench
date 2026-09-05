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
all-in reconciliation (smoke + probe + run, two rate sets) is under "ALL-IN COST RECONCILIATION".

## Gate log
- ✅ smoke actuals + rate note + roster-normalization PASS + batch-Opus confirmation → architect (2026-09-04).
- ✅ architect GO for full run (Waleed via architect, 2026-09-04 ~06:00 UTC — see "FULL RUN — GO").
- ⚠️ live CEFE probe (≤10 cells, $1 cap, separate dir) — **architect pre-authorized** before the batch
  smoke: *"YES, approved as a key-path probe only: at most 10 cells live on the CEFE key, cost cap 1
  USD, written to a separate probe dir, never merged into the run root."* Actual: 10 cells,
  **$1.23 live Opus** — cell count within the cap but **cost $0.23 (~23%) OVER the $1 cost cap**.
  Immaterial to the $450/$550/$600 tripwires, but it exceeded an architect-set cap → **flagged to the
  architect for ratification** (their cap, their call). See the corrected probe section below.
- No live top-ups were taken during the run (the 1 unparseable Opus cell was re-submitted as **batch**).

## CEFE-key probe — key path PASSED, but cost cap BREACHED (2026-09-04)
Live Opus judged 5 sittings → 10 valid judgments (judge id `claude-opus-4-8`, real scores, 0 failed),
**no org-cap block** — the #89 CEFE scar is resolved; the key path works. **Architect pre-authorized**
as a key-path probe (≤10 cells, **$1 cost cap**; see Gate log).

**COST CORRECTION (iter2, from claude review).** An earlier note recorded the probe at **$0.007** —
that was wrong: $0.007 is the *collection-only* total from `probe-cefe-opus/report.json`, which was
written **before** the Opus judgments landed (`judgments: 0, uncovered: 10`). The **actual live Opus
spend**, recomputed canonically from the 10 judgments' own usage records via `judging/report.py`
(`_usage_cost`, model `claude-opus-4-8` @ $5/$25, cache_write 2×, cache_read 0.1×, live not batch):
in 26,262 / out 25,747 / cache_write 44,760 / cache_read 11,190 → **$1.2282**.

So the probe **exceeded the architect's $1 cost cap by ~23% ($0.23)**. The cell count (10) was within
the authorized envelope; the cost cap was not. This is a small absolute overage, immaterial to the
$450/$550/$600 gates, but it is a breach of an architect-set cap and is **flagged for architect
ratification** — recorded honestly rather than papered over (repo scar: *sum usage from data for
exact spend; never trust a report figure*). Separate dir `../../tmp/judging-runs/probe-cefe-opus`,
never merged into the run root.

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
  **$328.28** (run only). See "ALL-IN COST RECONCILIATION" below for the smoke + probe + rate-range total.
- Run root: `../../tmp/judging-runs/20260904-protestant-unified/protestant-unified` (gitignored).
- Phase 4 DONE. Next: rebase on main (#121 two-judge-mean) → Phase 5 export.

## ALL-IN COST RECONCILIATION (Phase 4 total)
The `report.json` cost uses the **2026-08-03** price table (#89-verified) — token usage is measured
ground truth; only the per-token rates carry a date. Two **subject** models were on promo rates that
**expired 2026-08-31 — *before* this run (2026-09-04/05).** So the account was **most likely billed
at standard rates**, making the standard-rate column below the *likely actual* and the 2026-08-03
`report.json` figure a floor. `claude-sonnet-5` promo $2/$10 → standard $3/$15; `openai/gpt-5.6-terra`
promo $1/$6 → standard $2/$12. Judges (gemini-flash, Opus batch) are unaffected. I do not hold
console-invoice access, so both columns are shown; the Anthropic + OpenRouter console invoices are
authoritative and should be reconciled against this by whoever holds console access.

**Standard-rate figures are recomputed canonically** — the subject usage (with its cache_read/
cache_write/batch split) was re-accumulated from each run's `sittings.jsonl` and re-priced through
`judging/report.py`'s own `_usage_cost` at the standard rates. This is exact where a hand delta is
not: both promos are clean multiples of the standard rate (sonnet ×1.5, terra ×2.0), and because the
cache-tier rates are multiples of the base input price, each model's *entire* billed cost — cache
reads included — scales by that same factor:
- sonnet-5 (run): billed $21.1308 → std $31.6962  (×1.5)  → Δ **+$10.5654**
- terra (run):    billed $6.5162 → std $13.0323  (×2.0, incl. 633,652 cache-read tokens)  → Δ **+$6.5162**
- run collection Δ = **+$17.0816**; smoke collection Δ = **+$0.5098**.

(An earlier iter1/iter2 note used a naive per-token delta of +$7.09 for terra — wrong, because it
ignored terra's cache-read discount; the canonical ×2.0 gives +$6.52. Both independent reviewers
reached $345.37 for the run.)

| component | billed rates (2026-08-03, floor) | standard rates (likely actual, post-promo) |
|---|---|---|
| full run (36 scenarios) | $328.28 | $345.37 |
| batch smoke (1 scenario) | $9.10 | $9.61 |
| live CEFE probe (10 cells) | $1.23 | $1.23 |
| **all-in total** | **$338.61** | **$356.20** |

**All-in Phase 4 spend = $338.61 – $356.20** (2026-08-03 floor → standard-rate likely actual), well
under the $600 ceiling and below the $450 alert. The ~$18 spread is entirely the two expired subject
promos on the run+smoke collection; every *judgment* (both judges) was batch/normally priced, and the
only live spend was the $1.23 CEFE probe (over its $1 cap — see Gate log). No live top-ups occurred
during the run itself. Console invoices remain authoritative and should be reconciled against this.
