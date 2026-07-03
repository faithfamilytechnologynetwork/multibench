# spir-8 thread — workflows/judging (the judging workflow)

Issue #8. SPIR strict mode. Builder worktree `.builders/spir-8`, branch `builder/spir-8`.

## Specify phase — started 2026-06-23

### Context gathered
- **Spec 1** (merged) defines the canonical tradition format: `traditions/<id>/` with
  `tradition.yaml`, `guide.md`, `source.md`, and per-scenario folders holding
  `turn1.md`/`scenario.md`, `judge-guidance.md`, `pressures.md`, `probe.yaml`/`scenario.yaml`.
  Framings (unstated/stated/guided) + the six pressures are **universal core**
  (`apps/tradition_validator/tradition_validator/core.py`). Bands/rubric were explicitly
  left OUT of the tradition format (Spec 1 §5.6) — they're a judging concern → this spec.
- **Vocabulary dep #6** (OPEN, not merged): probe→scenario, scenario.md→turn1.md,
  probe_id_pattern→scenario_id_pattern, probes/→scenarios/. **Spec/build against POST-RENAME
  vocabulary**; rebase onto main after #6 merges. Current disk still uses old vocab.
- **JaleesBench reference** (github.com/iaser-ai/jaleesbench, fetched via `gh api`):
  - 5 bands: Burns(−2)/Sparks(−1)/Inert(0)/Scent(+1)/Perfume(+2) — perfume-seller hadith.
  - Judge = LLM-as-judge anchored to per-scenario proof texts (= `judge-guidance.md`),
    3-part prompt for prefix caching (static rubric | per-scenario proofs | conversation).
    JSON verdict: {band, direction, rationale, techniques_used}. V2 boundary rules
    (direction vs manner, deliverable ceiling). 7 teaching techniques tracked.
  - Pipeline: collect (subjects × scenarios × pressures × framings → sittings) →
    score.py (dual judge: claude-opus-4-8 + gemini, 2 scopes turn1/full, re-judge ≥2-band
    disagreements) → judge.py build_report (scorecards, steadfastness, judge agreement,
    pillar/heart/technique/citation breakdowns, by-scenario, cost). Reported scale halved
    (−2..+2 → −1..+1).
- **Claude API facts** (claude-api skill): judge model = `claude-opus-4-8`; structured
  outputs via `output_config.format` (guaranteed-valid verdict JSON); prefix caching
  `cache_control {ttl:"1h"}` (min 4096 tok on Opus, 4 breakpoints); Batch API = 50% cost
  for the grid; uv/Typer per repo conventions.

### Decisions — architect answered (2026-06-25)
1. **Collection scope** → Judge + **minimal Claude-only collector**. Broad multi-provider
   collection (GPT/Gemini-as-subject/Friendli/etc.) deferred to a sibling.
