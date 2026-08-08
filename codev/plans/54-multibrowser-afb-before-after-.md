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
- [ ] A generic writer module (e.g. `workflows/analysis/analysis/raw_writer.py`) exposing: a
      shard-writer (canonical pre-gzip bytes → `mtime=0` gz), the ceiling validator (≤ 1 MB/shard,
      ≤ 200 MB/run, validate-before-write), the fingerprint helpers (already in `analysis.fingerprint`),
      and a `write_catalog_and_shards(run_id, out, catalog_doc, shards)` entry point.
- [ ] `export_raw.py` refactored to call the primitive; MB-specific reading/catalog/preset code stays put.
- [ ] Tests proving behaviour-preservation (below).

#### Implementation Details
- Keep `_catalog_doc`, preset computation, `CANONICAL_SUBJECTS`, and the MB reader (`iter_tradition_raw`)
  in `export_raw.py`; move only the **generic writer/ceiling/fingerprint plumbing** into `raw_writer.py`.
- The primitive must be **catalog-agnostic**: it takes an already-built `catalog_doc` (dict) and an
  iterable of `(shard_path, shard_doc)` and does serialization + ceilings + gz + write + the
  `content_fingerprint` over the shard byte stream. `fingerprint` (judgment stream) is computed by the
  caller and passed into `catalog_doc` (AFB will stamp its own self-consistent value).
- No change to `mtime=0` / sorted-keys / gzip settings (byte-stability is load-bearing).

#### Acceptance Criteria
- [ ] Existing `test_export_raw.py`, `test_export_raw_writer.py`, `test_export_raw_presets.py` pass unchanged.
- [ ] A test re-exports the MB fixture (and, where feasible in-test, asserts identical
      `fingerprint` + `content_fingerprint`) through the extracted primitive — **byte-identical**.
- [ ] `uv --project workflows/analysis run pytest workflows/analysis` green.

#### Test Plan
- **Unit**: writer emits `mtime=0` deterministic gz; ceiling validator aborts before writing on breach.
- **Integration/regression**: MB export round-trips byte-identical (the cross-tier drift guard).

#### Rollback Strategy
Revert the commit; `export_raw.py` returns to its monolithic form (no data or schema change was made).

#### Risks
- **Risk**: the extraction changes MB output bytes. **Mitigation**: the byte-identical regression test
  gates the phase; do a pure move-then-call refactor, not a rewrite.

---

### Phase 2: AFB collection module + one-time runner (no spend; mock-tested)
**Dependencies**: None

#### Objectives
- Produce the **compact committed intermediate** — for each of 150 AFB items × 2 subjects (base, dpo),
  the cold-condition **response text** + Terra 0–4 `{score, rationale}` — via a **resumable, idempotent,
  completeness-validated** collector whose money-touching I/O (subject endpoint + Terra judge) is
  **injected** so the logic is unit-tested without spend.

#### Deliverables
- [ ] `workflows/analysis/analysis/afb_collect.py`: the intermediate schema + a `collect(...)` that takes
      injected `generate(subject, prompt)->str` and `judge(question, response)->{score,rationale}`
      callables, **checkpoints each completed cell to disk immediately**, **skips already-present cells on
      resume**, and **validates completeness** (exactly 150 unique items × 2 subjects = 300 cells, each
      judged 0–4) before marking the run done.
- [ ] `experiments/54_afb_before_after/`: a thin `collect_afb.py` runner wiring the real Modal endpoint
      (base + `dpo`=`mb-sft-dpo`) and the OpenRouter Terra client into `collect(...)`, plus the serve
      script (reuse #58's `serve_gemma_eval.py` with `dpo=` repointed to `/vol/runs/mb-sft-dpo/adapter`,
      **base+dpo only**). Keys read at runtime from `/Users/mwk/Development/fftn/taqwabench/.env`.
- [ ] pytest coverage with **mock** generate/judge callables (no network, no spend).

#### Implementation Details
- **Intermediate schema** (committed JSON; the export input-of-record): `{schema, run_id, condition:"cold",
  subjects:[...], judge:"gpt-5.6-terra", cells:[{item_id, question, subject, response, score, rationale}]}`.
  Item ids map `q0001→AFB-001` … `q0150→AFB-150`; the question text is carried for the shard transcript.
- **Checkpointing**: append/merge each finished cell to the intermediate file (or a per-cell sidecar the
  collector coalesces) so an interruption loses at most the in-flight cell; resume reads existing cells
  and only issues the missing ones.
