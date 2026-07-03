# workflows/analysis

Cross-tradition analysis for MultiBench: turn N per-tradition **judging** run-dirs
(`report.json` / `judgments.jsonl` / `judgments_v2.jsonl` / `sittings.jsonl`, one
`--results-dir` per tradition) into a self-contained **HTML report** +
**scenario-cluster bootstrap 95% CIs** + optional **matplotlib figures**.

It is a faithful port of JaleesBench's `html_report.py` / `make_figures.py` /
`paper_stats.py` / `score.py`, reframed so the comparison axis is the **tradition**
(subjects nested). See `codev/specs/26-workflows-analysis-port-jalees.md` (spec) and
`codev/plans/26-workflows-analysis-port-jalees.md` (plan).

## Status

Complete. `analysis report <run-dir>...` loads N judging run-dirs, reproduces each
`report.json`'s point estimates (≤1e−9), computes scenario-cluster bootstrap 95%
CIs, and writes a self-contained HTML report + `analysis_stats.json`; `--figures`
adds matplotlib PNG/PDF publication figures.

## Invocation

Run from the **repo root** (like `workflows/judging`):

```bash
uv --project workflows/analysis run python -m analysis report <run-dir>... [options]
```

Options (see `report --help`):

| Flag | Default | Meaning |
|------|---------|---------|
| `--out DIR` | `analysis-out` | Output directory; writes `report.html` + `analysis_stats.json` (+ `figures/` under `--figures`). Idempotent overwrite. |
| `--figures / --no-figures` | off | Also emit matplotlib PNG/PDF figures (needs the `figures` extra). |
| `--n-boot N` | `5000` | Bootstrap resamples for the scenario-cluster CIs. |
| `--seed N` | `12345` | Bootstrap RNG seed (determinism). |
| `--fig-format` | `pdf,png` | Comma list from `{pdf, png}` (with `--figures`). |

Each `<run-dir>` is one tradition's judging `--results-dir`. `analysis` is a
**read-only** consumer — it never modifies the judging output.

## Module map

```
analysis/
  __main__.py     # python -m analysis
  cli.py          # Typer app: `report` (heavy imports deferred inside the body)
  core_imports.py # single-source FRAMINGS/PRESSURES from tradition_validator.core
  # added in later phases:
  #   loaders.py      (Phase 2) read run-dirs; v2 overlay; fail-fast validation
  #   aggregate.py    (Phase 2) cell reducer + cross-tradition aggregates (parity ≤1e-9)
  #   stats.py        (Phase 3) scenario-cluster bootstrap (shared draws), stats_to_dict
  #   colors.py       (Phase 4) numeric score_color / score_axis (no band names)
  #   html_report.py  (Phase 4) self-contained inline-SVG report
  #   figures.py      (Phase 5) optional matplotlib PNG/PDF (lazy-imported)
```

## Tests

```bash
uv --project workflows/analysis run pytest workflows/analysis
```

Tests use committed miniature fixture run-dirs (`tests/fixtures/`, added in
Phase 2) — never the git-ignored `tmp/judging-runs/`.
