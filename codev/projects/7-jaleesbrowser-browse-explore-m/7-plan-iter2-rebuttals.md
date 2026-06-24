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
