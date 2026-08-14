# Plan 89 — ProtestantBench benchmark round (as-built)

## Approach

Drive the existing `workflows/judging` + `workflows/analysis` tooling; add no new pipeline. The
only code change is a one-line normalization fix (below) surfaced by running the Gemini judge
through OpenRouter.

## Config (derived from the real 20260803 record)

- Subjects (5, OpenRouter slugs, `OPENROUTER_API_KEY`): `openai/gpt-5.6-terra`,
  `anthropic/claude-sonnet-5`, `google/gemini-3.6-flash`, `qwen/qwen3-235b-a22b-2507`,
  `thinkingmachines/inkling`.
- Judges: Gemini `google/gemini-3.6-flash` via OpenRouter (ranking, full grid, safety-on per the
  record decision) + Opus `claude-opus-4-8` direct Anthropic (validation, `full_grid:false`,
  `max_tokens` 8000).
- Framings unstated/stated/guided; six pressures; scopes turn1/full; concurrency 8; retries 2.
- Configs committed: `workflows/judging/configs/protestantism-run.yaml` (full) +
  `protestantism-gemini.yaml` (gemini-only, for the live judge run parallel to the Opus batch).

## Phases (as executed)

1. **Smoke** — `run --scenarios 2` (both judges, end-to-end); reconcile usage-computed cost;
   project full-100; propose integration shape; architect gate.
2. **Collect** — full grid → 9000 sittings (resumable). Reconcile collection cost.
3. **Judge** — split: Gemini live (full grid) via the gemini-only config, in parallel with Opus
   submitted as Anthropic Message Batches (~50 % via `batch-judge submit`). Then `batch-judge
   collect` after the Gemini live judge finishes (concurrent-writer safety on `judgments.jsonl`).
4. **Report** — `report` → `report.json` (usage-computed, fully-priced) for the judge-end reconcile.
5. **Export** — `analysis export` (score tier) + `export-raw` (raw tier) from a per-tradition run
   root, `--run-id 20260813-protestantism`. Verify equal source fingerprint across tiers.

## Files touched

- `results/20260813-protestantism/` (score tier) + `results-raw/20260813-protestantism/` (raw tier).
- `workflows/analysis/analysis/export_results.py` — map the Gemini OpenRouter slug
  `google/gemini-3.6-flash` → canonical `gemini-3.6-flash` in `_JUDGE_VARIANTS` (the record's
  full-grid Gemini run used the canonical id, so the slug was previously unmapped; the Opus slug and
  all subject slugs were already mapped). +1 test.
- `workflows/judging/configs/protestantism-run.yaml`, `protestantism-gemini.yaml`.
- `results/README.md` — published-runs note (partial Opus + backfill).

## Test strategy

`.codev/checks/test.sh` dispatcher → `uv --project workflows/analysis run pytest workflows/analysis`
(the touched app). New test asserts the Gemini-slug normalization. The paper-reconciliation test
(on 20260803) is unaffected — the change only adds an alias for a run that uses the slug.
