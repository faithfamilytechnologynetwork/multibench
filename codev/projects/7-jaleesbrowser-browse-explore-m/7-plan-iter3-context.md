### Iteration 1 Reviews
- codex: REQUEST_CHANGES — Solid architecture and sequencing, but the plan misses explicit coverage for tradition-level prose loading/degradation and for required scenario-list sorting.
- claude: APPROVE — Comprehensive, spec-faithful plan with sound technical decisions (verified against codebase), clean phase decomposition, and thorough test strategy — ready for human review.

### Builder Response to Iteration 1
# Plan 7 — Plan iteration 1: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES), Claude (APPROVE). Both verified the plan against the
codebase; both endorsed the phase decomposition, the data/presentation split, and the I1
(vendor dataclasses) / I3 (markdown-it-py + nh3) decisions. **No disagreements** — I accepted
all three of Codex's gaps and Claude's non-blocking notes. Each maps to a concrete plan edit.

## Codex (REQUEST_CHANGES) — 3 gaps, all fixed

1. **Tradition-level prose (`README.md` / `source.md` / `guide.md`) loading/modeling/testing
   unassigned (spec M4); display-first degradation implied but not planned.** → Added
   `load_prose()` to the **Phase 1** loader deliverable (reads the three prose files via
   `safeio`, each degrading to a `Notice` on the `Tradition`); added prose fields to the
   `Tradition` model; added a missing/empty-prose fixture and a `test_loader_discovery.py`
   assertion (prose-degradation → notice, no exception); added a Phase-1 acceptance criterion.

2. **S1 sorting (by `id` or `source_locus`) required but only filter/search/counts were
   planned (Phase 4).** → Added explicit **sort by `id`/`source_locus`** to the Phase 4
   `filter.js` deliverable, to the implementation details (sort is a client-side reorder of the
   filtered set; static prev/next order unaffected), and to the Phase 4 acceptance/test (the
   filter-index must carry the data to sort).

3. **"Invalid `tradition.yaml` ⇒ stub page that still lists scenarios and skips manifest-derived
   UI with a notice" only implicit.** → Made explicit in the **Phase 3** templates deliverable
   (tradition page renders a top-of-page notice + the scenario list from folders/index +
   taxonomy-filter UI skipped with a notice) with a dedicated acceptance criterion and test.

## Claude (APPROVE) — non-blocking notes, all folded in

- **`source_locus` range UI underspecified** → specified as **min/max numeric inputs** in the
  Phase 4 `filter.js` deliverable.
- **Phase 4 is the densest phase** → added a **suggested intra-phase ordering** (output-path
  scheme → page-write → filter-index → `filter.js` → CLI wiring → tests).
- **`watchfiles` is Rust-backed (needs a wheel/compiler)** → already mitigated: `--watch` is
  kept off the CI-tested path; base `serve` (stdlib `http.server`) is the tested path. Left as
  a noted risk.
- Claude's spec-coverage table confirmed **every M/S/C requirement is covered and no phase
  exceeds scope** — no change needed.

## Also folded into this same plan revision (architect-directed, not from the consult)

- **Rename `jaleesbrowser` → `multibrowser`** (app/package/module/docs). The porch project slug
  and spec/plan/review **filenames** intentionally stay `7-jaleesbrowser-browse-explore-m.md`
  (porch state is keyed to the slug; renaming would break porch checks). Flagged to architect.
- **Results posture: "cut" → "results-ready" for #8.** Three inert seams threaded through
  P1–P3 (`Scenario.results=None`; `load_results()→None`; reserved `_results.html.j2`); **no
  results UI in v1**; concrete `ScenarioResults` schema deferred to a #8-coordinated follow-up.
  Spec §2.1/§4 reframed + new §4.1; recorded as a post-spec-approval amendment in spec §11.

Net: every REQUEST_CHANGES point is resolved by an added deliverable + acceptance + test; the
plan stays strictly linear (P1→P5) and within v1 scope.


