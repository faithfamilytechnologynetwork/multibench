# Plan: multibrowser — AFB before/after explorer (vanilla Gemma vs MultiWeights)

## Metadata
- **ID**: plan-2026-08-08-multibrowser-afb-before-after
- **Status**: draft
- **Specification**: [codev/specs/54-multibrowser-afb-before-after-.md](../specs/54-multibrowser-afb-before-after-.md)
- **Created**: 2026-08-08

## Executive Summary

Implements the spec's **Approach 1** for the two-subject (**vanilla `gemma-4-31b-it` ↔ DPO incumbent
`mb-sft-dpo`**, Waleed's scope) AFB before/after explorer, riding #51's generic raw-results viewer.

The work splits into a **no-spend, fully-testable build (Phases 1–4)** and a **single money/infra
integration (Phase 5)**:

1. **Extract** a generic raw-writer primitive from the monolithic `export_raw.py` — behaviour-preserving,
   guarded by a byte-identical re-export of the existing `results-raw/20260803` tier.
2. **Build** the AFB collection module (persist response text + Terra 0–4 judging, resumable/idempotent,
   completeness-validated to 300 cells, writing a compact committed intermediate) with the money-touching
   Modal/OpenRouter I/O **injected** so the logic is mock-tested; plus a thin one-time `experiments/54`
   runner that supplies the real clients.
3. **Add** the `analysis export-afb` sibling command that turns the intermediate into a drop-in
   `results-raw/<afb-run-id>/` catalog (shipped-`AFB_CATALOG` shape) via the Phase-1 writer, synthesizing
   each verdict `summary` and the single `dpo − base` preset, stamping both fingerprints.
4. **Generalize** SPA run discovery so a raw-only catalog (no `results/` scores tier) is enumerated and
   reachable through a first-class, **catalog-generic** entry point — no AFB vocabulary in the SPA core.
5. **Run it once** (~$17–23, after a serving smoke and an architect heads-up), commit the intermediate +
   `results-raw/<afb-run-id>/`, verify the real before/after path renders in the SPA, and update docs +
   AFB attribution.

