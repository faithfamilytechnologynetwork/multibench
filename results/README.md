# `results/` — committed, browsable judging-run datasets

Each `results/<run-id>/` is a compact, **scores-and-metadata-only** export of a judging run that
the **multibrowser** SPA reads at runtime (the same way it reads `traditions/`): SHA-pinned
git-trees + `raw` fetches, no backend, no baked data. Drop a new `results/<run-id>/` in and it
appears in the browser's **Results** explorer with **no code change** (Spec 49).

The per-scenario **transcripts + judge verdicts** live in the sibling [`results-raw/`](../results-raw/README.md)
tier (Spec 51); both tiers stamp the **same `fingerprint`** for a given `<run-id>` so they can
never disagree.

There are **no transcripts here** — raw run data is hundreds of MB; this export is single-digit MB
(the launch run is ~180 KB). It carries pre-aggregated per-tradition slice tables plus a manifest.

## Layout

```
results/<run-id>/
  manifest.json        # run metadata + vocab + counts/coverage
  <tradition>.json     # one shard per tradition (pre-aggregated slice tables)
```

## Producing / refreshing a dataset

The exporter lives in `workflows/analysis` and reuses the canonical aggregation
(`analysis/aggregate.py`), so the numbers reconcile with the paper by construction. Run from the
repo root against the judging run roots (the full-grid **Gemini** run — which carries `report.json`
— plus any report-less **Opus** judge layers):

```bash
uv --project workflows/analysis run python -m analysis export \
  tmp/judging-runs/20260803-merged \
  tmp/judging-runs/20260803-unstated-opus \
  tmp/judging-runs/20260803-framings-opus-sample \
  --run-id 20260803 --out results
```

Commit **only** the `results/<run-id>/` output (never from the gitignored `tmp/judging-runs/`).
Re-running with the same inputs is deterministic (sorted keys) — the shards are **byte-stable** and
the manifest differs only in its `generated_at` timestamp — so refreshing a run after more
judgments land is just the same command again, then a new commit.

**Which run the SPA shows.** The Results explorer defaults to the **newest** run by `generated_at`.
When more than one run is published it shows a **run selector**; you can also pin a specific run with
`?run=<run-id>` in the URL. So committing a new `results/<run-id>/` with a later timestamp makes it the
default automatically; older runs remain reachable via the selector or their id.

## `manifest.json`

| field | meaning |
|---|---|
| `schema_version` | dataset schema version (currently **1**); the SPA rejects other versions with a notice |
| `run_id`, `generated_at` | run id + ISO-8601 export timestamp |
| `subjects` | the (normalized) subject model ids, canonical spelling |
| `judges` | `[{key, model, aliases[], full_grid}]` — `key` is the UI short name (`gemini`/`opus`), `model` the canonical id, `full_grid` = judged every framing |
| `framings` | `["unstated","stated","guided"]` (universal core) |
| `pressures`, `pressure_all` | the six pressures + the `"all"` (pooled) sentinel |
| `scopes` | `["turn1","full"]` (first-response / post-pressure) |
| `metrics` | `["turn1","full","steadfastness"]` (the UI's leaderboard metrics) |
| `traditions` | `[{id, n_scenarios, shard}]` — `n_scenarios` is the judge-independent full grid; `shard` is the filename (source of truth) |
| `counts.judgments` | per-judge total judgment count (post-normalization/dedup) |
| `counts.coverage` | `{judge: {framing: {n_judged, n_expected}}}` roll-up (headline honesty signal) |

## `<tradition>.json` (shard)

```jsonc
{
  "tradition": "buddhism",
  "n_scenarios": 52,
  "judges": ["claude-opus-4-8", "gemini-3.6-flash"],   // sorted
  "means": {           // judge → subject → framing → scope → pressure(+"all") → [mean, n_judged, n_expected]
    "gemini-3.6-flash": { "claude-sonnet-5": { "unstated": { "full": { "all": [0.81, 312, 312] } } } }
  },
  "steadfastness": {   // judge → subject → framing → pressure(+"all") → [value, matched_n]
    "gemini-3.6-flash": { "claude-sonnet-5": { "unstated": { "all": [-0.06, 312] } } }
  }
}
```

- **Cells are arrays**: `means` cells are `[mean, n_judged, n_expected]`; `steadfastness` cells are
  `[value, matched_n]`. Numeric only — **no band names**. A `means` **`mean` is on −1…+1**; a
  `steadfastness` **`value` is on −2…+2** (a full − turn1 difference), and can be negative.
- **Zero-coverage slices are simply absent** (the SPA derives `n_expected` from `n_scenarios` and
  shows nothing rather than a 0).

## Semantics (how the numbers are built)

- **Cell** = `(subject, scenario_id, pressure, framing, scope)`; cell score = mean of present
  judges' scores. A breakdown **mean** = unweighted mean of the in-scope cells (uncovered excluded,
  never 0). Per-judge tables filter to one judge, so this is just that judge's cell mean.
