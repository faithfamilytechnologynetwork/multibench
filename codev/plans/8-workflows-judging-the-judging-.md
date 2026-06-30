# Plan: Spec 8 — `workflows/judging` (the judging workflow)

## Metadata
- **ID**: plan-2026-06-30-workflows-judging
- **Status**: draft
- **Specification**: [codev/specs/8-workflows-judging-the-judging-.md](../specs/8-workflows-judging-the-judging-.md)
- **Created**: 2026-06-30

## Executive Summary

Implement the approved Spec 8 design: a generalizable **LLM-as-judge** that scores an AI
assistant's responses to a tradition's scenarios — under the universal framings
(unstated/stated/guided) and the six pressures — against each scenario's `judge-guidance.md`,
on the canonical **five-number scale `{−1, −0.5, 0, +0.5, +1}`**. The workflow lives at
`workflows/judging/` (uv/Typer Python), reuses `tradition_validator.core` (framings/pressures)
and its loaders/models (no fork), and ships `collect → judge → report` plus an end-to-end `run`.

The build is sequenced so each phase is independently testable against **fixtures + canned
transcripts with the provider boundary mocked** (N3) — no live API calls in the default suite.
Phase order follows the data flow: foundation (scoring core) → judge inputs (loaders, rubric,
prompt) → the judge engine (providers + panel/scopes/re-judge) → the collector → the report →
integration. The three hardening additions the spec carries (schema-constrained verdicts,
self-judge skip, prompt-injection handling) and the Guided-framing-as-context-prefix handling
are confirmed and built in. **Phase 1 also registers `workflows/judging` in the per-builder
test dispatcher** (`.codev/checks/test.sh`) so porch's implement/review tests-check actually
runs this workflow's pytest (otherwise it silently skips — see Notes).

## Success Metrics

Spec criteria (M1–M12, S1–S4, N1–N5) and test scenarios (T1–T17) are the acceptance bar; the
per-phase **Acceptance** sections below map each to its phase. Plan-level rollup:

- [ ] All spec MUST criteria (M1–M12) met; SHOULD (S1–S4) met or explicitly deferred with a note.
- [ ] All test scenarios T1–T17 implemented (default suite mocks the provider boundary; the one
      live check, M8b, is gated behind `--live`).
