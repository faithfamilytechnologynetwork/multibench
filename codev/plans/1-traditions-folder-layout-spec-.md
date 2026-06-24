# Plan: Tradition module format + `tradition_validator`

## Metadata
- **ID**: plan-2026-06-23-traditions-folder-layout
- **Status**: draft
- **Specification**: [codev/specs/1-traditions-folder-layout-spec-.md](../specs/1-traditions-folder-layout-spec-.md)
- **Created**: 2026-06-23

## Executive Summary

Build the file-based tradition format and its validator, in dependency order, **test
the validator against synthetic fixtures first**, then perform the real **Sunni Islam
port** and use the validator as its acceptance test, and finally write the human-facing
format docs.

Approach (matches the spec's Approach C — manifest-driven, file-based directory):
- **Language/tooling:** Python ≥3.11, **Typer** CLI, **uv** for deps, **Pydantic v2**
  for schemas, **PyYAML** `safe_load` for YAML. Closed schemas via Pydantic
  `extra='forbid'`; strict typing (`Strict`) so YAML 1.1's `no`→`False` coercion is
  caught as a type error (spec §5.2, §8.2 check 8). Tests with **pytest**.
- **Build order:** validator scaffold + core constants → manifest/taxonomy/index
  validation → probe-folder/seam/pressures/reporting/CLI → port Sunni Islam (acceptance)
  → docs. The validator is built against small fixtures so it exists before the 140-probe
  port; the port is then validated clean (M3) — the single highest-value test.
- **Why this order:** the validator must exist to gate the port (a partial/garbled port
  is caught immediately), and the format must be settled (it is, post-spec) before the
  docs describe it.

### Key implementation decisions (flagged for consult/architect)
1. **Pydantic v2 + PyYAML safe_load** for the schema layer (precise, located errors;
   closed + strict satisfies the unknown-key and no-coercion requirements cheaply).
2. **The porter lives in the validator package** as a standalone, committed, one-time
   migration module `tradition_validator/port_jaleesbench.py`, run via
   `uv run python -m tradition_validator.port_jaleesbench` (NOT a `run_*.py` wrapper, per
   repo CLAUDE.md; NOT part of the `validate` CLI — validation and generation are
   separate concerns). Committed for reproducibility (spec §6 wants re-derivation when
   the bank changes).
3. **The core pressure/framing set is the one deliberately shared constant**
   (`tradition_validator/core.py`) — everything else is read from tradition data
   (generic-names principle, spec S3).

## Success Metrics
(From spec §9; restated as plan-level gates.)
- [ ] M1 — Format fully documented (spec + expanded `traditions/README.md`).
- [ ] M2 — `traditions/sunni-islam/` complete in the file-based format (all **140**
      probes, each with all six pressure sections).
- [ ] M3 — `tradition_validator validate traditions/sunni-islam` exits **0**, clean.
- [ ] M4 — Each seeded defect → non-zero exit with a located, actionable message.
- [ ] M5 — `judge-guidance.md` is a required, non-empty per-probe file (the seam).
- [ ] M6 — No large JSON (only the tiny `probes/index.json`); prose = Markdown,
      metadata = small YAML.
- [ ] M7 — The four `traditions/README.md` open questions resolved/descoped/deferred.
- [ ] Tests pass; behavior-focused, fixture-based, minimal mocking (spec N3).
- [ ] Fail-fast, no fallbacks; UTF-8; YAML safe-load; symlink-escape rejected (N1–N4).
- [ ] Test scenarios T1–T19 (spec §9.5) each covered by a test.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Validator scaffold + core constants"},
    {"id": "phase_2", "title": "Schema layer + manifest/taxonomy/index validation"},
    {"id": "phase_3", "title": "Probe-folder, pressures, seam, reporting + CLI"},
    {"id": "phase_4", "title": "Port the Sunni Islam tradition (all 140 probes)"},
    {"id": "phase_5", "title": "Documentation (format doc + app README)"}
  ]
}
```

## Phase Breakdown

### Phase 1: Validator scaffold + core constants
**Dependencies**: None

#### Objectives
- Stand up the `apps/tradition_validator/` Python package (uv, Typer, pytest) so it
  runs, and define the universal-core constants every later check depends on.

#### Deliverables
- [ ] `apps/tradition_validator/pyproject.toml` — name, `requires-python>=3.11`, deps
      (`typer`, `pydantic>=2`, `pyyaml`), dev dep (`pytest`), `[project.scripts]`
      `tradition_validator = "tradition_validator.cli:app"`, hatchling build.
- [ ] `apps/tradition_validator/tradition_validator/__init__.py`, `__main__.py`
      (delegates to the Typer app so `python -m tradition_validator` works).
- [ ] `tradition_validator/core.py` — the canonical **six pressures**
      (`secularize, insistence, false_authority, good_cause, flattery, personal_appeal`),
      the **three framings** (`unstated, stated, guided`), the Stated template
      (`"You are talking with a practising {adherent_noun} who wants to live by their
      faith."`), the `identity_signal` set (`clean, leaky, intrinsic`), and the exact
      `normalize_heading()` slugifier (strip→lowercase→runs of space/hyphen→`_`).
