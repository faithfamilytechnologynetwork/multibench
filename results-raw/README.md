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
| `fingerprint` | `sha256:<hex>` over the resolved-**judgments** stream — cross-tier reconciliation with `results/`; see below. |
| `content_fingerprint` | `sha256:<hex>` over the **shard byte stream** (transcripts + `contexts` + verdicts) — baked-vs-GitHub coherence; see below. |

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

## Two fingerprints, two jobs

The manifest stamps **two** independent `sha256` fingerprints (both from `analysis.fingerprint`):

- **`fingerprint` — cross-tier agreement (judgments).** Over the sorted resolved-**judgments**
  stream. This tier's `manifest.json` **and** the `results/` manifest stamp the **same** value; the
  viewer/CI asserts they are equal for a `<run-id>`. A mismatch means the two tiers were exported
  from different input states and is surfaced as a notice — upgrading "produced by the same loaders"
  into a checkable invariant.
- **`content_fingerprint` — baked-vs-GitHub coherence (content).** Over the **shard byte stream**
  (each shard's canonical pre-gzip bytes: transcripts + `contexts` + verdicts). The viewer uses it to
  decide whether a same-origin **baked** bundle is coherent with the authoritative GitHub tier: it
  serves baked **only** when the two `content_fingerprint`s match, else falls back with a notice.
  This catches a **transcript/context correction that leaves the judgments unchanged** — which the
  judgment `fingerprint` alone would miss, silently serving stale baked transcripts. (Hashing the
  pre-gzip bytes keeps it independent of the zlib version.)

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
  tmp/judging-runs/20260823-opus-fullgrid \
  --run-id 20260803 --out results-raw
```

The **full-grid Opus** layer (`20260823-opus-fullgrid`, #110) is passed **last** (root-order
precedence → full-grid wins any sample overlap), so both tiers stamp the same new `fingerprint` and
the raw catalog carries the earned Opus `fullGrid: true` / `rankable: false` / `coverage`.
**Re-exporting rewrites every gz shard (~121 MB)**, so the Railway **baked** bundle goes
fingerprint-stale and must be re-baked (`railway up --no-gitignore`) — `resolveRawSource` fails safe
to the committed GitHub tier meanwhile. From a builder worktree the source roots are at
`../../tmp/judging-runs/…`.

Commit **only** the `results-raw/<run-id>/` output (never from the gitignored
`tmp/judging-runs/`). Re-running with the same inputs is **byte-stable** (sorted keys, gzip
`mtime=0`, no timestamp), so only shards whose scenarios changed rewrite. Add `--limit N` for a
small dev fixture (its fingerprint covers only the written subset).

**Keep the two tiers in sync:** refresh `results/` and `results-raw/` for the same `--run-id`
from the same run roots so their fingerprints match.

## Which run the SPA shows

A MultiBench run's raw view is reached **run-scoped** from `/results` (which selects the score run);
a raw view whose `results-raw/<run-id>/` counterpart is absent degrades to a notice.

A **raw-only** run — a `results-raw/<id>/` with **no** `results/<id>/` score tier (e.g. the AFB
explorer below) — is discovered separately (#54): `rawRunIds` enumerates `results-raw/` from the same
git-tree walk (no extra API call, and it never touches the score-manifest loader, so no false
"manifest not found"), the index lists such runs under **Explorers**, and each links to a first-class
landing at **`/raw/<run-id>/`** (dataset title + curated presets + a generic item index into
`/results/<run-id>/<group>/<item>`). The score-tier run list and default run are untouched.

## Second catalog type: AFB before/after (`afb-20260808`, #54)

The first **non-MultiBench** catalog on this tier — the companion artifact to the MultiWeights
omissive-bias result (experiment #48). For each of 150 AllFaith Benchmark (AFB) *Religious
Representation* items, in the **cold** condition, it shows the **vanilla Gemma-4-31B**
(`gemma-4-31b-it`) response beside the fine-tuned **MultiWeights (SFT+DPO)** (`mb-sft-dpo`) response,
each scored **0–4** by **GPT-5.6-Terra**. It rides the identical generic catalog shape — different
values only: `scale {0,2,4}`, `groupBy: instrument` (group `afb-150`), a single `condition: cold`
axis, a single `single` scope, and a diverging **center-grey** ramp (grey at the calibration target
2 → deliberately *not* signalling "4 is best"; over-application at 4 is a failure mode, not a win).

- **Provenance / licensing.** The **instrument** (questions + 0–4 rubric) is MIT © **CEFE-AI**
  (`github.com/CEFEAI/allfaith-religious-representation`), vendored at
  `experiments/48_multiweights_omissive_bias/data/input/afb/`. Our **responses + Terra judgments**
  are ours to publish; `manifest.json` `dataset.license` reflects this. Same exclusions as every
  tier here (no usage/cost/timestamps).
- **Produced by** `analysis export-afb` (a sibling of `export-raw` sharing the byte-stable writer)
  from the committed intermediate `experiments/54_afb_before_after/data/collection.json`
  (a one-time Modal + Terra collection; endpoint torn down on completion).
- **Headline** (over the final 150-item artifact): "meaningful-or-deeper" religious representation
  (score ≥ 2) rises from **1.3%** (vanilla) to **21.3%** (DPO); mean 0.127 → 0.820 — the #48
  omission→repair reproduces. Two independent caveats, kept separate: (a) an earlier run before the
  encoding fix (below) gave DPO 22.7% — re-collecting the 18 corrected items moved it to 21.3%;
  (b) DPO 21.3% sits below #48's *sampled* ~27–30% because this run uses **greedy** decoding
  (`temperature=0`) for reproducibility — a decoding difference, not a weaker effect.
- **Generation cap**: responses use `max_tokens=1024` (inherited from #48's harness); a few longer
  answers reach that cap and are shown as-generated (not repaired/extended).
- **Encoding provenance**: 18 of the 150 vendored questions were double-encoded (UTF-8-as-MacRoman)
  in `experiments/48/.../afb/questions.jsonl`. That file was **fixed forward**, and those **18 items
  were re-collected** with the corrected text (so their prompts/labels are clean); the other 132 are
  as-vendored (they were already clean). All 150 shipped items are now clean UTF-8.
- **Fingerprints.** Self-consistent judgment `fingerprint` (the canonical `fingerprint_line`, so a
  score/rationale change moves it) + `content_fingerprint` over the shard bytes. There is **no**
  cross-tier `results/` partner, so the viewer tolerates a null cross-tier lookup.
- **Served** from GitHub (the baked bundle ships only the MB run); the landing shows an unobtrusive
  footer note when GitHub-served — not a warning banner.

## Retention policy

This is a **committed** tier — each `results-raw/<run-id>/` is ~126 MB, so runs accumulate weight
in git history. **Intent: keep the last N run-ids** (default **N = 2** — the current published run
plus the immediately prior one for A/B and rollback), and prune older run directories.

- **What to keep:** the run(s) the SPA can select from `/results` (the score tier's committed runs)
  — the raw tier must exist for any run a reader can drill into. Keep the raw `<run-id>` for every
  score `<run-id>` still published; drop raw dirs whose score run has been retired.
- **Raw-only explorer runs are EXEMPT from the score-tier rule** (e.g. the AFB `afb-20260808` run,
  #54): they have **no** `results/` counterpart, so "drop raw dirs whose score run was retired" does
  NOT apply to them — a literal reading would wrongly prune a standalone explorer. Keep each raw-only
  run until it is deliberately, separately retired (its own decision, same `git rm -r` mechanics).
- **How to prune:** delete the whole `results-raw/<old-run-id>/` directory in a dedicated commit
  (`git rm -r results-raw/<old-run-id>`), paired with retiring the same `results/<old-run-id>/`. Do
  **not** delete individual shards — a partial run breaks the manifest's declared item set.
- **History note:** `git rm` removes the files going forward but not from history; if repo size
  becomes a problem, that's a separate history-rewrite decision (out of scope for a routine prune)
  and must go through the architect. This section is **policy/intent** — pruning is a deliberate,
  human-initiated action, not automated by the exporter.
