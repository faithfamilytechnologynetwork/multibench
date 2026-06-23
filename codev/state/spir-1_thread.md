# spir-1 — Traditions folder layout spec + tradition validator

Builder thread for Issue #1 / Spec 1. SPIR, strict mode.

## 2026-06-23 — Specify phase: kickoff & research

Porch state on entry: `phase: specify`, iteration 1, no spec on disk (`codev/specs/`
held only `.gitkeep`). So I'm authoring the spec from scratch (not reviewing an
existing one).

Issue has **no `## Baked Decisions` section** — checked. Implicit constraints only
(Python/Typer/uv per CLAUDE.md, validator lives in `apps/tradition_validator/`,
fail-fast/no-fallbacks).

### Research done before drafting
Pulled the real JaleesBench repo (`iaser-ai/jaleesbench`) via `gh api` to derive the
format from a real tradition rather than guess. Key artifacts read:

- `jaleesbench/jaleesbench/data/{probes,proof_texts,chapters}.json` — the actual data
  schemas.
- `jaleesbench/jaleesbench/{prompts,judge,mapping,score}.py` — how the data is consumed.
- `docs/jaleesbench-design.md`, `docs/jaleesbench-authoring-standards.md`,
  `docs/jaleesbench-guide.md` — the conceptual frame + authoring contract.

### Load-bearing findings (drive the format design)
- **probes.json**: `{version, pressures[], probes[]}`. Each probe: `id` (JLS-NNN),
  `title`, `chapter` (locus label), `pillars[]`, `hearts[]`, `proof_texts` (an
  **embedded anchor string** — this is what the judge binds to), `turn1`,
  `pressure_turns{}` (keys == declared pressures), `bab` (source locus #), `islamic`
  (∈ clean|intrinsic|leaky). All 140 probes have all 11 fields. ids unique.
- **The judge anchors to the embedded `probe["proof_texts"]` string, NOT to a lookup
  in proof_texts.json.** proof_texts.json is the *source corpus* (keyed by bab →
  list of `{ref, english, arabic}`), from which each probe's anchor string was drawn.
  Confirmed: probe bab 261 is absent from proof_texts.json yet the probe is valid.
- **Taxonomy is a controlled vocabulary** (mapping.py): `PILLARS` = {courage,
  restraint, justice, patience, cross_cutting}; `HEARTS` = 10 al-Ghazālī states.
  mapping.py *validates probe tags against these sets and raises on unknown labels* —
  this is exactly the validator's core job, already proven in JaleesBench.
- **Framings/pressures/guide live in CODE in JaleesBench** (`prompts.py`: STATED,
  GUIDE, FRAMINGS, the six pressures). For MultiBench's "add a tradition = add a
  directory, not change core" goal, these must move OUT of code INTO the tradition
  dir as data. That's the heart of the refactor.
- Spec 3 in JaleesBench established a **"generic names" principle**: code uses generic
  field names, tradition-specific *values* come from data, never hardcoded. I'm
  applying the same principle to the tradition module schema.

### Design direction (going into the spec)
- Tradition = self-contained dir (skills/plugins inspiration). `tradition.yaml`
  manifest ≈ `SKILL.md` frontmatter. Manifest-driven discovery (`traditions/*/tradition.yaml`).
- Tradition declares its own **taxonomy axes** in the manifest; validator mechanically
  checks probe tags ⊆ declared axes/values (generalizes beyond Islam's pillars/hearts).
- Canonical schema uses generalized field names; Islam values are the instantiation.
- **Key scope call to flag at the gate:** port the Islam *data* into `traditions/islam/`
  (reference case for the validator) — IN scope. The JaleesBench *harness*
  (collect/judge pipeline) — OUT of scope.

Next: write `codev/specs/1-traditions-folder-layout-spec-.md`, commit, signal
SPEC_DRAFTED → porch runs 3-way consult → human spec-approval gate.

## 2026-06-23 — Specify iter 1: spec drafted + 3-way consult

Committed initial spec (`6149e35`). Ran `porch done 1` → 3-way consult (gemini/codex/
claude). **All three: REQUEST_CHANGES, HIGH confidence.** Findings converged tightly —
all genuine WHAT-level (format-contract) gaps, correctly belonging in the spec.

Consensus issues addressed in iter-2 spec revision:
1. `probe_id_pattern` missing from manifest (all 3) — added required field.
2. `stated_framing_sentence` had no home (all 3) — added to manifest, conditionally
   required when `stated` framing present; pressures.json can override. No templated
   default (fail-fast — no fallbacks).
3. `pressures.json` schema undefined (all 3) — defined it + resolved-pressure-set
   precedence rule.
4. `guide.md` REQUIRED vs conditionally-required contradiction (all 3) — now
   CONDITIONALLY REQUIRED.
5. `source_map.json` checked but unspecified (codex, claude) — defined minimal schema;
   updated §6 port to a light reshape.
6. `probes.<lang>.json` sparse-vs-full ambiguity (gemini, claude) — defined sparse
   schema {id, turn1, pressure_turns}.
7. `components` field structure undefined (claude) — defined shape + drift check.
8. `name` vs `id` redundancy (claude) — dropped `name`; kept id + display_name.
9. `--format` vs `--json` inconsistency (claude) — unified on `--format text|json`.
10. JaleesBench data access in sandbox (all 3) — added build prerequisite note
    (gh api proven in research; architect-stage fallback at tmp/jaleesbench-source/).
11. Security/robustness (codex) — added safe-load, symlink-escape rejection, malformed/
    huge-file handling as N-requirements.
12. More tests (codex, claude) — added T9–T12 (bad YAML/JSON, dup taxonomy values,
    components drift, lang-code mismatch).
13. Two `schema_version`s (claude) — clarified module vs bank version relationship.
14. `applies_to` semantics (claude) — added note (informational metadata).

All addressed — no pushback warranted; every finding is a real tightening.
