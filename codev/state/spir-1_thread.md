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

Committed `[Spec 1] Specification with multi-agent review` (`00cb2fc`), wrote rebuttal,
ran `porch done 1` → reached **spec-approval gate**, ran `porch gate 1`, notified
architect. Stopped and waited (strict mode — did NOT self-approve).

## 2026-06-23 — Spec gate feedback: MAJOR restructure (iteration 2)

Architect relayed user gate feedback (saved verbatim at
`codev/projects/1-.../spec-revision-brief.md`). **Top priority / approval condition:
file-based Markdown structure — the user hates large JSON.** This is a big reshape, not
a tweak. Changes incorporated:

1. **File-based format** — prose → Markdown; metadata → small YAML; only JSON is the
   tiny `probes/index.json`. No probes.json/proof_texts.json mega-blobs.
2. **`islam` → `sunni-islam`** — did the `git mv` on the branch, updated the stub
   README (now "Sunni Islam", notes the Sunni source) + root README link. Kept `JLS-`.
3. **Framings & pressures → universal core** — removed from per-tradition contract;
   kept `adherent_noun` (Stated template input) + `guide.md` + per-probe `pressures.md`.
4. **Probes are folders** — `probes/<JLS-NNN>/{probe.yaml, scenario.md,
   judge-guidance.md, pressures.md}` + `probes/index.json`; discovery globs `probes/*/`
   with an index⟺folders drift check.
5. **Removed** `source_map.json` (overkill), all multilingual (`languages`/variants/
   `translations`), and the `proof_texts.json` corpus.
6. **Seam strengthened** — per-probe `judge-guidance.md` is now unambiguously the
   judge's binding ground truth (no corpus to drift from).

Rewrote the whole spec (cleaner than piecemeal). Open question #1 now RESOLVED
(universal core), #3 DESCOPED (no multilingual). traditions/README.md full expansion is
M1 (Implement-phase) — left as-is for now; spec is the authoritative format doc for the
PR. Next: commit, re-run 3-way consult, return to spec-approval gate.

On approval: user pre-approved direction + plan contingent on file-based structure;
**deliverable = open a PR including the spec**, then grow it with plan + implementation
on the same branch.

Committed restructure as `[Spec 1] Specification with user feedback` (`3733f40`, after an
amend — first `git add` aborted on a stale `traditions/islam/README.md` pathspec and only
the rename landed; amended to fold in spec/README/thread/brief/rebuttal).

## 2026-06-23 — Iteration-2 consult (on restructured spec)

Porch is parked at `gate_pending` (spec-approval). Per strict mode I did NOT mutate that
state (no rollback/approve/status.yaml edit) — the architect's brief delegated the next
action to me ("re-run your 3-way consult, return to the gate"), so I ran the consult
manually (advisory; the human approves the gate).

**Verdicts: Gemini APPROVE, Claude APPROVE, Codex REQUEST_CHANGES — all HIGH.** Two
approvals. Codex's 5 points + the approvers' minors all converged on small tightenings;
all accepted (no pushback). Key changes: closed schemas (unknown keys = error); exact
`pressures.md` heading normalization; `tags == declared axes` (non-empty, no dupes —
verified vs real bank); M2 requires the COMPLETE 140-probe port; strict YAML typing (no
`no`→false); `--format json` shape; UTF-8; +tests T14–T19. Logged in spec §10 + iter2
rebuttal. Outputs: `1-specify-iter2-*.txt`.

Next: commit, re-notify architect that revised spec + iter2 consult (2× APPROVE) are
ready behind the still-pending spec-approval gate.

## 2026-06-23 — Spec gate APPROVED → PR opened → Plan phase

Architect approved `spec-approval` (file-based structure verified). Two standing
instructions: (1) **plan is PRE-APPROVED** — proceed plan→implementation; message
architect when porch parks at plan-approval and they approve promptly (no user wait).
(2) **Open a PR with the spec immediately** for sharing; grow it on the same branch.

**PR #2 opened:** https://github.com/faithfamilytechnologynetwork/multibench/pull/2
(base `main`, head `builder/spir-1`). Contains spec + rename + review record. Sent URL
to architect. Did NOT run `porch done 1 --pr` (would prematurely signal plan-build done);
will record the PR at the PR/review phase.

Porch advanced to **plan** phase. Writing `codev/plans/1-traditions-folder-layout-spec-.md`
next. Phase shape I'm leaning toward (file-based format → validator → port → docs):
P1 scaffold the validator package + core constants (framings/pressures); P2 core
validation engine + schemas (tradition.yaml/probe.yaml/index.json, taxonomies);
P3 probe-folder + pressures.md + seam checks + findings/report (text+json) + CLI;
P4 port Sunni Islam (all 140 probes) from JaleesBench + validate clean (acceptance);
P5 docs (expand traditions/README.md = M1, apps README). Tests land within each phase.

## 2026-06-23 — Plan drafted

Wrote `codev/plans/1-traditions-folder-layout-spec-.md`: 5 linear phases (scaffold+core →
schema/manifest/index → probe/seam/pressures/CLI → port Sunni Islam (acceptance) → docs).
Tech: Python/uv/Typer/Pydantic v2/PyYAML; closed schemas + strict typing handle the
unknown-key + `no`→bool requirements. Validator built test-first vs fixtures, THEN the
140-probe port is validated clean (M3) as the acceptance test. Porter = one-time module
`tradition_validator/port_jaleesbench.py` run via `python -m` (not a run_* wrapper; not in
the validate CLI) — flagged for consult/architect. Porch checks (plan_exists/phases_json/
≥2 phases) verified. Next: commit, `porch done 1` → 3-way plan consult → plan-approval gate
(pre-approved; will ping architect).
