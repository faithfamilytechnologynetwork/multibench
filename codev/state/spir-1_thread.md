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

## 2026-06-23 — Plan 3-way consult (iter 1)

Verdicts: **Claude APPROVE, Gemini COMMENT, Codex REQUEST_CHANGES** (all HIGH). All
accepted (no pushback), 5 edits, phases unchanged: (1) README.md/source.md non-empty
checks → Phase 3; (2) finalized sunni-islam README.md → Phase 4; (3) concrete oversized
handling (`MAX_FILE_BYTES` guard) → Phase 3; (4) Phase-4 fetch now pulls prompts.py +
mapping.py explicitly; (5) Pydantic-strict-rejects-int note → Phase 2. Logged in plan
Expert Review + `1-plan-iter1-rebuttals.md`. Next: commit, rebuttal via porch, → plan
gate, ping architect (pre-approved).

## 2026-06-24 — Plan gate APPROVED → Implement Phase 1

Architect approved plan-approval; cleared me to run implementation through to completion,
pinging at the pr-ready gate or on a real blocker.

**⚠️ BLOCKER flagged to architect (awaiting decision):** the SPIR skeleton's
implement-phase porch checks are Node defaults (`npm run build`, `npm test`). This is a
Python project, so `porch done 1` will fail those checks every implement phase. Proposed
sanctioned fix: project-local `codev/protocols/spir/protocol.json` overriding ONLY the
implement-phase checks → build = `uv --project apps/tradition_validator run python -c
"import tradition_validator"`, tests = `uv --project apps/tradition_validator run pytest`.
Pinged architect; holding `porch done 1` until resolved.

**Phase 1 DONE (code + tests, committed):** `apps/tradition_validator/` scaffolded —
`pyproject.toml` (typer/pydantic/pyyaml; uv), `core.py` (the universal six pressures +
three framings + STATED_TEMPLATE + identity_signals + `normalize_heading` + required-file
sets + supported schema versions), `cli.py` (Typer `validate`/`validate-all`, `--strict`,
`--format text|json`, Phase-1 structure-only check), `__main__.py`, README stub, tests
(`test_core.py`, `test_cli_smoke.py`). **19/19 tests pass** via `uv run pytest`;
`python -m tradition_validator` works; import-sanity (proposed build check) passes.
Held `porch done 1` pending the check-override decision.

## 2026-06-24 — npm-check confirmed REAL; fixed via .codev/config.json; +Phase 6

`porch done 1` confirmed the npm checks HARD-BLOCK (build: `npm run build` → ENOENT, no
package.json; not a false alarm). Architect (after confirming porch source) authorized the
surgical fix: `.codev/config.json` `porch.checks` (config > protocol, survives codev
updates) — `build: {skip:true}`, `tests: {command:"uv run pytest", cwd:"apps/tradition_validator"}`.
Verified porch honors per-check `cwd` (path.resolve). Applied + committed; re-ran
`porch done 1` → build skipped, tests ✓ (19/19), **BUILD COMPLETE** for phase_1.

