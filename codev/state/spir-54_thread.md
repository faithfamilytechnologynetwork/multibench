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

## Phase: PLAN (spec-approval APPROVED by Waleed 2026-08-08)
- Terra judge stands (AFB judge-of-record; keeps headline non-selection-judge-gameable per #48 review). No design change.
- Dispatcher check: `workflows/analysis` IS registered (`uv --project workflows/analysis run pytest`)
  + `apps/multibrowser` (pnpm). Both touched → both tested. `test_export_raw_writer.py` already exists
  = the byte-stability guard for the writer-extraction phase.
- Planned 5 phases (no-spend P1–P4, fixture/mock-tested; P5 = the one-time ~$17–23 run + commit + docs):
  P1 extract generic raw-writer (byte-identical guard on results-raw/20260803);
  P2 AFB collection module (base+dpo, persist text+Terra, resumable/idempotent, completeness=300,
     compact intermediate schema; money-I/O injected, mock-tested; thin experiments/54 runner);
  P3 `analysis export-afb` sibling (intermediate→AFB catalog via P1 writer, synth summary, dpo−base
     preset, fingerprints); P4 SPA generic raw-run discovery + entry point (no AFB vocab, guard green);
  P5 real run + commit intermediate + results-raw/<afb-run-id>/ + verify SPA path + docs/attribution.
  Notify architect before the P5 spend (serving smoke first, reconcile actual spend).

### Plan consult iter-1 (codex + claude, both REQUEST_CHANGES HIGH) — resolved, rebuttal written
Two correctness-critical catches (Claude):
- **Byte-identical guard NOT executable** — 20260803 source roots (report.json/sittings.jsonl) aren't
  committed. Fix P1: golden-hash fixture (recorded pre-refactor) + committed-tier content_fingerprint
  recompute (gunzip the 521 committed shards through the extracted primitive vs the committed manifest).
- **Phase 4 reinvented shipped machinery + landed single-column, 138/150 unreachable.** Fix: reuse
  useRawCatalog + <RawPresets>; add catalog-generic ITEM INDEX (all 150 reachable); links MUST carry
  a=subjects[0]+b=subjects[1] (rawSelection defaults b=null → single column) + two-column assertion;
  SEPARATE rawRunIds enumerator (never loadResultsManifest → no false "manifest not found" notice, maps
  spec NFT-3); extend static MB-vocab guard to the new entry file.
## Plan-approval APPROVED by Waleed (2026-08-08)
- **Ranking: KEEP absolute |dpo−base|** (paper evidence artifact; hiding regressions = curation bias;
  biggest moves in BOTH directions ship). Signed refinement rejected.
- Proceed P1–P4 (no-spend). **P5 requires architect's explicit GO after P4 lands** — message then.

## Phase: IMPLEMENT (P1–P4 no-spend, then P5 gated)

### P1 DONE — extract generic raw-writer (byte-identical)
- New `workflows/analysis/analysis/raw_writer.py`: `RawTierWriter` streaming finalizer
  (add_shard → gz mtime=0 + content-fp accrual; `.content_fingerprint`; `.write(catalog_doc,
  max_shard_bytes=,max_total_bytes=)` validate-before-write + prune) + moved `MAX_SHARD_BYTES`,
  `MAX_TOTAL_BYTES`, `_MANIFEST`, `_json_bytes`, `_require_safe_relpath`, `WriteSummary`.
- `export_raw.py`: re-imports those (keeps them patchable/importable at export_raw scope so the
  existing tests + monkeypatch stay green); `write_dataset` now streams through RawTierWriter,
  builds the MB catalog after the loop, passes ceilings in. Removed dead `gzip` import.
- Executable byte guard (source roots NOT in repo): `test_raw_writer.py` recomputes the committed
  `results-raw/20260803` content_fingerprint from its 519 gunzipped shards → == committed manifest
  value (sha256:ed694f1b…). + unit tests. Full analysis suite: 177 passed, 6 skipped.

### P1 consult iter-1 (codex + claude, both REQUEST_CHANGES HIGH) — resolved
Claude independently diffed pre/post exports hash-for-hash → confirmed byte-identical. Fixes:
- **Byte guard now routes through the primitive + checks gz bytes** (was gunzip-only fingerprint,
  which wouldn't catch a compresslevel/mtime drift). Committed-tier test re-gzips a deterministic
  SAMPLE (~24 shards, `i%step==0`) through `RawTierWriter.add_shard` and asserts
  `shard_bytes(rel)==shipped gz` (gzip drift is global → a sample catches it, keeps it ~1s vs ~17s
  for all 519), plus the full 519-shard content_fingerprint recompute == manifest.
- **Golden-hash fixture: SUBSUMED** by the strengthened committed-tier test (real production bytes
  > self-recorded fixture) — stated explicitly here + in the test docstring per reviewer request.
- **`add_shard` duplicate-relpath fail-fast** added (a second caller exists now).
- **`PRESET_CAP` + `_dedup_per_item` extracted** → new `analysis/raw_presets.py` (`dedup_per_item`),
  generic over the entry shape; export_raw re-imports (keeps names + test import green). Phase 3
  AFB exporter will reuse raw_presets, not MB code.
- Added `shard_bytes()` accessor; direct prune-true/false + total-ceiling + duplicate unit tests;
  fixed stale export_raw module docstring. Full suite: 180 passed, 6 skipped, 3.9s.

---
Other accepted fixes: P1 primitive = streaming finalizer (MB builds catalog after shard loop; carry
limit-gated prune; pull PRESET_CAP+_dedup_per_item); P2 two-state atomic checkpoint (response then
verdict; resume judges-only); pin+record decoding (temp/seed/max_tokens) + reconcile base/dpo dist vs
#48 before commit (base≈0/~1%≥2, dpo~27%≥2, escalate on divergence); intermediate path =
experiments/54_afb_before_after/data/collection.json; exact summary phrasing + ≤80-char word-boundary
label; COPY #58 serve script (never edit its committed file); BLOCKING spend gate (explicit approval,
not a heads-up); runner env uv --project workflows/judging (SDK-free afb_collect); usage→gitignored
run.log. Preset ships as spec's |dpo−base|; signed refinement flagged for plan-approval.
