# spir-54 — multibrowser: AFB before/after explorer

Builder thread. Strict-mode SPIR. Issue #54.

## Goal
Show the #48 MultiWeights result as browsable evidence: for each of 150 AFB (AllFaith
Benchmark) cold-condition items, the vanilla Gemma-4-31B response beside the fine-tuned
(SFT and SFT+DPO) responses, each with the GPT-5.6-Terra 0–4 judge score. Rides #51's
GENERIC raw-results viewer contract as a *second catalog type*, not a viewer rewrite.

## Phase: SPECIFY (in progress)

### Key context gathered (2026-08-08)
- **Architect correction (critical)**: per-item AFB response TEXT does not exist anywhere.
  `eval_afb_probes.py` discards responses after judging (persists `{id, score}` only), #48's
  raw outputs died with its worktree, #58 evaluated the full-grid head only. **#54 requires a
  dedicated collection run**: `EVAL_MODELS=base,sft,dpo-incumbent` through the Modal vLLM eval
  endpoint, script changed to persist response text + Terra judging. Budget ~$25–35,
  pre-authorized by Waleed. Keys: OpenRouter + Anthropic only, NEVER Waleed's personal keys.
  → The issue body's "saved #48 outputs / zero new spend" is SUPERSEDED by this correction.
- **Subjects** = `base` (google/gemma-4-31B-it), `sft` (mb-sft-guided adapter), `dpo`
  (mb-sft-dpo — the #48 shipped INCUMBENT, NOT #58's scaling-null `mb-dpo-full`). Both
  adapters live on Modal volume `gemma-dpo`. Serve script: experiments/58/modal/serve_gemma_eval.py
  (its `dpo=` module currently points at mb-dpo-full — must point at mb-sft-dpo for #54).
- **Instrument**: AFB-150 MIT-vendored at experiments/48/data/input/afb/ (questions.jsonl
  {id,question} ×150, scoring_prompt.json 0–4 template, LICENSE, SOURCE.md). No permanent
  instruments/ home yet — #52 merged it inside experiments/48. questions.jsonl has NO category
  field (paper's Inner Life/Relationships/Worldview split is not in the vendored data).
- **Judge**: gpt-5.6-terra via OpenRouter, official 0–4 scoring_prompt.json, returns
  `{rationale, score}`. NO direction "summary" (unlike #51 verdicts where summary is always present).
- **#51 contract** (`results-raw/README.md`, live on main): catalog-generic manifest declares
  scale/ramp/subjects/judges/conditionAxes/groupBy/scopes/items/presets + two fingerprints.
  Reusable export machinery in workflows/analysis/analysis/export_raw.py (shard writer, size
  ceilings ≤1MB/shard ≤200MB/run, gzip mtime=0 determinism, fingerprints).

### Open genericity questions (drive the spec)
1. AFB has NO `results/` scores tier — how does its run-id get discovered/selected in the SPA?
   (Explore agent tracing this.)
2. Does the viewer assert `results-raw.fingerprint == results.fingerprint`? AFB has no results/
   counterpart to reconcile.
3. Is `verdict.summary` required by the viewer? AFB judge has no direction summary.
4. scale 0–4 sequential vs #51's −1..+1 diverging ramp; center value; band names absent (good).
5. single scope (no pre/post pressure), single condition axis (cold), grouping axis for 150 items.

### Design shape (tentative, pre-consult)
- Data: dedicated collection run → persist {subject, item, condition, question, response,
  terra score+rationale}. Sibling export command reusing #51 shard/fingerprint/ceiling machinery.
- Catalog: scale 0–4, ramp catalog-declared, subjects=3 checkpoints, judges=[terra], single
  scope, conditionAxes=[condition:cold], groupBy=single AFB group (or category if vendored),
  items=150, AFB-appropriate presets (biggest base→dpo lift / still-omitted / over-applied).

### Consult iter-1 (codex + claude, both REQUEST_CHANGES, HIGH conf) — resolved in spec rev
Both verified against code; key findings incorporated:
- **BLOCKER: viewer is A/B, not 3-up.** `RawComparison.tsx` = `a` + optional `b` (two cols). My
  "three side-by-side" + "no render change" were contradictory. → Reframed to A/B default
  (base↔dpo) + subject selector + curated presets carry the 3rd checkpoint (Approach 1). Literal
  three-column grid = Approach 3, DEFERRED to architect (N-up render change).
- **`verdict.summary` + `catalog.fingerprint` are REQUIRED** (rawModel.ts:81,69), not optional as
  I wrote. Exporter must synthesize summary + stamp a self-consistent fingerprint. Fixed.
- **Shipped AFB fixture is the template/oracle**: `lib/rawData.test.ts:45` AFB_CATALOG +
  `routes/rawResults.test.tsx:156` genericity test. Fixes catalog shape: scale{0,2,4} center=2
  (mid-grey at calibration target — anti-"4 is best"), groupBy instrument/afb-150, condition/cold,
  scope/single, judge terra. Subject ids: gemma-4-31b-it, mb-sft-guided, mb-sft-dpo.
- **"Reuse #51 writer" understates scope**: write_dataset (export_raw.py:779) is a MB-specific
  monolith; sibling needs an EXTRACTED generic writer. Success criterion added: results-raw/20260803
  re-exports byte-identical after extraction (drift guard green).
- **Discovery can't naive-merge into loadResultsRuns** (filters null-scores runs); need a separate
  raw-run enumerator + landing that leaves default MB scores run untouched + keeps static MB-vocab
  guard green.
- **Collection**: needs 3-subject path (not just repointed dpo=), resumable/idempotent checkpointing
  + completeness validation (450 cells) before export. Endpoint: keyless short-lived, torn down after.

### Architect ruling (2026-08-08, re-confirm at spec-approval)
- **A/B is the call** (not 3-up). Presets: `base↔dpo` (default headline) + `base↔sft` + `sft↔dpo`.
  Keep the "next to" deviation note so Waleed can override to a literal 3-col grid at the gate.
- **Raw-only discovery approved in scope** — must stay catalog-GENERIC (enumerate results-raw/ runs
  generically; NO AFB vocab in SPA core; genericity guard applies).
Both folded into spec. Wrote iter-1 rebuttal.

### Waleed scope ruling + architect answers (2026-08-08) — spec revised
- **Waleed: vanilla ↔ DPO ONLY.** Two subjects (gemma-4-31b-it, mb-sft-dpo); SFT dropped from run
  AND catalog. Native A/B — no selector, no 3rd checkpoint, no N-up. Single `dpo−base` preset.
  Collection shrinks to EVAL_MODELS=base,dpo-incumbent; 150×2=300 cells; budget ~$17–23 (was $25–35).
  Matches the shipped AFB fixture subject list exactly.
- **Architect answers to my Critical item:** (1) volume VERIFIED — mb-sft-dpo adapter intact on
  gemma-dpo. (2) Ownership: I deploy/hold the Modal endpoint (Modal CLI machine-authed, as #48/57/58),
  tear down after. Keys OPENROUTER_API_KEY + ANTHROPIC_API_KEY from /Users/mwk/Development/fftn/
  taqwabench/.env — read at runtime, NEVER commit/echo. (3) Purged all stale SFT/3-preset/3-subject
  remnants. (4) Important resolved: preservation = commit compact intermediate (APPROVED); preset =
  top-N |dpo−base|, N≤12, tie-break at plan time; summary phrasing at plan time.
- Spec Critical open questions now EMPTY (pre-spend gate resolved). Approach 3 (N-up) WITHDRAWN.

### Next
- Committing revised spec; messaging architect (they'll bring the gate to Waleed).
- Still at spec-approval gate (WAITING). Only a human runs `porch approve 54 spec-approval`. I do not.
