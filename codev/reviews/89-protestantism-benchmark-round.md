# Review 89 — ProtestantBench benchmark round

## Outcome

Published `20260813-protestantism` — score tier (`results/`) + raw tier (`results-raw/`), same
fingerprint, `20260803` untouched. **Both judges are complete full grids: Gemini (ranking) and Opus
(badge-only validation) each 18000/18000 = 100 %.**

This shipped in two passes: first a **partial** dataset (Gemini 100 %, Opus 46 % — a contiguous
scenario block from a batch-boundary credit failure; see Deviations) merged via PR #93, then the
**Opus backfill** completing the grid to 100 %. The partial-coverage narrative below is retained as
the record of what happened; the final published dataset is full-grid.

## Verification evidence

- Tradition validator-clean (100 scenarios, `judge-guidance.md` per scenario).
- Collection 9000/9000 sittings, 0 failed. Gemini judging 18000/18000, 0 failed.
- **Final coverage (after backfill): unique Opus cells 18000/18000 = 100 %, Gemini 18000/18000 =
  100 %.** The re-exported manifest `counts.coverage` reports 3000/3000 for both judges in every
  framing. (Interim partial: Opus 8280/18000 = 46 % as a contiguous scenario block — see Deviations.)
- Both re-exported manifests stamp the **same** `fingerprint` (`sha256:33e62ad6…ced12`; the earlier
  partial export was `sha256:a0989a65…e3ed`).
- Score tier ~25 KB (well under the 8 MB/run, 1 MB/shard ceilings); raw tier 100 gz shards, ~31 MB.
- `uv --project workflows/analysis run pytest workflows/analysis` → 233 passed, 6 skipped
  (incl. the Gemini-slug normalization test; the Opus OpenRouter-slug alias + its test already
  existed).

## Spend — per key (final, actual billed)

| Key | Billed for | USD |
|---|---|---|
| OpenRouter (`OPENROUTER_API_KEY`) | 5 subjects + Gemini judge | $474.54 |
| OpenRouter | Opus backfill (live, all 10937 calls incl. 975 re-judge) + $3.34 smoke | $641.21 |
| Anthropic plain (`ANTHROPIC_API_KEY`, sk-ant-…F…) | Opus first pass (harvested, batch-priced) + probe | $277.74 |
| Anthropic judge (`ANTHROPIC_JUDGE_API_KEY`, sk-ant-…u…, CEFE) | blocked (org cap) — probes only | ~$0 |
| **Total actual spend** | | **≈ $1393** |

Budget history: the original run held under the **$1150 ceiling** at $752.27 (partial, $900 alert
never crossed). The Opus backfill was separately authorized at ~2× batch cost with an **$800 backfill
budget** — actual backfill spend **$637.87** (all live calls), well under; per-cell $0.051–0.054.
The canonical `report.json` total reads **$1305.85** because it dedups the re-judge overlay to
final-verdict cost (Opus backfill $553.58 there vs $637.87 actually billed — the ~$84 gap is the 975
superseded re-judge calls, real spend not reflected in final-verdict cost).

## Deviations from the original design

The design intent (architect go) was **Opus full grid, batched** (~$1030). What actually happened:

1. Opus batches were first submitted under the **plain** `ANTHROPIC_API_KEY`, which **ran out of
   Anthropic credit** mid-run — 8304/18000 cells succeeded (billed) before the balance depleted; the
   rest errored `credit balance is too low`.
2. Waleed corrected the key: Opus must bill to `ANTHROPIC_JUDGE_API_KEY` (the CEFE key). We ran a
   **credit probe** first (per the architect's guard) — it returned **429 org monthly-usage-cap**,
   "regain access 2026-09-01". A small **test batch** on the same key also 429'd — so **both live and
   batch are blocked on the judge key until Sept 1**.
3. Under Waleed's decision, we executed **Path B / D**: **harvest** the 8304 already-computed valid
   FPL verdicts (24 were unparseable → 8280 usable), read-only and zero-cost, and **ship the partial
   dataset now** with a backfill plan. This kept us under the ceiling (harvesting recovered the
   otherwise-wasted $277.74 of Opus compute as usable validation coverage).
4. **The harvested Opus coverage is a contiguous scenario block, not a sample.** The two batches
   split the grid by scenario order; the credit ran out during the batch covering PRO-001…050, so
   those errored while PRO-057…100 mostly succeeded. Coverage is therefore ~full for the upper half
   of scenarios and empty for the lower half. This was initially **mischaracterized** as "evenly
   spread 46 %" in the PR/README/docs because only the framing axis was checked (it *is* even on that
   axis); the integration reviewer caught the scenario-axis hole. Docs corrected here and in the
   README/PR.