- [ ] Non-functional: Typer CLI, uv-managed, fail-fast, secrets via env, results gitignored (N1–N5).
- [ ] No coverage reduction in the repo; `workflows/judging` registered in the test dispatcher.
- [ ] PR opened at/after the final implement phase (single PR; phase commits on the branch).

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Scaffold + scoring core + test-dispatcher registration"},
    {"id": "phase_2", "title": "Tradition loading, rubric, and judge-prompt assembly"},
    {"id": "phase_3", "title": "Providers + judge pass (panel, scopes, re-judge)"},
    {"id": "phase_4", "title": "Minimal Claude subject collector"},
    {"id": "phase_5", "title": "Report: per-scenario results + aggregates"},
    {"id": "phase_6", "title": "End-to-end run, docs, and optional batch/live"}
  ]
}
```

## Phase Breakdown

### Phase 1: Scaffold + scoring core + test-dispatcher registration
**Dependencies**: None

#### Objectives
- Stand up `workflows/judging/` as a uv/Typer project that runs (`python -m judging --help`).
- Establish the owned scoring primitives (the five numbers) and single-source the universal core.
- Make porch's tests-check actually run this workflow's suite.

#### Files (create unless noted)
- `workflows/judging/pyproject.toml` — uv project; deps: `anthropic`, `google-genai`, `typer`,
  `pyyaml`, and a **path dependency on `tradition_validator`** (`apps/tradition_validator`);
  `[dependency-groups]` `pytest>=8`; `[tool.pytest.ini_options] testpaths=["tests"]`.
- `workflows/judging/judging/__init__.py`, `__main__.py` (`python -m judging`), `cli.py`
  (Typer app with `collect`/`judge`/`report`/`run` command stubs that parse args and error
  "not yet implemented" — fleshed out in later phases).
- `workflows/judging/judging/scores.py` — the canonical `SCORES = (−1.0, −0.5, 0.0, +0.5, +1.0)`,
  a `validate_score()` (reject anything outside the set; **no snapping**, §5.5), and the
  −1…+1 mean helper used by the reducer/aggregates.
- `workflows/judging/judging/core_imports.py` — thin re-export of `tradition_validator.core`
  (`FRAMINGS`, `PRESSURES`, `STATED_TEMPLATE`, `normalize_heading`, `IDENTITY_SIGNALS`) so the
  workflow never redefines them (M9).
- `workflows/judging/judging/config.py` — defaults: `judges` (claude-opus-4-8 adaptive-thinking;
  gemini-3.5-flash thinking-on, safety-off), `subjects` (claude-opus-4-8, claude-sonnet-4-6),
  `framings` (all 3), `pressures` (six), `scopes` (turn1, full), concurrency/retries/results_dir;
  overridable by file/flags. **No band-label config** (§4.3).
- `workflows/judging/.gitignore` — ignore `results/`.
- `workflows/judging/tests/` — `conftest.py` + tests for this phase.
- **Modify** `.codev/checks/test.sh` — add one registry line:
  `workflows/judging) echo "uv --project workflows/judging run pytest" ;;` (see Notes).

#### Acceptance
- [ ] `uv --project workflows/judging run python -m judging --help` lists the four commands (M1, N1).
- [ ] `scores.validate_score` accepts only the five values; rejects e.g. `0.7`/`3` with a located
      error (T1, T2).
- [ ] `core_imports` re-exports the core constants; a test asserts identity with
      `tradition_validator.core` (M9).
- [ ] The dispatcher line is present and `bash .codev/checks/test.sh` runs this workflow's pytest
      when `workflows/judging` is touched.

#### Test Plan
- **Unit**: `scores` validation (T1/T2); `config` defaults; `core_imports` re-export identity (M9).
- **Integration**: CLI `--help` smoke (Typer app loads).

#### Risks
- **Path dependency on `apps/tradition_validator` mis-resolves under uv.** → Use a uv path
  dependency to the app dir; a CLI `--help` + an import test in CI catches it immediately.

---

### Phase 2: Tradition loading, rubric, and judge-prompt assembly
**Dependencies**: Phase 1

#### Objectives
- Read a tradition's judge inputs via `tradition_validator` (no re-implemented parsing, N5).
- Encode the universal rubric (five-level meanings, boundary rules, seven technique ids, verdict
  schema) and assemble the 3-part, cache-ordered, injection-safe judge prompt — all without any
  live API call.

#### Files (create)
- `workflows/judging/judging/loaders.py` — tradition-specific accessors **composed from**
  `tradition_validator`'s **generic** loaders (`load_text`/`load_yaml`/`load_json`, which return
  `(data, error)` tuples) + its Pydantic models (`TraditionManifest`, `ScenarioMeta`,
  `ScenariosIndex`, `TaxonomyAxis`) with path construction — *not* pre-existing tradition-specific
  loaders (none exist). Reads `guide.md` (construct), and per scenario `turn1.md`,
  `judge-guidance.md`, `pressures.md` (sections keyed via `core.normalize_heading`),
  `scenario.yaml` (tags/identity_signal), `tradition.yaml` (declared `taxonomies`,
  `adherent_noun`). Single-sources format parsing (N5).
- `workflows/judging/judging/rubric.py` — the universal rubric text (§5.4, de-Islamicised:
  "the tradition" / "the supplied guide/ground truth"), the five-level meanings (§5.3), the
  boundary rules, the anchoring instruction, the **seven canonical technique ids**
  (`reads_person`, `engages_reason`, `gentleness`, `gradualism`, `exit_ramp`, `proportion`,
  `open_door`) as the `techniques_used` validation set, and the verdict JSON schema
  (`{score, direction, rationale, techniques_used}`).
- `workflows/judging/judging/prompts.py` — 3-part assembly (static rubric | per-scenario anchor
  = guide+judge-guidance | conversation+output-spec, §5.5); framing **context-prefix** rendering
  (never a system prompt, §4.5/§6.1); **untrusted-`<transcript>` delimiting** + the
  ignore-in-transcript-instructions preamble (§5.5); conversation rendering; `turn1`(`[:2]`) vs
  `full` scoping.

#### Acceptance
- [ ] Given a fixture tradition + a canned sitting, the assembled prompt contains the rubric
      anchoring instruction **and** that scenario's `judge-guidance.md` (M8a, T3).
- [ ] The conversation sits last, inside a delimited `<transcript>` block, with the
      ignore-instructions preamble present (M11 assembly-level; T14 setup).
- [ ] `pressures.md` headings normalize via `core.normalize_heading` to the six ids; the matching
      turn-2 push is selected (T6).
- [ ] Loaders read the tradition only through `tradition_validator` (N5); taxonomy axes come from
      `tradition.yaml`, not hardcoded.

#### Test Plan
- **Unit**: rubric technique-id set; verdict schema shape; framing context-prefix text; scope
  trimming.
- **Integration**: full 3-part assembly over a fixture tradition + canned sitting (no API);
  heading normalization (T6); anchor carries guide + judge-guidance (M8a).

#### Risks
- **`tradition_validator` loader API differs from assumptions.** → Phase 2 starts by reading the
  actual loader/model signatures; if a needed accessor is missing, add a thin read helper in
  `loaders.py` (still single-sourcing parsing) rather than re-parsing files.

---

### Phase 3: Providers + judge pass (panel, scopes, re-judge)
**Dependencies**: Phase 2

#### Objectives
- Call the configured judge panel with schema-constrained output, scoring each sitting at both
  scopes; enforce the score set; skip self-judgments; resume idempotently; run the one-pass
  ≥2-level re-judge override.

#### Files (create)
- `workflows/judging/judging/providers.py` — a shared low-level client/creds/retry layer
  exposing two **distinct seams** (so collection and judging never share the wrong abstraction):
  **`subject_complete`** = ordinary **conversational** completion (plain text; Claude subjects;
  used by the collector, Phase 4) and **`judge_complete`** = **schema-constrained verdict**
  output (provider-specific mechanism; Anthropic 1-hour prefix-cache breakpoints on the two
  stable prompt parts §5.5/S3; Gemini **safety-off** — judging only; adaptive thinking (Claude)
  / thinking-on (Gemini)). Credentials from env with **loud failure** if a configured provider's
  key/SA is absent (N4); bounded retries with backoff, then report + leave resumable (N2).
  Subjects are **never** run safety-off.
- `workflows/judging/judging/judge.py` — for each sitting × judge × scope: build the prompt
  (Phase 2), call the provider, parse+`validate_score` the verdict (hard error outside the five
  values / unknown technique); **skip self-judgments** (judge `model` == subject `model`, exact
  id, §4.4) and record them; write `judgments.jsonl` keyed `sitting_key|judge|scope`
  (idempotent resume, §5.9); the **re-judge pass** (≥2 levels = gap ≥1.0) overriding by key,
  exactly once (§5.9/M10).

#### Acceptance
- [ ] Verdict parsing accepts the five values, rejects others (T1/T2); unknown technique → error.
- [ ] A judge whose model == the subject model is skipped and recorded (T5; M3).
- [ ] A ≥2-level disagreement cell is selected and re-judged once; the re-judgment overrides by
      key (T4, T16; M10).
- [ ] Re-running `judge` skips completed `sitting|judge|scope` cells (T9).
- [ ] `judge` **exits non-zero** if any targeted cell fails after retries, while leaving
      `judgments.jsonl` resumable — failed cells stay pending, never written as a score (M12; N2).
- [ ] A configured provider with no credential fails loudly, naming the env var (T10; N4).
- [ ] Mocked at the provider boundary only; behavior-focused (N3).

#### Test Plan
- **Unit**: verdict parse/validate; self-judge match; re-judge selection (≥2 levels); judgment
  keying.
- **Integration**: judge a canned sitting set with a **mocked panel** → `judgments.jsonl`
  written/keyed; resume is idempotent (T9); missing-credential path (T10).

#### Risks
- **Schema-constrained output differs per provider (Anthropic vs Gemini).** → Encapsulate each
  in `providers.py` behind a uniform "return a validated verdict dict" contract; the plan-level
  detail is resolved here, tests assert the contract not the wire format.
- **Gemini judge availability/credentials in this environment.** → Config-driven panel: a
  Claude-only panel is a valid fallback; fail loudly if a configured provider lacks creds (N4).

---

### Phase 4: Minimal Claude subject collector
**Dependencies**: Phase 3 (reuses `providers.subject_complete`)

#### Objectives
- Produce the sittings contract end-to-end on real data by running **Claude** subjects over the
  grid, framing-blinded, resumable.

#### Files (create)
- `workflows/judging/judging/collect.py` — grid `subjects × scenarios × pressures × framings`;
  4-turn sittings (`turn1` → reply1 → pressure-turn-2 → reply2) **via `providers.subject_complete`**
  (plain conversational completion — *not* the judge verdict seam); framing delivered as a
  **context prefix on every user turn**, never the API `system` (§4.5); **clean blinded turns**
  stored (scenario text only); `context_prefix` retained for audit only; idempotent resume keyed
  `sitting_key`; `--limit` smoke (S4); writes `sittings.jsonl` per the §5.6 contract (required
  vs optional fields).
- Wire `judging collect` in `cli.py`.

#### Acceptance
- [ ] One-cell collection yields a clean 4-turn sitting; framing appears only in `context_prefix`,
      not in `turns` (T11; M2).
- [ ] Sitting JSON matches §5.6 (required fields present; optional/audit fields populated).
- [ ] Resume skips completed cells; `--limit` bounds the run (S4).
- [ ] `collect` **exits non-zero** if any targeted cell fails after retries, leaving
      `sittings.jsonl` resumable (M12; N2).
- [ ] Mocked at the provider boundary (N3).

#### Test Plan
- **Unit**: grid construction; framing-fold (prefix on user turns only); sitting keying.
- **Integration**: collect one cell with a mocked Claude provider → valid blinded sitting (T11).

#### Risks
- **Framing leakage into stored turns** (would un-blind the judge). → A dedicated test asserts
  `turns` contain only scenario text and `context_prefix` carries the framing (T11).

---

### Phase 5: Report — per-scenario results + aggregates
**Dependencies**: Phase 3 (judgments format); exercised with fixtures (full pipeline wired in Phase 6)

#### Objectives
- Reduce judgments to per-cell scores and produce per-scenario results + tradition-level
  aggregates on the −1…+1 scale, with mechanical formulas, generic taxonomy breakdowns, coverage,
  agreement, and cost — generalizing across traditions with no code change.

#### Files (create)
- `workflows/judging/judging/report.py` — cell reducer = **mean of present judges' scores**
  (§5.9/M10); breakdown means = unweighted mean of in-scope cell scores (uncovered excluded,
  never 0); **headline** (unstated, full), **steadfastness** (full − turn1, overall + per-
  pressure), per-framing; **score distribution over per-judge verdicts** (§5.8); breakdowns by
  **declared taxonomy axes** read from `tradition.yaml` (never hardcoded) + seven-technique usage
  + optional citations; inter-judge agreement (exact / within-one-level, ≥2 judges); **coverage**
  (judged X/Y, uncovered, skipped self-judgments — no silent zeros, §5.9/M12); a cost table
  (kept minimal, marked approximate/dated); writes `report.md` + `report.json`.
- Wire `judging report` in `cli.py`.

#### Acceptance
- [ ] Mean reducer + aggregate math match hand-computed fixtures (T13, T15); two-judge cell
      `+1.0,0.0` → `+0.5` (T15).
- [ ] Score distribution is taken over per-judge verdicts (§5.8).
- [ ] Breakdowns use the tradition's **declared** axes; verified on a **real second tradition**
      (`taoism`, different axes) with no code change (T7; M7).
- [ ] A fully-skipped cell is null/excluded and counted uncovered — not 0 (T17; M12).
- [ ] Single-judge config: report produced, no agreement/re-judge (T12); ≥2 judges: agreement +
      re-judge reflected (M6).

#### Test Plan
- **Unit**: reducer; headline/steadfastness/per-framing formulas; distribution basis; agreement;
  coverage tallies.
- **Integration**: report over canned `sittings`+`judgments` fixtures for **two** traditions
  (sunni-islam + taoism) → `report.md`/`report.json` (T7/T13/T15/T17/M5/M7/M12).

#### Risks
- **Off-grid cell means polluting the score distribution.** → Distribution is defined over
  per-judge verdicts only (§5.8); a test asserts cell means never enter the distribution.

---

### Phase 6: End-to-end run, docs, and optional batch/live
**Dependencies**: Phases 1–5

#### Objectives
- Wire the full pipeline, document usage, and close the remaining SHOULD/opt-in criteria.

#### Files
- **Modify** `workflows/judging/judging/cli.py` — `run` = `collect → judge → report` for a
  tradition (S1).
- **Create** `workflows/judging/README.md` — how to run; the sittings/results contracts; env/creds.
- **Modify** `workflows/README.md` — point the "judging" entry at the workflow **and correct its
  copy**: judging scores against each scenario's `judge-guidance.md` (+ the tradition's
  `guide.md`), **not** "canonical proof texts" (the spec's binding seam — current wording is stale).
- **Optional**: `--batch` mode (Anthropic Message Batches, ~50% cost) **or** a clear deferral
  note (S2); an opt-in **`--live`** anchoring test (M8b) and a prefix-cache-hit check (S3),
  both outside the default mocked suite.

#### Acceptance
- [ ] `judging run <tradition> --limit N` executes the pipeline on a fixture end-to-end (S1);
      `report` **succeeds on partial data** (never hard-fails), printing coverage, and `run`
      surfaces a non-zero exit if `collect`/`judge` had failed cells (M12).
- [ ] `--limit` smoke path works cheaply (S4); README documents commands + contracts (M1).
- [ ] `--batch` implemented or its deferral noted (S2); `--live` anchoring test demonstrates the
      verdict follows supplied guidance against the model's prior when run (M8b); prefix-cache
      hit observed under `--live` (`cache_read_input_tokens > 0`) or documented (S3).

#### Test Plan
- **Integration**: `run` over a fixture tradition with mocked providers (S1); `--limit` bound.
- **Opt-in (`--live`, excluded from default CI)**: M8b anchoring; S3 cache-hit.

#### Risks
- **Live opt-in tests flaky/credential-dependent.** → Gate behind `--live`, never in the default
  suite (N3); skip cleanly when creds absent.

## Dependency Map
```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ─┐
                                    └→ Phase 5 ┴─→ Phase 6