- **`pressure="all"`** is the **cell-pooled** mean (all pressures pooled within the tradition before
  the mean), matching the paper — not a mean of per-pressure means.
- **`steadfastness`** = matched-cell `mean(full) − mean(turn1)` over cells present in **both** scopes.
- **Coverage**: `n_expected` = `n_scenarios × 6` for `pressure="all"`, else `n_scenarios`. The
  denominator is the **Gemini full grid** — so a small Opus sample reads as low coverage, honestly.

## Normalization (done by the exporter)

Source runs spell ids inconsistently; the export normalizes to a single canonical vocabulary:

- **Subjects** — an explicit alias map (e.g. `qwen/qwen3-235b-a22b-2507` →
  `Qwen/Qwen3-235B-A22B-Instruct-2507`; provider-prefixed/lowercased variants → canonical). An
  unmapped id fails the export loudly.
- **Judges** — the two Opus aliases (`claude-opus-4-8`, `anthropic/claude-opus-4.8`) collapse to one
  judge. Identity collisions across aliases are deduped (later `ts` wins); `judgments_v2.jsonl`
  overrides its base row (file-order last-wins).

## The Results explorer (SPA)

The `/results` leaderboard is a **dense, whole-picture-at-a-glance table** (jaleesbrowser-style,
Spec 55) — one row per subject:

- The **leaderboard ranks on Gemini only** (the full-grid judge) — the mean of per-tradition means.
- **Framing and metric are columns, not selectors.** Each row shows **First-response / Post-pressure /
  Δ (steadfastness)** on the paper's published slice (the first framing), plus one post-pressure column
  per framing (the staircase). Δ is the shard's matched-cell steadfastness, not post − initial.
- A **per-tradition heat strip** in each row (a `scoreColor` square per tradition) shows the spread
  behind the Post-pressure mean; every square is accessibly labelled with its value (or "no data").
- Any numeric column is **sortable**; a **canonical rank** column persists while sorted.
- A single **pressure** selector reframes the whole table (headline, framing columns, strip, rank) to
  one of the six pressures or `"all"`. The **judge selector** switches the **per-tradition drill-down**
  to Opus **where Opus data exists** (badged `sample n/N`); it never re-ranks or recolors the board.
- **Run, pressure, judge, column sort, and expanded subjects are all deep-linkable** in the URL.
- Numbers reconcile with the paper's standings (`tab_standings` / `subj_overall`) to displayed
  precision.

## Published runs

- **`20260803`** — the benchmark-of-record (7 traditions / 519 scenarios), the paper's snapshot.
  Guarded by the paper-reconciliation test; **never mutate it**.
- **`20260813-protestantism`** — the ProtestantBench round (issue #89): the `protestantism`
  tradition (100 scenarios) over the same 5-subject roster, framings, and pressures as the record
  run. **Gemini (ranking judge) is a complete full grid (18000/18000 = 100 %).** **Opus (the
  badge-only validation layer) is only 8280/18000 ≈ 46 %, and — importantly — that coverage is a
  CONTIGUOUS SCENARIO BLOCK, not a representative sample:**
  - **PRO-001…050 have ZERO Opus verdicts** (the lower half of the tradition);
  - **PRO-051…056** ramp up partially (16 → 127 of 180 cells);
  - **PRO-057…100 are ~fully Opus-judged** (179-180/180).

  This is a **batch-boundary artifact**: the Opus judging was submitted as two Anthropic Message
  Batches, and the funding key's credit ran out partway through the batch covering the earlier
  scenarios, so those cells errored. The aggregate "46 %" and the even *per-framing* split both
  **mask this per-scenario hole** — a user browsing PRO-001…050 sees no Opus data at all. Opus
  **never re-ranks** (the leaderboard is Gemini-only), so this is a validation-badge gap, not a
  ranking gap — but it is a real gap in the lower half and must not be read as a uniform sample.
  The manifest's `counts.coverage` currently reports coverage only per *framing* (which hides the
  scenario axis); a per-scenario coverage field is a recommended follow-up for a truthful SPA badge.
  **Backfill plan:** the 9720 pending Opus cells (almost all of PRO-001…056) are staged and
  resumable; they complete on the judge key once its org monthly cap lifts (2026-09-01), after which
  this run is re-exported in place (same `--run-id`, byte-stable shards, new fingerprint).

## Size ceilings

Enforced by the exporter (and by tests): **≤ 8 MB total per run**, **≤ 1 MB per tradition shard**.
