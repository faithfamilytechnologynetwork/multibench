# air-6 thread — Issue #6: rename probe → scenario (and scenario.md → turn1.md)

Protocol: AIR (strict). Mechanical terminology refactor of the Spec 1 subsystem — no behavior change.

## Plan / scope decisions

**Rename map** (from issue):
- `probes/` → `scenarios/`; `probe.yaml` → `scenario.yaml`; `scenario.md` (turn-1) → `turn1.md`
- `index.json {schema_version, probes:[...]}` → `{schema_version, scenarios:[...]}`
- `probe_id_pattern` → `scenario_id_pattern`
- "probe" terminology in code/models/messages/CLI/docs → "scenario"
- **Unchanged:** `JLS-NNN` id values, `judge-guidance.md`, `pressures.md`, `guide.md`, `source.md`, the six pressures, `applies_to: scenario|response` enum, all validation behavior.

**In scope (doing):**
- Validator code: core.py, models.py, validator.py, cli.py, port_jaleesbench.py (output layout). Renames: `PROBES_INDEX`→`SCENARIOS_INDEX`, `REQUIRED_PROBE_FILES`→`REQUIRED_SCENARIO_FILES`, `ProbesIndex`→`ScenariosIndex`, `ProbeMeta`→`ScenarioMeta`, `list_probe_folders`→`list_scenario_folders`.
- All validator tests + fixtures (conftest `write_probe`→`write_scenario`).
- Data: traditions/sunni-islam/ (140 folders via git mv).
- Skill: .claude/skills/create-tradition/SKILL.md
- Docs: traditions/README.md, apps/tradition_validator/README.md, root README.md, Spec 1 (surgical, preserving provenance), workflows/README.md (tiny, "our" vocab — describes the generator this rename prepares for).

**Out of scope (left for MAINTAIN / noted in PR):**
- `codev/resources/arch-critical.md` + its CLAUDE.md/AGENTS.md mirrors — HOT-tier governance docs with cap discipline; MAINTAIN/update-arch-docs owns these. They still say `probes/*/`; flagged for a follow-up MAINTAIN pass.
- `codev/plans/1`, `codev/projects/1/*`, `codev/reviews/1`, `codev/state/spir-1_thread.md` — historical porch/codev record; left verbatim.

**JaleesBench provenance preserved verbatim** everywhere: `probes.json`, `proof_texts.json`, `probes_ar.json`, JaleesBench `probes[]`/`bab`/`chapter`/`islamic`, `mapping.py`/`prompts.py`. Porter INPUT (reads JaleesBench `probes.json`, `bank["probes"]`, `p["turn1"]`) stays; porter OUTPUT (scenarios/, scenario.yaml, turn1.md, index `scenarios:[...]`) renamed.

## Progress
- Validator code renamed (core/models/validator/cli/porter-output). Compiles.
- Tests renamed (conftest fixtures, test_probes.py→test_scenarios.py, all assertions). 74 pass.
- Data: `git mv` probes→scenarios, 140× probe.yaml→scenario.yaml + scenario.md→turn1.md, index.json key, tradition.yaml field, sunni README/source prose. Validates clean (strict, exit 0).
- Skill + docs (traditions/README, validator/README, root README, workflows/README) updated; doc-consistency tests green.
- Spec 1: surgical vocabulary pass on normative sections §1–§9 + transparency banner. Preserved: §10 Consultation Log (historical), JaleesBench provenance (`probes.json`, port-table left column, JaleesBench-harness `probe-gen`, the §5.5 embedded-anchor evidence sentence).
- Verified: pytest 74 pass; validate/validate-all `--strict` exit 0; 140 scenario folders w/ scenario.yaml+turn1.md+judge-guidance.md+pressures.md; acceptance grep clean (only provenance).
- Committed (f99b3d6, conventional, no co-author per user pref), pushed. **PR #9** opened with review in body. porch advanced impl→pr; checks (pr_exists, e2e_tests) green.

## STATUS: PR gate reached — WAITING FOR HUMAN APPROVAL (`porch approve 6 pr`)

PR: https://github.com/faithfamilytechnologynetwork/multibench/pull/9

**Follow-up for architect (not in this PR's scope):** `codev/resources/arch-critical.md`
(+ CLAUDE.md/AGENTS.md mirrors) still reference `probes/*/` — HOT-tier governance docs owned
by MAINTAIN/update-arch-docs. Recommend a short MAINTAIN pass to refresh that one fact.

## UPDATE 2026-06-24: MERGE HELD — collision with eastern-christianity

Gate approved by architect (squash requested). But PR #9 is **CONFLICTING** with main:
a 2nd tradition **`eastern-christianity`** (ByzantineBench, 100 `BZ-NNN` folders) merged to
main (d175293) in the **OLD `probes/` format** (`probe.yaml`/`scenario.md`/`probe_id_pattern`/
`probes/index.json`) while I was at the gate.

Impact:
1. Textual conflicts in `README.md` + `traditions/README.md` (both sides edited).
2. **Semantic break:** after my rename merges, the renamed validator expects
   `scenarios/`/`scenario.yaml`/`turn1.md`/`scenario_id_pattern` → eastern-christianity would
   **fail `validate-all --strict`**. Merging as-is leaves main red.

This is materially larger than what was approved (140→240 scenarios) and touches another
builder's work, so I did NOT merge. Surfaced to architect with recommendation: fold the
eastern-christianity migration (same mechanical rename) into this PR, re-verify validate-all
--strict for both, then squash-merge. Working tree clean; no local merge started. Awaiting go.