### Iteration 2 Reviews
- codex: REQUEST_CHANGES — Strong, codebase-grounded plan with the prior gaps fixed, but it still underspecifies how the spec-required filter/query-state behavior will be automatically verified rather than mostly manual.
- claude: APPROVE — All iteration-1 gaps resolved; plan is comprehensive, spec-faithful, technically sound, and verified against the actual codebase — ready for human review.

### Builder Response to Iteration 2
# Plan 7 — Plan iteration 2: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES — one point) · Claude (APPROVE). Claude confirmed all
iteration-1 gaps resolved and every spec M/S/C requirement covered, with no blockers. Codex
raised a single remaining point; **accepted and fixed** — no disagreement.

## Codex (REQUEST_CHANGES) — the one remaining point, fixed

**"Phase 4 testability of client behavior is too manual."** Spec §10 requires automated tests
asserting filter results (OR-within-axis / AND-across-axes) and URL-restorable filter state;
the plan had weakened this to "unit-tested where feasible / documented manual check." Codex
offered an acceptable path: *a Python-side reference implementation checked against generated
filter-index cases.* → **Done exactly that.**

- Extracted the filter/sort/query-state semantics into a pure-Python module **`filtering.py`**:
  `build_filter_index`, `apply_selection` (OR-within / AND-across / identity_signal /
  source_locus-range / free-text), `sort_ids` (id | source_locus), and
  `encode_selection`/`decode_selection` (fail-soft round-trip). This is the **single source of
  truth** for the spec's filter semantics.
- Added **`tests/test_filtering.py`** — exhaustive, automated — exercising those functions over
  generated selections against **both real axis shapes** (sunni-islam `pillars`/`hearts`;
  eastern-christianity `passions`/`virtues`/`economia`/`register`), including OR/AND,
  locus-range edges, free-text, sort, and malformed-query → defaults.
- The client **`filter.js` is now a thin applier** of the embedded `build_filter_index` output
  (precomputed membership), mirroring the Python contract — so the JS surface is minimal and
  **no spec-required behavior rests on a manual check**. (No JS test toolchain is added; the
  semantics are Python-tested.)
- Reworded the Phase 4 deliverables / acceptance / test-plan / JS-drift risk accordingly; added
  `filtering.py` + `test_filtering.py` to the package layout.

## Claude (APPROVE) — non-blocking notes

- `normalize_heading` rule now spelled out in the `constants.py` deliverable (trim → lowercase
  → spaces/hyphens → `_`).
- `index.json` inner key `probes`→`scenarios`: **confirmed on real post-rename data** (see
  rebase note) and reflected in `constants.py`.
- `filter-index` size for 140 scenarios: negligible — no pagination (unchanged).

## Out-of-band this revision: #6 merged → branch rebased onto `main`

#6 (probe→scenario rename) merged on `main` mid-Plan (PR #9 `31620e2` + #10). Per the
architect, **rebased this branch onto `main`** so plan/implement run against real renamed data.
Verified the on-disk format matches `constants.py` (`scenarios/`, `scenario.yaml`, `turn1.md`,
`scenario_id_pattern`, `index.json` key `scenarios`). Risk **R1 (top risk) is resolved**; a
second real tradition `eastern-christianity` (100 scenarios, 4 different axes) now exercises
multi-tradition discovery + no-hardcoded-axes for real. Spec §9 R1 + plan risk table /
validation checkpoints updated.

Net: the one REQUEST_CHANGES point is resolved with an added pure-Python module + exhaustive
automated tests; the plan is now verifiable against two real traditions.


### IMPORTANT: Stateful Review Context
This is NOT the first review iteration. Previous reviewers raised concerns and the builder has responded.
Before re-raising a previous concern:
1. Check if the builder has already addressed it in code
2. If the builder disputes a concern with evidence, verify the claim against actual project files before insisting
3. Do not re-raise concerns that have been explained as false positives with valid justification
4. Check package.json and config files for version numbers before flagging missing configuration
