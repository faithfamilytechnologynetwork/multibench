# `results-raw/` — committed, browsable **raw** judging-run datasets (transcripts + verdicts)

Each `results-raw/<run-id>/` is a per-scenario export of a judging run that the **multibrowser**
raw-results viewer reads at runtime — the raw counterpart to the scores-only [`results/`](../results/README.md)
tier (Spec 49). Where `results/` carries aggregate slice tables, `results-raw/` carries, for
every scenario, each **subject × framing × pressure** cell's **transcript** and its
per-(judge, scope) **judge verdicts** (score, direction summary, rationale). Spec 51.

Drop a new `results-raw/<run-id>/` in and it appears in the browser with **no code change**
(same drop-in principle as `traditions/` and `results/`).

## Layout

```
results-raw/<run-id>/
  manifest.json                    # generic catalog (see below); no transcripts
  <tradition>/<scenario>.json.gz   # one gzip shard per scenario (transcripts + verdicts)
```

- **519 shards** for the launch run (`20260803`), ~**126 MB gz** total (median 233 KB/shard,
  max ≈ 533 KB). Shard paths are **manifest-declared** — the viewer never lists them via the
  GitHub API.

### Size ceilings (enforced at export)

The exporter serializes and gzips everything, **validates all sizes before writing anything**
(so a violation never leaves a partial tier), and aborts loudly on breach:

- **per-shard ≤ 1 MB** (gz) — calibrated above the real p99 (measured max 545,560 bytes ≈ 533 KB),
- **per-run ≤ 200 MB** (gz) — above the ~126 MB launch total.

## Two public sources, identical content (dual-source, Spec 51 Decision 14)

The exact same slimmed content is served from two places:

1. **Committed GitHub tier** (this directory) — the **authoritative** copy and the **fallback**.
   Read at runtime over SHA-pinned `raw.githubusercontent.com`.
2. **Baked deploy bundle** — `railway up` bakes these **same gz shards** into the static site
   (same-origin `public/data-raw/`), the **primary** source when present (no rate limits, no
   API budget). Deploy is from the local machine, so the bundle is not constrained by what is
   committed.

The viewer resolves **baked-first, GitHub-fallback**, using the **source fingerprint** (below)
to decide coherence, and shows a notice when serving the fallback. Refreshing the **baked**
copy requires **re-export + `railway up --no-gitignore`** (Railway respects `.gitignore` by
default, so the bake dir must be force-uploaded); the **GitHub** copy updates live on commit.

## `manifest.json` (generic catalog)

The catalog shape is **catalog-generic** (issue #54) — a non-MultiBench catalog (e.g. the
AFB 0–4 explorer) uses the identical structure with different values. Nothing MultiBench-specific
(`tradition`/`scenario`/framing/pressure names, the −1…+1 ramp) is baked into the *shape*.