```
(Phase 4 and Phase 5 both depend on Phase 3; Phase 6 integrates all. Phases are committed
sequentially per SPIR.)

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|---|---|---|
| Provider schema-constrained-output API mismatch | M | M | Encapsulate per-provider behind a uniform validated-verdict contract (Phase 3); test the contract, not the wire format. |
| Gemini-as-judge creds/availability in this env | M | M | Config-driven panel (Claude-only fallback); fail loudly on missing creds (N4). |
| `tradition_validator` loader API differs from assumptions | M | L | Read actual signatures at Phase 2 start; add thin read helpers, never re-parse (N5). |
| Framing leakage un-blinds the judge | L | H | Dedicated blinding test (T11); turns store scenario text only. |
| Test dispatcher not updated → tests silently skipped | L | H | Phase 1 adds the registry line; verify `bash .codev/checks/test.sh` runs the suite. |
| Live opt-in tests flaky | M | L | `--live`-gated, out of default CI; skip without creds. |

## Validation Checkpoints
1. **After Phase 1**: CLI loads; score validation + core re-export tested; dispatcher runs the suite.
2. **After Phase 3**: a canned sitting set is judged (mocked) with skip + re-judge + resume.
3. **After Phase 5**: a full report renders for **two** traditions from fixtures (M7).
4. **Before PR (after Phase 6)**: `run` end-to-end on a fixture; README complete; M1–M12 + S/N
   reviewed; coverage not reduced.

## Documentation Updates Required
- [ ] `workflows/judging/README.md` (usage, sittings/results contracts, env/creds).
- [ ] `workflows/README.md` judging entry.
- [ ] Review-phase: lessons learned + any arch/lessons hot-tier updates (handled in Review).

## Notes

- **Test dispatcher (critical):** `.codev/checks/test.sh` is a per-builder dispatcher keyed by
  touched top-level dir; an **unregistered** `workflows/judging` is *skipped* (exit 0) — so
  porch's implement/review tests-check would pass **without running my tests**. Phase 1 adds the
  registry line `workflows/judging) echo "uv --project workflows/judging run pytest" ;;`.
- **Consultation:** per-phase consult is **codex + claude** (`.codev/config.json`; Gemini's
  per-phase sandbox can't see the worktree). The architect runs the full 3-way integration CMAP
  at the PR gate (diff fed inline). Gemini-as-**judge** (the runtime feature) is unaffected — it
  uses the `google-genai` API directly.
- **PR strategy:** one PR; phase commits land on `builder/spir-8`; the PR opens at/after the
  final implement phase (Phase 6), per the issue. Do not open per-phase PRs.
- **No time estimates** (AI-age); progress is measured by completed phases.
- **Ground truth (post-#17/#18):** the four non-sunni traditions use bare-numeric
  `judge-guidance.md`; `sunni-islam` leans on proof texts + a judge note. The judge reads
  guidance as prose regardless (§5.3), so this doesn't change the code — only the M7/M8 fixtures
  and expectations reference current reality.

## Change Log
| Date | Change | Reason |
|------|--------|--------|
| 2026-06-30 | Initial implementation plan (6 phases) | Spec 8 approved; plan phase |
| 2026-06-30 | Plan-iter-1 consult (Codex REQUEST_CHANGES, Claude APPROVE): split `providers.py` into `subject_complete` vs `judge_complete` seams (collector ≠ judge abstraction); made M12 exit-code / partial-data behavior concrete acceptance items in Phases 3/4/6; corrected `workflows/README.md` "proof texts" → `judge-guidance.md`+`guide.md` seam; renamed `core_ref`→`core_imports`; clarified Phase-2 loaders compose generic loaders + models; cost-table kept minimal/dated | Address review |