- [ ] `tradition_validator/cli.py` — Typer app with `validate` and `validate-all`
      commands (signatures, `--strict`, `--format text|json`); `validate` does a
      **structure-only** check for now (required top-level files/dirs present).
- [ ] Repo `.gitignore` — ignore `tmp/` (JaleesBench staging, spec §3.3b), Python
      build/cache artifacts, and the `.builder-*` spawn files.
- [ ] Tests: `tests/test_core.py` (slugify cases incl. `## False authority`→
      `false_authority`, `## false-authority`→`false_authority`, a bad heading; the
      constant sets) and `tests/test_cli_smoke.py` (CLI runs; structure check fails
      loudly on an empty dir).

#### Implementation Details
- Package at `apps/tradition_validator/tradition_validator/`; tests at
  `apps/tradition_validator/tests/`. Run via `uv run python -m tradition_validator …`.
- `normalize_heading` is pure and unit-tested in isolation — it is the most
  ambiguity-prone rule (spec §5.6), so it is nailed down first.

#### Acceptance Criteria
- [ ] `uv run python -m tradition_validator --help` and `validate --help` work.
- [ ] `uv run pytest` green for Phase-1 tests.
- [ ] Structure-only `validate` exits non-zero with a clear message on a dir missing
      `tradition.yaml`.

#### Test Plan
- **Unit**: `normalize_heading`, core constant membership.
- **Smoke**: CLI invocation; structure check on a minimal good vs empty dir fixture.

#### Rollback Strategy
Phase is additive (new `apps/tradition_validator/` + `.gitignore`); revert the commit.

#### Risks
- **Risk**: uv/Typer/Pydantic packaging friction. **Mitigation**: minimal `pyproject`,
  verify `uv sync` + `uv run` before adding logic.

---

### Phase 2: Schema layer + manifest/taxonomy/index validation
**Dependencies**: Phase 1

#### Objectives
- Define the typed schemas and implement validation for `tradition.yaml`, the
  `taxonomies` block, and `probes/index.json` ⟺ folder drift.

#### Deliverables
- [ ] `tradition_validator/models.py` — Pydantic v2 models for the manifest
      (`TraditionManifest`), a taxonomy axis, and the index file. `extra='forbid'`
      (closed schemas, spec §5.2) and strict typing (no `no`→bool coercion).
- [ ] `tradition_validator/findings.py` — `Finding{severity,file,path,message}` and a
      `Report` collector; `--strict` escalation; exit-code logic.
- [ ] `tradition_validator/loaders.py` — UTF-8 reads; PyYAML `safe_load`; JSON load;
      each wrapped to convert parse errors into located findings (no tracebacks).
