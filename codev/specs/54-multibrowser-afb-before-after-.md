# Specification: multibrowser — AFB before/after explorer (vanilla Gemma vs MultiWeights responses)

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
Implementation phases, file-by-file edits, code, and ordering live in codev/plans/54-*.md.
-->

## Metadata
- **ID**: spec-2026-08-08-multibrowser-afb-before-after
- **Status**: draft
- **Created**: 2026-08-08

## Clarifying Questions Asked

A spec did not pre-exist; the issue body plus an architect correction (issue #54 comment,
2026-08-06, and a direct `afx` instruction 2026-08-08) answer the load-bearing questions. The
2-way consultation (codex + claude) then verified every structural claim against the code and
resolved several of my initial open questions empirically. No questions were put back to the user;
the one genuine product decision left for the architect is called out under **Open Questions**.

- **Q: Does per-item AFB response text already exist on disk (issue body says "saved #48 outputs, zero new spend")?**
  A: **No — superseded.** `eval_afb_probes.py` discards responses after judging (persists
  `{id, score}` only, verified `eval_afb_probes.py:118`); #48's raw outputs died with its worktree;
  #58 evaluated only the full-grid head. **#54 requires a dedicated collection run** with a script
  change to persist response text (and Terra judging alongside). Budget ~$17–23 (two subjects;
  revised down ~⅓ from the original ~$25–35 by Waleed's SFT-drop), pre-authorized. **Baked decision**
  (see Constraints).
- **Q: Which subjects?** A: **Two** — `gemma-4-31b-it` (vanilla base) and `mb-sft-dpo` (the #48
  shipped **incumbent** — NOT #58's scaling-null `mb-dpo-full`). **Waleed's ruling (2026-08-08):
  he cares ONLY about vanilla ↔ DPO** — the SFT checkpoint (`mb-sft-guided`) is dropped from both
  the collection run and the catalog. These two IDs are exactly the subject list in the shipped test
  fixture (`lib/rawData.test.ts:45` `AFB_CATALOG`).
- **Q: Which condition(s)?** A: **cold** (question verbatim). Faith-context is optional/low-value
  (near-saturated per #48) — out of scope for the launch catalog; the condition axis leaves room.
- **Q: Which judge / scale?** A: `gpt-5.6-terra` via OpenRouter, the AFB official `scoring_prompt.json`
  **0–4** religious-representation scale — catalog-declared, NOT the MultiBench −1…+1 ramp.
- **Q: Does this require viewer code changes (issue says "not a viewer change")?**
  A: **The render/model/parser/color path needs NO change** (verified generic, and a shipped test
  already renders an AFB 0–4 catalog). **One real-but-small SPA change is required:** run
  **discovery** (a raw-only catalog is currently undiscoverable). The side-by-side view is the
  viewer's native **A/B (two-column)** shape, which — after Waleed's vanilla↔DPO narrowing — is now
  an exact fit (two subjects, one comparison), so **no** selector/N-up work is needed either.

## Problem Statement

The #48 "MultiWeights" result — that judge-filtered context distillation on MultiBench's guided
data moves gemma-4-31b from **omitting** religion (AFB mean ≈ 0, "meaningful-or-deeper" ≈ 1%) to
**including** it as a live perspective (score ≥ 2 ≈ 27%) without over-application — currently
exists only as **distribution tables and aggregate figures**. A reader cannot *see* the omission
and its repair: there is no way to read, for a given ordinary-life question, the flat secular
answer from vanilla Gemma beside the fine-tuned answer that names a religious perspective, each
with the judge's 0–4 score and rationale.

MultiBench already ships a **raw-results viewer** (Spec 51, live on `main`) whose contract is
explicitly **catalog-generic** — scale, color ramp, subjects, judges, condition axes, grouping
axis, scopes, and items are all *declared by the catalog*, with no MultiBench vocabulary in the
render path (a shipped test already renders a NON-MultiBench 0–4 AFB catalog end-to-end). The AFB
before/after view is precisely the "second catalog type" that contract was designed to carry. The
gaps are: (a) the underlying per-item response text **does not exist anywhere** and must be
collected; and (b) a raw-only catalog (no `results/` scores tier) is currently **undiscoverable** in
the SPA. The comparison itself is a single **A/B** pairing — **vanilla base ↔ DPO incumbent** (Waleed's
2026-08-08 scope ruling) — which is exactly the viewer's native two-column shape.

## Current State

**The evidence is invisible.** A reader of the MultiWeights work sees a distribution PDF
(`experiments/48…/figures/afb_distribution.pdf`) and aggregate numbers — no per-item responses.
`eval_afb_probes.py:118` computes a Terra 0–4 score per response and **discards the response text**,
persisting `{id, score}` only. #48's raw eval outputs were lost with its worktree; #58 ran the lean
battery on the full-grid head alone.

**The instrument is in-repo (MIT).** `experiments/48_multiweights_omissive_bias/data/input/afb/`
holds the AllFaith Benchmark Religious-Representation instrument: `questions.jsonl` (150 items,
`{id, question}` — *no category field*), `scoring_prompt.json` (the official 0–4 judge template +
`{rationale, score}` JSON contract), `LICENSE` (MIT, © CEFE-AI), `SOURCE.md`.

**The model-serving stack exists.** `experiments/58/modal/serve_gemma_eval.py` serves base + LoRA
adapters as named models on one Modal vLLM endpoint. Both adapters live on volume `gemma-dpo`:
`mb-sft-guided` and `mb-sft-dpo` (incumbent, never overwritten) — alongside #58's `mb-dpo-full`.
The script's `dpo=` module currently points at `mb-dpo-full`; #54 must serve **`mb-sft-dpo`** as the
`dpo` subject. The collection runs **two subjects — `base` + `dpo`** (`EVAL_MODELS=base,dpo-incumbent`;
SFT dropped per Waleed) — so the runner needs a base+dpo path, not the harness's current base+sft
default.

**The export machinery exists but is a MB-specific monolith.**
`workflows/analysis/analysis/export_raw.py` writes `results-raw/<run-id>/{manifest.json,
<group>/<item>.json.gz}` with byte-stable gzip (mtime=0, sorted keys), size ceilings (≤ 1 MB/shard,
≤ 200 MB/run, validated before any write), and two `sha256` fingerprints. Its **manifest builder is
catalog-generic**, but `write_dataset` (≈`export_raw.py:779`) interleaves MB-specific *reading*
(`iter_tradition_raw` over `report.json`/`sittings.jsonl`), `CANONICAL_SUBJECTS`, MB preset
computation (`_models_split`, `_steadfastness_cliff`), ceilings, pruning, and writing in one path.
There is **no extracted generic writer** a sibling command can call yet.

**The viewer render path is already AFB-ready; discovery and A/B are the constraints.** Verified
against `apps/multibrowser/`:
- **Generic, no change:** catalog schema/parser (`lib/rawModel.ts`), score-bounds validation
  against `catalog.scale`, the generic ramp (`lib/rampColor.ts` `catalogScoreColor`, 0/2/4 works),
  and grid/controls that iterate the catalog's axes/subjects/judges/scopes/groupBy. A shipped test
  (`routes/rawResults.test.tsx:156`, *"renders a NON-MultiBench 0–4 catalog with NO #49 score
  tier"*) already renders an `AFB_CATALOG`/`AFB_SHARD` fixture; a second copy in
  `lib/rawData.test.ts:45` fixes the intended catalog shape (below). **These fixtures are the
  template and the acceptance oracle.**
- **Schema hard requirements (were wrong in my first draft):** `catalog.fingerprint` is
  **required** (`rawModel.ts:69`; `content_fingerprint` is the optional one) and each verdict's
  `summary` is **required** (`rawModel.ts:81`; `rationale` is optional). An AFB catalog/shard that
  omits either **fails validation** — not a graceful degrade.
- **A/B render, not 3-up:** `RawComparison.tsx` takes `a: string, b: string | null`
  (`single = !b`, `cellA`/`cellB`, two-column grid). `rawSelection.ts` models one A + one optional
  B; preset entries carry `a` + optional `b`. There is **no** three-subject grid.
- **Discovery blocker:** `lib/queries.ts` `resultsRunIds` regexes `^results/([^/]+)/manifest\.json$`
  only; `loadResultsRuns` builds the run list from **scores-tier** manifests and (per consult)
  `/results` filters runs lacking a valid `ResultsManifest`. The git-tree walk already includes
  `results-raw` (`github.ts:97` `WALK_DIRS`), so enumerating it adds **no** API calls — but a
  raw-only run yields zero IDs today and **nothing in the SPA links to it**. The raw route itself
  renders fine from a deep link and tolerates a `null` cross-tier fingerprint.
- **Non-blocking MB seams to respect:** `corpus.ts` `CORPUS_GROUP_KEY = "tradition"` → an AFB
  `groupBy.key = "instrument"` simply renders no judge-guidance/corpus cross-link (graceful, and a
  shipped test asserts this degrade); `RESERVED_AXIS_KEYS = {a, b, scope, judge}` → AFB's
  `condition` axis key is safe; `RAW_SUPPORTED_SCHEMA_VERSION = 1`; `RawResultsPage` has a static
  guard scanning it for MB vocabulary that new entry-point code must keep green.

**The intended AFB catalog shape is already codified** (`lib/rawData.test.ts:45` `AFB_CATALOG`) — and
its subject list is **exactly the two Waleed wants**: `schema_version: 1`; `scale {min:0, center:2,
max:4}`; sequential `ramp` (dark→mid→light); `subjects: [{id:"gemma-4-31b-it"}, {id:"mb-sft-dpo"}]`;
`judges: [{key:"terra", label:"gpt-5.6-terra", fullGrid:true}]`;
`conditionAxes: [{key:"condition", label:"Condition", values:[{id:"cold", label:"Cold"}]}]`;
`groupBy: {key:"instrument", label:"Instrument"}` with group `afb-150`; `scopes: [{id:"single"}]`;
`items` = `{id, label, group:"afb-150", shard:"afb-150/<item>.json.gz"}`; required `fingerprint`.

## Desired State

A reader visits the multibrowser SPA, reaches an **AFB before/after** run through a first-class
in-app entry point (no hand-typed URL), and for any of the 150 AFB cold-condition questions sees the
**before/after A/B comparison** — **vanilla Gemma-4-31B (A)** beside the **DPO incumbent
`mb-sft-dpo` (B)** — each response labeled with its **GPT-5.6-Terra 0–4** score + rationale and
colored by the catalog-declared 0–4 ramp (numeric scores, no band names; `center:2` renders the
calibration-target band as mid-grey, deliberately *not* signalling "4 is best"/over-application).
**Curated presets** deep-link the highest-contrast items (largest `dpo − base` lift) so the
omission→repair is one click away.

Underneath: a **new committed `results-raw/<afb-run-id>/`** drop-in catalog (single-digit MB) whose
`manifest.json` matches the shipped `AFB_CATALOG` shape (two subjects), produced by a **sibling
export command** that shares #51's shard writer / fingerprints / size ceilings / determinism
(extracted from the current monolith without changing its byte output). The per-item
responses+verdicts from the one-time (~$17–23, two-subject) collection run are **preserved durably in
the repo** so the spend is never repeated and the export is reproducible.

## Stakeholders
- **Primary Users**: readers of the MultiWeights paper / MultiBench browser — researchers, CEFEAI
  collaborators, reviewers who want to *see* the omission→repair on concrete items.
- **Secondary Users**: the MultiBench team (this is the paper's companion artifact; the paper's
  repo/browser links should point at it once live).
- **Technical Team**: this builder (spir-54); the architect (approvals, spend authorization,
  running/holding the Modal endpoint + provisioning the OpenRouter key).
- **Business Owners**: Waleed (pre-authorized the ~$17–23 regen; owns publication scope + the
  vanilla↔DPO scope ruling).

## Success Criteria
- [ ] **Collection**: a dedicated, **resumable/idempotent** run produces, for **all 150 AFB items ×
      2 subjects** (`gemma-4-31b-it`, `mb-sft-dpo` — `EVAL_MODELS=base,dpo-incumbent`) in the **cold**
      condition, the **response text** and a **GPT-5.6-Terra 0–4** score + rationale; it **checkpoints
      as it goes** (interruption never loses completed paid work) and **validates completeness**
      (exactly 150 unique items × 2 subjects = 300 cells, all judged) before export.
- [ ] **Durable preservation**: the collection output is committed to the repo, so re-export needs
      no re-spend and #48's "raw outputs died with the worktree" loss is not repeated.
- [ ] **Catalog**: a `results-raw/<afb-run-id>/` drop-in (`manifest.json` + per-item gz shards)
      **validates against the #51 schema** and matches the shipped `AFB_CATALOG` shape
      (`schema_version:1`; scale `{0,2,4}`; **two subjects** (`gemma-4-31b-it`, `mb-sft-dpo`); judge
      `terra`; `condition/cold`; `scope/single`; `groupBy instrument/afb-150`; 150 items).
      Every verdict carries a **synthesized `summary`** (schema-required) plus the judge `rationale`;
      the catalog carries a self-consistent **`fingerprint`** (schema-required) and a `content_fingerprint`.
- [ ] **Loads unchanged**: the catalog renders in the current raw viewer with **no change to the
      render/model/parser/color code** (0–4 scale, ramp, two subjects, 150 items) — the shipped AFB
      genericity test (`routes/rawResults.test.tsx:156`) is the oracle.
- [ ] **Exporter reuse is real, not a rewrite of behavior**: the sibling command shares an
      **extracted** generic writer, and the existing `results-raw/20260803` tier **re-exports
      byte-identical** (unchanged `fingerprint` + `content_fingerprint`) after the extraction — the
      cross-tier drift guard (`lib/rawData.test.ts`) stays green.
- [ ] **Reachable**: the AFB run is **discoverable and reachable through a first-class in-app entry
      point** (not a hand-typed URL), via a discovery path that enumerates `results-raw/` runs and a
      landing that **does not** disturb the default MultiBench scores run — adding **no** new GitHub
      API calls (enumerate from the already-walked tree).
- [ ] **Before/after legibility**: the A/B view shows, per item, the two responses (vanilla base ↔
      DPO incumbent) with correct numeric Terra scores + rationales and ramp colors, and a
      **deterministic curated preset** — top-N by the `dpo − base` score delta, one entry per item —
      surfacing the clearest omission→repair contrasts.
- [ ] **Licensing/hygiene**: AFB instrument stays MIT-attributed (`SOURCE.md`/`LICENSE`); our
      responses/judgments ship under the catalog `license`; the shipped tier excludes
      usage/raw/timestamps (the #51 allowlist).
- [ ] Touched apps' suites pass via `.codev/checks/test.sh`: `workflows/analysis` (pytest) +
      `apps/multibrowser` (pnpm test), including the static MB-vocab guard and the genericity test.
- [ ] Docs updated: `results-raw/README.md` (second-catalog example + raw-only discovery note), the
      AFB run's provenance/preservation, and the paper's companion-artifact link plan.

## Constraints

### Baked Decisions (architect — do not relitigate)
From the issue #54 comment (2026-08-06) and the architect instructions (2026-08-08):
- **Scope: vanilla ↔ DPO only (Waleed, 2026-08-08).** Two subjects — `gemma-4-31b-it` and
  `mb-sft-dpo`; **the SFT checkpoint is dropped** from both the collection run and the catalog.
- **A dedicated collection run is required** — `EVAL_MODELS=base,dpo-incumbent` through the eval
  endpoint, script changed to **persist response text**, with **Terra judging** for the scores.
- **`dpo-incumbent` = `mb-sft-dpo`** (the #48 shipped incumbent), not #58's `mb-dpo-full`.
- **Budget ~$17–23** (revised down ~⅓ from the original ~$25–35 by dropping the SFT subject),
  pre-authorized by Waleed.
- **Keys: OpenRouter + Anthropic only. NEVER Waleed's personal keys.** Terra judge via OpenRouter;
  the Modal endpoint uses Modal auth (keyless short-lived URL), not a personal API key.
- **Build on the #51 viewer + generic contract** (live on `main`) — a **second catalog type**.
  Verification found **one** small, in-scope SPA change (raw-run discovery); the A/B render path is a
  native fit for two subjects and is unchanged.
- **Catalog-declared** subjects/items/condition-axes/score-scale/ramp; Terra **0–4** (not −1..+1);
  **numeric scores + catalog ramp, no band names**.
- **Same exclusions discipline as #51**: no usage/raw/timestamps in the shipped tier.

### Technical Constraints
- Schema hard-requirements: `catalog.fingerprint` and every verdict `summary` are **required**
  (`rawModel.ts:69,81`); `schema_version:1`; condition-axis key ∉ `{a,b,scope,judge}` (satisfied by
  `condition`); `groupBy.key = "instrument"` forgoes the corpus cross-link (acceptable).
- Discovery must **not** be a naive merge into `loadResultsRuns` (which requires a valid scores
  manifest and would drop the null-scores AFB run); it needs a raw-run enumerator + a landing/entry
  point that leaves the default MB scores run selection unchanged, and keeps the `RawResultsPage`
  static MB-vocab guard green.
- Exporter change must preserve byte-stable re-export of the existing MB tier under the pinned
  `workflows/analysis` toolchain (gzip mtime=0, sorted keys) — export from `uv --project workflows/analysis`.
- Client GitHub data layer is unauthenticated/rate-limited; discovery adds no per-run listing calls.
- Multi-language repo: tests run through the per-builder dispatcher `.codev/checks/test.sh`.

### Business Constraints
- One-time spend ~$17–23, authorized; no recurring cost. No time estimates (AI-age).
- AFB items MIT (attribution required); our responses/judgments publishable per the catalog license.
  Companion artifact to the MultiWeights paper.

## Assumptions
- Volume `gemma-dpo` still carries `mb-sft-dpo` intact (#58: incumbent never overwritten). **Verify
  with a serving smoke BEFORE spending.**
- The endpoint serves both subjects on one deployment (base + the `mb-sft-dpo` LoRA module, `dpo`
  repointed from `mb-dpo-full`).
- Terra (`openai/gpt-5.6-terra`) remains on OpenRouter and honors the 0–4 JSON contract.
- The vendored AFB copy is authoritative; the launch catalog uses **cold** only.
- #51 is on `main` and its render path is unchanged since the genericity verification above.

## Solution Approaches

### Approach 1: Resumable collection → sibling AFB exporter (shared writer) → drop-in catalog → raw-run discovery + A/B presets (RECOMMENDED)

**Description**: Four pieces, no render rewrite.
1. **Collect** responses + Terra 0–4 verdicts for **2 subjects × 150 cold items** (base + dpo) via the
   Modal endpoint (serving `mb-sft-dpo` as `dpo`), persisting **response text** + `{score,
   rationale}`, **checkpointing incrementally** and validating completeness before export. Preserve
   the output durably in-repo.
2. **Export** via a **sibling command** (e.g. `analysis export-afb`) that calls a **generic writer
   primitive extracted** from `export_raw.py` (shard writing, ceilings, gzip determinism,
   fingerprints), takes the AFB collection as input, synthesizes each verdict `summary`, and emits
   the shipped-fixture catalog shape (scale 0–4; **2 subjects**; `terra`; `condition/cold`;
   `scope/single`; `instrument/afb-150`; 150 shards; a deterministic `dpo − base` before/after preset).
3. **Drop in** the committed `results-raw/<afb-run-id>/` — appears in the browser by data, not code.
4. **Discover + present**: add a `results-raw/` run enumerator and a first-class entry point/landing
   into `/results/$runId/$groupId/$itemId` that leaves the default MB scores run untouched; the native
   A/B grid (base ↔ dpo) + the `dpo − base` preset surface the omission→repair.

**Pros**: maximal #51 reuse; honors every baked decision; the SPA delta is the minimal
generalization the genericity mandate implies; durable one-time spend; deterministic drop-in.
**Cons**: real infra + ~$17–23 spend; a second exporter path + an extraction of a byte-critical
monolith (regression-guarded).
**Estimated Complexity**: Medium · **Risk Level**: Medium (spend + live serving + byte-stable refactor).

### Approach 2: Force the AFB catalog through the `results/` scores tier (rejected)
Emit a `results/<afb-run-id>/` scores manifest so existing discovery finds it. **Rejected**: the
`results/` leaderboard is MB-specific (Gemini mean-of-means, "Steadfastness (Δ)", framings) and would
misrender an AFB run; it reintroduces a scores tier AFB doesn't need and a cross-tier fingerprint with
nothing to reconcile.

### Approach 3: N-up (three-column) render change (WITHDRAWN)
An earlier alternative for a literal three-column grid (generalize `RawComparison` + `rawSelection`
to N subjects). **Withdrawn**: Waleed's 2026-08-08 ruling scopes the catalog to **two subjects
(vanilla ↔ DPO)**, which is the viewer's native A/B shape — there is no third checkpoint to place, so
the N-up question is moot. Recorded for history only.

### Approach 4: Reuse `export-raw` by faking MB roots (rejected)
Shoehorn AFB into `report.json`/`sittings.jsonl` shapes. **Rejected**: brittle impedance-matching; a
clean sibling sharing the *writer* (not the *reader*) is simpler and safer.

## Open Questions

### Critical (Blocks Progress)
- *(None open.)* The pre-spend gate — adapter integrity + endpoint ownership — is **resolved** (see
  Decided, below).

### Decided (2026-08-08 — to be RE-CONFIRMED at spec-approval)
- **Scope = vanilla ↔ DPO only (Waleed).** Two subjects (`gemma-4-31b-it`, `mb-sft-dpo`); SFT dropped
  from run and catalog. This is the viewer's native A/B shape — **no selector, no third checkpoint, no
  N-up render change** (Approach 3 withdrawn). The catalog carries a single `dpo − base` before/after
  preset. This narrows the issue's "next to SFT and SFT+DPO" wording; recorded so it is visible at the gate.
- **Adapter integrity: VERIFIED (architect, 2026-08-08).** `runs/mb-sft-dpo/adapter/adapter_model.safetensors`
  + `adapter_config.json` are intact on the `gemma-dpo` volume. A serving smoke still precedes any spend.
- **Endpoint ownership: the builder deploys and holds the Modal endpoint** (Modal CLI is
  machine-authed; same pattern as #48/#57/#58) and **tears it down after collection**.
- **Keys:** `OPENROUTER_API_KEY` (Terra judge) + `ANTHROPIC_API_KEY` are sourced from
  `/Users/mwk/Development/fftn/taqwabench/.env` — **read at runtime, never committed or echoed**;
  never a personal key.
- **Discovery is approved, and must stay catalog-GENERIC.** Build the raw-run enumerator + first-class
  entry point so it enumerates `results-raw/` runs **generically** — **no AFB-specific vocabulary in
  the SPA core**; the existing genericity/static-MB-vocab guard applies to the new code.

### Important (Affects Design) — all resolved at plan time
- **Preservation shape: APPROVED (architect).** Commit a **compact intermediate collection artifact**
  (the reproducible export input) **in addition to** the `results-raw/` tier, so a future
  catalog-shape change re-exports with zero re-spend. Exact location/format at plan time.
- **Preset selection rule: single `dpo − base` preset.** Deterministic **top-N by `|dpo − base|`
  score delta, N ≤ 12**, one entry per item; the exact **tie-break** is settled at plan time.
- **`summary` synthesis.** The AFB judge returns only `{score, rationale}`; the exporter synthesizes a
  short, deterministic direction `summary` (the fixture uses phrases like "omitted the concern");
  the exact **phrasing convention** is settled at plan time.

### Resolved by shipped code (recorded, not open)
- **groupBy / condition / scope / scale / subject-IDs**: fixed by `AFB_CATALOG`
  (`instrument`/`afb-150`, `condition/cold`, `scope/single`, `{0,2,4}`, checkpoint IDs).
- **Ramp semantics**: sequential 0→4 with `center:2` → mid-grey at the calibration target (anti-"4 is
  best"), which is the intended anti-over-application signal.
- **`fingerprint` / `summary` are required** (not optional) — hard exporter requirements, above.
- **`groupBy.key ≠ "tradition"`** → no corpus cross-link (graceful; shipped test asserts the degrade).

### Nice-to-Know (Optimization)
- [ ] Baked deploy bundle for AFB shards (the `railway up --no-gitignore` path) — likely unnecessary
      given the tiny size; confirm baked-first/GitHub-fallback treats a small AFB tier correctly.
- [ ] Later collection of the faith-context condition (a second axis value) — out of scope now.
- [ ] Later re-inclusion of the SFT checkpoint as a third subject — out of scope per Waleed's
      vanilla↔DPO ruling; the catalog `subjects` list leaves room if revisited.

## Performance Requirements
- **Catalog size**: single-digit MB committed (150 items × 3 short responses + verdicts) — far under
  the #51 ceilings (≤ 1 MB/shard, ≤ 200 MB/run), still validated before write.
- **Viewer load**: A/B item view interactive on a normal connection; discovery adds **no** new GitHub
  API calls per run.
- **Determinism**: byte-identical re-export from the same collection input under the pinned toolchain;
  and the existing MB tier re-exports byte-identical after the writer extraction.
- **Collection cost**: ~$17–23 total, one-time (two subjects × 150 cold items).

## Security Considerations
- **Credentials**: `OPENROUTER_API_KEY` (Terra judge) + `ANTHROPIC_API_KEY` **only** — sourced at
  runtime from `/Users/mwk/Development/fftn/taqwabench/.env`, **never committed or echoed**; **never**
  a personal key.
- **Endpoint ownership/auth**: the **builder deploys and holds** the Modal vLLM endpoint (Modal CLI is
  machine-authed, same pattern as #48/#57/#58).
- **Eval endpoint access/shutdown (explicit):** the endpoint is **keyless, short-lived, on an obscure
  Modal URL** — access control is URL-obscurity + short lifetime, and it is **torn down immediately
  after collection** (remove `min_containers` / stop the app). No persistent public inference surface
  is left running.
- **License compliance**: AFB items MIT — ship `SOURCE.md` + `LICENSE`; do not relicense. Our
  responses/judgments ship under the catalog `license`.
- **Data hygiene**: shipped tier excludes usage/raw/timestamps (#51 allowlist). AFB questions are the
  published instrument.

## Test Scenarios

### Functional Tests
1. **Happy path**: export the AFB collection → `manifest.json` + 150 shards; catalog validates
   against the #51 schema and matches the `AFB_CATALOG` shape; loads in the raw viewer with the 0–4
   scale and the two subjects (base + dpo).
2. **Determinism (both directions)**: (a) AFB re-export from the same committed input → byte-identical
   shards + identical `content_fingerprint`; (b) the existing `results-raw/20260803` tier re-exports
   byte-identical after the writer extraction (cross-tier drift guard green).
3. **Schema requireds**: an AFB shard missing verdict `summary`, or a manifest missing `fingerprint`,
   fails validation (guards the "required" facts); the produced catalog has both.
4. **A/B before/after legibility**: a known item (base = 0, dpo ≥ 2) renders the two responses (base ↔
   dpo) with correct numeric scores + rationales and ramp colors; the `dpo − base` preset deep-links
   the highest-contrast items deterministically.
5. **Discovery/reachability**: the AFB run appears via the raw-run enumerator and a first-class in-app
   link reaches `/results/$runId/$groupId/$itemId` — no hand-typed URL — **without** changing the
   default MB scores run; `RawResultsPage` static MB-vocab guard stays green.
6. **Genericity regressions**: the shipped `routes/rawResults.test.tsx:156` AFB test stays green;
   reserved-axis-key / wrong-`schema_version` catalogs fail soft with a notice.
7. **Collection resilience**: an interrupted collection resumes without re-spending completed
   subject×item cells; completeness validation rejects a run missing any of the 300 cells.

### Non-Functional Tests
1. **Size-ceiling guard**: exporter aborts before any write if a shard/run would exceed ceilings.
2. **No-API-call-inflation**: discovery enumerates from the walked tree without extra GitHub requests.
3. **Cross-tier tolerance**: a raw-only run with `null` scores fingerprint loads without a false notice.

## Dependencies
- **External Services**: Modal (vLLM eval endpoint + `gemma-dpo` volume); OpenRouter (Terra judge);
  GitHub raw + git-trees (SPA runtime); Railway (SPA host).
- **Internal Systems**: Spec 51 raw viewer + `results-raw/` contract (live on `main`) and its export
  machinery in `workflows/analysis` (shard writer, fingerprints, ceilings — to be partly extracted);
  the #48/#58 eval harness (`serve_gemma_eval.py`, `eval_afb_probes.py`) as the collection basis.
- **Libraries/Frameworks**: `workflows/analysis` (`uv`, pytest); `apps/multibrowser`
  (Vite/React19/TS/Tailwind4/HeroUI/TanStack, pnpm).
- **Data/Instrument**: AFB-150 MIT instrument under
  `experiments/48_multiweights_omissive_bias/data/input/afb/`.

## References
- Issue #54 (body + 2026-08-06 data-source-correction comment) and the 2026-08-08 architect instruction.
- Spec 51 — `codev/specs/51-multibrowser-raw-results-brows.md`; `results-raw/README.md`.
- Spec 49 — `results/` scores tier / aggregator reuse.
- Spec 48 — `codev/specs/48-multiweights-omissive-bias.md`.
- #58 — `experiments/58_multiweights_full_grid_dpo/notes.md` (incumbent `mb-sft-dpo`; `gemma-dpo`
  volume; serve script).
- Viewer/genericity evidence: `lib/rawModel.ts` (`fingerprint`:69, `summary`:81, reserved keys, schema
  version), `lib/rampColor.ts`, `lib/queries.ts` (`resultsRunIds`/`loadResultsRuns`), `lib/corpus.ts`,
  `components/RawComparison.tsx`, `lib/rawSelection.ts`, `src/router.tsx`, and the AFB fixtures/tests
  `lib/rawData.test.ts:45` + `routes/rawResults.test.tsx:156`.

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Adapters missing/altered on `gemma-dpo` | Low | High | Verify + serving smoke BEFORE spend; escalate to architect if absent. |
| Collection interrupted → paid work lost | Med | High | Incremental checkpointing + idempotent resume + completeness validation before export. |
| Collection output lost again (worktree death) | Med | High | Commit the collection output durably as export input-of-record; committed `results-raw/` is preservation. |
| Writer extraction changes MB tier bytes | Med | High | Regression test: `results-raw/20260803` re-exports byte-identical (fingerprints unchanged) — gate the refactor on it. |
| `summary`/`fingerprint` omitted → shard fails validation | Low | High | Treat as hard exporter requirements; test scenario 3 guards both. |
| Discovery naive-merge drops the null-scores AFB run | Med | Med | Separate raw-run enumerator + landing that keeps the default MB scores run; test scenario 5. |
| Spend overrun beyond ~$23 | Low | Med | Cold-only, 300 cells (2 subjects), concurrency-bounded; reconcile ACTUAL spend from usage, stop at ceiling, no faith-context. |
| 0–4 ramp mis-signals "4 is best" | Low | Low | `center:2` mid-grey at the calibration target; numeric scores, no band names. |
| Terra JSON contract drift | Low | Med | Fail-fast on non-conforming judge output (`{score∈0..4, rationale}`), bounded retry, no fallback scoring. |
| Endpoint left running post-collection | Low | Med | Explicit teardown (remove `min_containers`/stop app) as a completion step. |

## Expert Consultation
**Date**: 2026-08-08 · **Models Consulted**: codex + claude (per `porch.consultation.models`).
**Verdict**: both `REQUEST_CHANGES` (HIGH confidence) on the initial draft — resolved in this revision.
**Sections Updated**:
- *Current State / Constraints / Open Questions*: promoted `verdict.summary` and `catalog.fingerprint`
  to **hard exporter requirements** (schema-required, not optional as first drafted); removed the
  "omit fingerprint" branch.
- *Approach 1 / Success Criteria*: made the exporter reuse an **extraction** of a monolithic
  byte-critical writer, gated by a byte-identical re-export of the existing MB tier.
- *Discovery*: specified a **separate raw-run enumerator + landing** (not a merge into
  `loadResultsRuns`), preserving the default MB scores run and the static MB-vocab guard.
- *Collection*: added **resumable/idempotent checkpointing + completeness validation**.
- *Security*: made the eval-endpoint access model + **teardown** explicit; reconciled the "Modal auth"
  vs "keyless URL" wording.
- *Open Questions*: cited the shipped `AFB_CATALOG`/AFB genericity test that pre-answers
  groupBy/condition/scope/scale/subject-IDs; fixed ramp `center:2` semantics.

**Post-consult architect/Waleed rulings (2026-08-08):** the consult flagged that the viewer is A/B,
not 3-up. Waleed then **scoped the catalog to two subjects (vanilla ↔ DPO only)**, which is the
viewer's native A/B shape — so *Desired State / Success Criteria / Test Scenarios / Approaches* were
revised to two subjects + a single `dpo − base` preset, the SFT checkpoint and the N-up alternative
(Approach 3) were dropped, and the collection shrank to `EVAL_MODELS=base,dpo-incumbent` (~$17–23).

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- **Scope + deviations decided 2026-08-08 (to be RE-CONFIRMED at spec-approval):**
  (1) **Waleed scoped the catalog to two subjects — vanilla ↔ DPO only** (SFT dropped). This is the
  viewer's native A/B shape, so there is **no** selector, **no** third checkpoint, and **no** N-up
  render change. It narrows the issue's "next to SFT and SFT+DPO" wording — stated here so it is
  visible at the gate and Waleed can revisit if he wants SFT back.
  (2) a raw-only catalog is **undiscoverable** without a small discovery/entry-point addition —
  architect **approved in scope**, provided it stays **catalog-generic** (no AFB vocab in SPA core;
  genericity guard applies). The render/model/parser/color path itself needs **no** change.
- **`dpo` = `mb-sft-dpo`** throughout; the serve script's `dpo=` module must be repointed from
  `mb-dpo-full` for the collection run.
- Add the companion-artifact link from the MultiWeights paper's repo/browser once the run is live
  (Review-phase follow-up).
