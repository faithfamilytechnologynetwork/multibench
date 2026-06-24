# spir-7 — jaleesbrowser: browse & explore MultiBench traditions

Builder thread (cohort situational-awareness log). Issue #7, SPIR strict mode.

## 2026-06-23 — Specify phase started

**Goal**: an `apps/jaleesbrowser/` app to *browse and explore* MultiBench traditions
and their scenarios (read-only). Reference: JaleesBench's `jaleesbrowser` (iaser-ai/jaleesbench).

**Key research findings**:
- JaleesBench's `jaleesbrowser` is a **static TS/React (Vite) SPA** on GitHub Pages that
  browses **model-vs-model RESULTS** (scores, judge verdicts, side-by-side compare),
  fed by a Python `export_web.py` that emits `index.json` + lazy gzip per-probe shards.
- **Crucial divergence**: MultiBench #7 browses the **authored corpus** (scenarios,
  pressures, judge-guidance, taxonomy metadata) — there are NO model results to compare
  yet. Same *spirit* (static, zero-install, deep-linkable explorer), different *subject*.
  So JaleesBench's score-matrix / model-compare / shard machinery is largely irrelevant;
  we adapt the *browsing/viewer* experience, not the results-comparison.
- Repo is **Python (uv)**; sibling app `apps/tradition_validator/` is Typer + pydantic +
  pyyaml, flat-package layout, with a ready data model (`models.py`) + loaders (`loaders.py`).

**Firm constraints from the issue** (treated as baked, though no formal Baked-Decisions heading):
- Read-only: NEVER modify `traditions/` data.
- Python conventions (uv/Typer where CLI).
- App lives at `apps/jaleesbrowser/`.
- **Approach (web vs TUI vs static-site) is explicitly LEFT OPEN** for the spec + 3-way to decide.

**⚠️ #6 vocabulary dependency (critical risk)**:
- Issue says spec/build against POST-RENAME vocab: `scenarios/`, `scenario.yaml`,
  `turn1.md`, `scenario_id_pattern`, `scenarios/index.json`.
- But #6 (AIR, branch `builder/air-6`) is NOT merged AND the rename isn't even committed to
  its branch yet (diff vs main = only a status.yaml). Real data on main still uses OLD vocab
  (`probes/`, `probe.yaml`, `scenario.md`, `probe_id_pattern`).
- Plan: build against post-rename, verify with synthetic post-rename fixtures, isolate the
  format names in one constants module, rebase onto main after #6 merges. Documented as a risk.

Next: draft spec → `porch done 7` → porch runs 3-way consult → iterate → spec-approval gate.
