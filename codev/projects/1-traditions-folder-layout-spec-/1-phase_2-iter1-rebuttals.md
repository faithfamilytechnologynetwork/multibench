# Phase 2 (schema) — Rebuttal to iteration-1 impl review

**Reviews:** Claude **APPROVE** (HIGH, 40/40), Codex **REQUEST_CHANGES** (MEDIUM).
(2-way per the approved consultation policy; architect runs full 3-way at the PR gate.)

## Codex REQUEST_CHANGES (2) — both ACCEPTED and fixed
1. **Inconsistent index-drift location.** The "folder on disk but not listed in
   index.json" drift was reported against `probes/<id>/` with no `path`, while the
   inverse ("index lists a missing folder") was on `index.json`. The spec §8.3 example
   locates *both* on `probes/index.json` at `probes`. **Fixed:** the extra-folder drift
   is now reported on `index.json` with `path="probes"`, matching the inverse case and
   the spec contract.
2. **Tests asserted message substrings only**, not the located contract. **Fixed:** added
   a `find_finding` helper and tightened the two drift tests and the id≠dirname test to
   assert the finding's **severity + file + path** (e.g. drift → `error`,
   `…/probes/index.json`, `path == "probes"`; id → `error`, `…/tradition.yaml`,
   `path == "id"`). 40 tests pass.

## Claude APPROVE
No changes — confirmed all Phase-2 deliverables, closed+strict Pydantic schemas faithful
to the spec contract, 40/40 acceptance tests.