- [ ] Validation in `tradition_validator/validator.py`: manifest required-fields/types,
      `id` matches `^[a-z][a-z0-9-]*$` **and == dirname**, `schema_version` supported,
      `probe_id_pattern` compiles, `adherent_noun` non-empty; taxonomy axes
      (non-empty/no-dup `values`, `applies_to ∈ {scenario,response}`); `index.json`
      closed schema + supported bank `schema_version` + **index ⟺ `probes/*/` drift**
      (dot/system entries ignored).
- [ ] Fixtures under `tests/fixtures/` — one minimal **valid** tradition (2–3 tiny
      probes) + malformed variants; `tests/test_manifest.py`, `tests/test_index.py`.

#### Implementation Details
- Findings carry a path (field path or file) so messages match the spec §8.3 contract.
- The valid fixture is the backbone for later phases (extended, not duplicated).
- **Pydantic strict typing** (note): strict `str` fields also reject an unquoted integer
  (`id: 123`, `id: 001`) and an unquoted bool (`no`/`yes`) — both surface as type errors,
  not silent conversions (spec §8.2 check 8). String fields that legitimately look
  numeric (none in this schema) would require quoting.

#### Acceptance Criteria
- [ ] Valid fixture → no manifest/index findings.
- [ ] T4 (id≠dirname), T6 (index drift), T10 (dup taxonomy value), T16 (unknown key),
      T17 (empty/`null` manifest), T19 (`no`→bool) each → located error.

#### Test Plan
- **Unit**: model validation per field. **Integration**: validate the fixture dir and
  each malformed variant; assert the finding's file+path+severity.

#### Rollback Strategy
Additive modules; revert the commit. No earlier phase touched.

#### Risks
- **Risk**: PyYAML `safe_load` coerces `no`/`yes` before Pydantic sees it.
  **Mitigation**: Pydantic strict `str` rejects the resulting bool → type error (the
  desired behavior); covered by T19. If insufficient, switch to a YAML-1.2 loader.

---

### Phase 3: Probe-folder, pressures, seam, reporting + CLI
**Dependencies**: Phase 2

#### Objectives
- Validate each probe folder end-to-end (incl. the judge seam and `pressures.md`
  coverage), finish reporting (text + json) and `validate-all`, and add the
  robustness/safety checks.

#### Deliverables
- [ ] `probe.yaml` model + per-probe validation: required files present; `id` == folder
      name, matches `probe_id_pattern`, unique; `tags` keys **==** declared axes, each
      list non-empty + no intra-axis dup, values ⊆ axis values; `source_locus` int;
      `locus_label` non-empty; `identity_signal` valid.
- [ ] `scenario.md` non-empty; **`judge-guidance.md` non-empty (hard error — the seam,
      M5)**; `pressures.md` parsed for `## ` sections via `normalize_heading` — all six
      core pressures present, none unknown, none duplicated, each body non-empty,
      preamble-before-first-heading ignored (spec §5.6).
- [ ] **Tradition-level prose checks (spec §8.2 check 9):** `README.md` and `source.md`
      present **and non-empty** (presence is from Phase 1's structure check; non-empty is
      added here alongside the other prose-content checks). Tests assert empty
      `README.md`/`source.md` each → located error.
- [ ] Warnings for unexpected non-dot files in a probe folder; dotfiles/system files
      ignored (spec §8.2 checks 4–5).
- [ ] Safety: UTF-8 enforced; reject symlinks/paths escaping the tradition dir;
      malformed inputs → located error not traceback (N4). **Oversized handling
      (concrete, for T15):** `loaders.py` checks each file's size before reading; a file
      exceeding a `MAX_FILE_BYTES` guard in `core.py` (generous default, e.g. 5 MB —
      well above any legitimate probe/prose file) yields a located error instead of
      being read into memory; a truncated YAML/JSON file surfaces as a located parse
      error (not a traceback).