| field | meaning |
|---|---|
| `schema_version` | dataset schema version (currently **1**); the viewer rejects other versions with a notice. Stamped in the catalog **and every shard**. |
| `dataset` | `{title, description, language, license}` — `license` is **`CC-BY-4.0`** (SPDX). |
| `scale` | numeric score domain `{min, center, max}` (MultiBench: `-1 / 0 / +1`). No band names. |
| `ramp` | the diverging color-ramp stops (the `scoreColor` colormap), catalog-declared data. |
| `subjects` | `[{id, label}]` — catalog-declared (the run's subjects, not a leaderboard set). |
| `judges` | `[{key, label, fullGrid}]` — `key` is the UI short name (`gemini`/`opus`); `fullGrid=false` (Opus honest-sample) is badged by the viewer. |
| `conditionAxes` | `[{key, label, values:[{id,label}]}]` — MultiBench ships `framing` + `pressure`; the viewer iterates these generically. |
| `groupBy` | the item grouping axis (`{key:"tradition", label}`). |
| `scopes` | `[{id, label}]` — `turn1` (initial) / `full` (post-pressure). |
| `items` | `[{id, label, group, shard}]` — one per scenario; `shard` is the manifest-declared path. |
| `presets` | curated deep-link lists (below). |
| `fingerprint` | `sha256:<hex>` over the resolved-judgments stream — see below. |

There is **no `generated_at`/timestamp** anywhere in this tier — provenance is the fingerprint,
so re-exports are byte-identical.

## `<tradition>/<scenario>.json.gz` (shard)

```jsonc
{
  "schema_version": 1,
  "contexts": {                      // per-framing "what the model was told" text (deduped)
    "stated": "[Context …]", "guided": "[Context …]"   // unstated has none
  },
  "cells": [
    {
      "subject": "claude-sonnet-5",
      "conditions": {"framing": "stated", "pressure": "secularize"},
      "transcript": [{"role": "user", "content": "…"}, {"role": "assistant", "content": "…"}],
      "contextKey": "stated",        // stated/guided cells reference contexts[<contextKey>]
      "verdicts": [
        {"judge": "gemini", "scope": "turn1", "score": 1.0, "summary": "…", "rationale": "…"}
      ]
    },
    {
      "subject": "claude-sonnet-5",
      "conditions": {"framing": "unstated", "pressure": "secularize"},
      "transcript": [{"role": "user", "content": "…"}, {"role": "assistant", "content": "…"}],
      // no contextKey — unstated cells are context-free (not in the contexts pool)
      "verdicts": [
        {"judge": "opus", "scope": "full", "score": -0.5, "summary": "…"}
      ]
    }
  ]
}
```

- **Verdict** = `{judge, scope, score, summary, rationale?}`. `score` is a **number on −1…+1**
  (the `is_valid_score` five-point scale, no rescale); `summary` is the judge's direction and is
  **always present**; `rationale` is present when recorded. **Both judges** appear where present.
- Transcripts come **only** from the full-grid (report.json-bearing) run; other roots contribute
  verdicts only.

### Export field allowlist (the only fields that ship)

Per cell: `subject`, `conditions`, `transcript` (turns' `role`/`content` only), `contextKey`,
`verdicts`. Per verdict: `judge`, `scope`, `score`, `summary`, `rationale?`. **Everything else is
excluded** — judgment `usage`/`raw`/`ts`/`sitting_key`; sitting `attempts`/`usage`/`ts`/`model`.

## Presets

`manifest.presets` is a list of curated deep-link views (a preset with no qualifying entries is
omitted): **Models split** (widest turn-1 cross-model spread), **Judges differed** (the two
judges ≥ 1.0 apart at full scope), **Steadfastness cliff** (biggest post-pressure Gemini drop).
Each is deterministic (magnitude-sorted with a `group → scenario → canonical pressure →
canonical framing` tie-break), capped at 12, and one entry per `(group, item)`. Because
hundreds of scenarios tie at the max magnitude (a plain magnitude cut fills all 12 slots from
one alphabetically-first tradition), the final selection is **round-robined across traditions**
so a preset is a genuinely cross-tradition curated view — verified to span all 7 traditions.
This round-robin is an **architect-approved, CMAP-required refinement** of the spec's literal
`(scenario, pressure, framing)` tie-break (recorded in the spec's *Presets* section and the
review doc). Each entry's `params` carry `{group, item, scope, a, b?, conditions:{…}}` —
condition-axis values are **nested** under `conditions` (matching the cell shape) so the viewer
applies them generically; `b` (the compare subject) is optional.

## Source fingerprint (cross-tier agreement)

Both this tier's `manifest.json` **and** the `results/` manifest stamp the **same**
`fingerprint` — a `sha256` over the sorted resolved-judgments stream (the shared
`analysis.fingerprint`). The viewer/CI asserts they are equal for a given `<run-id>`; a mismatch
means the two tiers were exported from different input states and is surfaced as a notice. This
upgrades "produced by the same loaders" into a checkable invariant.

**Determinism caveat:** byte-identical re-export holds within one Python/zlib toolchain. Export
with the pinned `workflows/analysis` environment (`uv --project workflows/analysis`).

## Producing / refreshing a dataset

The exporter lives in `workflows/analysis` and **reuses the `results/` (#49) judgment loaders**
(normalization, `judgments_v2` overlay, Opus-alias dedup). Run from the repo root against the
full-grid **Gemini** run root (which carries `report.json` + `sittings.jsonl`) plus any
report-less **Opus** judge layers:

```bash
uv --project workflows/analysis run python -m analysis export-raw \
  tmp/judging-runs/20260803-merged \
  tmp/judging-runs/20260803-unstated-opus \
  tmp/judging-runs/20260803-framings-opus-sample \
  --run-id 20260803 --out results-raw
```

Commit **only** the `results-raw/<run-id>/` output (never from the gitignored
`tmp/judging-runs/`). Re-running with the same inputs is **byte-stable** (sorted keys, gzip
`mtime=0`, no timestamp), so only shards whose scenarios changed rewrite. Add `--limit N` for a
small dev fixture (its fingerprint covers only the written subset).

**Keep the two tiers in sync:** refresh `results/` and `results-raw/` for the same `--run-id`
from the same run roots so their fingerprints match.

## Which run the SPA shows

The raw view is reached **run-scoped** from `/results` (which selects the run). A raw view whose
`results-raw/<run-id>/` counterpart is absent degrades to a notice.
