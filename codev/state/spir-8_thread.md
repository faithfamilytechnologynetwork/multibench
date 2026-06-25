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

Next: commit "[Spec 8] Specification with multi-agent review", then `porch next 8`
(iter-2 consult or gate).
