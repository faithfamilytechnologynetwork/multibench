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

All commands read/write a single `--results-dir` (default `results/`). `--limit N` caps the
grid for cheap smoke runs. Failed cells are left pending (resumable) and make the command exit
**non-zero**; `report` always runs and never hard-fails, so partial data still yields a report
with explicit coverage (no silent zeros).

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
| `usage` | judge token usage (incl. cache read/write) |

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

The default suite mocks every provider (deterministic, no network, no credentials). The opt-in
**`--live`** tests call real APIs and are excluded from CI: `test_live_anchoring_...` shows the
verdict follows the *supplied* guidance (flipping only the guidance flips the score), and
`test_live_prefix_cache_hit` shows the shared rubric/anchor prefix is cache-read on a repeat
judgment. They skip cleanly when credentials are absent.

## Not yet implemented

- **`--batch` (Anthropic Message Batches, ~50% cost)** is **deferred** — the judging grid is a
  natural batch workload, but the default path is synchronous per-cell (resumable). Batch mode
  is a future cost optimization, not a correctness gap.
