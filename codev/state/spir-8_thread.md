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
- Next: commit, rebuttal, re-verify (iter2) → Phase 4.
