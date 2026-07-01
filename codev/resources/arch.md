# Architecture

Current system shape. This is the cold reference archive; the always-on distillation lives
in [`arch-critical.md`](arch-critical.md), whose "Map of arch.md" indexes the sections below.
Each section is a summary plus a pointer to the authoritative doc — not a copy of it. Update
during the review phase of any work that introduces or changes an architectural pattern.

## System purpose & shape

MultiBench measures whether an AI assistant is *good spiritual company* — judged by the
formative residue its counsel leaves, against each **tradition's own** canonical proof texts
rather than the evaluator's. It is built to host **many traditions**: the harness (collection,
judging, scoring) is tradition-agnostic, and a tradition supplies its own source, scenario bank,
proof texts, and companionship guide. The one expandability axis is the **tradition**; adding
one adds a directory, never changes the core. Origin: generalizes
[JaleesBench](https://github.com/iaser-ai/jaleesbench) (which instantiated the construct for
Sunni Islam only). See the root [`README.md`](../../README.md).

## Tradition module format

A tradition is a self-contained `traditions/<id>/` directory in a **file-based, human-first**
format: authored prose is **Markdown** (`README.md`, `source.md`, `guide.md`, and per-scenario
`turn1.md` / `judge-guidance.md` / `pressures.md`); structural metadata is small **YAML**
(`tradition.yaml`, per-scenario `scenario.yaml`); the only JSON is the tiny `scenarios/index.json`.
**No large JSON blobs.** `tradition.yaml`, `scenario.yaml`, and `index.json` are **closed schemas**
(an unknown key is an error) with no string coercion, and `<id>` is a slug that must equal the
manifest `id`. Authoritative contract: **Spec 1** and
[`traditions/README.md`](../../traditions/README.md).

## Universal core — framings & pressures

For cross-tradition comparability, **framings** and **pressures** are defined once in core,
identical for every tradition, and are **not** part of the per-tradition contract:

- **Framings (3):** `unstated` (no system prompt), `stated` (the core template keyed on
  `adherent_noun`), `guided` (the tradition's `guide.md`).
- **Pressures (6):** `secularize`, `insistence`, `false_authority`, `good_cause`, `flattery`,
  `personal_appeal` — one `## <pressure>` section per scenario's `pressures.md`, heading-normalized.

The only faith-specific framing inputs a tradition supplies are `adherent_noun`, `guide.md`,
and each scenario's `pressures.md` push text.

## The judge seam

Each scenario's `judge-guidance.md` **is** the proof texts and direction the judge is bound to when
scoring that scenario — the binding is **local by construction**. There is no separate proof-text
corpus to drift from; do not reintroduce one. The file is required and must be non-empty.

## The judging workflow

`workflows/judging/` (Python / uv / Typer) is the first pipeline that *consumes* a validated
tradition. It scores a subject model's responses to a tradition's scenarios — under the universal
framings × six pressures — against each scenario's `judge-guidance.md` (anchored to the
tradition's `guide.md`; **the judge seam above is its ground truth**), on the canonical −1…+1
scale (five values `−1, −0.5, 0, +0.5, +1`). Four commands over one `--results-dir`:
`collect` (subjects → `sittings.jsonl`, framing delivered as a context prefix so judged turns
stay blinded) → `judge` (config-driven panel — YAML `--config` overrides defaults — default Opus 4.8 + Gemini Flash 3.5, two scopes
`turn1`/`full`, one re-judge pass over ≥2-level disagreements, self-judgments skipped) →
`report` (per-scenario + aggregate scorecard, agreement, generic taxonomy breakdowns from the
tradition's *declared* axes, coverage, cost) → `run` (end-to-end). Failed cells are resumable
and force a non-zero exit; `report` never hard-fails. Provider access is behind two seams
(`subject_complete` / `judge_complete`); both are injectable so the pipeline is testable fully
mocked. See its [README](../../workflows/judging/README.md).

## tradition_validator

`apps/tradition_validator/` (Python / uv / Typer / Pydantic v2 / PyYAML) is the mechanical gate a
tradition must pass before any workflow consumes it. It reads the same files an author writes,
**fails fast**, and reports **located, actionable** findings (it never guesses or "fixes"). It
checks structure, the manifest schema, `index ⟺ folders` drift, per-scenario tags/seam/pressure
coverage, prose non-emptiness, and safety (UTF-8, YAML safe-load, symlink/`..`-escape rejection,
size cap). Run from the repo root:

```bash
uv --project apps/tradition_validator run python -m tradition_validator validate <dir>
```

(`validate-all` for every tradition; `--strict`, `--format text|json`). See its
[README](../../apps/tradition_validator/README.md).

## Repository layout

- `traditions/` — pluggable per-tradition modules (`sunni-islam`, 140 scenarios, is the first; `eastern-christianity` adds 100).
- `apps/` — applications and standalone tools (`tradition_validator`; `jaleesbrowser`).
- `workflows/` — pipelines over traditions: `judging/` (implemented; see above), scenario generation (not yet migrated in). Each workflow is its own uv project.
- `codev/` — the Codev process: `specs/`, `plans/`, `reviews/`, `resources/` (these docs),
  `state/` (builder threads). `git ls-files` is authoritative for file-level detail.

## Toolchain & protocol environment

This is a **Python (uv)** repo. Codev/porch defaults assume Node, so `.codev/config.json` overrides
them (config > protocol, survives `codev update`): `porch.checks` skips `build` and runs tests via
`uv run pytest` (`cwd: apps/tradition_validator`); per-phase `porch.consultation.models` is
`["codex","claude"]` because Gemini's per-phase sandbox can't see the worktree. The full 3-way CMAP
runs at the PR gate, where the diff is fed inline.
