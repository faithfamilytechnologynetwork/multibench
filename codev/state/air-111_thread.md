# air-111 — Apply Daniel Slate's judaism review corrections

Protocol: AIR (strict). Issue #111. Worktree: `.builders/air-111`.

## What the issue asked
Apply expert reviewer **Daniel Slate**'s (Yeshiva/Kollel) corrections to `traditions/judaism/`
as a versioned revision. The corrected files already existed under
`tmp/experiments/` — **copy, do not re-author**. This is instrument integrity, not a score
correction (two controlled experiments 2026-09-02 showed no score change within judge noise;
the published `20260803` results were judged against the pre-revision guidance).

## What I did
- **Diffed** each source-corrected file against the current tradition file and confirmed the
  changes match the review notes, then **copied** them byte-for-byte:
  - `guide.md` ← `tmp/experiments/guide-msr/judaism-guidefix/guide.md` (the "read this person"
    paragraph: dropped Prov 22:6 / *al pi darko* child-training framing; added *yishuv ha-daat*;
    "help that one").
  - `scenarios/{MSR-010,MSR-015,MSR-020,MSR-029}/judge-guidance.md` ←
    `tmp/experiments/sensitivity-msr/judaism-corrected/...` (matriarchs rebuked Gen 30:2 / 18:13–15,
    *nechama*=comfort accepting grief not manufactured hope, Chana-only citation; *sheker*'s
    distancing is the essence of the command; Mishlei 24:16 + teshuva/Hashem's love + counsel may
    not grant leniencies it has no authority to grant; Pinchas permitted-but-untaught).
- **`tradition.yaml` `scholar_review`:** `none` → `in_progress`, reviewers `[Daniel Slate]`.
  This is the only version/state field the module contract carries (see decision below).
- **`README.md`:** added a `## Revisions` section (2026-09, reviewer credited by name, scope,
  and the note that `20260803` results are unaffected) and updated the `## Scholar review`
  section off "status is none".
- **Test:** `apps/tradition_validator/tests/test_judaism_slate_revision.py` — validates the real
  on-disk module clean + pins each load-bearing correction so an accidental revert is caught.

## Key decision: no `schema_version` bump
The issue said "bump any version field the module contract carries." The contract's only version
field is `schema_version` (module-**format** version), and the validator supports **only `{1}`**
(`core.SUPPORTED_MODULE_SCHEMA_VERSIONS`); the manifest model is `extra="forbid"`, so a new
`revision:` field would also fail validation. Bumping `schema_version` for a **content** revision
would be semantically wrong and break validation. So I recorded the revision via `scholar_review`
(the contract's reviewer-credit field) + the README Revisions note. Status set to `in_progress`
(a 10-scenario sample by one Orthodox reviewer, not the full multi-stream review the README asks for).

## Verification
- `validate traditions/judaism` → PASS (0 errors, 0 warnings).
- New test: 8 passed. Scoped validator suite: my 8 + 107 others pass.

## Pre-existing issues (NOT mine — flagged, not fixed)
- `test_governance_docs.py` (4 failures: CLAUDE.md/AGENTS.md hot-context mirror + hot-map).
  The files those tests read are **byte-identical to origin/main** (`git diff --stat origin/main`
  empty) — pre-existing base-tree drift, independent of my diff.
- The test **dispatcher** (`.codev/checks/test.sh`) runs `uv --project apps/tradition_validator
  run pytest` from repo root, which over-collects the WHOLE repo; in this fresh worktree the
  `workflows/*` venvs aren't provisioned → `numpy` import/collection errors. Environmental,
  pre-existing, and out of scope for this AIR issue (dispatcher is global/shared — lessons say keep it).

## PR + merge path (2026-09-03)
- **PR #114** opened and **APPROVED** by the architect (files verified byte-identical to the
  reviewed versions). Body carries the full change list, verification, the no-schema_version-bump
  rationale, and blockers A/B described as pre-existing/out-of-scope, linked to **#112** (dispatcher
  over-collection) and **#113** (governance-doc drift). Recorded via `porch done 111 --pr 114`.
- porch intentionally left at PHASE=implement — not forced past the tests-check (won't bypass).
- **Merge path (architect's plan):** a task builder (`builder-task-1aut`) is fixing #112+#113. When
  its PR merges to main: merge main into `builder/air-111` → re-run `porch done 111` (tests-check
  goes green) → pass the pr gate → merge #114 with a **merge commit** (not squash). If the fix PR
  hasn't merged in ~3h, message the architect. Baseline origin/main at wait start: `d84ea3e`.
- Waiting via a background poll (5-min cadence, ~3h cap) on issue-close / main-advance — turn ends,
  not foreground-blocking.