## Backfill (COMPLETED — live via OpenRouter)

Rather than wait for the Sept-1 CEFE-key unblock, Waleed authorized finishing the 9720 pending Opus
cells **live via OpenRouter** (`anthropic/claude-opus-4.8`, which routes to `provider: Anthropic` —
verified by probe as the same Opus 4.8), accepting the ~2× live-vs-batch cost. Do not touch the FPL
or CEFE keys (OpenRouter-only wrapper, Anthropic keys explicitly unset).

Mechanics that made it precise + cheap:
- Fed a **pending-*sitting* subset** (4981 sittings), not whole scenarios: the live `judge` scores
  whole sittings and resumability keys on the raw judge id, so whole-scenario judging would re-judge
  4140 already-done cells (~$928, over budget). The sitting subset judged 9962 cells (9720 pending +
  242 unavoidable redundant, deduped at export by later-ts).
- Smoke-gated (~50 cells, $0.0668/cell ≤ $0.075 gate; projected $665 < $800).
- Full backfill: 9962 base cells + a standard disagreement **re-judge pass** (975 v2 overrides on
  Opus↔Gemini ≥2-level disagreements). One cell failed on a JSON truncation and was retried → **Opus
  18000/18000**. Actual spend **$637.87**.
- Re-exported the **same run-id in place** (`analysis export` + `export-raw`); the export already
  aliased `anthropic/claude-opus-4.8` → `claude-opus-4-8`, unifying the batch + live key-paths into
  one full-grid Opus judge. New fingerprint; partial export superseded.

Raw run data under `tmp/judging-runs/89-full/` (gitignored) must be **archived before any cleanup**,
never deleted.

## Lessons

- **Probe a funded key before batch scale.** One tiny live call caught both the FPL credit
  exhaustion (in hindsight) and the judge-key org cap — cheaply, before a 18000-cell batch failed.
- **Retrieving batch results needs no credit.** A depleted key can't *create* work but can still
  *read* completed results — so partial-success batches are harvestable, turning "waste" into
  coverage.
- **The Gemini judge via OpenRouter records a provider-prefixed slug** (`google/gemini-3.6-flash`)
  the export didn't map — the record's full-grid Gemini run used the canonical id. Any
  OpenRouter-slug judge run needs the alias (now added, like the Opus slug and every subject).
- **Split live-Gemini from batched-Opus** to parallelize, but gate `batch-judge collect` on the live
  judge finishing — both write `judgments.jsonl`.
- **`report.json` cost ≠ actual spend when a re-judge pass runs.** `report.json` dedups the v2
  overlay to *final-verdict* cost, so the superseded re-judge calls (real money) don't show. Track
  actual billed spend from all rows (base + v2) against a budget/ceiling, and reconcile the two.
- **Two key-paths, one judge at export.** Completing a judge across two providers (Anthropic batch +
  OpenRouter live) is fine because the export normalizes the id aliases and dedups the overlap by
  timestamp — verify the model is the *same underlying version* (OpenRouter `provider: Anthropic`
  confirmed it) before mixing paths.
- **Check coverage on EVERY axis, not one.** A partial run's coverage looked uniform on the framing
  axis and I reported it as an even sample; the real gap was a contiguous *scenario* block (a
  batch-order artifact). When a batch fails partway, the survivors cluster by whatever the batch was
  ordered on — verify per-scenario (and per-subject/pressure) coverage, and prefer a coverage view
  that surfaces contiguous holes, before calling a partial run "a representative sample."

## Flaky tests

None encountered.