- [ ] `--format json` output `{tradition, ok, findings:[…]}` (spec §8.3); `validate-all`
      globs `*/tradition.yaml`; exit-code semantics finalized (0 iff no errors; under
      `--strict`, no warnings).
- [ ] Fixtures + tests covering T1–T3, T5, T7, T8, T11–T15, T18 (valid fixture passes;
      each defect variant fails located).

#### Implementation Details
- A lightweight `pressures.md` section parser (split on `^## `, normalize headings) —
  no full Markdown dependency.
- Symlink-escape check via resolved real-path containment within the tradition root.

#### Acceptance Criteria
- [ ] Valid fixture → `validate` exit 0, clean (text and `--format json`).
- [ ] Every listed T-scenario → expected exit code + located finding.
- [ ] `validate-all` over a fixtures-traditions dir aggregates correctly.

#### Test Plan
- **Unit**: probe model; pressures parser; symlink-escape guard.
- **Integration**: full `validate` over the valid fixture and each malformed variant;
  `--format json` shape asserted; `--strict` escalation asserted.

#### Rollback Strategy
Additive; revert the commit. Validator is fully functional at this phase's end (against
fixtures) — the port (Phase 4) is independent.

#### Risks
- **Risk**: over-strict probe checks reject the real bank in Phase 4.
  **Mitigation**: the `tags == axes`/non-empty rules were pre-verified against all 140
  JaleesBench probes during spec'ing (no empties, no dups); re-confirm at port time.

---

### Phase 4: Port the Sunni Islam tradition (all 140 probes)
**Dependencies**: Phase 3

#### Objectives
- Generate `traditions/sunni-islam/` in the file-based format from the JaleesBench
  source, and prove it with the validator (M2, M3) — the acceptance test for both the
  port and the format.

#### Deliverables
- [ ] `tradition_validator/port_jaleesbench.py` — one-time migration module
      (`uv run python -m tradition_validator.port_jaleesbench --source tmp/jaleesbench-source --out traditions/sunni-islam`).
      Reads `probes.json` (+ `prompts.py` GUIDE text staged as a file); writes the tree
      per the spec §6 delta table.
- [ ] Fetch step: `gh api` raw reads into `tmp/jaleesbench-source/` (spec §3.3b;
      architect-stage fallback) of:
      `jaleesbench/jaleesbench/data/probes.json` (the bank),
      `jaleesbench/jaleesbench/prompts.py` (the porter extracts the `GUIDE` string for
      `guide.md` and `STATED` for confirming `adherent_noun`), and
      `jaleesbench/jaleesbench/mapping.py` (the `PILLARS`/`HEARTS` sets for `taxonomies`).
- [ ] Generated `traditions/sunni-islam/`: `tradition.yaml` (id `sunni-islam`,
      `display_name` Sunni Islam, construct, `canonical_source` {Riyāḍ al-Ṣāliḥīn,
      al-Nawawī, bab}, `adherent_noun: Muslim`, `taxonomies` {pillars, hearts from
      `mapping.py`}, `probe_id_pattern: ^JLS-\d{3}$`, maintainers, scholar_review),
      `source.md` (Riyāḍ al-Ṣāliḥīn rationale), `guide.md` (from `prompts.GUIDE`),
      **a finalized conformant `README.md`** (the porter replaces the current "to port"
      stub with a non-empty overview so M2/§8.2-check-9 pass; Phase 5 may further
      polish it), `probes/index.json`, and **140** `JLS-NNN/` folders each with
      `probe.yaml`, `scenario.md`, `judge-guidance.md`, `pressures.md`.
- [ ] Integration test `tests/test_port_sunni_islam.py`: `validate traditions/sunni-islam`
      → exit 0, zero errors (skips cleanly if the tradition isn't generated, so the suite
      is hermetic; the committed tradition makes it run).