- **Judge contract**: fail-fast on any non-conforming Terra output (`{score∈0..4, rationale}`), bounded
  retry, **no fallback scoring** (per repo fail-fast principle).
- **Serving**: base bf16 + the `mb-sft-dpo` LoRA module; endpoint keyless/short-lived; teardown is a
  Phase-5 step. The runner does a **serving smoke** (one base + one dpo call) before the full loop.

#### Acceptance Criteria
- [ ] Resume test: pre-seed N completed cells → collector issues only the remaining `(300 − N)` calls.
- [ ] Completeness test: a run missing any cell (or with a non-0..4 score) is **rejected** before export.
- [ ] Idempotence test: re-running a complete collection issues **zero** subject/judge calls and leaves the
      intermediate unchanged.
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
  `items:[{id:"AFB-00N", label:<question, truncated>, group:"afb-150", shard:"afb-150/AFB-00N.json.gz"}]`;
  `presets:[<dpo−base>]`; required `fingerprint`; `content_fingerprint`.
- **Shard** per item: `contexts:{}` (cold is context-free); `cells:[{subject, conditions:{condition:"cold"},
  transcript:[{role:"user",content:question},{role:"assistant",content:response}], verdicts:[{judge:"terra",
  scope:"single", score, summary:<synth>, rationale}]}]` for both subjects.
