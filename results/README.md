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
  tmp/judging-runs/20260823-opus-fullgrid \
  --run-id 20260803 --out results
```

The **full-grid Opus** stated+guided layer (`20260823-opus-fullgrid`, #110) is passed **last** so its
verdicts deterministically win any overlap with the earlier `framings-opus-sample` layer (the merge
uses a root-order source precedence; the sample now only back-fills cells the full-grid run failed).
With it, Opus earns `full_grid: true` from real coverage (≈0.9994), while **Gemini values stay
byte-identical** and `rankable` stays Gemini-only. From a **builder worktree** the gitignored source
roots are reachable at `../../tmp/judging-runs/…` (the paths above are repo-root-relative).

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
| `judges` | `[{key, model, aliases[], full_grid, rankable, coverage}]` — `key` is the UI short name (`gemini`/`opus`), `model` the canonical id. **`full_grid`** = the **earned coverage badge** (tolerant: every framing covered at full-grid scale, per-framing ≥ 0.95 — #96), computed per run, NOT a static flag. **`rankable`** = the **static ranking role**: the leaderboard ranks on the single rankable judge (Gemini); a validation judge that reaches full coverage earns `full_grid` but stays `rankable:false` and never ranks. **`coverage`** = the judge's actual pooled coverage **fraction over the full scope** (`scope=full`, ÷ 46,710 = 519 scenarios × 5 subjects × 6 pressures × 3 framings), for display/citation. (`rankable`/`coverage` are optional — pre-#110 manifests omit them and the SPA falls back to `full_grid` then Gemini.) |
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
  denominator is the report-declared full grid — so a designed sub-sample reads as low coverage,
  honestly, while a full-grid layer with a few persistent judge-side failures reads as ~1.0. Note
  the per-judge manifest `coverage` fraction is over the **full scope only** (÷ 46,710); it will
  differ slightly from `counts.judgments / (2 × 46,710)`, which pools both scopes.

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

- The **leaderboard ranks on Gemini only** (the `rankable` judge) — the mean of per-tradition means.
  Ranking is keyed off the static `rankable` flag, **not** `full_grid`: Opus is now also full-grid
  but is a badged validation layer and never re-ranks (#96).
- **Framing and metric are columns, not selectors.** Each row shows **First-response / Post-pressure /
  Δ (steadfastness)** on the paper's published slice (the first framing), plus one post-pressure column
  per framing (the staircase). Δ is the shard's matched-cell steadfastness, not post − initial.
- A **per-tradition heat strip** in each row (a `scoreColor` square per tradition) shows the spread
  behind the Post-pressure mean; every square is accessibly labelled with its value (or "no data").
- Any numeric column is **sortable**; a **canonical rank** column persists while sorted.
- A single **pressure** selector reframes the whole table (headline, framing columns, strip, rank) to
  one of the six pressures or `"all"`. The **judge selector** switches the **per-tradition drill-down**
  to Opus **where Opus data exists**, labelled `opus (validation)`; a validation judge that is only a
  sub-sample is badged `sample n/N`, while a full-grid validation judge shows its coverage % instead.
  The selector never re-ranks or recolors the board.
- **Run, pressure, judge, column sort, and expanded subjects are all deep-linkable** in the URL.
- Numbers reconcile with the paper's standings (`tab_standings` / `subj_overall`) to displayed
  precision.

## Published runs

- **`20260803`** — the benchmark-of-record (7 traditions / 519 scenarios), the paper's snapshot.
  The **Gemini (ranking) values never change** — guarded by the paper-reconciliation test, and
  byte-identical across re-exports. A **validation layer may be extended in place** (e.g. #110 grew
  the Opus layer to the full grid): re-run the export, which re-stamps the shared `fingerprint`
  across both tiers and bumps `generated_at`, and record a dated revision note here.
- **`20260813-protestantism`** — the ProtestantBench round (issue #89): the `protestantism`
  tradition (100 scenarios) over the same 5-subject roster, framings, and pressures as the record
  run. **Both judges are complete full grids: Gemini (ranking judge) 18000/18000 = 100 %, and Opus
  (the badge-only validation layer) 18000/18000 = 100 %.** Opus **never re-ranks** (the leaderboard
  is Gemini-only); it is a per-cell validation badge.

  *Provenance note (two-key Opus path):* the Opus grid was completed in two stages under one model
  (Claude Opus 4.8). The first ~46 % (8280 cells, PRO-057…100 plus a partial ramp) came from
  Anthropic Message Batches (judge id `claude-opus-4-8`); the remaining ~54 % (PRO-001…056 plus
  scattered stragglers) were backfilled **live via OpenRouter** (`anthropic/claude-opus-4.8`, which
  OpenRouter routes to `provider: Anthropic` — the same underlying model). The export normalizes the
  two ids to a single judge and dedups the small overlap by later timestamp, so the published tier
  is one uniform Opus 4.8 full grid. Earlier partial exports of this run-id are superseded.

## Size ceilings

Enforced by the exporter (and by tests): **≤ 8 MB total per run**, **≤ 1 MB per tradition shard**.
