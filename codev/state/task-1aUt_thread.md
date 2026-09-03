# task-1aUt thread — Green the tests-check (#112 + #113)

## 2026-09-03 — MAINTAIN, single PR

Both issues make porch's tests-check red on `main` for **every** builder, regardless of what
they touched. Fixed both in one PR.

### #112 — dispatcher over-collects
`.codev/checks/test.sh` registered the validator suite as
`uv --project apps/tradition_validator run pytest` **from the repo root**, so pytest collected
`workflows/*` too. In a fresh worktree those venvs are unprovisioned → 126 collection errors
(numpy etc.) that abort the whole run and turn the tests-check red.

- Fix: scope the registry entry to the app dir → `... run pytest apps/tradition_validator`.
  Confirmed: unscoped collect-only = 126 errors; scoped = 103 tests, clean.
- Audited the **multibrowser** line as the issue asked: `pnpm -C apps/multibrowser test` already
  runs *inside* the app dir via `-C`, so vitest never over-collects — no change needed. The
  `workflows/*` entries already pass an explicit path arg. Per-builder dispatcher design kept.

### #113 — governance-doc drift (4 tests in test_governance_docs.py)
Pre-existing drift on `main` (files byte-identical to main), likely from the Spec 49/51/54
arch-doc edits. Fixed per the `update-arch-docs` skill's rule: **fix the map, do not pad the
cold doc.**

1. `arch-critical.md` map had one combined topic "The judging & analysis workflows" but
   `arch.md` carries two real sections, "The judging workflow" and "The analysis workflow".
   Split the map entry into the two matching topics.
2. `lessons-critical.md` map was **missing** two real `lessons-learned.md` sections —
   "Testing LLM pipelines" and "Porting fidelity" (the test checks the map both directions).
   Added both topics. (Issue only named arch-critical, but the same-class lessons drift also
   failed the suite; both are needed for green.)
3. Re-mirrored the hot tier into `CLAUDE.md` / `AGENTS.md`: the HOT CONTEXT block had regressed
   to `@import` lines (a `codev update`, commit 69e232b), but the test requires the hot files
   **inlined verbatim**. Regenerated both blocks byte-exact from the hot files (script-spliced
   between the BEGIN/END markers) — matches the pre-regression db17b8c format.

Caps still hold: arch-critical 29 lines / 9 facts / 9 map topics; lessons-critical 25 lines /
10 lessons / 5 map topics (≤35 lines, ≤10 entries, ≤12 topics).

### Verification
- `test_governance_docs.py`: 9 passed.
- Full validator suite (`pytest apps/tradition_validator`): 103 passed.
