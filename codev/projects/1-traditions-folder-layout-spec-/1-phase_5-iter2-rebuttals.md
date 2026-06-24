# Phase 5 (docs) — Rebuttal to iteration-2 impl review

**Reviews:** Claude **APPROVE** (HIGH), Codex **REQUEST_CHANGES** (HIGH).

## Codex REQUEST_CHANGES (1) — ACCEPTED and fixed
- **Validator README documented an exit-code the CLI doesn't implement.** The README said
  bad paths exit `2`, but `validate <bad-path>` exits `1` (a non-directory path is reported
  as a located finding, not a usage error). **Fixed:** corrected the README's exit-code
  paragraph to state `0` clean / `1` validation problems (incl. non-directory path) / `2`
  invocation error (bad `--format`, or for `validate-all` a missing/empty traditions dir).
  Added `test_validate_nonexistent_path_exits_1` to pin the contract. 70 tests pass.

## Claude APPROVE
Confirmed all four Phase-5 docs complete and accurate, the iter-1 stale-README fix
landed, and the doc-drift test is a solid guardrail.