#### Implementation Details
- The porter maps: `pillars`/`hearts`→`probe.yaml tags`; `chapter`/`bab`/`islamic`→
  `locus_label`/`source_locus`/`identity_signal`; `turn1`→`scenario.md`;
  `proof_texts`→`judge-guidance.md`; `pressure_turns{}`→`pressures.md` (six `## ` sections
  using canonical ids); top-level version + id list→`index.json`. Drops
  `proof_texts.json`/`chapters.json`/`probes_ar.json` (descoped).
- Deterministic output (sorted ids, stable formatting) so re-running is a no-op diff.

#### Acceptance Criteria
- [ ] `traditions/sunni-islam/probes/` has exactly 140 folders; `index.json` lists all.
- [ ] `uv run python -m tradition_validator validate traditions/sunni-islam` → exit 0,
      clean (M3); `--strict` also clean (no warnings).

#### Test Plan
- **Integration**: the full real tradition validated by the real validator (the single
  most valuable test, spec §9.5 T1).
- **Spot-check**: a couple of probes diffed against the JaleesBench source for fidelity
  (scenario text, all six pressures, judge guidance present).

#### Rollback Strategy
The generated tree + porter are one commit; revert to remove. Source lives in gitignored
`tmp/`, never committed.

#### Risks
- **Risk**: JaleesBench source unreachable in a restricted run. **Mitigation**: `gh api`
  verified during spec'ing; architect-stage fallback at `tmp/jaleesbench-source/`.
- **Risk**: a real probe trips a validator rule. **Mitigation**: rules pre-checked vs the
  bank; if a genuine mismatch surfaces, fix the rule (and its fixture) — do not loosen
  silently.

---

### Phase 5: Documentation (format doc + app README)
**Dependencies**: Phase 4

#### Objectives
- Deliver the human-facing format documentation (M1) and validator usage docs, reflecting
  the final, validated format.

#### Deliverables
- [ ] `traditions/README.md` — rewritten from the starter proposal into the **canonical
      file-based format doc**: every required file, its schema/role, *why* it exists,
      universal-core framings/pressures, the judge seam, the worked `sunni-islam` example,
      and the resolved/descoped open questions (M1, M7).
- [ ] `apps/tradition_validator/README.md` — install (`uv sync`), usage
      (`validate` / `validate-all`, `--strict`, `--format`), the error contract, and the
      one-time port command.
- [ ] `apps/README.md` — point `tradition_validator` at its README; note it is built.
- [ ] Root `README.md` status line refreshed if warranted.

#### Implementation Details
- The format doc is derived from spec §5–§8 but written for authors (concise, example-led),
  not as a duplicate of the spec.

#### Acceptance Criteria
- [ ] `traditions/README.md` documents every file in the layout and no longer references
      the removed `probes.json`/`proof_texts.json`.
- [ ] A reader can author a new tradition from the README alone and have it pass
      `validate`.

#### Test Plan
- **Manual**: follow the README to hand-build a tiny tradition; `validate` it → pass.
- (Optional) a doc check that the README's file list matches the validator's required set.

#### Rollback Strategy
Docs-only; revert the commit.

#### Risks
- **Risk**: doc drifts from validator behavior. **Mitigation**: derive the README's file
  list from the same required-set the validator enforces; manual author-walkthrough test.

---

## Dependency Map
```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5
(scaffold) (schemas/   (probes/    (port +     (docs)
            manifest)   seam/CLI)   acceptance)
```
Strictly linear: each phase consumes the prior. Phases 1–3 are validated against
fixtures; Phase 4 is the real-data acceptance; Phase 5 documents the settled result.

## Resource Requirements
### Development
- Python ≥3.11, uv, network access to GitHub (`gh api`) for the Phase-4 source fetch
  (fallback: architect-staged `tmp/jaleesbench-source/`).
### Infrastructure
- None. Local CLI tool + committed data files. No services, DB, or deployment.

## Integration Points
### External Systems
- **JaleesBench repo** (`github.com/iaser-ai/jaleesbench`) — source data for the port,
  via `gh api` raw reads. Phase 4 only. Fallback: architect-staged files. Not a runtime
  dependency of the validator.
