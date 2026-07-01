# Review: workflows-judging-the-judging-

## Summary

Implemented the MultiBench **judging** workflow (`workflows/judging/`, issue #8): an LLM-as-judge
pipeline that scores a subject model's responses to a tradition's scenarios — under the universal
framings (unstated / stated / guided) × the six pressures — against each scenario's
`judge-guidance.md` (anchored to the tradition's `guide.md`), on the canonical **−1…+1** scale
(five values `−1, −0.5, 0, +0.5, +1`).

Four Typer commands over one `--results-dir`:

- **`collect`** — run subjects over the framing × pressure × scenario grid → `sittings.jsonl`
  (4-turn sittings; framing delivered as a per-turn context prefix so judged turns stay blinded).
- **`judge`** — score each sitting with the config-driven panel (default Opus 4.8 + Gemini Flash
  3.5) at both scopes (`turn1`, `full`); one re-judge pass over ≥2-level disagreements; self-
  judgments skipped and recorded → `judgments.jsonl` (+ `judgments_v2.jsonl`, `skipped.jsonl`).
- **`report`** — aggregate to per-scenario results + a tradition-level scorecard (headline,
  steadfastness overall + per-pressure, per-framing, score distribution, inter-judge agreement +
  worst scenario, generic taxonomy breakdowns from the tradition's declared axes, coverage, cost)
  → `report.md` / `report.json`.
- **`run`** — end-to-end `collect → judge → report`.

Delivered across 6 plan phases; **107 tests pass, 2 opt-in `--live` tests** (excluded from CI).

## Spec Compliance

### Musts (M1–M12)
- [x] **M1** CLI with `collect`/`judge`/`report`/`run` + README documenting commands & contracts.
- [x] **M2** Universal framings × six pressures grid (from `tradition_validator.core`).
- [x] **M3** Config-driven judge panel; self-judgments skipped **and recorded** (`skipped.jsonl`).
- [x] **M4** Two scopes (`turn1` baseline / `full` after pressure); steadfastness = full − turn1.
- [x] **M5** Cost aggregation (dated price table, collection + judging, partial-priced flag).
- [x] **M6** Canonical −1…+1 five-value scale; no band names anywhere (per the architect's fully-
  numeric decision).
- [x] **§5.7 config-driven** — all commands take `--config <file.yaml>` (fail-loud YAML override of
  judges/subjects/framings/pressures/scopes/retries); `report` uses the supplied config for correct
  coverage. (Added in the PR review round — see Consultation Feedback.)
- [x] **M7** Generalizes with no code change — taxonomy breakdowns read the tradition's *declared*
  axes; verified on both `sunni-islam` and `taoism` fixtures.
- [x] **M8** Judge anchored to `guide.md` + `judge-guidance.md` (M8a prompt assembly; M8b live
  anchoring test).
- [x] **M9** Reuses `tradition_validator` loaders/models/core (path dep) — no re-parsing.
- [x] **M10** Cell reducer = mean of present judges; one re-judge pass overrides by key.
- [x] **M11** Untrusted transcript placed last, delimited, defanged; injection-hardened.
- [x] **M12** Failed cells resumable → non-zero exit; `report`/`run` never hard-fail on partial data.

### Shoulds (S1–S4)
- [x] **S1** `run` end-to-end on a fixture (mocked integration test).
- [~] **S2** `--batch` mode **deferred** with a documented note (see Technical Debt) — a cost
  optimization, not a correctness gap.
- [x] **S3** Prefix-cache-hit check as an opt-in `--live` test (asserts `cache_read > 0`).
- [x] **S4** `--limit` cheap smoke path.

### Nevers (N1–N5)
- [x] **N1** No large JSON / no new corpus; file-based, reuses the judge seam.
- [x] **N2** Fail-loud on malformed input (`JudgeInputError`, `LoadError`) — no silent degrade.
- [x] **N3** Live tests gated behind `--live`, never in the default suite.
- [x] **N4** Fail-loud on missing credentials (Anthropic key; Gemini key **or** Vertex SA).
- [x] **N5** Read real loader signatures; thin read helpers, never re-parse.

### Tests (T1–T17)
All represented in the suite (scores, core re-export, loaders on real traditions incl. heading
normalization, rubric/prompt assembly, transcript blinding + breakout, providers, judge panel +
skip + re-judge + resume, collector, report math + generic taxonomy + coverage, end-to-end
pipeline). 107 pass.

## Deviations from Plan

- **`report` CLI signature** — the plan sketched three positional args; implemented as
  `report <tradition> --results-dir` (reads all artifacts from the results dir), consistent with
  `collect`/`judge`. Documented deviation; reviewers accepted.
- **New `pipeline.py` module** — `run` is a thin CLI wrapper over `run_pipeline()` (not inline in
  `cli.py`) so the end-to-end path is unit-testable with injected seams. Additive, within scope.
- **`--batch` (S2) deferred** — see Technical Debt.
- No phase-structure deviations; all 6 phases delivered in order as approved.

## Lessons Learned

### What Went Well
- **Injectable provider seams** (`subject_fn` / `judge_fn`) made the entire multi-stage pipeline
  testable with zero live calls — the end-to-end `run` test exercises grid, resume, re-judge,
  coverage, cost, and the M12 non-zero-exit contract deterministically.
- **Reusing `tradition_validator`** (loaders, Pydantic models, universal core) as a path dep kept
  the workflow thin and guaranteed the grid/format stay identical to what the validator gates.
- **The judge seam held** — anchoring to `judge-guidance.md` + `guide.md` needed no code change to
  span traditions that express guidance as proof texts (`sunni-islam`) vs bare numbers (others).

### Challenges Encountered
- **Prompt-injection via the judged transcript**: took three Phase-2 iterations to fully close —
  output-spec-last ordering, then a delimiter-breakout (`</transcript>` inside a turn), fixed with
  a zero-width-space defang + a regression test asserting exactly one real closing delimiter.
- **Fail-fast input handling**: several Phase-3 rounds hardened `_read_sittings` (missing file,
  malformed rows, non-empty-string fields) and the authoritative `tradition` id on judgments.
- **Report scope consistency**: the per-scenario agreement initially mixed scopes; scoped it to the
  same Unstated/full condition as the table it annotates, and rendered per-pressure steadfastness.

### What Would Be Done Differently
- Declare the exact contracts (`sittings.jsonl`/`judgments.jsonl` fields, aggregate formulas) in
  the spec up front — Codex's specify-round COMMENT asked for this, and getting it precise earlier
  would have pre-empted several implement-phase fail-fast rounds.
- Write the transcript-blinding + injection tests in the same pass as the prompt assembly, not as
  a reaction to review.

### Methodology Improvements
- The **iteration-3 safety ceiling** worked as intended: Gemini can't see the worktree, so
  per-phase consult is codex+claude; a lone persistent Codex REQUEST_CHANGES (often a genuine but
  minor point) force-advances rather than stalling, with the rebuttal preserved as audit trail.
  Every such force-advance in this project was accompanied by a real fix committed before advancing.
- Maintaining the cohort **thread file** per phase made assembling this review's consultation
  history straightforward.

## Technical Debt
- **`--batch` mode (S2) deferred.** The judging grid is a natural Anthropic Message Batches
  workload (~50% cost); the default path is synchronous per-cell and resumable. Batch is a future
  cost optimization, documented in `workflows/judging/README.md`.
- **Multi-provider collection deferred** (architect decision): the collector is Claude-only;
  broad GPT/Gemini-as-subject collection is a sibling workflow.

## Consultation Feedback

Per-phase consult was **codex + claude** (Gemini's per-phase sandbox can't see the worktree). The
full 3-way integration CMAP runs at the PR gate.

### Specify Phase (Round 1) — Codex REQUEST_CHANGES, Claude APPROVE
#### Codex
- **Concern**: cell reducer / re-judge combine semantics under-specified. **Addressed**: added
  §5.9 (mean reducer; re-judge overrides by key; persistent disagreement reported, not re-adjudicated).
- **Concern**: prompt-injection handling for judged transcripts missing. **Addressed**: §5.5
  untrusted-transcript-last + delimited (M11/T14).
- **Concern**: skips/failures/coverage report contract incomplete. **Addressed**: §5.9 no-silent-zeros.
#### Claude
- No blocking concerns (APPROVE); verified codebase and surfaced that **#6 had merged** → prompted the rebase.

### Specify Phase (Round 2) — Codex COMMENT, Claude APPROVE
#### Codex (COMMENT, non-blocking)
- **Concern**: define `sittings`/`judgments` contracts mechanically; state aggregate formulas;
  define self-judge matching precisely. **Addressed**: contracts + exact-model-id skip pinned down
  (and later realized concretely in the code + README).
#### Claude — No concerns (APPROVE).

### Plan Phase (Round 1) — Codex REQUEST_CHANGES, Claude APPROVE
#### Codex
- **Concern**: Phase 4 reused the judge provider abstraction. **Addressed**: split into
  `subject_complete` (conversational) vs `judge_complete` (schema-constrained) seams.
- **Concern**: M12 exit-code / partial-data semantics under-assigned. **Addressed**: made concrete
  acceptance items in Phases 3/4/6.
- **Concern**: `workflows/README.md` "proof texts" copy. **Addressed**: Phase 6 corrects it to the
  `judge-guidance.md` + `guide.md` seam.
#### Claude — No concerns (APPROVE); verified loader tuple/model API + dispatcher silent-skip risk.

### Implement Phase 1 — Scaffold (Round 1 RC→CH, Round 2 APPROVE/APPROVE)
#### Codex
- **Concern**: pyproject omitted plan-required deps (`anthropic`, `google-genai`, `pyyaml`).
  **Addressed**: declared them (the approved plan is the contract).
#### Claude — No concerns (APPROVE).

### Implement Phase 2 — Loaders/rubric/prompts (3 rounds)
#### Codex
- **Concern**: `load_scenario` didn't check `meta.id` vs folder id. **Addressed**: `LoadError` on mismatch.
- **Concern**: `render_conversation` mislabeled unknown roles. **Addressed**: `ValueError` on unknown role.
- **Concern**: output spec emitted after the transcript. **Addressed**: reordered — transcript last.
- **Concern**: literal `</transcript>` in a turn could break out. **Addressed**: `_defang_transcript`
  (zero-width space) + regression test.
#### Claude — No concerns (APPROVE) across rounds.

### Implement Phase 3 — Providers + judge pass (3 rounds)
#### Codex
- **Concern**: Gemini auth only supported an API key, not a Vertex SA (N4). **Addressed**:
  `_gemini_has_creds` / `_gemini_client` support both; fail-loud when neither.
- **Concern**: self-judgments skipped but not recorded (T5/M3). **Addressed**: `skipped.jsonl` + `load_skips`.
- **Concern**: missing/malformed sittings not fail-fast. **Addressed**: `_read_sittings` raises
  `JudgeInputError` (located by file:line); required non-empty-string fields validated.
- **Concern**: judgment `tradition` from the sitting's optional field could be null. **Addressed**:
  write the authoritative `tradition.id`.
#### Claude (Round 1 COMMENT, then APPROVE)
- **Concern**: Gemini `thinking` configured but not wired. **Addressed**: `ThinkingConfig(thinking_budget=-1)`.
- **Concern**: `parse_verdict` allowed empty `direction`. **Addressed**: require non-empty direction.

### Implement Phase 4 — Collector (Round 1 RC→CH, Round 2 APPROVE/APPROVE)
#### Codex
- **Concern**: `attempts` missing from the §5.6 sittings contract. **Addressed**: `subject_complete`
  returns `(text, usage, attempts)`; collector records `attempts`.
#### Claude — APPROVE; observation folded in: added a `guided`-framing collection blinding test.

### Implement Phase 5 — Report (3 rounds)
#### Codex
- **Concern**: no cost table (§5.8 #6). **Addressed**: dated `PRICES` + `_usage_cost` + cost rows/total.
- **Concern**: subjects/scenarios only from judgments → fully-skipped vanish. **Addressed**: union
  with sittings + skips (shown null, M12).
- **Concern**: per-scenario table not rendered. **Addressed**: added it.
- **Concern**: agreement missing the worst scenario; per-scenario table missing an agreement column
  (§5.8 #3/#5). **Addressed**: per-scenario agreement + worst scenario; Agreement column.
- **Concern (Round 3)**: per-scenario agreement mixed scopes; per-pressure steadfastness computed
  but not rendered (§5.8 #1/#5). **Addressed**: scoped agreement to Unstated/full; rendered a
  "Steadfastness by pressure" table. *(Round 3 was the iteration ceiling; Claude APPROVE. Both
  points were fixed and committed before force-advance.)*
#### Claude (Round 1 COMMENT, then APPROVE)
- **Concern**: "Prophetic-method" heading too Islam-specific. **Addressed**: renamed
  "Counseling-technique use" (M7). **Concern**: T13 fixture gap. **Addressed**: hand-computed
  by_framing + per-pressure steadfastness assertions.

### Implement Phase 6 — End-to-end run + docs (Round 1) — Codex APPROVE, Claude APPROVE
#### Codex — No concerns (APPROVE).
#### Claude — APPROVE; one cosmetic note (an invented "spec §5.10" reference). **Addressed**: removed it.

### Review Phase — PR consult (Round 1) — Codex REQUEST_CHANGES, Claude APPROVE
#### Codex
- **Concern**: §5.7 says the config is overridable by a config file and/or CLI flags, but the CLI
  only accepted `tradition`/`results_dir`/`limit` — the panel/subjects/framings/etc. were fixed to
  `default_config()` unless a caller imported Python internals, missing the config-driven contract.
  **Addressed**: added `config.py::load_config` (YAML, fail-loud, validated against the universal
  core) and threaded a `--config <file.yaml>` option through all four commands.
- **Concern**: `build_report()` reconstructs expected coverage from `config.judges`/`config.scopes`
  defaulting to `default_config()`, so a standalone `report` against artifacts made with a
  non-default panel/scope reports wrong `expected_cells`/`uncovered` — a real user-facing bug once
  the CLI couldn't pass the original config. **Addressed**: the same `--config` flows into `report`;
  a regression test asserts coverage tracks the supplied config (1 judge × 1 scope → 1 expected,
  not the default 4). README instructs passing the same `--config` to `report`.
#### Claude — No concerns (APPROVE).

## Architecture Updates

Routed to the **cold** archive (`codev/resources/arch.md`) — the judging workflow is a subsystem/
reference detail, not an always-on invariant, and the hot tier is at its cap:
- Added **"## The judging workflow"** to `arch.md` (commands, the grid, panel/scopes/re-judge,
  blinding, the injectable seams, M12 exit behavior — anchored to the existing judge-seam section).
- Updated the Repository-layout `workflows/` bullet (`judging/` is now implemented, not "not yet
  migrated in"; each workflow is its own uv project).

No **hot** (`arch-critical.md`) change: the always-on judge-seam fact already covers the binding
ground truth that a future builder must know up front; the workflow's mechanics are on-demand.

## Lessons Learned Updates

Routed to the **cold** archive (`codev/resources/lessons-learned.md`) — these are reusable recipes,
not always-on behavior-changers, and the hot tier is at its cap. Added a **"## Testing LLM
pipelines"** section:
- Put the provider call behind an injectable seam so a multi-stage LLM pipeline is fully testable
  with mocked models (no live API in CI).
- Gate costly/credentialed tests behind an opt-in `--live` pytest flag (addoption + collection
  hook), don't just skip them; add `skipif(no creds)`.
- Verify a judge anchors to *supplied* guidance (not its own prior) with a guidance-flip test.

No **hot** (`lessons-critical.md`) change: the always-on "Gemini per-phase consult can't see the
worktree" and "verify the real user path" lessons already cover the cross-cutting rules this
project reinforced.

## Flaky Tests
No flaky tests encountered. The default suite is deterministic (all providers mocked); the two
`--live` tests are opt-in and credential-gated, excluded from CI.

## Follow-up Items
- **`--batch` mode** (Anthropic Message Batches, ~50% cost) — deferred cost optimization.
- **Multi-provider collection** (GPT/Gemini/etc. as subjects) — a sibling workflow.
- Consider promoting the price table to a small config file if provider prices churn often.
