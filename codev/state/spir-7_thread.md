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

## 2026-06-23 — Spec iter-1 consult done, feedback incorporated

Ran the 2-way consult (codex + claude; Gemini excluded by repo config). **Codex:
REQUEST_CHANGES, Claude: COMMENT — no blockers**, strong convergence. Both praised the §2.1
"this is NOT JaleesBench's results browser, there are no results to browse" reframing as the
key risk-killer. Incorporated all 11 sharpenings (see spec §11 Consultation Log table):
the substantive one was a real fail-soft/fail-loud inconsistency → added an explicit §8
**degradation-scope table** (invocation aborts; tradition/scenario/section degrade to inline
notices). Also nailed down: OR-within/AND-across filter semantics, index↔folder drift policy,
prev/next order, read-only tree-snapshot test, output escaping/path-containment/no-CDN, and
an "inline notice = rendered HTML warning" definition. Deferred to Plan: watch mechanism,
validator-import-vs-vendored-model, markdown renderer/sanitizer pick. Both endorsed Approach A
(Python static-site generator) over B and the post-rename-with-synthetic-fixtures sequencing.

Next: `porch next 7` → expect spec-approval gate (human). Will notify architect.

## 2026-06-24 — Spec-approval APPROVED; Plan phase (consult done + 2 architect changes folded)

Spec gate approved by human (architect relayed: "corpus-not-results reframing + Approach A
exactly right"). Wrote the implementation **plan** (5 strictly-linear phases: reader-core →
scenarios/notices → render → static-build → serve+README). Resolved the spec's deferred Plan
decisions: **I1** vendor dataclass read-model (don't import the strict validator); **I3**
`markdown-it-py`+`nh3`; **watch** = `watchfiles`.

Plan consult: **Codex REQUEST_CHANGES** (3 gaps: tradition prose loading M4; S1 sort;
stub-tradition-on-bad-manifest rendering) + **Claude APPROVE** (no blockers). All folded in.

**Two architect-directed changes folded into spec+plan mid-phase:**
1. **Rename `jaleesbrowser` → `multibrowser`** (app/package/module/docs). ⚠️ Kept the porch
   slug + spec/plan/review FILENAMES as `7-jaleesbrowser-browse-explore-m.md` (porch state is
   keyed to slug; renaming breaks porch checks). Reference project's own app stays `jaleesbrowser`.
2. **Results "cut" → "results-ready"** anticipating judging #8: three inert seams
   (`Scenario.results=None`; `load_results()→None`; reserved `_results.html.j2`) across P1–P3.
   **No results UI in v1.** Concrete `ScenarioResults` schema deferred to a #8-coordinated
   follow-up. Spec §2.1/§4 reframed + new §4.1; logged as post-approval amendment in spec §11.

**Re-gate judgment:** amendments don't change v1's build surface (rename cosmetic; results
unbuilt) → no separate spec re-gate; rides to human at plan-approval. Flagged to architect.

Next: rebuttal written → `porch done 7` → expect plan-approval gate. Notify architect +
coordinate with #8 (spir-8) on the eventual result schema.