2. **Judge panel** → **config-driven**; DEFAULT = `claude-opus-4-8` + `gemini-3.5-flash`
   (thinking on). Cross-provider (overrides issue's "Claude models" wording). NB: Gemini-as-
   JUDGE is via `google-genai` API — distinct from the consult-CLI Gemini file-access bug.
   Re-judge ≥2-band disagreements; skip self-judgments (judge≠its own subject output).
3. **Bands** → per-tradition allowed but the BINDING CONTRACT is the normalized **−1..+1
   scale**; labels are cosmetic ("the key thing is the range"). Design: 5-band rubric
   (−2..+2 native) → linear /2 → −1..+1 reported. Labels = workflow-side per-tradition
   config (default perfume-seller for sunni-islam), NOT in tradition.yaml (no Spec 1 change).

### Other design calls (decided in spec, gate can adjust)
- Reuse `tradition_validator` (core constants + loaders/models) as a dependency — don't fork
  the universal framings/pressures (issue directive: "don't fork divergently").
- Framing delivered as a **context prefix on every user turn**, never the API system prompt
  (Waleed's JaleesBench ruling: no privileged channel). Reconcile w/ Spec 1's "guide.md =
  system prompt" wording in the spec.
- Judge anchors: construct ← tradition `guide.md`; per-scenario direction ← `judge-guidance.md`;
  universal band rubric + boundary rules. Generalizes JaleesBench's hardcoded GUIDE.

Drafting `codev/specs/8-workflows-judging-the-judging-.md` now.

### Spec iter-1 review + branch rebase (2026-06-25)
- **2-way consult** (codex+claude, porch-driven): **Codex REQUEST_CHANGES (HIGH)**,
  **Claude APPROVE (HIGH)**. Outputs in `codev/projects/8-.../8-specify-iter1-{codex,claude}.txt`.
- **Big discovery:** Claude verified #6 is **MERGED** (`31620e2`). My worktree was cut pre-#6
  and was **16 commits behind origin/main** (old vocab `probes/scenario.md/probe.yaml`).
  → **Rebased `builder/spir-8` onto `origin/main`** (clean, no conflicts; my 3 commits replayed).
  Worktree now post-rename + has **5 traditions** (buddhism, eastern-christianity, judaism,
  sunni-islam, taoism). **Heads-up sent to architect.**
- **Spec revised** to address all feedback:
  - §5.9 NEW — cell reducer = **mean of judges' normalized scores**; re-judge **overrides**
    (1 pass); skips/failures/missing = null/excluded (never 0) + coverage reporting. (Codex)
  - §5.5 — untrusted-transcript / prompt-injection handling. (Codex)
  - cross-ref typos fixed (§6.6→6.2, §6.3→6.1). (both)
  - #6 status → merged; rebase noted (§1/3.1/3.3/6.2/8). (Claude)
  - M8 split into mocked unit check + opt-in `--live` anchoring test. (Claude)
  - structured-output wording softened to provider-specific schema-constrained output. (Claude)
  - M7 + T7 now use a **real** second tradition (taoism) instead of a synthetic fixture.
  - Added M10–M12, T14–T17.
- Sittings contract (§5.6) = the collection↔judging seam; report on −1..+1 (§5.8).

Committed `0d0e06f [Spec 8] Specification with multi-agent review`; wrote iter-1 rebuttal
(`8-specify-iter1-rebuttals.md`); `porch done 8` → re-verify accepted → **spec-approval GATE
reached**.

### Gate: spec-approval — WAITING FOR HUMAN (2026-06-25)
- Porch state advanced to gate_pending, but its auto-`git push` failed (non-fast-forward) —
  expected, because the rebase rewrote history vs the stale remote `builder/spir-8`.
- Fixed with `git push --force-with-lease origin builder/spir-8` (replaced only my own
  superseded pre-rebase commits; verified remote 0/0 with local). Porch's future pushes now
  fast-forward.
- **STOPPED at spec-approval gate.** Did NOT call `porch approve` (human-only). Architect
  notified (heads-up + gate-ready). Awaiting `porch approve 8 spec-approval`.

### Iter-2 revision — architect decision: scores fully numeric (2026-06-26)
Architect instruction (before approving): bands → **fully numeric, no names**. Revised spec:
- Canonical scale = five bare numbers {−1,−0.5,0,+0.5,+1}; **dropped the −2..+2 native layer**
  and the ÷2 step (traditions author on −1..+1, judge matches them).
- §5.3 table = number + tradition-neutral one-line meaning, NO names (Burns/… kept as lineage
  only in §1/§6). §5.4 rubric uses numbers.
- Removed ALL label machinery: §4.3 per-tradition labels, `band_labels` config (§5.7),
  report-time label resolution. `bands.py`→`scores.py`.
- Verdict schema (§5.5): `score ∈ {−1,−0.5,0,+0.5,+1}`. Re-judge trigger restated as ≥2 levels
  (gap ≥1.0). Updated §1, §3.3/§3.4, §4.x, §5.x, §6, §7, §8, §9.1/§9.3/§9.4/§9.5, §10.
- Kept all iter-1 hardening (cell reducer, prompt-injection, coverage), anchoring, collection.
- Gate still PENDING; did not approve. Ran advisory 2-way re-consult on the revision:
  **Codex COMMENT (HIGH)**, **Claude APPROVE (HIGH)** — no blockers. Folded in their minor
  tightenings: mechanical sittings/judgments contracts (§5.6/§5.8), explicit aggregate formulas
  (§5.8), self-judge skip = exact model-id match (§4.4), softened the §4.2 "already author on
  −1..+1" claim (Claude verified files are heterogeneous — sunni JLS-001 has no scores, taoism
  uses band names), canonical technique ids `reads_person…open_door` (§5.4). Outputs:
  `8-specify-iter2-{codex,claude}.txt`.
- Resubmitting revised spec to architect for spec-approval. STILL not self-approving.

### spec-approval APPROVED → Plan phase (2026-06-30)
- **User approved** spec-approval gate (`55185cb chore(porch): 8 spec-approval gate-approved`).
- Architect: rebase onto current main first — **bugfix #17 / PR #18** merged → the 4 non-sunni
  traditions now use **bare numeric** scores in judge-guidance.md (no band names). My branch was
  9 ahead / **137 behind** origin/main.
- **Rebased onto origin/main** (clean; 9 commits replayed; now 9/0). Verified taoism TAO-001 no
  longer has "Like water (+1)" band labels; core.py exports intact; 5 traditions present.
- Synced stale spec facts: §4.2 / §5.3 examples updated to post-#17 ground truth (bare numeric);
  §10 post-approval note added. Approved design unchanged (numeric scale + 3 hardening +
  guided-framing-as-context-prefix, architect-confirmed).
- Force-pushed builder/spir-8 (rebase rewrote history). `porch next 8` → **Plan phase**.

### Plan phase — drafted (2026-06-30)
- `codev/plans/8-...md`: **6 phases** — (1) scaffold + scores core + **test-dispatcher
  registration** (`.codev/checks/test.sh` line for `workflows/judging`→`uv … pytest`, else porch
  silently skips my tests), (2) loaders + rubric + 3-part prompt assembly, (3) providers + judge
  (panel×scope, schema verdict, self-judge skip, ≥2-level re-judge, resume), (4) Claude collector
  → sittings, (5) report (mean reducer, mechanical aggregates, generic taxonomy breakdowns,
  coverage), (6) run + docs + optional batch/`--live`.
- Default tests mock the provider boundary (N3); only M8b anchoring + S3 cache-hit are `--live`.
- All M1–M12 / S1–S4 / N1–N5 / T1–T17 mapped to phases. Plan checks pass (6 phase ids).
- `porch done 8` → plan consult: **Codex REQUEST_CHANGES (HIGH)**, **Claude APPROVE (HIGH)**.
  Folded in:
  - Codex: split `providers.py` → `subject_complete` (collector, plain) vs `judge_complete`
    (schema verdict, safety-off) — the collector was wrongly reusing the judge seam.
  - Codex: M12 exit-code/partial-data made concrete acceptance items in Phases 3/4/6.
  - Codex: Phase 6 corrects `workflows/README.md` "proof texts" → judge-guidance.md+guide.md seam.
  - Claude: `core_ref`→`core_imports`; Phase 2 loaders clarified (compose generic
    load_text/yaml/json + Pydantic models, no tradition-specific loaders exist); cost table minimal/dated.
  Outputs: `8-plan-iter1-{codex,claude}.txt`.
- Committed `fa6ff52 [Spec 8] Plan with multi-agent review`; wrote `8-plan-iter1-rebuttals.md`;
  `porch done 8` → checks pass → **plan-approval GATE reached** (porch auto-pushed
  `1f18df0 gate-requested`; remote 0/0).
- **STOPPED at plan-approval gate.** Did NOT call `porch approve` (human-only). Architect
  notified. Awaiting `porch approve 8 plan-approval`. After approval: `porch next` → Implement
  Phase 1 (scaffold + scores core + test-dispatcher registration).

### Implement Phase 1 — scaffold + scoring core + dispatcher (2026-06-30)
- **Plan APPROVED** by user → `porch next` → implement phase, iteration 1.
- Built `workflows/judging/`: pyproject (uv, hatchling, **path dep on tradition_validator** via
  `[tool.uv.sources]`), `judging/{__init__,__main__,cli,scores,core_imports,config}.py`,
  README stub, .gitignore (results/), tests (scores, core_imports, config, cli smoke).
  - `scores.py`: canonical `(-1,-0.5,0,0.5,1)` + `validate_score` (no snapping) + `mean` (None
    on empty, never 0).
  - `core_imports.py`: re-export tradition_validator.core (M9, no fork).
  - `config.py`: default judges (opus-4-8 + gemini-3.5-flash safety-off) + Claude subjects.
  - `cli.py`: Typer skeleton (collect/judge/report/run stubs fail-loud).
- **Deviation (documented):** declared only deps Phase 1 uses (typer + path dep); provider SDKs
  (anthropic, google-genai) deferred to Phase 3 with lazy imports — keeps early envs minimal,
  tests mock the boundary.
- **Dispatcher:** added `.codev/checks/test.sh` registry line. First run collided
  (test_cli_smoke.py basename clash with validator when pytest ran from repo root) → **scoped
  the line** to `uv --project workflows/judging run pytest workflows/judging`. **31 tests pass.**
- Committed `[Phase: scaffold]`; dispatcher verified (detects workflows/judging, 31 pass);
  `porch done 8` → tests-check pass → impl consult (phase_1).
- **Phase-1 consult:** Codex **REQUEST_CHANGES** (my pyproject deferred anthropic/google-genai/
  pyyaml — a deviation from the approved plan which lists them in Phase 1), Claude **APPROVE**
  (endorsed the deferral, else flawless). Reviewers split on the deviation.
  → **Resolved by honoring the approved plan:** declared `anthropic>=0.40`, `google-genai>=0.3`,
  `pyyaml>=6.0` in pyproject now (the plan is the contract; achieves unanimity). uv.lock updated
  (24 pkgs), 31 tests still pass. Providers.py (Phase 3) will use them.
- Phase-1 re-consult (iter2): **Codex APPROVE + Claude APPROVE** (unanimous) → phase_1 done.

### Implement Phase 2 — loaders + rubric + 3-part prompt (2026-06-30)
- `loaders.py`: `Tradition`/`Scenario` accessors composed from tradition_validator generic
  loaders + strict models (no fork); `_parse_pressures` normalizes `## <pressure>` headings via
  core.normalize_heading; fail-loud `LoadError` on missing/malformed/empty/missing-pressure.
- `rubric.py`: universal RUBRIC (numeric, NO band names; boundary rules; untrusted-transcript
  directive), `TECHNIQUE_IDS` (7 canonical), `verdict_schema()` (score enum = five values,
  techniques enum = the 7).
- `prompts.py`: `judge_prompt_parts` = (static rubric | per-scenario anchor guide+judge-guidance |
  `<transcript>`-delimited conversation + JSON spec); scope trim turn1=[:2]/full; `framing_context`
  (unstated→None, stated→stated_prompt(adherent_noun), guided→guide) for the collector.
- Tests: real sunni + **taoism** (M7, axes departures/te/pivot/register), heading-normalization
  (T6), anchor carries guide+ground-truth (M8a), transcript delimited+untrusted (T14 setup),
  scope trims, fail-loud. **49 tests pass.**
- Phase_2 consult: **Codex REQUEST_CHANGES** (2 fail-fast gaps), **Claude APPROVE**.
  Fixed both: (1) `load_scenario` now fails loud if `scenario.yaml` id != folder/requested id
  (keying integrity); (2) `render_conversation` rejects roles outside user/assistant instead of
  silently labeling ASSISTANT. +2 tests → **51 pass**.
- Phase_2 iter2: **Codex REQUEST_CHANGES** (transcript must be LAST per §5.5; my output-spec
  followed it), **Claude APPROVE**. Fixed: output spec now precedes the `<transcript>` block
  which ends the prompt; +assertion (transcript last). 51 pass.
- Phase_2 iter3: **Codex REQUEST_CHANGES** (transcript breakout: a turn with literal
  `</transcript>` could escape the block), **Claude APPROVE**. Fixed: `_defang_transcript`
  splits the delimiter with a zero-width space; +regression test (only one real closing tag,
  at end). 52 pass.
- Phase_2 reached porch's **iter-3 safety ceiling** → porch **force-advanced** to phase_3
  (`13b1962`). My defang fix (`6089f17`) is committed BEFORE the advance, so phase_2 completed
  WITH it; 52 tests pass. NB: per-phase consult caps at 3 rounds; the architect's PR integration
  CMAP (full 3-way) is the authoritative final review — all 3 codex points (id-match, role
  validation, transcript-last, delimiter-defang) are implemented + tested regardless.
- **phase_1 ✓, phase_2 ✓** (porch). Now **phase_3: providers + judge pass.**

### Implement Phase 3 — providers + judge (2026-06-30)
- `providers.py`: two seams — `subject_complete` (anthropic-only, plain conversational, folds
  framing prefix onto user turns) + `judge_complete` (anthropic: output_config json_schema +
  1h prefix-cache on rubric/anchor + adaptive thinking; gemini: response_schema + safety-off).
  Lazy SDK imports; fail-loud creds (`_require_env`); bounded retries (`_retry`).
- `judge.py`: `parse_verdict` (validate score off-grid→error, techniques⊆7, non-empty rationale);
  `should_skip` (exact model-id self-judge); `judge_all` (panel×scope, idempotent resume keyed,
  failures left pending + counted → exit nonzero M12); one-pass re-judge over ≥1.0-gap cells →
  `judgments_v2.jsonl`; `load_judgments` overlays v2 over base by key.
- cli `judge` wired. Tests (provider boundary injected, no live API): parse_verdict valid/reject,
  self-judge skip (T5), panel×scope keying (M3), resume (T9), failure counted (M12), re-judge on
  disagreement (T4/T16/M10) + no-rejudge-on-agreement, creds fail-loud (T10), claude-only subjects.
  **70 tests pass.**
- Phase_3 consult: **Codex REQUEST_CHANGES** (Gemini auth only GEMINI_API_KEY not Vertex SA;
  self-judge skips not durably recorded), **Claude COMMENT** (Gemini thinking not wired;
  parse_verdict empty-direction inconsistency). Fixed all four:
  - providers: Gemini auth = Vertex SA (ADC) OR GEMINI_API_KEY (`_gemini_has_creds`/`_gemini_client`);
    wired Gemini thinking (`ThinkingConfig(thinking_budget=-1)` when judge.thinking).
  - judge: record skips → `skipped.jsonl` + `load_skips`; `parse_verdict` requires non-empty direction.
  - tests updated (gemini cred = all 3 vars; skip-recording; empty-direction reject). **71 pass.**
- Phase_3 iter2: **Codex REQUEST_CHANGES** (missing sittings file silently empty; required
  sitting fields used before validation → raw KeyError), **Claude APPROVE**. Fixed:
  `_read_sittings` validates the INPUT upfront — missing file / invalid JSON / missing required
  fields / empty turns → `JudgeInputError` located by file:line; output files keep resume
  semantics. +3 tests. **74 pass.**
- Phase_3 iter3: **Codex REQUEST_CHANGES** (judgment `tradition` from optional sitting field →
  could be null; sitting validation didn't check non-empty strings), **Claude APPROVE**. Fixed:
  `_record` writes authoritative `tradition.id`; `_read_sittings` rejects non-string/empty
  subject/scenario_id/pressure/framing. +4 tests. **78 pass.** (iter-3 ceiling → porch
  force-advances; fixes committed first; PR CMAP is final review.)
- **phase_3 ✓** → **phase_4: minimal Claude collector.**

### Implement Phase 4 — collector (2026-06-30)
- `collect.py`: grid subjects×scenarios×pressures×framings → 4-turn sittings via
  `providers.subject_complete`; framing handed as ctx (folded onto user turns by the provider,
  never system prompt); stored turns CLEAN (blinded); `context_prefix` audit-only; idempotent
  resume keyed; `--limit`; failures counted → non-zero exit (M12). Made `providers.ctx_block`
  public; `_fold` prefixes user turns only.
- cli `collect` wired. Tests (subject boundary injected): one-cell clean+blinded (T11), stated
  framing in ctx+prefix not turns, resume no-duplicate, limit caps, failure counted; +_fold tests.
  **85 pass.**
- Phase_4 consult: **Codex REQUEST_CHANGES** (`attempts` field missing from §5.6 sittings),
  **Claude APPROVE** (same `attempts` note + suggest guided-framing test). Fixed:
  `subject_complete` now returns `(text, usage, attempts)` (inline retry counts the try);
  collector records `attempts:[a1,a2]`; +guided-framing collection test + attempts assertion.
  **86 pass.**
- Phase_4 iter2: **Codex APPROVE + Claude APPROVE** (unanimous) → phase_4 done.

### Implement Phase 5 — report (2026-06-30)
- `report.py`: `build_report` — cell reducer (mean of present judges, overlay v2); mechanical
  headline (unstated/full), steadfastness (full−turn1, +per-pressure), per-framing; score
  distribution over per-judge verdicts; inter-judge agreement (exact/within-one-level, ≥2);
  **generic taxonomy breakdowns** from declared axes (M7, works on taoism); seven-technique
  usage; per-scenario; **coverage** (expected vs judged, uncovered, skipped_self — no silent
  zeros). `render_markdown` + `write_report` (report.md + report.json). Computable from partial/
  empty data (never hard-fails).
- cli `report <tradition> --results-dir` wired (reads all artifacts from results_dir —
  documented deviation from the plan's 3-positional-arg sketch; consistent with collect/judge).
- Tests: reducer/headline (T15), steadfastness (T13), distribution basis, single-judge no
  agreement (T12), agreement math, **generic taxonomy on taoism** (T7/M7), coverage uncovered
  (M12), skips counted, write files, empty-partial. **96 pass.**
- Phase_5 consult: **Codex REQUEST_CHANGES** (no cost table; subjects/scenarios only from
  judgments → fully-skipped vanish; per-scenario table not rendered), **Claude COMMENT**
  (same + "Prophetic-method" heading too Islam-specific; T13 fixture gap). Fixed all:
  cost table (PRICES dated + usage_cost, collection+judging rows + total, partial-priced flag);
  subjects/scenarios = judgments∪sittings∪skips (fully-skipped still shown null, M12); render
  per-scenario + cost tables in report.md; heading → "Counseling-technique use" (M7). +tests
  (cost, unpriced-partial, fully-skipped-appears, markdown sections, by_framing+per-pressure T13).
  **101 pass.**
- Phase_5 iter2: **Codex REQUEST_CHANGES** (agreement worst-scenario + per-scenario agreement
  column missing — both from §5.8), **Claude APPROVE**. Fixed: per-scenario agreement (exact%
  over a scenario's ≥2-judge cells) + worst-scenario in agreement; per-scenario table gains an
  Agreement column; markdown worst-scenario line. +test. **102 pass.**
- Phase_5 iter3: **Codex REQUEST_CHANGES** (iter-3 ceiling), **Claude APPROVE** (no issues).
  Both Codex §5.8 points fixed: (1) per-scenario agreement + worst-scenario now scoped to the
  Unstated/full condition so the number matches its "By scenario" table (turn1/stated/guided
  disagreements no longer move an unstated/full row; global exact/within-one stays whole-panel);
  (2) render "Steadfastness by pressure" table in report.md (was in report.json only, §5.8 #1).
  +2 tests. **103 pass.** Porch force-advanced to Phase 6 (audit trail preserved).

## Implement phase_6 — End-to-end run + docs — started 2026-06-30
- New `judging/pipeline.py::run_pipeline` orchestrates collect → judge → report against one
  results_dir, threading sittings→judge→report; subject_fn/judge_fn seams injectable (testable
  fully mocked). Returns `{collect, judge, report, failed}`; `failed` = collect.failed +
  judge.failed → CLI `run` exits non-zero (M12). `run <tradition> --results-dir --limit N`.
- Docs: `workflows/judging/README.md` (commands, sittings/results contracts, env/creds, the
  judge seam = judge-guidance.md + guide.md); fixed `workflows/README.md` judging entry (was
  stale "canonical proof texts" → judge-guidance.md/guide.md seam).
- `--batch` DEFERRED with a documented note (S2); opt-in `--live` M8b anchoring + S3 cache-hit
  tests gated out of the default suite via a `--live` pytest option (conftest hook).
- Removed the now-dead `_not_yet` stub from cli.py (all four commands implemented); repurposed
  the stale "unimplemented fails loudly" smoke test → "bad input fails loudly".
- Tests: +test_pipeline.py (end-to-end mocked, --limit bound S4, M12 collect/judge failure →
  non-zero + report still runs), +test_live.py (2 opt-in, skipped by default). **107 pass, 2
  skipped (live).**
- Phase_6 consult iter1: **Codex APPROVE, Claude APPROVE** (Claude flagged one cosmetic invented
  "spec §5.10" ref → removed). All 6 implement phases done. Porch → **Review phase**.

## Review phase — started 2026-06-30
- Wrote `codev/reviews/8-workflows-judging-the-judging-.md`: spec compliance (M1–M12/S1–S4/N1–N5/
  T1–T17), deviations, lessons, full per-phase consultation feedback, arch/lessons update routing.
- Cold-doc updates (hot tiers at cap): `arch.md` +"The judging workflow" section + fixed the
  workflows layout bullet; `lessons-learned.md` +"Testing LLM pipelines" (injectable seams,
  --live gating, judge guidance-flip anchoring test).
- Opened **PR #20** (`Closes #8`). Ran builder-side 2-way PR consult.
- PR consult iter1: **Codex REQUEST_CHANGES**, **Claude APPROVE**. Two legit §5.7 points:
  (1) config-driven contract not exposed on the CLI (panel/subjects/framings fixed to defaults
  unless importing internals); (2) `report` recomputed coverage from `default_config()` → wrong
  `expected_cells` for artifacts made with a non-default panel/scope. **Both fixed:** added
  `config.py::load_config` (YAML, fail-loud, validated vs universal core) + `--config` on all four
  commands; `report` uses the supplied config for correct coverage. +17 tests (**124 pass**, 2
  live-skipped). Updated README (Configuration section), review doc (PR round + §5.7), arch.md.
- Porch advanced straight to the **pr gate** (review consult is single-pass, not the 3-iter
  implement loop). Surfaced it (`porch gate 8`); STOPPED for human approval.
- **pr gate APPROVED** by the user; architect's 3-way integration CMAP: Gemini+Claude APPROVE
  (HIGH, no blockers), codex 3-way hung (stopped) but the builder-side codex already caught the
  two §5.7 issues (fixed). **PR #20 MERGED** (merge commit `2afc35a`, 2 parents, not squash);
  **issue #8 CLOSED** (auto via `Closes #8`).

## Verify phase — 2026-07-01
- Post-merge integration sanity check on `origin/main`: pipeline.py/config.py/README/review all
  present; dispatcher registry line present; `workflows/README.md` stale "proof texts" copy gone;
  **124 tests pass** (2 live-skipped) against the integrated tree.
- Real acceptance = the architect's live 5-scenarios-per-tradition run (needs creds). Signalled
  `porch done` → verify-approval gate; architect approves after the live run. Builder work done.

## Follow-up bugfix — Gemini judge schema (fix/gemini-judge-schema, 2026-07-02)
- The architect's **live 5×5 run** exposed a real bug the mocked suite + CMAP missed: the Gemini
  judge **400'd on every call** (dual judging fully broken). Two google-genai schema
  incompatibilities: `verdict_schema.score` is a **numeric** enum (Gemini requires STRING enums)
  and the schema carries `additionalProperties` (Gemini rejects it).
- Landed the architect's **validated patch** (did not re-implement) on a fresh branch off
  origin/main: `providers._to_gemini_schema` (recursively strip `additionalProperties`; present
  `score` as a string enum; cast back to float on return); plus a new `--scenarios N` selector
  (collect/pipeline/cli) since `--limit` caps CELLS subject-outer, not scenarios.
- One deviation from the literal patch: removed a stray **unused `import copy`** it added
  (`_to_gemini_schema` uses comprehension, not copy) — cleanup, not re-implementation. Flagged.
- **Regression tests (the mock boundary hid this):** `test_gemini_schema.py` — sanitized schema
  has no `additionalProperties` at any depth, `score.enum` all strings, and **constructs as
  `google.genai.types.Schema`** (raw numeric-enum schema does NOT); `test_collect.py` —
  `scenarios=N` builds the first N scenarios × full framing/pressure/subject grid (both subjects).
- **128 pass, 2 live-skipped.** Next: commit → push → PR (Refs #8) → STOP at pr-ready for the
  architect's integration review + pr gate. No self-approve/merge.
- **PR #24 MERGED** (merge commit `d4a7ac1`, 2 parents). Gemini schema fix + `--scenarios` on
  `main`. verify-approval gate for project 8 still pending the architect's live run.

## JaleesBench fidelity remediation — Plan phase (2026-07-02)
- User (via architect) disappointed: "port, don't redesign" — v1 dropped 2 core JaleesBench
  behaviors (serial collection, `config.concurrency` DEAD; batch judging dropped). Architect ran a
  full 4-agent audit → authoritative remediation ledger. Baked user decisions (NOT relitigated):
  thinking STAYS ON (deviation), FULL restoration (parallel + batch), Gemini stays flash (deviation).
- Prep: merged `origin/main` into stale `builder/spir-8` (non-destructive; resolved the thread
  conflict by union) so the branch has the bugfix + sibling work; 128 tests pass. `porch rollback
  8 plan` (verify→plan; spec stays approved — architect wants only a plan-approval stop).
- **Spec amended** (`[Spec 8][amend]`): promoted parallelism/batch/subject-caching/full-rubric from
  shoulds to REQUIREMENTS **M13–M21**; added §4.6 (execution), §4.7 (port ledger + 2 deviations +
  reframes), §5.4/5.5/5.7/5.8 updates, T18–T27, §10 amendment log.
- **Plan rewritten** (3 remediation phases, architect's phasing): r1 parallel collect+judge (wire
  dead concurrency via bounded ThreadPool + cell-major interleave) + subject-side caching; r2 batch
  judging + live fallback + 0.5× batch cost + gemini thinking-token cost; r3 judge-quality (full
  rubric + 5 worked examples, raw text, gemini diagnostic, v2 re-judge verify) + live verification
  (real-client/schema check in default suite + `--live` smoke run before done) + docs. Port source:
  JaleesBench at `/Users/mwk/Development/fftn/taqwabench/jaleesbench/jaleesbench/` (confirmed present).
- Plan consult iter2 (porch inherited the original plan-iter1 codex-RC across the rollback, so it
  started at iter2): **Codex REQUEST_CHANGES, Claude APPROVE** — all plan-tightening, no design
  changes. Fixed: (1) M21 real-client construction checks distributed per phase — Anthropic subject
  payload (r1), batch submit payload (r2), Gemini schema (r3); (2) M19 `raw` retention made an
  explicit **provider return-shape seam change** (raw text discarded at `json.loads` today); (3)
  `batch-judge submit|collect` CLI + manifest-lifecycle tests explicit in r2; (4) r1 serial-vs-
  parallel = **set-equivalence** (line order non-deterministic).
- **plan-approval APPROVED by the user.** `porch done` → implement phase; porch re-extracted the
  3 remediation phases (r1/r2/r3). Implementing r1→r2→r3, one PR (`Refs #8`). No self-approve/merge.

## Implement phase_r1 — parallel collect+judge + subject caching (2026-07-02)
- `collect.py`: cell-major interleave (scenario/pressure/framing outer, subject inner) + bounded
  `ThreadPoolExecutor(max_workers=config.concurrency)` over per-cell calls, lock-guarded JSONL
  append + scenario cache; concurrency=1 stays serial; resume/limit/scenarios/exit-code preserved.
- `judge.py`: classify self-judge skips first (no API), then fan out the base + re-judge passes
  under `config.concurrency` (same lock pattern).
- `providers.py`: replaced `_fold` with `_subject_messages` — folds framing onto EVERY user turn
  (blinding, §4.5) but sets cache breakpoints on the FIRST user turn only (framing 1h ephemeral +
  turn-1 default TTL), mirroring JaleesBench `collect.py` so turn-2 rereads turn-1 from cache (M16).
- Tests: collect concurrency honored (max in-flight >1, ≤N) + concurrency=1 serial + parallel
  set-equivalence (no dup/loss); judge concurrency honored; `_subject_messages` cache-breakpoint
  contract + real-client-shape check (M21 subject path). **133 pass, 2 live-skipped.**
- Next: commit → `porch done` → per-phase consult (codex+claude) → converge → r2.
- r1 iter1: **Codex REQUEST_CHANGES** (3: weak anthropic real-client check; judge concurrency
  base-only; `rejudge_cells` collapsed to (scenario,scope)), **Claude APPROVE**. Fixed all
  (real-SDK MessageCreateParams validation + reject-test; judge set-equivalence + re-judge-under-
  concurrency; rejudge_cells over the FULL cell key). iter2: **both APPROVE** → r1 done.

## Implement phase_r2 — batch judging + batch/thinking cost (2026-07-02)
- **Fidelity call (flagged to architect):** JaleesBench `batching.py` batches **Anthropic only**;
  Gemini is NOT batched (Vertex has no developer file-batch) → Gemini cells go to the live `judge`
  fallback. So the faithful port = Anthropic Message Batches @0.5× + Gemini live-fallback. Corrected
  the spec's "+ Gemini batch job" wording (§4.6/§4.7/M14) to match the reference.
- New `batching.py`: `submit` (pending Anthropic-judge cells → Message Batches mirroring the live
  request: 2 cached blocks + `output_config` schema + thinking; `batch_state.json` manifest,
  in-flight-manifest exclusion) + `collect` (poll → succeeded verdicts written with `usage.batch=True`;
  errored/unparseable left pending → live fallback; idempotent append). Injectable `client` for tests.
- `cli.py`: `batch-judge submit|collect` sub-app. `report.py`: batch-aware cost (`b_` keys @0.5×,
  `_tokens_in/_out` include batch variants). `providers._gemini_usage`: counts `thoughts_token_count`
  (M18 — thinking is ON so cost was undercounted).
- Tests (`test_batching.py` + report/providers): submit→manifest→collect batch-priced; submit &
  collect idempotency; errored→live-fallback; Gemini not batched; real-SDK batch-request construction;
  batch-judge CLI wiring; 0.5× cost unit + report-level; gemini thinking-token count. **146 pass, 2 live-skipped.**
- Next: commit → `porch done` → per-phase consult → converge → r3.
- r2 iter1: **Codex REQUEST_CHANGES** (live fallback not wired; CLI-lifecycle test missing;
  real-client check stripped output_config), **Claude COMMENT**. Fixed all (collect fallback +
  CLI sittings arg/--fallback; CLI lifecycle test; full batch-Request construction incl
  output_config). iter2: **both APPROVE** → r2 done.
- **Architect + user CONFIRMED** the Anthropic-only batching (Gemini=live fallback); corrected all
  spec/plan wording + logged in the amendment table. Do NOT add developer-API Gemini batching.

## Implement phase_r3 — judge-quality fidelity + live verification + docs (2026-07-02)
- `rubric.py`: restored the FULL deliverables rule (6(i) artifact-sets-ceiling, 6(ii) exit-ramp-
  eligible, 7 worst-of-both) + the **5 worked BOUNDARY EXAMPLES** (de-Islamicized) — M17.
- `providers.py`: `judge_complete`/`_anthropic_judge`/`_gemini_judge` now return
  `(verdict, raw_text, usage)` — **raw verdict text retained** (M19, provider seam change threaded
  through JudgeFn/_judge_pass/_record + batching._rec_from_key + all test fakes); `_gemini_text`
  gives an explicit finish_reason/block_reason **diagnostic** on blocked/empty responses (M18).
- **M20 = no-op (verified):** JaleesBench folds V2_BOUNDARY into the standard judge prompt and
  `rejudge_disagreements` reuses the SAME blocks (the "v2 prompt" docstring is aspirational). Our
  re-judge already reuses `judge_prompt_parts`, so once the boundary rules are in `rubric.py` both
  passes carry them. No stricter v2 prompt to port.
- Tests: rubric worked-examples/full-rule (M17); judgment carries `raw` (M19); gemini blocked
  diagnostic (M18); + the opt-in `--live` end-to-end **run smoke** (M21/T27, default panel incl.
  Gemini). README updated (parallelism/caching/batch/scenarios/deviations). **150 pass, 3 live-skipped.**
- **BLOCKER for T27/M21:** no provider creds in the builder env — the `--live` smoke can't actually
  execute here (skips cleanly). Architect required it RUN before done → flagged; **architect is
  running the full live suite against this worktree with real creds** (option a) and will return
  pass/fail as verification evidence. Done gated on that.
- r3 iter1: **Codex REQUEST_CHANGES** (live smoke not run [→ architect running it]; T21 tested the
  JUDGE path not SUBJECT) + **Claude COMMENT** (`_gemini_judge` annotation). Fixed: added
  `test_live_subject_turn2_reads_cache` (M16/T21, subject turn-2 cache_read>0); annotation →
  `tuple[dict,str,dict]`. **150 pass, 4 live-skipped.**
## ⚠️ STATUS 2026-07-02 (afx send is DOWN — reading this thread is how to reach me)
- **Two infra blockers, both the architect's domain, neither fixable by me:**
  1. **codex consult binary missing** — codev's vendored `@openai/codex` (expects **0.130.0** native
     aarch64) has an EMPTY binary dir; PATH `codex` is **0.139.0** (a JS wrapper, wrong version +
     wrong kind) → NOT a safe drop-in. codev install needs repair (`npm rebuild`/reinstall) to
     restore per-phase codex consults. I did NOT patch global node_modules (shared infra) or
     fabricate a codex verdict.
  2. **`afx send architect` fails** — "Cannot resolve canonical builder id for worktree 'spir-8' …
     no matching builder row in global.db" (issue #1094). I cannot proactively message the
     architect; this thread + the PR body are my only channel out.
- **Live suite: architect ran it, 3/3 PASSED incl. T27 (36-sitting grid, real dual-judge incl.
  Gemini) — M21 satisfied** (evidence: `8-live-verification-evidence.md`).
- **Decision (per architect's explicit "finish consult, porch done, open the single PR"):** opening
  the PR now. r1+r2 fully consulted & converged (codex+claude APPROVE); r3 has Claude APPROVE +
  both codex-iter1 points addressed; the only open r3 item is the codex-iter2 verdict, blocked by
  the missing binary — and the architect runs the full 3-way CMAP (incl. codex) at the pr gate.
- **Porch desync note:** porch is mechanically parked at implement/phase_r3/iter2 ("Run remaining
  consultations (codex)") awaiting the codex verdict it can't get. To reconcile: repair codev →
  the codex consult completes → `porch done`/advance; or accept r3 on Claude-APPROVE + pr-gate CMAP.
- **PR #25 OPEN** (Refs #8): https://github.com/faithfamilytechnologynetwork/multibench/pull/25 —
  r1+r2+r3, 150 pass + architect's live 3/3. PR body surfaces both infra blockers. Over to the
  architect's 3-way integration CMAP + pr gate. NOT self-approving/merging. (afx send still down.)
- **Integration CMAP (architect, on PR #25):** **Claude APPROVE** (HIGH, no blockers); **Gemini
  COMMENT** — its lone issue (ValueError from `resp.text` bypassing the M18 diagnostic) **REFUTED**
  by the architect (google-genai `_get_text` returns None on empty/blocked; my fall-through is
  correct — the raise was legacy `google-generativeai`); **Codex CMAP** hit the same vendored-binary
  ENOENT (workspace infra, being handled).
- CMAP cleanup done: fixed the stale `providers.py` module docstring (2-tuple → 3-tuple seam
  returns). 150 pass. Pushed.
- **porch STILL BLOCKED at implement/r3/iter2 → "Run remaining consultations (codex)".** `check`/
  `done` pass (build complete) but `next` won't advance to the pr gate without the codex verdict,
  which can't run (binary missing). Per architect: reported, NOT patching the global package or
  `.codev/config.json`. **Needs the architect to repair codev (restore the 0.130.0 vendored codex)
  so the r3 codex consult completes → porch advances to review/pr gate**, OR to advance r3 another
  way. Handing off — this is the one thing standing between here and the pr gate.

- r3 iter2 re-consult: **Claude APPROVE (no issues).** **Codex BLOCKED — vendored binary missing:**
  `@cluesmith/codev/node_modules/@openai/codex-darwin-arm64/vendor/.../codex/` is EMPTY
  (first attempt EPIPE, retry `spawn codex ENOENT`). codex ran fine through r3-iter1, so it broke
  recently — a codev package-integrity issue affecting ALL codev consults, not just me. Standalone
  `codex` 0.139.0 IS on PATH but the wrapper invokes the vendored one. NOT reinstalling the global
  package unilaterally (shared infra). Flagged to architect for a decision (fix install / accept on
  Claude-APPROVE + addressed codex-iter1 points / other).
- **codex REPAIRED by architect** (symlinked brew codex into codev vendor path, reversible). Re-ran
  r3 iter2 codex → **REQUEST_CHANGES** on ONE fair point: the new M16/T21 subject-side live cache
  test was added *after* the architect's 3-test live run, so its live `cache_read>0` isn't OBSERVED
  yet (r3 requires it). Codex cleared everything else in r3. **Asked architect to re-run the updated
  4-test live suite** (creds-gated); judge-side cache hit already passed live (same mechanism).
  **Holding porch at r3/iter2** — not force-advancing past a real unverified item. Next: 4/4 live
  result → record evidence → re-consult codex (expect APPROVE) → pr gate.

- **Live suite 4/4 PASSED (architect, 384s, exit 0):** anchoring, judge prefix-cache, **NEW test_live_subject_turn2_reads_cache (M16/T21 subject cache_read>0 OBSERVED live)**, T27 smoke. Codex's iter2 RC point is satisfied. Re-consulting codex → pr gate.

- **r3 iter3: codex APPROVE + claude APPROVE → r3 CONVERGED.** porch advanced to **review phase**. Updated review doc (remediation consultation feedback r-plan/r1/r2/r3 + CMAP + live 4/4 evidence), arch.md (parallel/batch/caching/real-client checks), lessons-learned.md (mock-boundary + porting-fidelity). Next: review checks → surface pr gate → ping architect.

- **Review phase: refreshed the stale-v1 PR consult on the remediated branch → Codex COMMENT (non-blocking; fixed the --limit README note + stale v1 Summary numbers; commit-hygiene explained), Claude APPROVE.** porch reached the **pr gate** (PENDING human approval). Pinged architect. NOT self-approving.

- **pr gate APPROVED (user). PR #25 MERGED** — merge commit `8fa4d26` (2 parents, not squash); issue #8 already closed (no action). **Verify phase:** post-merge integration on origin/main clean (batching/parallel collect+judge/raw text/full rubric all present; 150 pass against merged tree). Surfacing the verify-approval gate — **architect approves it after their full live 5-tradition re-run** (they own verify-approval + cleanup). NOT self-approving.

## COMPLETE — 2026-07-03
- **verify-approval APPROVED (user).** Architect's live 5x5 run passed clean: **900/900 sittings, 2700 judgments, uncovered=0, ~$100.** porch phase = **verified**. SPIR protocol complete for Spec 8.
- Delivered: v1 judging workflow (PRs #20/#24) + JaleesBench fidelity remediation (PR #25, r1 parallel / r2 batch@0.5x / r3 judge-quality+live-verify). All merged to main via merge commits. 150 tests + 4 --live.
- Builder finished. Worktree clean; nothing uncommitted. Handing off to architect for `afx cleanup`.
