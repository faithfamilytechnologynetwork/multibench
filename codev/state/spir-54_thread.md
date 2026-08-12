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

### P1 consult iter-2 (claude APPROVE, codex REQUEST_CHANGES) — addressed
- Claude APPROVE (ran suite + ruff + probed real tier). Two cleanups + codex's golden-fixture ask done:
  - **noqa F401** on the two intentional re-exports (PRESET_CAP, _require_safe_relpath) — file lint-clean.
  - **_json_bytes canonical form pinned** vs committed bytes (manifest + sampled shard) — catches a
    sort_keys/separators/newline drift that would rewrite every shipped byte with tests green.
  - **Frozen golden-fixture test** (codex AC1): `test_full_export_matches_frozen_golden` exports the
    fixture via write_dataset, compares manifest + every shard hash (over PRE-GZ bytes → zlib-version
    independent) to committed `tests/fixtures/raw_writer_golden.json`; catches catalog/preset/ordering/
    membership drift the self-consistent tests miss. Also drives the primitive end-to-end
    (RawTierWriter.content_fingerprint == exported manifest's).
  - Codex (b) all-519-through-primitive: kept SAMPLE re-gzip (global gzip drift → sample suffices) +
    full 519-shard content_fp recompute; the golden test drives the primitive fully on a small export.
    Rationale in rebuttal (all-519 re-gzip = +16s/check for zero added coverage). Full suite: 181, ruff clean.

### P1 consult iter-3: BOTH APPROVE ✅ (codex + claude; claude re-verified base≡HEAD gz-identical)
Phase 1 DONE. 3 non-blocking notes captured as follow-ups (not re-litigating a unanimous APPROVE):
- **[Phase-3 opening task]** rename `WriteSummary.scenarios` → `shards` (MB vocab in the catalog-agnostic
  primitive) BEFORE adding the AFB CLI consumer. Blast radius: raw_writer.py field+ctor, cli.py:201
  (field + JSON key `"scenarios"`→`"shards"`), test_export_raw_writer.py:45,155. (export.scenarios /
  RawScenario are UNRELATED — don't touch.)
- **[review-doc]** golden fixture committed after the refactor (harmless — base≡HEAD proven out-of-band
  by claude + the committed-tier test carries pre/post weight); golden fixture is 1 item/1 group so its
  docstring's "preset selection/order, membership" claim is covered by test_export_raw_presets, not it —
  soften docstring or widen fixture when convenient.

### P2 DONE — AFB collection module + runner (no spend; mock-tested)
- `workflows/analysis/analysis/afb_collect.py` — SDK-FREE core (injected generate/judge). Two-state:
  pass1 generate (persist response), pass2 judge (persist verdict); atomic full-file replace
  (write .tmp + os.replace); single-writer even under concurrency. Resume skips satisfied state;
  judge-after-generate resumes judge-ONLY (never re-generates). Completeness = 150×2=300 unique cells,
  each response+score∈0..4. Records pinned decoding {temperature:0.0, seed:0, max_tokens:1024}
  (identical both subjects → reproducible). Mismatched checkpoint (run_id/subjects/decoding) refused.
  Intermediate schema at experiments/54_afb_before_after/data/collection.json. `afb_item_id` q0001→AFB-001.
- `experiments/54_afb_before_after/collect_afb.py` — thin runner: builds real OpenAI clients (Modal
  subject endpoint + OpenRouter Terra), pinned decoding, serving smoke, keys from taqwabench/.env
  (never echoed), usage→gitignored run.log. Run via `uv --project workflows/judging run python …`.
- `experiments/54_afb_before_after/modal/serve_gemma_eval.py` — COPY of #58's serve (not edited),
  dpo→/vol/runs/mb-sft-dpo/adapter (incumbent, NOT mb-dpo-full), base+dpo only.
- 11 mock-tests (resume, judge-after-gen resume, idempotence/byte-stable, completeness, bad-score,
  empty-response, mismatched-checkpoint, concurrency, item-id, loader). Full suite 192 passed, ruff clean.
- NO SPEND this phase (runner is wiring; real run is P5). run.log gitignored.

### P2 consult iter-1 (codex + claude, both REQUEST_CHANGES HIGH) — resolved
Both flagged the FLAGSHIP spend bug (claude verified empirically):
- **Mid-pass failure discarded completed paid work + paid for the whole remaining queue**
  (ThreadPoolExecutor shutdown(wait=True) w/o cancel_futures + as_completed raising early). Fixed:
  `_run_pass` now DRAINS all futures, persists every success on the main thread, collects failures,
  raises an aggregate AFTER the drain → resume re-issues only failed cells. Test: concurrent mid-pass
  judge failure persists the other 3 cells; resume issues exactly 1 judge call, 0 generations.
- **Strict judge contract**: score must be a real int 0–4 (reject bool/float/str; `score in (0..4)`
  alone accepted True==1 / 2.0==2) + non-empty rationale. Parametrized rejection tests. Runner's judge
  also raises on non-int/blank-rationale → _retry.
- **Checkpoint integrity**: reject schema_version mismatch, duplicate cells, unknown item (was a bare
  KeyError on flush → now clean error), unknown subject, question mismatch. Tests for each.
- **Usage race**: threading.Lock around the shared usage counters (worker threads). **Retry+progress
  logging** to run.log (was a black box for a paid ceiling-gated run). **len(items)==150 assertion**.
  **#48 decoding-divergence note** logged at start (greedy vs #48 server-default sampling — benign
  for the P5 reconciliation). $ reconciled in P5 from OpenRouter activity + Modal billing (tokens
  logged, not $, since OpenRouter cost needs a separate query — documented, not guessed).
- Full suite 203 passed, ruff clean.

### P2 consult iter-2 (claude APPROVE, codex REQUEST_CHANGES) — addressed
Both converged on one real hole I'd introduced + claude caught a drain edge:
- **Checkpoint-loaded cells bypassed strict validation**: `validate_complete` used `not in VALID_SCORES`
  (accepts 2.0/True) and skipped rationale/response checks → a resumed COMPLETE corrupt checkpoint could
  validate. Fixed: extracted `_bad_score`/`_bad_text`; validate_complete now applies the FULL strict
  contract (int 0–4 not bool/float, non-empty response+rationale). Parametrized tests (2.0/True/blank
  rationale/whitespace+non-str response). Note: a FALSY response self-heals (regenerated) — only
  truthy-invalid is the real bypass.
- **persist raising escaped the concurrent drain** (set_verdict rejecting inside the loop discarded
  other completed futures). Fixed: persist moved INSIDE the try → a persist failure is collected like a
  task failure, others still persist. Test added.
- **Direct missing-cell test** for validate_complete's defensive branch (unreachable via collect).
- **Cost capture**: added OpenRouter `extra_body={"usage":{"include":true}}` → log `usage.cost` (defensive
  getattr → judge_cost_usd) for real per-call USD; $ still cross-checked vs OpenRouter activity + Modal in P5.
- Aligned run-id example to afb-<YYYYMMDD>. Full suite 210 passed, ruff clean.
- **P5 gate TODO**: surface the greedy-vs-#48-sampling decoding divergence explicitly in the spend-gate
  message (claude note 5) — #48 is the reconciliation oracle.

### P3 DONE — analysis export-afb sibling exporter
- FIRST: applied the P1 follow-up rename `WriteSummary.scenarios`→`shards` (raw_writer + cli export-raw
  JSON key + 2 test assertions) — done before adding the 2nd caller, as the P1 reviewer advised.
- `workflows/analysis/analysis/export_afb.py` — intermediate → drop-in results-raw/<run-id>/ catalog via
  the P1 RawTierWriter + raw_presets.dedup_per_item (NO MB code). Catalog matches the shipped AFB_CATALOG
  fixture: scale{0,2,4}, subjects=[gemma-4-31b-it,mb-sft-dpo] (readable labels), judges=[terra/gpt-5.6-terra],
  conditionAxes=[condition:cold], groupBy instrument/afb-150, scopes=[single]. Ramp = cool→grey→warm
  (center grey at target 2 = anti-"4 is best", colorblind-safe, theme-robust). Fixed score→summary map.
  Item label = whitespace-collapsed question ≤80 on word boundary +…. Shard = 2 cells (base,dpo) single-turn
  transcript + terra verdict {score,summary,rationale}. fingerprint = self-consistent combine over verdict
  lines (no cross-tier partner); content_fingerprint from the writer. Preset dpo-base = |Δ| desc, N≤12,
  one/item (absolute per approved spec — biggest moves both directions ship).
- `export-afb` CLI command (intermediate arg, --run-id, --out), mirrors export-raw output.
- 14 tests (catalog shape vs fixture, shard/summary, label truncation, byte-identical re-export, preset
  ranking + cap, invalid-intermediate rejection, missing-subject, size accounting, CLI smoke).
  Full suite 224 passed, ruff clean. Phase 4 renders it in-app against the real parser.

### P3 consult iter-1 (claude APPROVE, codex REQUEST_CHANGES) — resolved
Both converged on provenance + label; addressed all:
- **Provenance validation** (would publish a FALSE claim): the catalog hardcodes subject labels + Terra
  judge, so `_index` now requires subjects EXACTLY `[gemma-4-31b-it, mb-sft-dpo]` (list+order) AND judge
  `openai/gpt-5.6-terra`. Rejection tests (wrong id, reversed order, wrong judge). Resolves the "≥2 subjects
  but preset uses first two" concern too.
- **Label ≤80 INCLUDING "…"** (was 81): reserve 1 char; test asserts ≤80 + hard-cut case.
- **Fingerprint**: added `condition` to the judgment-fp line + documented the intentional #51 two-fingerprint
  SPLIT (fingerprint=score-level judgment identity; content_fingerprint=transcripts+rationale). Codex wanted
  rationale IN the fingerprint — but that breaks the split's purpose; instead I test it: a SCORE change moves
  `fingerprint`, a RATIONALE change moves only `content_fingerprint`. (Rebuttal explains.)
- Ramp center-grey distinct from no-data grey (#AEB6BF→#8B95A1); DIVERGING-vs-plan-"sequential" deviation
  documented in code + plan Change Log (architect ack at PR). CLI catches file/JSON errors→exit 2.
  Promoted `_json_bytes`→public `json_bytes`. Summary map tested 0–4; dup-cell + inconsistent-question tests.
  Full suite 232 passed; my files ruff-clean (html_report.py:407 F541 pre-existing/out-of-scope).

### P3 consult iter-2 (claude APPROVE incl. e2e 150-item CLI run, codex REQUEST_CHANGES) — CODEX WAS RIGHT
- I misread the convention: `analysis/fingerprint.py:_fingerprint_tuple` INCLUDES direction+rationale, and
  BOTH #49/#51 tiers stamp it. So my score-only AFB fingerprint diverged. Fixed: AFB fingerprint now uses
  the CANONICAL `fingerprint_line` (maps condition→pressure slot, summary→direction; includes rationale).
  content_fingerprint still adds transcript/response coverage the judgment fp lacks. Test rewritten:
  score OR rationale change → BOTH fps move; a RESPONSE-text change → only content_fingerprint. 232 passed.

### P4 DONE — SPA generic raw-run discovery + entry point (the one real frontend change)
- `queries.ts`: `rawRunIds(entries)` (regex `^results-raw/([^/]+)/manifest.json$`) + `useRawExplorerRunIds`
  = raw-ONLY runs (results-raw with no results/), from the walked tree only — NEVER via loadResultsManifest
  (so no false "manifest not found", no extra API call, score-tier run list/default untouched).
- `RawRunPage.tsx` (`/raw/$runId` route): catalog-generic landing. useRawCatalog(sha,runId,NULL) →
  dataset title/desc + shipped `<RawPresets>` + a generic item index over catalog.items. Every item link
  carries a=subjects[0], b=subjects[1] (+scope+judge) so it opens TWO-COLUMN (b defaults null→single else).
  All-150 reachable (presets alone = ≤12). MB-vocab-free (all from catalog).
- `IndexPage.tsx`: "Explorers" section lists raw-only runs → /raw/$runId. `router.tsx`: +/raw/$runId route.
- Static guard extended: RawRunPage.tsx added to the MB-vocab file list + new AFB-literal ban
  (afb-150/mb-sft-dpo/gemma-4-31b-it/AFB) on RawRunPage+IndexPage.
- Tests `rawRun.test.tsx` (4): rawRunIds+raw-only filter (unit); landing lists ALL items w/ a+b/scope/judge
  links + reused presets + no false notice; landing on an item renders BOTH columns (VANILLA + TUNED);
  index Explorers lists AFB but NOT a score-tier MB run. Full multibrowser suite 301 passed; tsc clean.

### P4 consult iter-1 (both REQUEST_CHANGES) — resolved
Two real blocking issues:
- **Codex**: landing ignored shaQ.isLoading/error → flashed "not found" while SHA loads + misreported SHA
  failures permanently (catalog query disabled until SHA arrives, so catQ.isLoading alone is false). Fixed:
  spinner on shaQ.isLoading||catQ.isLoading; rate-limit banner + error Notice on shaQ/catQ error (mirrors
  RawResultsPage). SHA-error test (commits→500 → error, not "not found").
- **Claude**: landing rendered kind:"source" notices as a TOP banner → the GitHub-served AFB run (no baked
  bundle, by design) would show a permanent yellow warning. Fixed: split dataNotices/sourceNotices (source
  → unobtrusive footer, matching RawResultsPage/model.ts contract); filter applied to the empty-notice
  fallback too. Test asserts the "no baked bundle" note is ONLY in the footer (getAllByText length 1).
- Also (non-blocking, done): added a **home link** on the landing (dead-end fix) + a **no-new-API-call**
  data-layer test (git-trees called exactly once for traditions+results+explorers). Full suite 304, tsc clean.
- Deferred: Explorers list shows bare run id (not dataset.title) — defensible (avoids N index fetches);
  follow-up if Waleed wants richer labels. Item-page back-link → /results dead-ends for raw-only (P5 real-path).

### P4 consult iter-2: BOTH APPROVE ✅ (claude verified all criteria + diff scope). Phase 4 DONE.
Minor follow-ups for P5: (a) RawResultsPage "← Results" back-link dead-ends for a raw-only run (real-path);
(b) item links rely on parseRawSelection condition default (fine for single cold value); (c) index heading
uses groupBy.label over a flat list. All non-blocking.

## Phase 5 (money/infra) — GATED on explicit architect approval before ANY spend
P1–P4 complete, consult-approved, NO SPEND. Phase 5 = deploy Modal endpoint (serving smoke) → run
collection (~$17–23) → export-afb → commit intermediate + results-raw/afb-<date>/ → deployed-path SPA
verify → docs + AFB MIT attribution. Per plan + global rule: BLOCK on explicit architect GO before spending.
Gate message must flag: decoding greedy (temp=0) vs #48 sampled defaults → #48 distribution reconciliation
may diverge benignly. Also offer: review/merge P1–4 as a first PR before the spend, or authorize spend now.

### P5 SPEND RELEASED (architect, 2026-08-08): GO option (a), one PR. Hard ceiling $30, usage-reconciled in PR.
Both flags ACKED (greedy right; diverging ramp accepted). **CRITICAL GUARDRAIL: the DIRECTION of the DPO
lift must reproduce — if the LIFT ITSELF vanishes, STOP and message before committing anything.** Teardown
the endpoint when COLLECTION completes (not after the PR).

### P5 EXECUTION IN PROGRESS
- Modal endpoint deployed: `multibench-afb-eval-serve` → https://waleedkadous--multibench-afb-eval-serve-serve.modal.run
  (H200, scale-to-zero; adapter mb-sft-dpo re-verified on gemma-dpo volume: adapter_model.safetensors + config).
- run-id = **afb-20260808**. Collection running as background task (warmup curl /v1/models to survive the
  ~10-15min vLLM cold start, then collect 300 cells greedy/cold at concurrency 16). Orchestration log +
  run.log in scratchpad/experiments data. Awaiting completion → then: reconcile vs #48 (STOP if lift gone)
  → export-afb → commit intermediate + results-raw/afb-20260808/ → deploy-verify → docs → TEARDOWN endpoint.

### P5 EXECUTION COMPLETE (data + code committed; deployed-path deferred to post-merge Verify)
- Cold-start quirk: GET /v1/models returned 303 during warmup (correctly did NOT spend). vLLM finished
  loading (Modal logs); POST /v1/chat/completions works for BOTH base + dpo (verified). Re-ran collection
  directly against the warm endpoint → 300/300 cells.
- **Reconciliation vs #48 (architect gate)**: P>=2 vanilla 1.3% → DPO 22.7% (mean 0.127→0.887). LIFT
  REPRODUCES STRONGLY (~17x) — NOT the vanished-lift STOP case. DPO 22.7% modestly below #48 sampled
  ~27-30%, plausibly greedy-vs-sampling. Proceeded (per architect: escalate only if lift vanishes).
- **TEARDOWN**: `modal app stop multibench-afb-eval-serve --yes` → state=stopped, 0 tasks (done right after
  collection, per architect, before the rest of the PR work).
- **Spend**: Terra judge $0.50 (captured via OpenRouter usage.include); Modal H200 a few $ of endpoint
  time. Total well under the $30 ceiling (actuals to reconcile in PR body from OpenRouter activity + Modal).
- export-afb → committed results-raw/afb-20260808/ (manifest + 150 shards, 536KB, byte-stable) + the
  intermediate collection.json. run.log gitignored (not committed). AFB-001 real result: base 0 → dpo 2.
- Docs: results-raw/README.md AFB second-catalog + raw-only discovery + MIT attribution (in README, NOT the
  run dir — exporter prune would delete a run-dir SOURCE.md). Cross-language guard: TS parseRawCatalog on
  the REAL committed manifest (35 rawData tests). Vite build clean; multibrowser 305, analysis 232.
- **DEPLOYED-PATH check is POST-MERGE (Verify phase)**: the live Railway site reads main at runtime; #54
  adds SPA CODE (/raw route + Explorers), so a `railway up` REDEPLOY is required after merge (data alone
  appears without redeploy, but the discovery UI is new code). Do NOT deploy the unreviewed branch to prod.

### P5 consult iter-1 (both REQUEST_CHANGES; science APPROVED) — all resolved
- **Mojibake (18/150)**: architect approved re-collection (B). Repaired vendored questions.jsonl (fix-
  forward), dropped the 18 items' cells, redeployed briefly + re-collected 36 cells with clean text, TORE
  DOWN again. All 150 items now clean UTF-8. FINAL headline recomputed over the 150-item artifact:
  **P>=2 vanilla 1.3% -> DPO 21.3%** (mean 0.127 -> 0.820). Pre-fix reconciliation (1.3%->22.7%) kept in PR.
- **Real-data render (was 'never exercised')**: added an RTL test rendering the REAL committed manifest +
  shards through the app (AFB-005 0->4 both columns; all 150 items on the landing). Deployed Railway path
  stays post-merge Verify (needs railway up for the new SPA code).
- **Back-link dead-end**: raw-only item pages now back-link to /raw/<runId> ('← Explorer'), not /results.
- **MIT attribution**: © CEFE-AI clause in the shipped manifest dataset.description (re-exports deterministic).
- **gitignore** the atomic-write *.tmp.
- **SPEND reconciliation (EXACT, dashboard)**: `modal billing report --for today` → 3 afb-eval-serve
  instances (main $1.23787 + leg-2b $0.66081 + leg-2a-failed $0.19414) = **$2.0928 Modal**. Terra
  (OpenRouter usage.cost) = **$0.5624** (leg1 0.5037 + leg2 0.0587). **TOTAL = $2.6552** — ~8x under the
  $17-23 estimate, far under the $30 ceiling.

### P5 consult iter-2: claude APPROVE (verified everything empirically), codex REQUEST_CHANGES on 2 items
- Codex #2 (Modal exact): RESOLVED — dashboard figure above ($2.0928).
- Codex #1 (deployed-path gate): claude APPROVES deferring to post-merge Verify (the real-data RTL test
  can't catch the serve-s-dist baked-miss/GitHub-fallback landmine; needs railway up for new SPA code).
  → requesting the architect's FORMAL sign-off to move this acceptance gate to Verify (record it).
- claude minor: added the encoding-repair note to experiments/48/.../afb/SOURCE.md.

### ARCHITECT FORMAL SIGN-OFF (2026-08-12): deployed-path → post-merge Verify. APPROVED.
Rationale recorded (plan Change Log 2026-08-12): live site reads main; #54 discovery UI is new SPA code
in prod only after merge + railway up; unreviewed-branch-to-prod prohibited; serve -s dist baked-miss/
GitHub-fallback only testable live; RTL real-data render test is the pre-merge stand-in. Spend $2.6552
accepted. Nothing else was pending. Next: porch re-verify → Review phase → open PR (Waleed pre-authorized
merge on a clean integration review).
- Endpoint DOWN (all afb-eval-serve apps stopped, 0 tasks). Suites: analysis 232, multibrowser 308, tsc+ruff clean.

### P3 consult iter-3: BOTH APPROVE ✅ (claude ran an e2e 150-item CLI export). Phase 3 DONE.
Minor non-blocking follow-ups:
- exporter doesn't assert 150-item count (runner collect_afb enforces len==150; exporter stays generic
  over count — small fixtures need <150). OK as-is.
- intermediate["run_id"] not cross-checked vs CLI --run-id (P5 uses matching ids). Optional.
- **[Phase 4]** add a TS-side fixture of a REAL exported AFB manifest → genuine cross-language schema
  guard (renders in RTL against the real zod parser). Naturally addressed by Phase 4.

### P2 consult iter-3: BOTH APPROVE ✅ (codex + claude). Phase 2 DONE.
Non-blocking follow-ups captured (apply at Phase 5 / opportunistically):
- (a) extend the serving smoke to also make ONE judge call (fail a judge misconfig before the full
  generation spend) — runner tweak, do at P5 start.
- (b) gitignore `experiments/54_afb_before_after/data/*.tmp` (transient atomic-write temp) — do at P5.
- (c) carry greedy-vs-#48-sampling divergence into the P5 #48 distribution reconciliation + gate msg.
- (d) explicit regression test: `score: 0` cells are NOT re-judged on resume (modal base score; core
  already correct via `get("score") is None`, but pin it). Add opportunistically.

---
Other accepted fixes: P1 primitive = streaming finalizer (MB builds catalog after shard loop; carry
limit-gated prune; pull PRESET_CAP+_dedup_per_item); P2 two-state atomic checkpoint (response then
verdict; resume judges-only); pin+record decoding (temp/seed/max_tokens) + reconcile base/dpo dist vs
#48 before commit (base≈0/~1%≥2, dpo~27%≥2, escalate on divergence); intermediate path =
experiments/54_afb_before_after/data/collection.json; exact summary phrasing + ≤80-char word-boundary
label; COPY #58 serve script (never edit its committed file); BLOCKING spend gate (explicit approval,
not a heads-up); runner env uv --project workflows/judging (SDK-free afb_collect); usage→gitignored
run.log. Preset ships as spec's |dpo−base|; signed refinement flagged for plan-approval.

### P5 consult iter-3: BOTH APPROVE ✅ — Phase 5 DONE (claude re-ran export independently)
Minor doc-polish for REVIEW phase: (1) README retention policy should exempt raw-only explorer runs (a
literal read could prune afb-20260808); (2) clarify headline parenthetical — encoding-fix delta (22.7→21.3)
is separate from greedy-vs-sampling (22.7 vs #48 ~27-30%); (3) one-line note that 11/300 responses hit the
1024-token cap (inherited from #48 harness); (4) arch-critical.md: add /raw explorer + export-afb/raw_writer
seam (update-arch-docs).

## Phase: REVIEW — write review doc + arch-docs + open PR (Waleed pre-authorized merge on clean integration)
