# Review: multibrowser — AFB before/after explorer (#54)

## Summary

Shipped the MultiWeights (#48) omission→repair as **browsable evidence**: for each of the 150 AFB
(AllFaith Benchmark) cold-condition items, the vanilla **Gemma-4-31B** response beside the fine-tuned
**MultiWeights (SFT+DPO)** response, each with its **GPT-5.6-Terra 0–4** score, riding Spec 51's
generic raw-results viewer as a **second catalog type**. Five phases (extract writer → collection core
→ `export-afb` → SPA discovery → the one-time run), all consult-approved. Total spend **$2.6552** (~8×
under estimate). Headline reproduces: **P≥2 vanilla 1.3% → DPO 21.3%** (mean 0.127 → 0.820).

## Spec Compliance

- [x] Dedicated resumable/idempotent collection, 300 cells, response text + Terra 0–4 (Phase 2, run in Phase 5)
- [x] Collection output preserved durably in-repo (committed intermediate + `results-raw/`) — no re-spend (Phase 5)
- [x] Drop-in `results-raw/afb-20260808/` via a **sibling exporter reusing the extracted writer**; byte-stable re-export (Phases 1, 3)
- [x] Catalog validates against the #51 schema; loads with **no** render/model/parser/color change (Phases 3, 4; cross-language test)
- [x] Reachable via a **first-class in-app entry point** (`/raw/<runId>` + Explorers), not a hand-typed URL (Phase 4)
- [x] Before/after legibility: A/B columns + Terra scores/rationales + a deterministic `|dpo−base|` preset (Phases 3, 4)
- [x] Licensing/hygiene: AFB MIT © CEFE-AI attributed; no usage/raw/timestamps shipped (Phases 3, 5)
- [x] Touched suites green via `.codev/checks/test.sh` (analysis 232, multibrowser 308); docs updated
- [~] **Deployed-path (Railway) verification** — formally moved to **post-merge Verify** (architect sign-off, plan Change Log 2026-08-12); pre-merge stand-in = the real-committed-data RTL render test

## Deviations from Plan

- **Scope narrowed to two subjects (vanilla ↔ DPO only)** at spec time (Waleed) — dropped the SFT
  checkpoint; the viewer's native A/B shape made the "3-up vs A/B" question moot.
- **Ramp is diverging (center-grey), not the plan's literal "sequential dark→mid→light"** — the
  `center:2 → grey` + anti-"4-is-best" intent requires a grey center; architect-accepted (Change Log).
- **18 items re-collected** after an encoding fix (mojibake in the vendored instrument) — a second,
  architect-approved short endpoint uptime; the vendored `questions.jsonl` was fixed forward.
- **Deployed-path check → post-merge Verify** (Change Log 2026-08-12).

## Consultation Feedback

Per-phase consult was `[codex, claude]` (Gemini can't see the worktree here). Every phase reached
**both-APPROVE**; the substantive rounds:

### Specify / Plan (gated)
- Both REQUEST_CHANGES → **Addressed**: viewer is A/B not 3-up (reframed); `summary`/`fingerprint`
  schema-required (fixed); "reuse the writer" is a real extraction (added a byte-identical guard);
  discovery needs a separate enumerator (not `loadResultsManifest`); collection needs two-state
  resumability + decoding pinning + #48 reconciliation.

### Phase 1 (extract writer)
- "Byte guard not executable (source roots uncommitted)" → **Addressed**: golden fixture + a
  committed-tier `content_fingerprint`/gz-byte recompute through the extracted primitive.
- "Primitive signature self-contradictory" → **Addressed** (streaming finalizer). `PRESET_CAP`/dedup
  extracted → `raw_presets`.

### Phase 2 (collection core)
- "Mid-pass failure discards completed paid work" → **Addressed**: drain-and-persist, raise after;
  resume re-issues only failed cells. Strict judge contract + checkpoint integrity; usage race → lock.

### Phase 3 (export-afb)
- "Catalog can mislabel provenance" → **Addressed**: exact subjects/order + judge validated.
  "Fingerprint omits rationale" → **Addressed**: use the canonical `fingerprint_line` (score +
  direction + rationale); `content_fingerprint` adds transcript coverage; label ≤80 incl. ellipsis.

### Phase 4 (SPA discovery)
- "Landing flashes 'not found' while SHA loads; source note as a top banner" → **Addressed**: mirror
  `RawResultsPage` (spinner on sha/catalog loading, source notes → footer). Two-column links carry a+b.

### Phase 5 (the run)
- Both verified the science; **Addressed**: mojibake re-collection (architect-approved), exact
  dashboard spend ($2.0928 Modal + $0.5624 Terra), MIT attribution in the manifest, raw-only back-link
  fix, real-committed-data RTL render test. **N/A / moved**: deployed-path → Verify (architect sign-off).

No COMMENT verdicts; no `CONSULT_ERROR`.

## Lessons Learned

### What Went Well
- **Reusing the #51 generic contract paid off** — a whole non-MB dataset shipped with *zero* viewer
  render/model/parser/color change; the one real SPA change was small (discovery + a landing).
- **Consult caught two correctness bugs I'd have shipped**: the A/B-vs-3-up contradiction, and the
  concurrent drain discarding paid work. The adversarial per-phase review earned its keep.
- **Spend came in ~8× under estimate** ($2.66 vs $17–23) — conservative estimates + resumable
  collection (the failed warmups cost pennies, not re-runs).

### Challenges Encountered
- **Modal cold-start 303s** cost two collection attempts before I switched to a polling POST warmup
  (now a lessons-learned entry).
- **Mojibake in the vendored instrument** surfaced only in Phase-5 review — a reminder to eyeball the
  *rendered* artifact, not just the pipeline.

### What Would Be Done Differently
- Eyeball a sample of the actual prompts/labels earlier (the mojibake would have been caught in Phase 2).

### Methodology Improvements
- The per-phase `[codex, claude]` consult with a written rebuttal per round worked well; nothing to change.

## Architecture Updates

- Routed: **hot** — `arch-critical.md` raw-tier fact **extended** (edited in place, no new line → cap
  respected): the generic byte-stable writer + preset helpers are extracted to
  `analysis.raw_writer`/`raw_presets`; a **raw-only** dataset (no `results/` tier) is a sibling
  `export-afb` reusing them, discovered via `rawRunIds` → a first-class `/raw/<runId>` landing.

## Lessons Learned Updates

- Routed: **cold** — `lessons-learned.md` § Testing LLM pipelines: a scale-to-zero Modal
  `@modal.web_server` returns **303 during the vLLM cold start**; poll a POST inference call until 200
  before the collection so no per-call timeout races the cold start (GET `/v1/models` is a poor probe).

## Flaky Tests

No flaky tests encountered.

## Follow-up Items

- **Verify phase**: deployed-path check on Railway after merge + `railway up` (the discovery UI is new
  SPA code; confirm Explorers → `/raw/afb-20260808` → item two-column + clean GitHub fallback, no false
  coherence notice).
- Link this artifact from the MultiWeights paper's repo/browser once live, **carrying the greedy-decoding
  caveat** next to the headline.
- (Optional) the #58 copy of `afb/questions.jsonl` has the same pre-fix encoding bug — a separate cleanup.
- (Optional) Explorers list shows the bare run id; a dataset-title label is a one-line follow-up if wanted.
