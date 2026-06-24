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
- Next: acceptance grep + full verify, then commit/PR.
