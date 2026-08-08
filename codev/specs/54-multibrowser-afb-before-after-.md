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
  change to persist response text (and Terra judging alongside). Budget ~$25–35, pre-authorized.
  **Baked decision** (see Constraints).
- **Q: Which three subjects?** A: `gemma-4-31b-it` (base), `mb-sft-guided` (stage-1 SFT), `mb-sft-dpo`
  (the #48 shipped **incumbent** — NOT #58's scaling-null `mb-dpo-full`). These exact IDs are the
  ones the shipped test fixture and issue body use.
- **Q: Which condition(s)?** A: **cold** (question verbatim). Faith-context is optional/low-value
  (near-saturated per #48) — out of scope for the launch catalog; the condition axis leaves room.
- **Q: Which judge / scale?** A: `gpt-5.6-terra` via OpenRouter, the AFB official `scoring_prompt.json`
  **0–4** religious-representation scale — catalog-declared, NOT the MultiBench −1…+1 ramp.
- **Q: Does this require viewer code changes (issue says "not a viewer change")?**
  A: **The render/model/parser/color path needs NO change** (verified generic, and a shipped test
  already renders an AFB 0–4 catalog). **Two real-but-small SPA changes are required:** (1) run
  **discovery** (a raw-only catalog is currently undiscoverable), and (2) the side-by-side view is
  **A/B (two columns), not three** — so the three-checkpoint story is told via A/B + a subject
  selector + curated presets, not one 3-column grid. Both are surfaced to the architect below.

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
collected; (b) a raw-only catalog (no `results/` scores tier) is currently **undiscoverable** in
the SPA; and (c) the comparison grid is **A/B**, so "before/after across three checkpoints" must be
expressed through A/B + selector + presets rather than a three-wide grid.

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
`dpo` subject, and the runner needs a **3-subject** path (its docstring today says "BOTH checkpoints
base, sft").

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

**The intended AFB catalog shape is already codified** (`lib/rawData.test.ts:45` `AFB_CATALOG`):
`schema_version: 1`; `scale {min:0, center:2, max:4}`; sequential `ramp` (dark→mid→light);
`subjects` = the checkpoint IDs; `judges: [{key:"terra", label:"gpt-5.6-terra", fullGrid:true}]`;
`conditionAxes: [{key:"condition", label:"Condition", values:[{id:"cold", label:"Cold"}]}]`;
`groupBy: {key:"instrument", label:"Instrument"}` with group `afb-150`; `scopes: [{id:"single"}]`;
`items` = `{id, label, group:"afb-150", shard:"afb-150/<item>.json.gz"}`; required `fingerprint`.

## Desired State

A reader visits the multibrowser SPA, reaches an **AFB before/after** run through a first-class
in-app entry point (no hand-typed URL), and for any of the 150 AFB cold-condition questions sees a
**before/after A/B comparison** — by default **vanilla Gemma-4-31B (A)** beside a **fine-tuned
checkpoint (B)** — with a **subject selector** to swap B between `mb-sft-guided` and `mb-sft-dpo`,
each response labeled with its **GPT-5.6-Terra 0–4** score + rationale and colored by the
catalog-declared 0–4 ramp (numeric scores, no band names; `center:2` renders the calibration-target
band as mid-grey, deliberately *not* signalling "4 is best"/over-application). **Curated presets**
carry the three-checkpoint story by deep-linking the highest-contrast items across `base↔sft`,
`base↔dpo`, and `sft↔dpo` pairings — so the omission→repair is one click away even though the grid
shows two columns at a time.

Underneath: a **new committed `results-raw/<afb-run-id>/`** drop-in catalog (single-digit MB) whose
`manifest.json` matches the shipped `AFB_CATALOG` shape, produced by a **sibling export command**
that shares #51's shard writer / fingerprints / size ceilings / determinism (extracted from the
current monolith without changing its byte output). The per-item responses+verdicts from the
one-time (~$25–35) collection run are **preserved durably in the repo** so the spend is never
repeated and the export is reproducible.

## Stakeholders
- **Primary Users**: readers of the MultiWeights paper / MultiBench browser — researchers, CEFEAI
  collaborators, reviewers who want to *see* the omission→repair on concrete items.
- **Secondary Users**: the MultiBench team (this is the paper's companion artifact; the paper's
  repo/browser links should point at it once live).
- **Technical Team**: this builder (spir-54); the architect (approvals, spend authorization,
  running/holding the Modal endpoint + provisioning the OpenRouter key).
- **Business Owners**: Waleed (pre-authorized the ~$25–35 regen; owns publication scope).

## Success Criteria
- [ ] **Collection**: a dedicated, **resumable/idempotent** run produces, for **all 150 AFB items ×
      3 subjects** (`gemma-4-31b-it`, `mb-sft-guided`, `mb-sft-dpo`) in the **cold** condition, the
      **response text** and a **GPT-5.6-Terra 0–4** score + rationale; it **checkpoints as it goes**
      (interruption never loses completed paid work) and **validates completeness** (exactly 150
      unique items × 3 subjects, all judged) before export.
- [ ] **Durable preservation**: the collection output is committed to the repo, so re-export needs
      no re-spend and #48's "raw outputs died with the worktree" loss is not repeated.
- [ ] **Catalog**: a `results-raw/<afb-run-id>/` drop-in (`manifest.json` + per-item gz shards)
      **validates against the #51 schema** and matches the shipped `AFB_CATALOG` shape
      (`schema_version:1`; scale `{0,2,4}`; subjects = the three checkpoints; judge `terra`;
      `condition/cold`; `scope/single`; `groupBy instrument/afb-150`; 150 items). Every verdict
      carries a **synthesized `summary`** (schema-required) plus the judge `rationale`; the catalog
      carries a self-consistent **`fingerprint`** (schema-required) and a `content_fingerprint`.
- [ ] **Loads unchanged**: the catalog renders in the current raw viewer with **no change to the
      render/model/parser/color code** (0–4 scale, ramp, subjects, 150 items) — the shipped AFB
      genericity test (`routes/rawResults.test.tsx:156`) is the oracle.
- [ ] **Exporter reuse is real, not a rewrite of behavior**: the sibling command shares an
      **extracted** generic writer, and the existing `results-raw/20260803` tier **re-exports
      byte-identical** (unchanged `fingerprint` + `content_fingerprint`) after the extraction — the
      cross-tier drift guard (`lib/rawData.test.ts`) stays green.
- [ ] **Reachable**: the AFB run is **discoverable and reachable through a first-class in-app entry
      point** (not a hand-typed URL), via a discovery path that enumerates `results-raw/` runs and a
      landing that **does not** disturb the default MultiBench scores run — adding **no** new GitHub
      API calls (enumerate from the already-walked tree).
- [ ] **Before/after legibility**: the A/B view shows, per item, two responses with correct numeric
      Terra scores + rationales and ramp colors, a selector to swap the tuned checkpoint, and
      **three deterministic curated presets** — `base↔dpo` (default headline), `base↔sft`, `sft↔dpo`
      (architect-confirmed) — each top-N by the pair's `|score delta|`, one entry per item, so all
      three checkpoints are one click apart.
- [ ] **Licensing/hygiene**: AFB instrument stays MIT-attributed (`SOURCE.md`/`LICENSE`); our
      responses/judgments ship under the catalog `license`; the shipped tier excludes
      usage/raw/timestamps (the #51 allowlist).
- [ ] Touched apps' suites pass via `.codev/checks/test.sh`: `workflows/analysis` (pytest) +
      `apps/multibrowser` (pnpm test), including the static MB-vocab guard and the genericity test.
- [ ] Docs updated: `results-raw/README.md` (second-catalog example + raw-only discovery note), the
      AFB run's provenance/preservation, and the paper's companion-artifact link plan.

## Constraints

### Baked Decisions (architect — do not relitigate)
From the issue #54 comment (2026-08-06) and the architect instruction (2026-08-08):
- **A dedicated collection run is required** — `EVAL_MODELS=base,sft,dpo-incumbent` through the eval
  endpoint, script changed to **persist response text**, with **Terra judging** for the scores.
- **`dpo-incumbent` = `mb-sft-dpo`** (the #48 shipped incumbent), not #58's `mb-dpo-full`.
- **Budget ~$25–35**, pre-authorized by Waleed.
- **Keys: OpenRouter + Anthropic only. NEVER Waleed's personal keys.** Terra judge via OpenRouter;
  the Modal endpoint uses Modal auth (keyless short-lived URL), not a personal API key.
- **Build on the #51 viewer + generic contract** (live on `main`) — a **second catalog type**.
  Verification found two small, in-scope SPA changes (discovery + A/B framing); the render path is
  unchanged.
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
- One-time spend ~$25–35, authorized; no recurring cost. No time estimates (AI-age).
- AFB items MIT (attribution required); our responses/judgments publishable per the catalog license.
  Companion artifact to the MultiWeights paper.

## Assumptions
- Volume `gemma-dpo` still carries `mb-sft-guided` + `mb-sft-dpo` intact (#58: incumbent never
  overwritten). **Verify with a serving smoke BEFORE spending.**
- The endpoint serves all three subjects on one deployment (base + two LoRA modules), `dpo` repointed
  to `mb-sft-dpo`.
- Terra (`openai/gpt-5.6-terra`) remains on OpenRouter and honors the 0–4 JSON contract.
- The vendored AFB copy is authoritative; the launch catalog uses **cold** only.
- #51 is on `main` and its render path is unchanged since the genericity verification above.

## Solution Approaches

### Approach 1: Resumable collection → sibling AFB exporter (shared writer) → drop-in catalog → raw-run discovery + A/B presets (RECOMMENDED)

**Description**: Four pieces, no render rewrite.
1. **Collect** responses + Terra 0–4 verdicts for 3 subjects × 150 cold items via the Modal endpoint
   (serving `mb-sft-dpo` as `dpo`, 3-subject path), persisting **response text** + `{score,
   rationale}`, **checkpointing incrementally** and validating completeness before export. Preserve
   the output durably in-repo.
2. **Export** via a **sibling command** (e.g. `analysis export-afb`) that calls a **generic writer
   primitive extracted** from `export_raw.py` (shard writing, ceilings, gzip determinism,
   fingerprints), takes the AFB collection as input, synthesizes each verdict `summary`, and emits
   the shipped-fixture catalog shape (scale 0–4; 3 subjects; `terra`; `condition/cold`;
   `scope/single`; `instrument/afb-150`; 150 shards; deterministic before/after presets).
3. **Drop in** the committed `results-raw/<afb-run-id>/` — appears in the browser by data, not code.
4. **Discover + present**: add a `results-raw/` run enumerator and a first-class entry point/landing
   into `/results/$runId/$groupId/$itemId` that leaves the default MB scores run untouched; the A/B
   grid + subject selector + presets tell the three-checkpoint story.

**Pros**: maximal #51 reuse; honors every baked decision; the SPA delta is the minimal
generalization the genericity mandate implies; durable one-time spend; deterministic drop-in.
**Cons**: real infra + ~$25–35 spend; a second exporter path + an extraction of a byte-critical
monolith (regression-guarded); the A/B framing is not the issue's literal three-wide grid.
**Estimated Complexity**: Medium · **Risk Level**: Medium (spend + live serving + byte-stable refactor).

### Approach 2: Force the AFB catalog through the `results/` scores tier (rejected)
Emit a `results/<afb-run-id>/` scores manifest so existing discovery finds it. **Rejected**: the
`results/` leaderboard is MB-specific (Gemini mean-of-means, "Steadfastness (Δ)", framings) and would
misrender an AFB run; it reintroduces a scores tier AFB doesn't need and a cross-tier fingerprint with
nothing to reconcile.

### Approach 3: N-up (three-column) render change (deferred — architect decision)
Generalize `RawComparison` + `rawSelection` + URL params to N subjects for a literal three-column
grid. **Deferred**: a real render change beyond "minimal discovery generalization," needs a third URL
param outside the reserved set, and contradicts the "not a viewer change" baked decision. Offered to
the architect as the alternative to Approach 1's A/B framing (see Open Questions).

### Approach 4: Reuse `export-raw` by faking MB roots (rejected)
Shoehorn AFB into `report.json`/`sittings.jsonl` shapes. **Rejected**: brittle impedance-matching; a
clean sibling sharing the *writer* (not the *reader*) is simpler and safer.

## Open Questions

### Critical (Blocks Progress)
- [ ] **Endpoint/adapter availability + ownership before spend.** Verify `mb-sft-dpo` + `mb-sft-guided`
      intact on `gemma-dpo` and the endpoint serves all three, *before* authorizing the run. Who
      spins up/holds the Modal endpoint and provides the OpenRouter key?

### Architect-Decided (2026-08-08 — to be RE-CONFIRMED at spec-approval)
- **A/B + selector + presets is the call (NOT a 3-up render change).** The architect confirmed
  Approach 1: the shipped viewer is A/B and a literal N-up grid would contradict the issue's own
  "not a viewer change" statement. **Deviation from the issue's "next to" wording, stated explicitly
  so Waleed can override to the literal three-column grid (Approach 3) at the gate:** the baseline
  shows two response *texts* at a time, with the three-checkpoint story carried by a subject selector
  + three curated presets (below), not one three-wide grid.
- **Discovery is approved, and must stay catalog-GENERIC.** Build the raw-run enumerator + first-class
  entry point so it enumerates `results-raw/` runs **generically** — **no AFB-specific vocabulary in
  the SPA core**; the existing genericity/static-MB-vocab guard applies to the new code.

### Important (Affects Design)
- [ ] **Preservation shape of the collection output.** Recommend committing a compact intermediate
      collection artifact (reproducible export input) **in addition to** the `results-raw/` tier, so a
      future catalog-shape change re-exports with zero re-spend. Confirm location/format.
- [ ] **Preset selection rule (pairings decided; N/tie-break to confirm).** Architect-confirmed
      pairings: **`base↔dpo`** (the headline repair, default), **`base↔sft`**, and **`sft↔dpo`** — so
      all three checkpoints are one click apart. Each preset: deterministic top-N (recommend N≤12) by
      the pair's `|score delta|`, one entry per item, magnitude-sorted with a stable tie-break.
      Confirm N and tie-break at plan time.
- [ ] **`summary` synthesis.** The AFB judge returns only `{score, rationale}`; the exporter must
      synthesize a short, deterministic direction `summary` (the fixture uses phrases like "omitted
      the concern"/"held"). Confirm the phrasing convention.

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
- [ ] Optional: surface all three subjects' scores in a compact per-item strip (a small render add) —
      out of baseline scope; would need architect sign-off like Approach 3.

## Performance Requirements
- **Catalog size**: single-digit MB committed (150 items × 3 short responses + verdicts) — far under
  the #51 ceilings (≤ 1 MB/shard, ≤ 200 MB/run), still validated before write.
- **Viewer load**: A/B item view interactive on a normal connection; discovery adds **no** new GitHub
  API calls per run.
- **Determinism**: byte-identical re-export from the same collection input under the pinned toolchain;
  and the existing MB tier re-exports byte-identical after the writer extraction.
- **Collection cost**: ~$25–35 total, one-time.

## Security Considerations
- **Credentials**: OpenRouter + Anthropic funded keys only; **never** personal keys. No key material
  committed.
- **Eval endpoint access/shutdown (explicit):** the Modal vLLM endpoint is **keyless, short-lived, on
  an obscure Modal URL** (as #48/#58) — access control is URL-obscurity + short lifetime, and it is
  **torn down immediately after collection** (remove `min_containers` / stop the app). No persistent
  public inference surface is left running.
- **License compliance**: AFB items MIT — ship `SOURCE.md` + `LICENSE`; do not relicense. Our
  responses/judgments ship under the catalog `license`.
- **Data hygiene**: shipped tier excludes usage/raw/timestamps (#51 allowlist). AFB questions are the
  published instrument.

## Test Scenarios

### Functional Tests
1. **Happy path**: export the AFB collection → `manifest.json` + 150 shards; catalog validates
   against the #51 schema and matches the `AFB_CATALOG` shape; loads in the raw viewer with the 0–4
   scale and the three checkpoint subjects.
2. **Determinism (both directions)**: (a) AFB re-export from the same committed input → byte-identical
   shards + identical `content_fingerprint`; (b) the existing `results-raw/20260803` tier re-exports
   byte-identical after the writer extraction (cross-tier drift guard green).
3. **Schema requireds**: an AFB shard missing verdict `summary`, or a manifest missing `fingerprint`,
   fails validation (guards the "required" facts); the produced catalog has both.
4. **A/B before/after legibility**: a known item (base = 0, dpo ≥ 2) renders two responses with correct
   numeric scores + rationales and ramp colors; the selector swaps B between `mb-sft-guided`/
   `mb-sft-dpo`; presets deep-link the highest-contrast items deterministically.
5. **Discovery/reachability**: the AFB run appears via the raw-run enumerator and a first-class in-app
   link reaches `/results/$runId/$groupId/$itemId` — no hand-typed URL — **without** changing the
   default MB scores run; `RawResultsPage` static MB-vocab guard stays green.
6. **Genericity regressions**: the shipped `routes/rawResults.test.tsx:156` AFB test stays green;
   reserved-axis-key / wrong-`schema_version` catalogs fail soft with a notice.
7. **Collection resilience**: an interrupted collection resumes without re-spending completed
   subject×item cells; completeness validation rejects a run missing any of the 450 cells.

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
| Spend overrun beyond ~$35 | Low | Med | Cold-only, 450 cells, concurrency-bounded; reconcile ACTUAL spend from usage, stop at ceiling, no faith-context. |
| 0–4 ramp mis-signals "4 is best" | Low | Low | `center:2` mid-grey at the calibration target; numeric scores, no band names. |
| Terra JSON contract drift | Low | Med | Fail-fast on non-conforming judge output (`{score∈0..4, rationale}`), bounded retry, no fallback scoring. |
| Endpoint left running post-collection | Low | Med | Explicit teardown (remove `min_containers`/stop app) as a completion step. |

## Expert Consultation
**Date**: 2026-08-08 · **Models Consulted**: codex + claude (per `porch.consultation.models`).
**Verdict**: both `REQUEST_CHANGES` (HIGH confidence) on the initial draft — resolved in this revision.
**Sections Updated**:
- *Desired State / Success Criteria / Test Scenarios*: reframed the three-checkpoint promise to **A/B +
  selector + presets** (viewer is hardcoded A/B, `RawComparison.tsx`); the literal three-up grid is now
  Approach 3, deferred to the architect.
- *Current State / Constraints / Open Questions*: promoted `verdict.summary` and `catalog.fingerprint`
  to **hard exporter requirements** (schema-required, not optional as first drafted); removed the
  "omit fingerprint" branch.
- *Approach 1 / Success Criteria*: made the exporter reuse an **extraction** of a monolithic
  byte-critical writer, gated by a byte-identical re-export of the existing MB tier.
- *Discovery*: specified a **separate raw-run enumerator + landing** (not a merge into
  `loadResultsRuns`), preserving the default MB scores run and the static MB-vocab guard.
- *Collection*: added **resumable/idempotent checkpointing + completeness validation** and a
  **3-subject** collection path (not just a repointed `dpo=` module).
- *Security*: made the eval-endpoint access model + **teardown** explicit; reconciled the "Modal auth"
  vs "keyless URL" wording.
- *Open Questions*: cited the shipped `AFB_CATALOG`/AFB genericity test that pre-answers
  groupBy/condition/scope/scale/subject-IDs; fixed ramp `center:2` semantics.

## Approval
- [ ] Technical Lead Review
- [ ] Product Owner Review
- [ ] Stakeholder Sign-off
- [ ] Expert AI Consultation Complete

## Notes
- **Two deviations surfaced for the architect** (the issue frames #54 as "not a viewer change") and
  **both decided 2026-08-08, to be RE-CONFIRMED at spec-approval**:
  (1) the comparison grid is **A/B**, so three-checkpoint before/after is told via A/B + selector +
  three presets (`base↔dpo`/`base↔sft`/`sft↔dpo`) — architect confirmed **A/B (Approach 1)** over the
  literal N-up grid (Approach 3); the deviation from the issue's "next to" wording is stated so Waleed
  may override to the literal three-column grid at the gate.
  (2) a raw-only catalog is **undiscoverable** without a small discovery/entry-point addition —
  architect **approved in scope**, provided it stays **catalog-generic** (no AFB vocab in SPA core;
  genericity guard applies). The render/model/parser/color path itself needs **no** change.
- **`dpo` = `mb-sft-dpo`** throughout; the serve script's `dpo=` module must be repointed from
  `mb-dpo-full` for the collection run.
- Add the companion-artifact link from the MultiWeights paper's repo/browser once the run is live
  (Review-phase follow-up).
