# workflows/judging

The MultiBench **judging** workflow: score an AI assistant's responses to a tradition's
scenarios — under the universal framings (unstated / stated / guided) and the six pressures —
against each scenario's `judge-guidance.md` (the binding ground truth), on the canonical
**−1…+1** scale (the five values `−1, −0.5, 0, +0.5, +1`).

- Spec: `codev/specs/8-workflows-judging-the-judging-.md`
- Plan: `codev/plans/8-workflows-judging-the-judging-.md`

## The judge seam (what "ground truth" means here)

There is **no separate proof-text corpus**. For each scenario the judge is anchored to two
files from the tradition module:

- the tradition's **`guide.md`** — the construct (what "good company" means for this tradition);
- the scenario's **`judge-guidance.md`** — the *binding* direction for that scenario. The
  reported direction is settled **only** by this file.

The judge reads that guidance as prose and returns a verdict on the −1…+1 scale, regardless of
whether a tradition expresses its guidance via proof texts (e.g. `sunni-islam`) or as bare
numeric anchors (the other traditions). The score is one of the five canonical values; the
verdict also carries a `direction`, a `rationale`, and any of the seven counseling techniques
it observed.

## Install / run

Each workflow is its own `uv` project. Run everything from the **repo root**:

```bash
uv --project workflows/judging run python -m judging --help
```

### Commands

| Command | What it does | Writes |
|---|---|---|
| `collect <tradition>` | Run subject models over the framing × pressure × scenario grid, producing 4-turn sittings. | `sittings.jsonl` |
| `judge <sittings> <tradition>` | Score each sitting with the judge panel at both scopes; one re-judge pass over ≥2-level disagreements. | `judgments.jsonl` (+ `judgments_v2.jsonl`, `skipped.jsonl`) |
| `report <tradition>` | Aggregate judgments → per-scenario results + tradition-level scorecard. | `report.md`, `report.json` |
| `run <tradition>` | End-to-end: `collect → judge → report`. | all of the above |
| `batch-judge submit <sittings> <tradition>` | Submit pending Anthropic-judge cells as Message Batches (~50% cost). | `batch_state.json` |
| `batch-judge collect <sittings> <tradition>` | Poll batches → verdicts (batch-priced); live-judge everything still pending. | `judgments.jsonl` |

All commands read/write a single `--results-dir` (default `results/`). `--limit N` caps to the
first N raw grid cells (an arbitrary slice of the cell-major order — it may cut a scenario off
mid-grid); `--scenarios N` caps to the first N **whole scenarios** over the full
framing × pressure × subject sub-grid — the representative smoke that keeps each scenario complete
across every subject. Failed cells are left pending (resumable) and make the command exit
**non-zero**; `report` always runs and never hard-fails, so partial data still yields a report
with explicit coverage (no silent zeros).

### Parallelism, caching & cost

- **Parallel** — `collect` and `judge` (base + re-judge) run concurrency-bounded parallel over
  their per-cell provider calls, bounded by `concurrency` in the config (default 8); collection
  interleaves cell-major so concurrency spreads across subjects. Set `concurrency: 1` for a strictly
  serial run.
- **Prompt caching** — the Anthropic **judge** caches the rubric + per-scenario anchor (1h); the
  Anthropic **subject** caches the framing block (1h) + turn-1 so turn-2 doesn't re-pay. (Verify
  under `--live`: `usage.cache_read_input_tokens > 0`.)
- **Batch judging** — `batch-judge submit` then `batch-judge collect` judges via **Anthropic
  Message Batches at ~50% price** (a `batch_state.json` manifest makes it idempotent). **Gemini is
  not batched** (Vertex has no developer file-batch — matches JaleesBench); its cells fall to the
  **live `judge`**, which `batch-judge collect` runs automatically as the fallback (`--no-fallback`
  to collect batch results only). The report prices batched tokens at 0.5× and counts Gemini
  thinking tokens.

```bash
# Batch the judging grid (~50% cost), then collect + live-judge the rest:
uv --project workflows/judging run python -m judging batch-judge submit out/sittings.jsonl traditions/sunni-islam --results-dir out
uv --project workflows/judging run python -m judging batch-judge collect out/sittings.jsonl traditions/sunni-islam --results-dir out
```

### Configuration (`--config`)

Every command takes `--config <file.yaml>` — a YAML file overriding the defaults in
`judging/config.py` field-by-field (spec §5.7). Only keys you list override; unknown keys, bad
providers, or framings/pressures/scopes outside the universal core **fail loud**. Example:

```yaml
# judges: neither may equal a subject model, or it self-skips that cell.
judges:
  - {model: claude-opus-4-8, provider: anthropic, thinking: true}
  - {model: gemini-3.5-flash, provider: gemini, thinking: true, safety_off: true}
subjects:
  - {model: claude-opus-4-8}
  - {model: claude-sonnet-4-6}
framings: [unstated, stated, guided]
pressures: [secularize, insistence, false_authority, good_cause, flattery, personal_appeal]
scopes: [turn1, full]
retries: 2
```

> **Pass the same `--config` to `report` that produced the artifacts.** Coverage counts
> (`expected_cells` / `uncovered`) are computed from the panel × scopes in the config, so a
> standalone `report` under the wrong config would miscount uncovered cells. `run` uses one
> config for all three stages, so it is always consistent.

```bash
# Cheap end-to-end smoke run over a few grid cells:
uv --project workflows/judging run python -m judging run traditions/sunni-islam --limit 4

# Or stage by stage, into a chosen results dir:
uv --project workflows/judging run python -m judging collect traditions/sunni-islam --results-dir out
uv --project workflows/judging run python -m judging judge out/sittings.jsonl traditions/sunni-islam --results-dir out
uv --project workflows/judging run python -m judging report traditions/sunni-islam --results-dir out
```

## Contracts

### Sittings (`sittings.jsonl`) — the collector's output, the judge's input

One JSON object per line. The judged **`turns`** hold *clean scenario text only* — the framing
is delivered to the subject as a context prefix and recorded in `context_prefix` **for audit**,
never leaked into the turns (so judges stay framing-blinded).

| Field | Meaning |
|---|---|
| `subject` | subject model id |
| `tradition` | tradition id |
| `scenario_id`, `pressure`, `framing` | grid coordinates |
| `turns` | `[user, assistant, user, assistant]` — clean scenario text + subject replies |
| `context_prefix` | the framing the subject saw (audit only; `null` for `unstated`) |
| `attempts`, `usage` | per-reply retry counts + token usage |

### Judgments (`judgments.jsonl`) — the judge's output, the report's input

One JSON object per line, keyed `subject|scenario_id|pressure|framing|judge|scope`.

| Field | Meaning |
|---|---|
| `score` | one of `−1, −0.5, 0, +0.5, +1` |
| `direction`, `rationale` | the judge's short justification |
| `techniques_used` | subset of the seven counseling-technique ids |
| `judge`, `scope` | judge model id; `turn1` (baseline) or `full` (after pressure) |
| `raw` | the judge's unparsed response text (audit/debug) |
| `usage` | judge token usage (`in`/`out`/cache; `batch: true` for batched cells, priced 0.5×) |

`judgments_v2.jsonl` holds re-judge overrides (applied by key, v2 wins); `skipped.jsonl`
records self-judgments (a judge never scores its own subject's output).

### Results are data, not code

`results/` is git-ignored. Sittings/judgments/reports are run artifacts — never checked in.

## Judge panel & credentials

The panel is config-driven (`judging/config.py`). The default panel is **Claude Opus 4.8**
(`anthropic`) + **Gemini Flash 3.5** (`gemini`, with thinking; judging runs safety-off — subjects
never do). Missing credentials **fail loudly** (no silent fallback).

| Provider | Credentials |
|---|---|
| Anthropic (subjects + judge) | `ANTHROPIC_API_KEY` |
| Gemini judge | `GEMINI_API_KEY`, **or** a Vertex service account (`GOOGLE_APPLICATION_CREDENTIALS` + `GOOGLE_CLOUD_PROJECT`, optional `GOOGLE_CLOUD_LOCATION`) |

## Tests

```bash
uv --project workflows/judging run pytest workflows/judging          # default (mocked) suite
uv --project workflows/judging run pytest workflows/judging -m live --live   # opt-in live tests
```

The default suite mocks every provider (deterministic, no network, no credentials) **and** adds
real-client contract checks (it builds the actual Anthropic subject/batch request objects and the
Gemini response schema through the real SDK types — the mock boundary alone hid a Gemini bug once).
The opt-in **`--live`** tests call real APIs and are excluded from CI: anchoring (flipping only the
guidance flips the score), the prefix-cache hit, and a tiny end-to-end **`run` smoke** across the
default panel. They skip cleanly when credentials are absent — but the live smoke should be run
before trusting a real judging run.

## Deviations from JaleesBench (intentional)

This workflow is a faithful port of JaleesBench's judging pipeline, with two deliberate,
user-approved deviations (documented in the spec, §4.7):

- **Judge thinking is ON** (JaleesBench judged without it). An enhancement; its cost is counted
  (Gemini `thoughts_token_count` is included in usage).
- **Gemini judge = `gemini-3.5-flash`** (JaleesBench used a different Gemini model).

Reframes carried from the earlier design: numeric scores (no band names), the
`guide.md` + `judge-guidance.md` anchor (no separate proof-text corpus), Claude-only subjects, and
citation/HTML/web-export left out of scope.
