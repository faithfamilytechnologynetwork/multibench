# Review 89 — ProtestantBench benchmark round

## Outcome

Published `20260813-protestantism` — score tier (`results/`) + raw tier (`results-raw/`), same
fingerprint, `20260803` untouched. **Gemini (ranking judge): full grid, 18000/18000 = 100 %.**
**Opus (badge-only validation): 8280/18000 ≈ 46 %, but as a CONTIGUOUS SCENARIO BLOCK, not a
sample** — PRO-001…050 have **zero** Opus verdicts, PRO-051…056 ramp up partially, PRO-057…100 are
~full (a batch-boundary artifact; see Deviations). The 9720 remaining Opus cells (almost all of
PRO-001…056) are staged/resumable for backfill (see below).

## Verification evidence

- Tradition validator-clean (100 scenarios, `judge-guidance.md` per scenario).
- Collection 9000/9000 sittings, 0 failed. Gemini judging 18000/18000, 0 failed.
- Canonical `report.json` (usage-computed, `fully_priced: true`): **total $752.27** —
  collection $226.02 · Gemini judge $248.52 · Opus judge $277.74.
- Both exported manifests stamp the **same** `fingerprint` (`sha256:a0989a65…e3ed`). NOTE:
  `counts.coverage` reports coverage only per *framing* (Gemini 3000/3000, Opus ~1375-1381) — which
  is even on the framing axis and so **masks the per-scenario hole** (PRO-001…050 = 0 Opus). Scenario
  coverage from `judgments.jsonl`: Opus zero for PRO-001…050, partial for PRO-051…056 (16/40/66/68/
  81/127 of 180), ~full (179-180) for PRO-057…100. Gemini full for all.
- Score tier 26 KB (well under the 8 MB/run, 1 MB/shard ceilings); raw tier 100 gz shards, 30 MB.
- `uv --project workflows/analysis run pytest workflows/analysis` → 233 passed, 6 skipped
  (incl. the new Gemini-slug normalization test).

## Spend — per key

| Key | Billed for | USD |
|---|---|---|
| OpenRouter (`OPENROUTER_API_KEY`) | 5 subjects + Gemini judge | $474.54 |
| Anthropic plain (`ANTHROPIC_API_KEY`, sk-ant-…F…) | Opus (harvested, batch-priced) + probe | $277.74 |
| Anthropic judge (`ANTHROPIC_JUDGE_API_KEY`, sk-ant-…u…, CEFE) | blocked (org cap) — probes only | ~$0 |
| **Total** | | **$752.27** |

Under the $1150 ceiling; the $900 alert line was never crossed.

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

## Backfill plan (deferred completion)

The 9720 pending Opus cells (9696 FPL-errored + 24 unparseable) complete on the CEFE judge key once
its org monthly cap lifts (**2026-09-01**), or sooner if that org's Anthropic API tier is raised.
Everything is staged and resumable: re-run `batch-judge submit`/`collect` for the pending Opus cells
under the judge key, then re-export in place (same `--run-id`, byte-stable shards, new fingerprint).
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
- **Check coverage on EVERY axis, not one.** A partial run's coverage looked uniform on the framing
  axis and I reported it as an even sample; the real gap was a contiguous *scenario* block (a
  batch-order artifact). When a batch fails partway, the survivors cluster by whatever the batch was
  ordered on — verify per-scenario (and per-subject/pressure) coverage, and prefer a coverage view
  that surfaces contiguous holes, before calling a partial run "a representative sample."

## Flaky tests

None encountered.