Phases 1–4 land and can be reviewed before any spend; Phase 5 is the only phase that costs money or
touches live infra. All ship as git commits on one branch / one PR (per the issue's PR strategy).

## Success Metrics
- [ ] All specification Success Criteria met (collection, durable preservation, catalog validity,
      loads-unchanged, exporter byte-stability, reachability, before/after legibility, licensing, docs).
- [ ] `workflows/analysis` pytest + `apps/multibrowser` pnpm test both green via `.codev/checks/test.sh`.
- [ ] The existing `results-raw/20260803` tier re-exports **byte-identical** after the Phase-1 extraction.
- [ ] The AFB catalog validates against the #51 schema and renders in the current raw viewer with **no**
      render/model/parser/color change; the shipped genericity test (`routes/rawResults.test.tsx:156`)
      stays green.
- [ ] Actual collection spend reconciled from usage and within ~$17–23; endpoint torn down after.
- [ ] Zero secrets committed/echoed; AFB MIT attribution shipped.

## Phases (Machine Readable)

```json
{
  "phases": [
    {"id": "phase_1", "title": "Extract generic raw-writer primitive (byte-identical refactor)"},
    {"id": "phase_2", "title": "AFB collection module + one-time runner (no spend; mock-tested)"},
    {"id": "phase_3", "title": "analysis export-afb sibling exporter → drop-in catalog"},
    {"id": "phase_4", "title": "SPA generic raw-run discovery + first-class entry point"},
    {"id": "phase_5", "title": "Execute collection run, commit catalog, verify SPA, docs + attribution"}
  ]
}
```

## Phase Breakdown

### Phase 1: Extract generic raw-writer primitive (byte-identical refactor)
**Dependencies**: None

#### Objectives
- Turn the reusable half of `export_raw.py` (shard serialization, size-ceiling validation, gzip
  determinism, the two fingerprints, and manifest assembly from generic pieces) into a **primitive both
  `export-raw` and the new `export-afb` call** — without changing any byte the existing exporter emits.

#### Deliverables
- [ ] A generic writer module (e.g. `workflows/analysis/analysis/raw_writer.py`) exposing, as a
      **streaming finalizer** (not a "hand me a finished catalog" call — MB builds the catalog *after*
      the shard loop, `export_raw.py:805-838`): a shard-writer (canonical pre-gzip bytes → `mtime=0`
      gz), the ceiling validator (≤ 1 MB/shard, ≤ 200 MB/run, **validate-before-write**, buffer-all-then-write),
      `content_fingerprint` accumulation over the shard byte stream, and the **`limit`-gated stale-file
      prune** (`export_raw.py:857`). Shape: the caller iterates shards through the primitive (which
      accumulates `content_lines` + validates + buffers), then calls a finalizer that returns the
      `content_fingerprint`; the caller builds its own `catalog_doc` (MB or AFB) and hands it back to a
      `write(catalog_doc)` call that flushes the manifest + buffered shards and runs the prune.
- [ ] The generic `PRESET_CAP = 12` + `_dedup_per_item` (`export_raw.py:553,584`) pulled into the
      primitive/shared helpers for Phase 3 reuse (`_entry` stays MB-specific and does **not** move).
- [ ] `export_raw.py` refactored to call the primitive; MB-specific reading/catalog/preset code stays put.
- [ ] The byte-identical guard (below), committed as a golden fixture + a tier-recompute test.

#### Implementation Details
- Keep `_catalog_doc`, MB preset computation, `CANONICAL_SUBJECTS`, and the MB reader
  (`iter_tradition_raw`) in `export_raw.py`; move only the **generic writer/ceiling/fingerprint/prune
  plumbing** into `raw_writer.py`. Pure move-then-call — **no** change to `mtime=0` / sorted-keys / gzip
  settings (byte-stability is load-bearing).
- `fingerprint` (the judgment stream) is computed by each caller and placed into its own `catalog_doc`
  (AFB stamps a self-consistent value); the primitive owns only `content_fingerprint`.

#### Acceptance Criteria (the byte-identical guard is EXECUTABLE — the `20260803` source roots are NOT committed)
- [ ] **Golden-hash fixture**: *before* editing `export_raw.py`, export the committed MB test fixtures
      through the current code and record per-file `sha256` (+ both manifest fingerprints) into a
      committed golden JSON; after the extraction, a test re-exports and asserts **every** hash equals
      the golden — the real regression gate.
- [ ] **Committed-tier recompute** (no source roots needed): a test `gzip.decompress`es the **521
      committed `results-raw/20260803` shards** to their pre-gz bytes, feeds them through the extracted
      primitive's `content_fingerprint` accumulation, and asserts it equals the value committed in
      `results-raw/20260803/manifest.json`. Mark `slow` if 121 MB of IO is too heavy for the default run.
- [ ] Existing `test_export_raw.py`, `test_export_raw_writer.py`, `test_export_raw_presets.py` pass unchanged.
- [ ] `uv --project workflows/analysis run pytest workflows/analysis` green.

#### Test Plan
- **Unit**: writer emits `mtime=0` deterministic gz; ceiling validator aborts before writing on breach;
  the `limit`-gated prune behaves as before.
- **Regression**: the golden-hash fixture test + the committed-tier `content_fingerprint` recompute.

#### Rollback Strategy
Revert the commit; `export_raw.py` returns to its monolithic form (no data or schema change was made).

#### Risks
- **Risk**: the extraction changes MB output bytes. **Mitigation**: golden-hash fixture + committed-tier
  recompute gate the phase; pure move-then-call, not a rewrite.
- **Risk**: the finalizer reshuffles MB's during-loop accumulation (items/subjects/judges/preset cells).
  **Mitigation**: leave that accumulation in `export_raw.py`; the primitive only takes shards + returns
  the content fingerprint, so MB's control flow is unchanged.

---

### Phase 2: AFB collection module + one-time runner (no spend; mock-tested)
**Dependencies**: None

#### Objectives
- Produce the **compact committed intermediate** — for each of 150 AFB items × 2 subjects (base, dpo),
  the cold-condition **response text** + Terra 0–4 `{score, rationale}` — via a **resumable, idempotent,
  completeness-validated** collector whose money-touching I/O (subject endpoint + Terra judge) is
  **injected** so the logic is unit-tested without spend.

#### Deliverables
- [ ] `workflows/analysis/analysis/afb_collect.py` — **SDK-free** (imports no `openai`; pure logic +
      injected callables so its pytest needs no SDK/network): the intermediate schema + a `collect(...)`
      taking injected `generate(subject, prompt)->str` and `judge(question, response)->{score,rationale}`,
      that persists cells in **two atomic state transitions** (see below), **skips already-satisfied
      state on resume**, and **validates completeness** (exactly 150 unique items × 2 subjects = 300
      cells, each with a response AND a 0–4 verdict) before marking the run done.
- [ ] `experiments/54_afb_before_after/`: a thin `collect_afb.py` runner that constructs the real
      OpenAI-SDK clients (subject endpoint + OpenRouter Terra) and injects them into `collect(...)`; plus
      a **copy** of #58's `serve_gemma_eval.py` (do **NOT** edit #58's committed file — it is that
      experiment's provenance) with `dpo=` set to `/vol/runs/mb-sft-dpo/adapter`, **base+dpo only**.
- [ ] pytest coverage with **mock** generate/judge callables (no network, no spend).

#### Implementation Details
- **Runner environment**: `afb_collect.py` lives in `workflows/analysis` (SDK-free, dispatcher-tested).
  The `experiments/54` runner needs the OpenAI SDK, so it is invoked under an env that has it —
  `uv --project workflows/judging run python experiments/54_afb_before_after/collect_afb.py` (judging
  depends on `openai`; analysis does not). Keys read at runtime from
  `/Users/mwk/Development/fftn/taqwabench/.env`; **never committed or echoed**.
- **Intermediate schema** (committed JSON at **`experiments/54_afb_before_after/data/collection.json`** —
  verified not gitignored; the export input-of-record): `{schema_version, run_id, condition:"cold",
  subjects:["gemma-4-31b-it","mb-sft-dpo"], judge:"openai/gpt-5.6-terra", decoding:{temperature, seed,
  max_tokens}, cells:[{item_id, question, subject, response, score, rationale}]}`. Item ids map
  `q0001→AFB-001` … `q0150→AFB-150`. **No usage/cost/timestamps** in this file (allowlist discipline).
- **Two-state atomic checkpointing** (so a judging failure after generation never repays generation):
  transition 1 persists `{response}` for a cell; transition 2 adds `{score, rationale}`. Each write is an
  atomic replace (write temp + `os.replace`) or a per-cell sidecar the collector coalesces; resume skips
  cells whose state is already satisfied. Concurrency: writes serialized through a single writer
  (workers return results; the main thread persists) to keep atomic replacement safe.
- **Decoding is pinned and recorded**, identical for both subjects (else the before/after contrast is
  confounded by sampling, not weights): fixed `temperature` + `seed` + `max_tokens`, stamped into the
  intermediate `decoding` block and the run log. Judge model string pinned to `openai/gpt-5.6-terra`.
- **Judge contract**: fail-fast on any non-conforming Terra output (`{score∈0..4, rationale}`), bounded
  retry, **no fallback scoring**.
- **Usage/cost capture**: the runner tallies provider usage/cost to a **local, uncommitted** run log
  (`experiments/54_afb_before_after/data/run.log`, gitignored) for the Phase-5 spend reconciliation —
  never into the shipped intermediate/catalog.
- **Serving**: base bf16 + the `mb-sft-dpo` LoRA module; endpoint keyless/short-lived; teardown is a
  Phase-5 step. The runner does a **serving smoke** (one base + one dpo call) before the full loop.

#### Acceptance Criteria
- [ ] Resume test: pre-seed N completed cells → collector issues only the remaining `(300 − N)` calls.
- [ ] **Judge-after-generate resume**: a cell with a persisted response but no verdict (interrupted after
      generation) resumes by issuing **only the judge call**, not a re-generation.
- [ ] Completeness test: a run missing any cell (or with a non-0..4 score) is **rejected** before export.
- [ ] Idempotence test: re-running a complete collection issues **zero** subject/judge calls and leaves the
      intermediate byte-unchanged.
- [ ] Decoding block is present and identical across subjects in the produced intermediate.
- [ ] `uv --project workflows/analysis run pytest workflows/analysis` green.

#### Test Plan
- **Unit**: schema round-trip; checkpoint/resume; completeness/validation; judge fail-fast on bad JSON.
- **Manual (Phase 5)**: serving smoke + the real run.

#### Rollback Strategy
Revert the commit; no committed data yet (the real intermediate is produced/committed in Phase 5).

#### Risks
- **Risk**: collection logic in `experiments/` would be untested by the dispatcher. **Mitigation**: the
  tested logic lives in `workflows/analysis` (dispatcher-registered); `experiments/54` is a thin,
  injection-only wiring layer.
- **Risk**: partial-write corruption of the intermediate. **Mitigation**: atomic per-cell append/merge;
  completeness validation before any export consumes it.

---

### Phase 3: `analysis export-afb` sibling exporter → drop-in catalog
**Dependencies**: Phase 1 (writer primitive), Phase 2 (intermediate schema)

#### Objectives
- Turn the committed intermediate into a drop-in `results-raw/<afb-run-id>/` catalog matching the shipped
  `AFB_CATALOG` shape, written through the Phase-1 primitive (ceilings + determinism + fingerprints).

#### Deliverables
- [ ] `workflows/analysis/analysis/export_afb.py`: builds the catalog + one shard per item and writes via
      the Phase-1 writer.
- [ ] `analysis export-afb` CLI command in `workflows/analysis/analysis/cli.py` (input = the intermediate;
      `--run-id`, `--out results-raw`).
- [ ] Tests against a small **synthetic** intermediate fixture.

#### Implementation Details
- **Catalog**: `schema_version:1`; `dataset {title, description, language:"en", license:"MIT"}`;
  `scale {min:0, center:2, max:4}`; sequential `ramp` (dark→mid→light, catalog data);
  `subjects:[{id:"gemma-4-31b-it",label},{id:"mb-sft-dpo",label}]`;
  `judges:[{key:"terra", label:"gpt-5.6-terra", fullGrid:true}]`;
  `conditionAxes:[{key:"condition", label:"Condition", values:[{id:"cold", label:"Cold"}]}]`;
  `groupBy:{key:"instrument", label:"Instrument"}`; `scopes:[{id:"single", label:"single"}]`;
  `items:[{id:"AFB-00N", label:<question label>, group:"afb-150", shard:"afb-150/AFB-00N.json.gz"}]`;
  `presets:[<dpo−base>]`; required `fingerprint`; `content_fingerprint`.
- **Item label (deterministic truncation)**: `label` = the question with whitespace collapsed, cut to
  **≤ 80 chars on a word boundary** (last space ≤ 80), appending `…` when truncated; the full question is
  always the shard's user turn. (Fixed rule — spec Important item.)
- **Shard** per item: `contexts:{}` (cold is context-free); `cells:[{subject, conditions:{condition:"cold"},
  transcript:[{role:"user",content:question},{role:"assistant",content:response}], verdicts:[{judge:"terra",
  scope:"single", score, summary:<synth>, rationale}]}]` for both subjects.
- **`summary` synthesis (schema-required, FIXED phrasing — not "e.g.")**: exact map by integer score —
  `0`→"no religious representation", `1`→"passing mention of religion", `2`→"meaningful religious
  reference", `3`→"balanced religious and secular", `4`→"predominantly religious". Every verdict gets a
  non-empty `summary`; `rationale` carries Terra's text verbatim.
- **Preset (`dpo − base`) — exact rule**: rank items by the **absolute** delta `|score(mb-sft-dpo) −
  score(gemma-4-31b-it)|` (honors the approved spec's `|dpo − base|`), descending; **N ≤ 12** (reuse the
  Phase-1 `PRESET_CAP`); **one entry per item** (reuse `_dedup_per_item`); tie-break stable on
  `group → item` id ascending. Each entry `params:{group, item, scope:"single", a:"gemma-4-31b-it",
  b:"mb-sft-dpo", conditions:{condition:"cold"}}`. *(Deviation flag for the architect: a **signed**
  `dpo − base` descending rank would surface repairs-only and drop regressions — arguably better for the
  omission→repair headline. Left as `|·|` per the approved spec + architect's earlier wording; will confirm
  at plan-approval whether to switch to signed.)*
- **`fingerprint`**: a self-consistent sha256 over the sorted resolved-verdict stream (no cross-tier
  partner; the viewer tolerates the lookup miss). `content_fingerprint` over the shard byte stream (from
  the Phase-1 primitive).

#### Acceptance Criteria
- [ ] Exported catalog parses/validates like `AFB_CATALOG` (mirror `lib/rawData.test.ts` expectations):
      `scale {0,2,4}`, `groupBy.key==="instrument"`, `conditionAxes[0].key==="condition"`, two subjects,
      every verdict has a `summary`, `fingerprint` present.
- [ ] Re-export from the same fixture is **byte-identical** (fingerprints stable).
- [ ] Preset is deterministic and ≤ 12, one entry per item.
- [ ] Size ceilings honored (they will be; assert the validator ran).
- [ ] `uv --project workflows/analysis run pytest workflows/analysis` green.

#### Test Plan
- **Unit**: catalog field-by-field vs the fixture shape; summary present for scores 0–4; preset ordering/cap.
- **Integration**: synthetic intermediate → full `results-raw/<id>/` tree; determinism re-run.

#### Rollback Strategy
Revert the commit; the CLI subcommand and module are additive (no change to `export-raw`).

#### Risks
- **Risk**: catalog drift from the schema the viewer enforces. **Mitigation**: test mirrors the shipped
  `AFB_CATALOG`/parser expectations; Phase 4 also renders it in-app.

---

### Phase 4: SPA generic raw-run discovery + first-class entry point
**Dependencies**: None (uses fixtures; catalog shape is settled by shipped tests)

#### Objectives
- Make a raw-only catalog (no `results/` scores tier) **discoverable and reachable** in the SPA through a
  first-class, **catalog-generic** entry point, without disturbing the default MultiBench scores run and
  without adding GitHub API calls.

#### Deliverables (reuse shipped generic machinery — do NOT hand-roll)
- [ ] A **separate** raw-run enumerator `rawRunIds(entries)` in `queries.ts` (regex
      `^results-raw\/([^/]+)\/manifest\.json$`) from the already-walked tree (`WALK_DIRS` includes
      `results-raw`), plus its **own** hook — it must **never** route ids through `loadResultsManifest`
      (that returns a `notice("error","results",…,"manifest not found")` for a scores-tier-less run,
      `queries.ts:194-207`, which would paint a false red error on `/results`).
- [ ] A first-class, catalog-generic **raw-run landing** that resolves the run's catalog via the shipped
      `useRawCatalog(sha, runId, /*expectedFingerprint*/ null)` (`queries.ts:536`) and renders the shipped
      `<RawPresets>` (`components/RawPresets.tsx`, already generic — emits `/results/$runId/$groupId/$itemId`
      links with `{...conditions, a, b?, scope, judge}`), passing `judge = catalog.judges.find(j =>
      j.fullGrid)?.key` — mirroring `ResultsPage.tsx:107-121,251-260`.
- [ ] A **catalog-generic item index** on that landing (list `catalog.items`, each linking to
      `/results/$runId/$item.group/$item.id` **with `a=catalog.subjects[0].id`, `b=catalog.subjects[1].id`,
      `scope=catalog.scopes[0].id`, `judge=<fullGrid>`**) so **all 150 items are reachable in-app** — not
      only the ≤12 preset entries (AFB has no corpus cross-link and `RawResultsPage` has no item picker).
- [ ] Extend the **static MB-vocab guard** (`rawData.test.ts` file list) to include the new landing/entry
      file(s), and additionally forbid the AFB literals `"afb-150"`, `"mb-sft-dpo"`, `"AFB"` there.
- [ ] Tests.

#### Implementation Details
- **Links MUST carry `a` and `b`.** `parseRawSelection` defaults `b` to `null` (`rawSelection.ts:46-48`),
  so a bare item link renders **vanilla only, single column** — failing the before/after criterion. Both
  the preset links (already carry a/b) and the new item-index links carry `a=subjects[0]`, `b=subjects[1]`
  generically.
- **Everything MB-vocab-free**: read `dataset.title`, `groupBy.label`, `items`, `subjects` from the raw
  manifest; no AFB literals in SPA core. Reuse the raw loader/source-resolver unchanged (the null scores
  fingerprint path already exists).
- **Do not disturb the score tier**: `defaultRunId` and the `/results` leaderboard come from
  `loadResultsRuns` (scores) untouched; the raw-run landing is an additive, separate surface.

#### Acceptance Criteria
- [ ] A raw-only fixture run (AFB catalog, **no** `results/` manifest) is discovered and its landing lists
      **all** items; a rendered item link resolves to `/results/$runId/afb-150/AFB-001?a=gemma-4-31b-it&b=mb-sft-dpo&scope=single&judge=terra`.
- [ ] **Two-column render assertion**: landing on that link renders **both** response columns (base + dpo),
      not a single column.
- [ ] **No false notice** (spec NFT-3): a raw-only run with a null scores fingerprint produces **no**
      "manifest not found"/coherence error notice on `/results` or the landing.
- [ ] The default MB scores run selection + leaderboard are unchanged (regression test).
- [ ] No new GitHub API calls beyond the existing tree walk (assert in the data-layer test).
- [ ] The shipped genericity test (`routes/rawResults.test.tsx:156`) and the (extended) static MB-vocab
      guard stay green; the new entry-point file is covered by the guard.
- [ ] `pnpm -C apps/multibrowser test` green.

#### Test Plan
- **Unit**: `rawRunIds` regex; the raw-run hook never calls `loadResultsManifest`; run-list separation.
- **Integration (RTL)**: raw-only run discoverable; item index lists all items; landed item link renders
  two columns; no false notice; default MB run unchanged; typecheck/lint clean.

#### Rollback Strategy
Revert the commit; discovery returns to scores-only (the AFB catalog would again be deep-link-only).

#### Risks
- **Risk**: hand-rolling a link that drops `b` → single-column. **Mitigation**: reuse `<RawPresets>` +
  generic item-index links that always carry a/b; the two-column render assertion guards it.
- **Risk**: routing raw ids through `loadResultsManifest` → false error notice. **Mitigation**: a separate
  enumerator/hook that never touches the scores manifest loader; the no-false-notice acceptance test.
- **Risk**: leaking AFB vocab past the guard's file list. **Mitigation**: extend the guard to the new file
  and forbid the AFB literals.

---

### Phase 5: Execute collection run, commit catalog, verify SPA, docs + attribution
**Dependencies**: Phases 1–4

#### Objectives
- Do the one-time run, commit the durable artifacts, prove the real user path renders, and finish docs +
  licensing. **This is the only phase that spends money or touches live infra.**

#### Deliverables
- [ ] **BLOCKING spend gate**: message the architect and **wait for an explicit approval reply** before
      running — a heads-up is not an authorization (irreversible-action discipline). Then run a **serving
      smoke** (adapter integrity re-confirmed live: one base + one `mb-sft-dpo` call) **before** the loop.
- [ ] The real collection run (base + dpo × 150 cold, pinned decoding) → the committed compact
      **intermediate** artifact (`experiments/54_afb_before_after/data/collection.json`).
- [ ] **Reconciliation sanity-check vs #48's published numbers** BEFORE committing: compute the collected
      base/dpo distribution (mean, P≥2) and compare to #48 (base ≈ 0 / ~1% ≥2; dpo ~27% ≥2). If it diverges
      materially, **escalate to the architect** rather than committing a companion artifact that contradicts
      the paper (repo standing lesson: derived numbers must reconcile with the authoritative source).
- [ ] `analysis export-afb` → committed `results-raw/afb-<YYYYMMDD>/`, size-validated.
- [ ] **Actual spend reconciled** from the local run log (target ~$17–23); **endpoint torn down** (remove
      `min_containers`/stop app) — confirmed no lingering container.
- [ ] **Deployed-path** in-app verification (state target = the Railway deployment): the AFB run is
      discoverable, the before/after A/B view renders on the **real** committed data, and — since the baked
      bundle ships only the MB run — the AFB run **falls back to GitHub cleanly with no false coherence
      notice** (the known `serve -s dist` baked-miss landmine).
- [ ] AFB **MIT attribution** carried (SOURCE.md/LICENSE referenced/provenance in the run dir or README).
- [ ] Docs: `results-raw/README.md` gains a **second-catalog (AFB) + raw-only discovery** note; the
      MultiWeights paper companion-artifact link plan recorded (link added once live).
- [ ] Arch-doc routing via the `update-arch-docs` skill if a durable system-shape fact warrants it.

#### Implementation Details
- Run-id: `afb-<YYYYMMDD>` chosen at run time. Commit **only** the intermediate + `results-raw/afb-<YYYYMMDD>/`
  (never secrets, never the gitignored `run.log`/`tmp/`). Explicit `git add` per file.
- If the architect prefers, Phases 1–4 can be reviewed/merged before authorizing the Phase-5 spend
  (the code is fully testable without it) — see Notes.

#### Acceptance Criteria
- [ ] Explicit architect approval received before the run; serving smoke passed.
- [ ] 300/300 cells collected and judged; completeness validation passed; distribution reconciles with #48
      (or divergence escalated); spend within ~$17–23 (reconciled from the run log).
- [ ] Committed catalog validates + renders in the SPA on real data, on the **deployed** site, with clean
      GitHub fallback (no false coherence notice).
- [ ] Endpoint confirmed torn down; no secrets in the diff.
- [ ] `.codev/checks/test.sh` green for both touched apps.

#### Test Plan
- **Manual**: serving smoke; full-run monitoring; real-path SPA verification (the "it works" check).
- **Automated**: the committed catalog passes the exporter/schema tests; SPA tests green.

#### Rollback Strategy
Data is additive drop-in; to revert, `git rm -r results-raw/<afb-run-id>/` + the intermediate. No core
code depends on the presence of the AFB run.

#### Risks
- **Risk**: adapter missing/altered at run time despite the earlier verify. **Mitigation**: serving smoke
  gates the spend; escalate to architect if it fails.
- **Risk**: spend overrun. **Mitigation**: cold-only 300 cells, concurrency-bounded, reconcile ACTUAL
  usage, stop at ceiling; no faith-context.
- **Risk**: endpoint left running. **Mitigation**: teardown is an explicit acceptance item.

## Dependency Map
```
Phase 1 ─┐
         ├─→ Phase 3 ─┐
Phase 2 ─┘            ├─→ Phase 5
Phase 4 ──────────────┘
```
(Phases 1, 2, 4 have no inter-dependencies and could be built in any order; Phase 3 needs 1 + 2;
Phase 5 needs all of 1–4. Porch runs them sequentially in the listed order.)

## Resource Requirements
### Development Resources
- **Environment**: `uv` (`workflows/analysis`), `pnpm` (`apps/multibrowser`); Modal CLI (machine-authed)
  for Phase 5; OpenRouter + Anthropic keys from `taqwabench/.env` for Phase 5 only.
### Infrastructure
- Modal vLLM endpoint (base + `mb-sft-dpo` LoRA), Phase 5 only; volume `gemma-dpo` (`mb-sft-dpo` verified).
- New committed data: the compact intermediate + `results-raw/<afb-run-id>/` (single-digit MB).

## Integration Points
### External Systems
- **Modal** (Phase 5): subject serving; keyless short-lived; **fallback**: none — serving smoke gates spend.
- **OpenRouter / Terra** (Phase 5): 0–4 judge; **fallback**: fail-fast + bounded retry, no fallback scoring.
- **GitHub raw + git-trees** (Phase 4): SPA runtime data; **fallback**: existing baked/GitHub resolution.
### Internal Systems
- **#51 raw viewer + `results-raw/` contract** (render path unchanged); **#51 export machinery**
  (`export_raw.py` writer, extracted in Phase 1); **#58 serve script** (repointed in Phase 2).

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Writer extraction changes MB bytes | M | H | Golden-hash fixture + committed-tier `content_fingerprint` recompute (Phase 1) | builder |
| Collection interruption / judge-fail repays generation | M | H | Two-state atomic checkpoint + judge-after-generate resume (Phase 2) | builder |
| Entry-point link drops `b` → single-column view | M | H | Reuse `<RawPresets>` + a/b-carrying item index; two-column render assertion (Phase 4) | builder |
| Only ≤12/150 items reachable in-app | M | M | Catalog-generic item index lists all `catalog.items` (Phase 4) | builder |
| Raw ids routed through scores loader → false error notice | M | M | Separate `rawRunIds` enumerator/hook; no-false-notice test (Phase 4) | builder |
| Responses are a fresh sample that contradicts #48 | M | H | Pin+record decoding; reconcile base/dpo dist vs #48 before commit; escalate on divergence (Phase 5) | builder |
| Catalog drifts from viewer schema | L | M | Tests mirror shipped `AFB_CATALOG`; in-app render (Phase 4/5) | builder |
| Discovery leaks AFB vocab / trips guard | L | M | Manifest-driven; extended static guard covers the entry file (Phase 4) | builder |
| Spend overrun | L | M | Cold-only 300 cells; reconcile ACTUAL usage from run log; stop at ceiling | builder |
| Adapter missing at run time | L | H | Serving smoke gates the spend; escalate | builder/architect |

### Schedule Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Phase 5 blocked on spend authorization | L | L | Pre-authorized (~$17–23); architect heads-up before run | architect |

## Validation Checkpoints
1. **After Phase 1**: MB tier re-exports byte-identical; existing export tests green.
2. **After Phase 2**: resume/idempotence/completeness tests green (no spend).
3. **After Phase 3**: synthetic intermediate → valid, deterministic AFB catalog.
4. **After Phase 4**: raw-only run discoverable + rendered from fixtures; default MB run unchanged.
5. **Before Production (Phase 5)**: serving smoke; spend reconciled; real-path SPA render; endpoint down.

## Monitoring and Observability
### Metrics to Track
- Phase 5 run: cells completed / 300; per-cell subject+judge latency; **actual token/$ spend vs ~$17–23**.
### Logging Requirements
- Collection: per-cell progress + retries at INFO; the intermediate file IS the durable record.
### Alerting
- N/A (one-time run); the builder monitors the run and stops on ceiling breach.

## Documentation Updates Required
- [ ] `results-raw/README.md` — second-catalog (AFB) example + raw-only discovery note.
- [ ] AFB provenance/attribution (SOURCE.md/LICENSE) alongside the committed run.
- [ ] `codev/reviews/54-*.md` (Review phase) + companion-artifact link plan for the paper.
- [ ] Arch/lessons routing via `update-arch-docs` if a durable fact warrants it.

## Post-Implementation Tasks
- [ ] Confirm endpoint torn down (no lingering Modal container).
- [ ] Add the companion-artifact link from the MultiWeights paper repo/browser once live (Review follow-up).
- [ ] Reconcile and record actual spend.

## Expert Review
**Date**: 2026-08-08 · **Model**: codex + claude (per `porch.consultation.models`). Both `REQUEST_CHANGES`
(HIGH), code-verified. **Resolved in this revision.**
**Key Feedback → Plan Adjustments**:
- *Byte guard not executable* (the `20260803` source roots aren't committed) → Phase 1 now uses a
  **golden-hash fixture** + a **committed-tier `content_fingerprint` recompute** (decompress the 521 gz
  shards through the extracted primitive).
- *Primitive signature self-contradictory* (takes a built catalog yet computes `content_fingerprint`; MB
  builds the catalog after the shard loop) → reshaped as a **streaming finalizer**; MB's during-loop
  accumulation + the `limit`-gated prune stay in `export_raw.py`; generic `PRESET_CAP`/`_dedup_per_item`
  pulled out for Phase 3.
- *Phase 4 reinvented shipped machinery & landed single-column, 138/150 unreachable* → rewritten to
  **reuse `useRawCatalog` + `<RawPresets>`**, add a **catalog-generic item index** (all 150 reachable),
  make every link **carry `a`+`b`** (a two-column assertion guards it), use a **separate `rawRunIds`
  enumerator** (never `loadResultsManifest` → no false notice, maps spec NFT-3), and **extend the static
  guard** to the new file.
- *No decoding pinned / no reconciliation with #48* → Phase 2 **pins+records decoding** (temp/seed/max_tokens,
  identical across subjects) + judge string; Phase 5 **reconciles the base/dpo distribution vs #48** before
  commit and escalates on divergence.
- *Checkpoint could repay generation* → **two-state atomic** persist (response, then verdict) + resume.
- *Unspecified items fixed*: intermediate path `experiments/54_afb_before_after/data/collection.json`;
  **exact** score→summary phrasing; deterministic ≤80-char word-boundary label truncation; preset rule
  stated exactly as `|dpo − base|` (signed alternative flagged for plan-approval); **copy** (not mutate)
  #58's serve script; **blocking** spend gate (explicit architect approval, not a notification);
  deployed-path verification incl. clean GitHub fallback; runner env (`uv --project workflows/judging`,
  SDK-free `afb_collect`); usage/cost to a **gitignored** run log, never shipped.

## Approval
- [ ] Technical Lead Review
- [ ] Engineering Manager Approval
- [ ] Resource Allocation Confirmed
- [ ] Expert AI Consultation Complete

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-08-08 | Initial plan | Spec 54 approved (Waleed); vanilla↔DPO scope | builder |
| 2026-08-08 | Phase-3 ramp is DIVERGING (cool→slate-grey→warm), not the literal "sequential dark→mid→light" phrasing | The `center:2 → grey` + anti-"4-is-best" intent (both stated) require a grey center → diverging; a true sequential lightness ramp is theme-fragile. Center `#8B95A1` chosen distinct from the viewer's no-data grey. Flagged for architect acknowledgement at PR. | builder |
| 2026-08-12 | Phase-5 deployed-path (Railway) acceptance check moved to **post-merge Verify** | Architect FORMAL sign-off: the live site reads `main` at runtime and #54's discovery UI is new SPA code that exists in prod only after merge + `railway up`; deploying an unreviewed branch to prod is prohibited; the `serve -s dist` baked-miss/GitHub-fallback is only testable live. Pre-merge stand-in = the real-committed-data RTL render test. | architect + builder |

## Notes
- **Spend isolation**: Phases 1–4 are no-spend and fully testable; the architect may review/merge them
  before authorizing the Phase-5 run. The builder will notify the architect (and run a serving smoke)
  **before** spending, per the irreversible-action discipline.
- **`dpo` = `mb-sft-dpo`** throughout; Phase 2 **copies** #58's `serve_gemma_eval.py` into
  `experiments/54_afb_before_after/` with `dpo=/vol/runs/mb-sft-dpo/adapter` (base+dpo only) — the #58
  committed file is **never edited** (it is that experiment's provenance).
- **Blocking spend gate**: Phase 5 sends the architect an explicit request and **waits for approval**
  before spending; a heads-up is not authorization.
- **Preset rule** ships as `|dpo − base|` (approved spec); a signed-`dpo − base` refinement is flagged for
  plan-approval. Decoding params are pinned + recorded; the collected distribution is reconciled vs #48.
- **Secrets**: `OPENROUTER_API_KEY` + `ANTHROPIC_API_KEY` read at runtime from
  `/Users/mwk/Development/fftn/taqwabench/.env`; never committed or echoed.
- **Item id mapping**: `q0001…q0150` → `AFB-001…AFB-150`; group `afb-150`; shards
  `afb-150/AFB-00N.json.gz`.
