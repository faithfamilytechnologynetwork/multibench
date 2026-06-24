# air-4 — Issue #4: Fill hot-tier governance docs; decide codev/projects/* policy

Protocol: AIR (strict). Implement → PR. No spec/plan/review files; review goes in the PR body.

## Phase: implement

### What the issue actually needs (after reading the four governance files)
- The HOT files (`arch-critical.md`, `lessons-critical.md`) already have **real** critical
  facts/lessons (filled during Spec 1's review routing). The only leftover template is the
  **Map** sections — `<Top-level arch.md section>` / `<List your … sections>` placeholders.
- The COLD files (`arch.md`, `lessons-learned.md`) are still empty STARTERs
  (`_No architecture documented yet._`). A map can only point at *real* cold-doc top-level
  sections (skill: "map accuracy"), so the cold docs must get real, **current-state** content
  first. Review 1 already routed "cold detail in arch.md / lessons-learned.md" — writing it
  now completes that routing; it is grounded, not aspirational.

### Decisions
1. **Hot/cold governance docs.** Write grounded cold content (summary + pointer per section,
   no README duplication) into `arch.md` (7 top-level sections) and `lessons-learned.md`
   (3 sections), all drawn from merged Spec 1 / READMEs / validator / `.codev/config.json`.
   Then replace the placeholder Map entries in both hot files with one `consult-when` line per
   real cold section. Keep hot files within the cap (≤10 entries, ≤12 map topics, ≤35 lines).
2. **`codev/projects/*` policy → gitignore.** These are porch's per-project working/
   orchestration artifacts (state machine `status.yaml` + intermediate consult rebuttals/
   context) — same category as the already-ignored `.agent-farm/` and `.consult/`. The durable
   per-feature record is spec + plan + review (committed) plus the builder thread in
   `codev/state/` (committed); projects/ duplicates none of them and accrues per-iteration
   noise. Pattern `codev/projects/*` + `!codev/projects/.gitkeep` (keep the dir), then
   `git rm -r --cached` the tracked project subdirs. `git rm --cached` does NOT touch
   working-tree bytes — porch state is untouched and it recreates the dir on spawn; this does
   not edit `status.yaml`.

### Test (AIR requires tests)
Add `apps/tradition_validator/tests/test_governance_docs.py` (repo-root reads, skip-if-absent,
matching `test_docs.py`): no `<word word>` placeholders in hot files; hot files within cap;
every Map topic names a real cold-doc `##` section; consult artifacts gitignored / status.yaml kept.

### Refinement — porch commits status.yaml (don't ignore it)
First cut gitignored all of `codev/projects/` and `git rm --cached`'d everything. `porch done`
then FAILED at `writeStateAndCommit`: porch does `git add codev/projects/<id>/status.yaml` on
every phase transition, and a blanket ignore blocks it. Refined the policy to the issue's actual
scope ("consult outputs, rebuttals"): ignore `codev/projects/*/*` but **negate**
`!codev/projects/*/status.yaml` so porch's state file stays tracked. Re-added both status.yamls;
`git check-ignore` confirms rebuttals ignored, status.yaml tracked. 81 tests green.

Porch state note: that failed `porch done` still advanced the phase on disk → porch now reports
phase `pr` (uncommitted). The implement deliverables are complete and checks pass.

### HOLD — architect coordination (issue #6 / PR #9 rename)
Architect: the probe→scenario / scenario.md→turn1.md rename (issue #6, PR #9) is about to merge;
fill the hot-tier docs with the NEW vocab (`scenario`, `scenarios/`, `scenario.yaml`, `turn1.md`),
fix the residual `probes/*/` line in arch-critical.md, and rebase onto main after #6 merges.
Checked: **PR #9 is still OPEN (not merged)**; `origin/main` still uses `probes/` vocab (and has
moved ahead with `d175293` eastern-christianity). So I am HOLDING before opening the PR — my docs
currently use the pre-rename vocab on purpose (matches my branch's tree). Plan once #6 merges:
rebase builder/air-4 onto origin/main → resolve → sweep all four governance docs to the new
vocab (verifying exact new file names from #6's diff) → re-run pytest → open PR → notify architect.
Notified architect; waiting for the merge signal.

### Finalized — #6 merged, rebased, vocab swept, mirrors regenerated
Architect confirmed PR #9 merged (31620e2; plus #10 follow-up + eastern-christianity on main).
- Rebased `builder/air-4` onto `origin/main` cleanly (no conflicts).
- Swept all governance docs to the new vocab: `probes/`→`scenarios/`, `probes/index.json`→
  `scenarios/index.json`, `probe.yaml`→`scenario.yaml`, `scenario.md`→`turn1.md`, `per-probe`→
  `per-scenario`, "probe bank"→"scenario bank", "probe generation"→"scenario generation",
  "140-probe"→"140 scenarios". Fixed the residual `probes/*/` line in arch-critical.md. Updated
  arch.md's tradition list to current state (sunni-islam 140 + eastern-christianity 100).
  `grep` confirms zero old-vocab tokens left in codev/resources/.
- Regenerated the CLAUDE.md + AGENTS.md HOT CONTEXT mirrors (they were stale generic-template
  placeholders — the exact stale-mirror bug air-6 flagged). Did this deterministically (preserve
  the BEGIN/END boilerplate, inline the updated hot files verbatim) rather than `codev update`,
  which would treat CLAUDE.md as customized and pull unrelated framework churn. Diff is a single
  hunk inside the markers in each file — nothing else touched.
- Added a mirror-sync test so the mirrors can't silently go stale again. 83 tests green.
Next: amend commit → push → open PR (review in body) → `porch check` → STOP at the PR gate
(human approval) → notify architect.
