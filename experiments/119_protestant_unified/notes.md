# Experiment 119 — protestant-unified scoring round

House-convention run notes for the Spec 119 scoring run (Phase 4). Spend ceiling **$600 hard**
(alert $450, pause $550). Dual judge: Gemini (rankable, full grid) + Opus 4.8 (badge validation).

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

## Spend table (per-key, from usage data — TO FILL after smoke)
| stage | key | cells | $ (usage-computed) |
|---|---|---|---|
| smoke subjects+Gemini | OPENROUTER | | |
| smoke Opus (batch) | CEFE | | |

## Gate log
- (pending) smoke actuals + rate verification + roster-normalization result + batch-Opus confirmation → architect.
- (pending) architect GO for full run.

## CEFE-key probe — PASSED (2026-09-04, <$1)
Live Opus judged 5 sittings → 10 valid judgments (judge id `claude-opus-4-8`, real scores, 0 failed),
**no org-cap block** — the #89 CEFE scar is resolved; the key path works. Separate dir
`../../tmp/judging-runs/probe-cefe-opus`, never merged.

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
- **FINAL ACTUALS (usage-computed):** OpenRouter $160.25 + Opus batch $168.03 = **$328.28** total.
  (ceiling $600; alert $450, pause $550 — not tripped.) On the ~$328 estimate.
- Run root: `../../tmp/judging-runs/20260904-protestant-unified/protestant-unified` (gitignored).
- Phase 4 DONE. Next: rebase on main (#121 two-judge-mean) → Phase 5 export.