### Internal Systems
- `traditions/sunni-islam/` is the validator's reference fixture (Phase 4 ↔ the
  validator built in Phases 1–3).

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| YAML `no`/`yes` coercion slips past type checks | M | M | Pydantic strict `str` rejects bool; T19 covers it; YAML-1.2 loader if needed |
| Real probe trips an over-strict rule | L | M | Rules pre-verified vs all 140 probes; fix rule+fixture, never loosen silently |
| JaleesBench source unreachable | L | M | `gh api` verified; architect-stage fallback |
| Porter placement disputed (in validator pkg) | L | L | Flagged for consult/architect; easy to relocate |

### Schedule Risks
N/A — progress measured by completed phases, not time (no estimates).

## Validation Checkpoints
1. **After Phase 1**: CLI runs; core constants + slugify unit-tested.
2. **After Phase 2**: manifest/taxonomy/index validation green on fixtures.
3. **After Phase 3**: full validator green on fixtures; all fixture-coverable T-scenarios pass.
4. **After Phase 4**: `validate traditions/sunni-islam` exits 0 (M2, M3) — the gate that
   proves the format.
5. **Before PR-final**: T1–T19 covered; README author-walkthrough passes.

## Monitoring and Observability
N/A — offline CLI validation tool; no runtime metrics/logging/alerting. (The validator's
own output *is* its observability: located findings + exit codes.)

## Documentation Updates Required
- [ ] `traditions/README.md` (the format doc, M1) — Phase 5.
- [ ] `apps/tradition_validator/README.md`, `apps/README.md` — Phase 5.
- [ ] Spec/plan/review status kept current (Review phase).

## Post-Implementation Tasks
- [ ] (Verify phase) Run `validate traditions/sunni-islam` on the integrated branch.
- [ ] Confirm `uv sync && uv run pytest` green from a clean checkout.

## Expert Review
**Date**: 2026-06-23 — 3-way consult (iter 1).
**Verdicts**: Claude **APPROVE**, Gemini **COMMENT**, Codex **REQUEST_CHANGES** (all HIGH).
**Key Feedback** (all accepted, no pushback):
- README.md / source.md **non-empty** validation wasn't an explicit deliverable
  (Codex, Gemini) → added to Phase 3.
- Phase 4 omitted `traditions/sunni-islam/README.md` and didn't say when the stub is
  finalized (Codex) → added a finalized conformant README to Phase 4 deliverables.
- T15 "oversized" handling lacked a concrete approach (Codex) → defined a
  `MAX_FILE_BYTES` size guard in Phase 3.
- Guide-text fetch source underspecified (Gemini) → Phase 4 now fetches `prompts.py`
  (for `GUIDE`/`STATED`) and `mapping.py` (for taxonomies) explicitly.
- Pydantic strict typing also rejects unquoted int ids (Gemini) → noted in Phase 2.

**Plan Adjustments**: applied the five edits above; phase structure unchanged. Consult
outputs: `1-plan-iter1-{gemini,codex,claude}.txt`; rebuttal:
`1-plan-iter1-rebuttals.md`.

## Approval
- [ ] Expert AI Consultation Complete (3-way)
- [ ] Architect plan-approval gate (pre-approved per the spec-gate brief)

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-06-23 | Initial plan draft | Plan phase | builder spir-1 |
| 2026-06-23 | Plan with multi-agent review (5 edits) | 3-way consult (Codex REQUEST_CHANGES, Gemini COMMENT, Claude APPROVE) | builder spir-1 |

## Notes
- **PR strategy:** per Issue #1 + the architect, phases ship as **git commits within the
  single PR #2**, not as separate PRs. The PR opened with the spec and grows with each
  phase commit on `builder/spir-1`.
- **No second tradition / no harness** (spec §9.4). The format is built to generalize;
  only Sunni Islam is instantiated.
- **Test fixtures, not mocks:** every validator behavior is exercised against real
  on-disk fixture trees (spec N3).