**Scope addition (issue #3): Phase 6 = `create-tradition` skill.** Added to the plan
(JSON now 6 phases + prose + M8 + dep map). The skill walks an author through scaffolding
traditions/<id>/ and runs `tradition_validator validate` as the final step, using
sunni-islam as the worked example. Sequenced after port (P4) + docs (P5).

**Porch phase-tracking snag:** porch caches `plan_phases` (5) in status.yaml and only
re-extracts at the plan→implement transition (verified in porch source: next.js/index.js
call extractPlanPhases only on entering implement; rollback-to-plan also). So phase_6 in
the plan FILE isn't yet in porch's tracking. Cheapest fix is NOW (phase_1 build done but
not yet 3-way-consulted): either (a) I rollback to plan + re-approve (re-runs plan consult,
resets phase_1 — code committed so cheap), or (b) architect adds phase_6 to status.yaml
plan_phases directly (their domain; no re-consult). Asked architect to pick before I run
the phase_1 verification (which would be wasted if we rollback).

## 2026-06-24 — Rollback to plan (option a) → Phase 6 reviewed → plan gate (iter 2)

Architect chose (a) the porch-sanctioned rollback (not status.yaml hand-edits). Confirmed
both required commits on PR #2 first (config override `2a12d76`, Phase 6 plan `fa1bf9d`),
then `porch rollback 1 plan`. Porch retained iter-1 review history → opened plan iteration
2. `porch done` → 3-way consult (iter 2); I augmented the `--context` file to direct
reviewers at the new Phase 6.

**Plan iter-2 verdicts: Claude APPROVE, Gemini COMMENT, Codex REQUEST_CHANGES (HIGH)** —
all on Phase 6 details, all accepted: skill-conformance tests go in
`apps/tradition_validator/tests/` (run under porch's pytest), SKILL.md located via
`Path(__file__).parents`; added an end-to-end test (scaffold scratch tradition per skill →
validate exits 0); skill enumerates the six pressure headings + prose-non-empty reminder;
validator command stated run-from-repo-root; description trigger phrasing. Rebuttal:
`1-plan-iter2-rebuttals.md`.

Reached **plan-approval gate (iter 2)**; requested it; pushed (origin==local edea8be);
notified architect. Holding phase_1 verification until after plan re-approval + implement
re-entry (so it isn't reset). On approval porch re-extracts all 6 phases.

## 2026-06-24 — Implement Phase 1 verification + GEMINI IMPL-CONSULT BLOCKER

Plan gate approved → implement re-entry → porch tracks all 6 phases (phase_1 in_progress,
build check skipped via override). Ran phase_1 impl 3-way consult:
- **iter 1:** codex REQUEST_CHANGES (real bug: `validate-all --format json` emitted
  concatenated JSON objects → invalid), claude APPROVE, gemini no-verdict. Fixed: cli.py
  now emits one `{ok, traditions:[...]}` doc; added validate-all tests (23 pass). Committed.
- **iter 2:** codex COMMENT (minor: README run-cwd), claude APPROVE, gemini no-verdict.
  Fixed README cwd. Committed.

**BLOCKER (flagged to architect): Gemini impl consults can't see the worktree.** Its
consult sandbox (`/var/folders/.../codev-consult-*`) is empty and it stalls asking
permission to search the home dir → produces **no VERDICT** → porch's parseVerdict
defaults that to **REQUEST_CHANGES** → `allApprove` is never true → every implement phase
will iterate to the ceiling (`max_iterations=3`) then **force-advance**. (Gemini worked
for spec/plan because that content is inline in the prompt; impl needs file access.)
Codex+Claude (the substantive reviewers) are already satisfied on phase_1.

Fix found in porch source: `.codev/config.json` `porch.consultation.models`
(config > protocol verify.models; accepts a subset or `"none"`). Recommended:
set `["codex","claude"]` to drop the non-functional gemini → clean 2-way impl review,
no force-advances. This is a review-policy change (governance) → architect's call, so I
flagged it and am HOLDING the phase_1 iter-3 consult pending their decision (running it
would just burn consults + force-advance).

## 2026-06-24 — Gemini dropped (option a) → Phase 1 clean pass → Phase 2 built

Architect/user approved option (a). Added `.codev/config.json` `porch.consultation.models =
["codex","claude"]` (merged with porch.checks). On `porch next`, porch re-evaluated phase_1's
codex+claude verdicts under the 2-way policy → **allApprove true → phase_1 COMPLETE (clean,
force_advanced: NONE)**. Architect runs a full 3-way integration CMAP at the PR gate.

**Phase 2 DONE** (schema layer): `findings.py` (Finding+Report, text/json), `loaders.py`
(UTF-8 + yaml.safe_load + json → located findings, no tracebacks), `models.py` (Pydantic v2
closed `extra=forbid` + `strict=True` → catches unknown keys and `no`→bool coercion;
TraditionManifest with id-slug + ==dirname + probe_id_pattern-compiles, TaxonomyAxis
non-empty/no-dup values + applies_to, ProbesIndex), `validator.py` (structure + manifest +
taxonomy + index⟺folders drift), cli.py rewired to the engine, conftest valid-tradition
factory. **40 tests pass** (manifest, index/drift, cli smoke). Real stub sunni-islam fails
gracefully with located errors (ported in Phase 4). Next: `porch done 1` → 2-way consult.

## 2026-06-24 — Phase 2 COMPLETE (2-way) → Phase 3

Phase 2 2-way consult: iter1 codex REQUEST_CHANGES (MEDIUM — extra-folder drift located on
probes/<id>/ not index.json; tests asserted message substrings not file/path/severity) +
claude APPROVE. Fixed: drift now located on index.json at `probes` (spec §8.3 contract);
added `find_finding` helper + tightened drift/id tests to assert severity+file+path. iter2:
**codex APPROVE + claude APPROVE → phase_2 COMPLETE (clean)**. Now at **phase_3** (probe
folders, judge seam, pressures.md, prose non-empty, safety).

## 2026-06-24 — Phase 3 built (probe folders, seam, pressures, safety)

Added: `ProbeMeta` model; per-probe validation (id==folder + probe_id_pattern + unique;
tags keys == declared axes, non-empty/no-dup, values ∈ axis); scenario.md non-empty;
**judge-guidance.md non-empty = the seam** (hard error); `pressures.md` parsed via
`normalize_heading` (all six core pressures present, none unknown/dup, each non-empty,
preamble ignored); tradition prose (README/source/guide) non-empty; unexpected probe
files → warning; safety: `MAX_FILE_BYTES` size guard (loaders) + symlink-escape rejection
(validator). conftest now scaffolds complete valid probe folders. **60 tests pass**;
end-to-end CLI validates a complete tradition (exit 0). Next: `porch done 1` → 2-way consult.

## 2026-06-24 — Phase 3 COMPLETE (3 iters) → Phase 4 (port)

Phase 3 2-way consult took 3 iters: iter1 codex RC (symlink guard only covered .md reads,
not yaml/json; missing prose/guide tests) + claude COMMENT (T5/T13/empty-prose tests) →
fixed (guard all loads, fullmatch id, +test_prose, T13, file-symlink test; 66 tests);
iter2 codex RC (duplicate-id only flagged 2nd occurrence; T13 wants both named) → fixed
(track first file, emit on both); iter3 **codex APPROVE + claude APPROVE → phase_3
COMPLETE**. Porch cadence note: after a rebuttal, it takes TWO `porch done`s (one records
prev-iter history + bumps, one marks new-iter build complete) before `porch next` gives
the consult. Now at **phase_4** — port Sunni Islam (140 probes) as the acceptance test.
Architect will verify the real tradition.yaml + per-probe structure at the PR gate.

## 2026-06-24 — Phase 4 COMPLETE (port) → Phase 5 (docs)

Built `port_jaleesbench.py` (ast-parses prompts.py/mapping.py — no exec — reading
gitignored tmp/jaleesbench-source/). Generated `traditions/sunni-islam/`: tradition.yaml
(taxonomies from mapping.py PILLARS/HEARTS), source.md, guide.md (prompts.GUIDE), finalized
README.md, probes/index.json, **140 probe folders** (probe.yaml + scenario.md +
judge-guidance.md + pressures.md). **`validate traditions/sunni-islam` → PASS, exit 0
(M2/M3 met)**. 68 tests pass (added acceptance test). Committed 567 files. Phase 4 consult:
claude APPROVE; codex consult initially didn't write output (porch flagged "run remaining
consultations (codex)") → re-ran codex → APPROVE. **Both APPROVE → phase_4 COMPLETE.** Now
at **phase_5** (docs: expand traditions/README.md = M1, app READMEs).

## 2026-06-24 — Phase 5 COMPLETE (docs) → Phase 6 (skill)

Rewrote `traditions/README.md` as the canonical format doc (M1); expanded
`apps/tradition_validator/README.md` (usage + JSON shape + port cmd); updated `apps/README.md`;
added `test_docs.py` doc-drift guard. Phase 5 consult took 3 iters: iter1 (codex RC / claude
COMMENT) stale root-README status → fixed; iter2 (codex RC / claude APPROVE) validator README
claimed bad-path→exit2 but it's exit1 → corrected README + added exit-code test; iter3
**both APPROVE → phase_5 COMPLETE**. 70 tests pass. Now at **phase_6** — the
`create-tradition` skill (final phase).
