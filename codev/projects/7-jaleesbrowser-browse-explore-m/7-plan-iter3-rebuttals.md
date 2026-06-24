# Plan 7 — Plan iteration 3: rebuttal

**Reviewers:** Codex (REQUEST_CHANGES — two points) · Claude (APPROVE — "all previous review
gaps resolved; every spec requirement covered; all codebase claims verified accurate"). Both
of Codex's points **accepted and fixed**; no disagreement.

## Codex (REQUEST_CHANGES) — two points, both fixed

1. **Ghost / index-only stub rows' participation in filtering was underspecified.** The filter
   layer was described over normal scenario data only; ghost rows (index entry, no folder, so no
   tags/locus/identity metadata) are part of the filterable list (M6/M7), and without explicit
   rules the rendered rows, counts, and filtered results could diverge. → **Added an explicit
   "Filtering of incomplete rows (ghost + stub-tradition)" rule to Phase 4:**
   - `build_filter_index` emits an entry for **every rendered row** (incl. ghost/stub) with
     null/empty metadata (`tags={}`, `identity_signal=None`, `source_locus=None`,
     `search_text=id`).
   - In `apply_selection`, a metadata-less row **cannot satisfy a positive predicate** → any
     active tag/identity/locus filter excludes it; with no active filter (or a free-text query
     matching its id) it appears.
   - `sort_ids`: always by `id`; for `source_locus`, `None` sorts **last** (deterministic).
   - Counts and the rendered filtered list both derive from `apply_selection` over the same
     index → they **cannot diverge**.
   - **Stub-tradition** (invalid manifest → no axes): tag-axis filter UI skipped with a notice;
     identity/locus/free-text/sort still operate over each scenario's own `scenario.yaml`.
   - `test_filtering.py` now explicitly covers a ghost row + a no-axes stub tradition.

2. **Stale mitigation note contradicting the new testing posture.** The bottom Risk Analysis
   table still said client-filter drift is mitigated by "manual verify," conflicting with the
   authoritative-`filtering.py` approach adopted in iter-2. → **Updated that row** to: semantics
   live in the Python-tested `filtering.py` reference; the JS is a thin applier; **test-of-record
   is automated, not manual.** Swept the whole plan for other "manual" mentions — the remaining
   ones are legitimate per-phase confirmatory steps (REPL/eyeball/`--help`/`serve`), each already
   marked subordinate to the automated tests; no contradiction remains.

## Claude — APPROVE

No blockers; confirmed all prior gaps resolved, full spec coverage, and verified every codebase
claim (validator strictness, `_within_root`, flat layout, real post-rename data). No change
requested.

Net: both REQUEST_CHANGES points resolved with concrete, testable rules; the plan is internally
consistent about its automated test-of-record and explicit about incomplete-row filter behavior.
