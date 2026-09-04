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