- **`summary` synthesis (schema-required)**: deterministic from the score band (e.g. `0`→"no religious
  representation", `1`→"passing mention", `2`→"meaningful reference", `3`→"balanced", `4`→"predominantly
  religious"), so every verdict has a non-empty `summary`; `rationale` carries Terra's text. Final phrasing
  fixed here (spec Important item).
- **Preset (`dpo − base`)**: deterministic top-N by `score(dpo) − score(base)` per item, **N ≤ 12**, one
  entry per item, magnitude-sorted with a stable `group → item` tie-break; each entry
  `params:{group, item, scope:"single", a:"gemma-4-31b-it", b:"mb-sft-dpo", conditions:{condition:"cold"}}`.
- **`fingerprint`**: a self-consistent sha256 over the sorted resolved-verdict stream (no cross-tier
  partner; the viewer tolerates the lookup miss). `content_fingerprint` over the shard byte stream.

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

#### Deliverables
- [ ] A generic `results-raw/` run enumerator in `apps/multibrowser/src/lib/queries.ts` (sibling to
      `resultsRunIds`, regex `^results-raw\/([^/]+)\/manifest\.json$`) sourced from the already-walked tree
      (`WALK_DIRS` already includes `results-raw`).
- [ ] Run-list assembly that **merges raw-only runs** (those with a `results-raw/` manifest and no
      `results/` manifest) into the browsable set **without** changing `defaultRunId` (the MB scores
      default is untouched).
- [ ] A first-class entry point/landing (e.g. a section on `/results` and/or the index) that links a
      raw-only run into `/results/$runId/$groupId/$itemId`, **initial target = the run's first preset entry
      if present, else its first item**.
- [ ] Tests.

#### Implementation Details
- Keep everything **MB-vocab-free**: read `dataset.title`, `groupBy.label`, `items` from the raw manifest;
  no AFB literals in SPA core. The `RawResultsPage` static MB-vocab guard must stay green.
- Do **not** merge into the score-tier `loadResultsRuns` in a way that requires a `ResultsManifest`
  (it filters nulls); the raw-only run is a separate, additively-listed entity that reuses the raw route
  (which already tolerates a null cross-tier fingerprint).
- Reuse the existing raw loader/source-resolver unchanged (a raw-only run’s absent scores fingerprint is
  already handled).

#### Acceptance Criteria
- [ ] A raw-only fixture run (AFB catalog, **no** `results/` manifest) appears in the browsable run set and
      a rendered in-app link resolves to `/results/$runId/afb-150/AFB-001` (or the first preset item).
- [ ] The default MB scores run selection is unchanged (regression test).
- [ ] No new GitHub API calls beyond the existing tree walk (assert in the data-layer test).
- [ ] The shipped genericity test (`routes/rawResults.test.tsx:156`) and the MB-vocab static guard stay green.
- [ ] `pnpm -C apps/multibrowser test` green.

#### Test Plan
- **Unit**: the enumerator regex + run-list merge (raw-only vs score-backed vs both).
- **Integration (RTL)**: raw-only run is discoverable + linked; default run unchanged; typecheck/lint clean.

#### Rollback Strategy
Revert the commit; discovery returns to scores-only (the AFB catalog would again be deep-link-only).

#### Risks
- **Risk**: leaking AFB vocab / tripping the genericity guard. **Mitigation**: drive everything off the
  manifest; run the static guard + genericity test in this phase.
- **Risk**: disturbing the default MB run. **Mitigation**: additive listing + an explicit
  default-unchanged regression test.

---

### Phase 5: Execute collection run, commit catalog, verify SPA, docs + attribution
**Dependencies**: Phases 1–4

#### Objectives
- Do the one-time run, commit the durable artifacts, prove the real user path renders, and finish docs +
  licensing. **This is the only phase that spends money or touches live infra.**

#### Deliverables
- [ ] **Serving smoke** (adapter integrity re-confirmed live: one base + one `mb-sft-dpo` call) **before**
      the full loop; **architect notified before the spend**.
- [ ] The real collection run (base + dpo × 150 cold) → the committed compact **intermediate** artifact.
- [ ] `analysis export-afb` → committed `results-raw/<afb-run-id>/` (run-id `afb-<YYYYMMDD>`), size-validated.
- [ ] **Actual spend reconciled** from usage (target ~$17–23); **endpoint torn down** (remove
      `min_containers`/stop app).
- [ ] In-app verification: the AFB run is discoverable and the before/after A/B view (base ↔ dpo, Terra
      scores + rationales, ramp colors, `dpo − base` preset) renders on the **real** committed data.
- [ ] AFB **MIT attribution** carried (SOURCE.md/LICENSE referenced/provenance in the run dir or README).
- [ ] Docs: `results-raw/README.md` gains a **second-catalog (AFB) + raw-only discovery** note; the
      MultiWeights paper companion-artifact link plan recorded (link added once live).
- [ ] Arch-doc routing via the `update-arch-docs` skill if a durable system-shape fact warrants it.

#### Implementation Details
- Run-id: `afb-<YYYYMMDD>` chosen at run time. Commit **only** the intermediate + `results-raw/<afb-run-id>/`
  (never secrets, never gitignored `tmp/`). Explicit `git add` per file.
- If the architect prefers, Phases 1–4 can be reviewed/merged before authorizing the Phase-5 spend
  (the code is fully testable without it) — see Notes.

#### Acceptance Criteria
- [ ] 300/300 cells collected and judged; completeness validation passed; spend within ~$17–23 (reconciled).
- [ ] Committed catalog validates + renders in the SPA on real data (verified manually + genericity test).
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
| Writer extraction changes MB bytes | M | H | Byte-identical regression test gates Phase 1 | builder |
| Collection interruption loses paid work | M | H | Per-cell checkpoint + idempotent resume (Phase 2) | builder |
| Catalog drifts from viewer schema | L | M | Tests mirror shipped `AFB_CATALOG`; in-app render (Phase 4/5) | builder |
| Discovery leaks AFB vocab / trips guard | L | M | Manifest-driven; static guard + genericity test (Phase 4) | builder |
| Spend overrun | L | M | Cold-only 300 cells; reconcile ACTUAL usage; stop at ceiling | builder |
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
**Date**: (pending) · **Model**: codex + claude (per `porch.consultation.models`).
**Key Feedback**: (to be filled after consultation)
**Plan Adjustments**: (to be filled after consultation)

## Approval
- [ ] Technical Lead Review
- [ ] Engineering Manager Approval
- [ ] Resource Allocation Confirmed
- [ ] Expert AI Consultation Complete

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-08-08 | Initial plan | Spec 54 approved (Waleed); vanilla↔DPO scope | builder |

## Notes
- **Spend isolation**: Phases 1–4 are no-spend and fully testable; the architect may review/merge them
  before authorizing the Phase-5 run. The builder will notify the architect (and run a serving smoke)
  **before** spending, per the irreversible-action discipline.
- **`dpo` = `mb-sft-dpo`** throughout; the #58 serve script's `dpo=` module is repointed to
  `/vol/runs/mb-sft-dpo/adapter` in Phase 2 (base+dpo only).
- **Secrets**: `OPENROUTER_API_KEY` + `ANTHROPIC_API_KEY` read at runtime from
  `/Users/mwk/Development/fftn/taqwabench/.env`; never committed or echoed.
- **Item id mapping**: `q0001…q0150` → `AFB-001…AFB-150`; group `afb-150`; shards
  `afb-150/AFB-00N.json.gz`.
