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
