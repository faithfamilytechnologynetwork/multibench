# Plan: multibrowser raw-results browser — per-scenario transcripts + judge verdicts

## Metadata
- **ID**: plan-2026-08-06-multibrowser-raw-results-brows
- **Status**: draft
- **Specification**: [codev/specs/51-multibrowser-raw-results-brows.md](../specs/51-multibrowser-raw-results-brows.md)
- **Created**: 2026-08-06

## Executive Summary

Implements Spec 51's **Approach 1**: a new committed, per-scenario `results-raw/<run-id>/`
gzip tier (transcripts + judge verdicts) produced by a **sibling `analysis export-raw`**
command reusing the #49 judgment loaders, plus a **catalog-generic** raw-results view in the
multibrowser SPA that lights up the inert `ResultsRegion` seam and adds a run+scenario-scoped
view (A/B compare, presets, deep links). Data is served from **two public sources of
identical content** (Spec Decision 14): a Railway-baked **gz** bundle (same-origin, primary —
see amendment below) with the SHA-pinned committed gz tier as authoritative + fallback,
reconciled by a shared **source fingerprint**.

Ordered producer → consumer so each phase is an independently testable, committable unit.

### Amendments folded in from plan iter-1 review (Codex + Claude, both REQUEST_CHANGES)
- **Baked representation = gz, not uncompressed (architect-approved 2026-08-06).** Measured
  gzip ratio ~3.7× → an *uncompressed* bake is ~400–550 MB (~1 GB in the Nixpacks image after
  Vite copies `public/`→`dist/`); the *gz* bake is ~115 MB. Waleed's directive's substance was
  *full-data-same-origin*; encoding is implementation. The client already gunzips via the
  magic-byte sniff, so baked-`.gz` and GitHub-`.gz` share one code path — identical UX, ~4×
  smaller image. **Baked source = the same gz shards, served same-origin.**
- **Railway honors `.gitignore` by default** → a gitignored bake dir silently never uploads.
  Deploy uses **`railway up --no-gitignore`** + a **`.railwayignore`** (re-excluding
  `node_modules`/`dist`); the bake is a **separate predeploy script**, *not* part of
  `pnpm build` (so `deploy.test.ts`'s real build never copies the bundle).
- **Generic contract** uses catalog-declared **`conditionAxes`** + cells carrying
  `conditions: Record<string,string>` (jaleesbench shape) — no `framing`/`pressure` literals
  in schemas/components (resolves the Decision-5-vs-13 tension).
- **Fingerprint is *threaded*, not a trivial add**: `build_manifest` never sees
  `resolve_judgments` output (discarded at `export_results.py:370`). Both tiers call **one**
  shared `source_fingerprint(global_resolved_stream)` on the **same global sorted stream**.
- **Shard carries no title/taxonomy** (removes a `--corpus-root` dependency); item labels
  live in the **catalog** (scenario-id-based for MultiBench); the SPA enriches MultiBench
  context via a `(group,item)→(tradition,scenario)` adapter.
- **Per-tradition streaming** writer (buffer only compressed bytes) — the corpus is ~430 MB
  of source sittings; don't hold it all live.
- **URL ownership**: `run/group/item` = **route path params**; `A/B/framing/pressure/scope`
  = **validated search** (route `validateSearch` zod, not `searchParams.ts` alone).
- Multi-segment **safe relative-path** validator (Py + TS) for `<group>/<item>.json.gz`.
- **Presets split** into their own phase; **committed launch dataset** its own phase.
- Test fixture lives in **`src/test/`** (not `public/data-raw/`); the baked-coherent test
  uses an **injectable expected fingerprint** (a `--limit` fixture can't match the real
  full-stream fingerprint).

### Two spec-flagged plan decisions — resolved
- **`context_prefix`**: per-shard `contexts` object keyed by framing (`{stated,guided}`;
  unstated absent) — measured ~2–3 KB gz/shard, negligible vs the 512 KB ceiling.
- **`export-raw` wiring**: sibling Typer command reusing #49 loaders + a new normalized
  sitting reader + the shared fingerprint helper.
- **`results/` `generated_at`** (spec Important open Q): **kept** (default-run selection needs
  it); we only **add** the `fingerprint` field additively.

## Success Metrics
- [ ] All Spec 51 success criteria (incl. Baked Decisions 1–14).
- [ ] Raw and score tiers stamp an **equal** source fingerprint per run-id; field-parity +
      aggregate-reconciliation tests pass.
- [ ] Byte-identical re-export (no wall-clock); size ceilings enforced pre-write.
- [ ] Genericity: the raw view renders from a synthetic non-MultiBench 0–4 catalog with no
      component change; static no-MB-literals check passes.
- [ ] Dual-source: baked-first, GitHub-fallback + `Notice`, fingerprint coherence.
- [ ] Both suites pass via `.codev/checks/test.sh`; no coverage regression.

## Phases (Machine Readable)

<!-- REQUIRED: porch uses this JSON to track phase progress. Update this when adding/removing phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Raw export core: normalized sitting reader + validation, verdict join, generic shard/catalog build, shared fingerprint (pure transform)"},
    {"id": "phase_2", "title": "Fingerprint cross-tier plumbing + streaming writer + export-raw CLI + size measurement"},
    {"id": "phase_3", "title": "Presets (export-computed): Models split, Judges differed, Steadfastness cliff"},
    {"id": "phase_4", "title": "Committed launch dataset + results-raw/README (data contract)"},
    {"id": "phase_5", "title": "SPA raw data layer: generic zod contract, dual-source resolver, gunzip sniff, version+fingerprint checks, safe paths, dev fixture"},
    {"id": "phase_6", "title": "Raw view route: transcripts + verdicts (catalog-generic ramp) + live ResultsRegion entry + drill-down"},
    {"id": "phase_7", "title": "A/B compare + deep-link URL state (path params + validated search, incl. run-id) + preset navigation"},
    {"id": "phase_8", "title": "Railway gz-baked deploy wiring (--no-gitignore) + deploy-test safety + documentation + arch-docs"}
  ]
}
```

## Phase Breakdown

### Phase 1: Raw export core — normalized sitting reader + validation, verdict join, generic shard/catalog build, shared fingerprint (pure transform)
**Dependencies**: None

#### Objectives
- Produce in-memory raw-tier documents (generic per-scenario shards + catalog) from the run
  roots, reusing #49 verdict resolution, with agreement guaranteed and a shared fingerprint.

#### Deliverables
- [ ] `workflows/analysis/analysis/export_raw.py`:
  - `read_full_grid_sittings(root)` — **new** reader over the **report.json-bearing run
    only**; keys sittings by **normalized** subject + `(scenario_id, pressure, framing)`;
    validates vocab; **rejects duplicate sitting identities** and **conflicting
    `context_prefix`** for one `(scenario, framing)`; extracts allowlisted turns +
    `context_prefix`. Non-full-grid roots' sittings ignored.
  - `build_raw_corpus(roots)` — resolve verdicts via `read_run_root` + `resolve_judgments`
    (per tradition) and join to full-grid transcripts. **Abort loudly** on: a resolved
    verdict with no matching transcript (orphan); a sitting subject normalizing outside
    `CANONICAL_SUBJECTS`; a per-scenario grid that disagrees with the report universe.
    Returns the per-tradition exports **and** the global resolved-judgments stream.
  - `build_scenario_shard(...)` — self-contained shard: `schema_version`, a `contexts` pool
    keyed by framing, and `cells[]` (each: normalized `subject`, generic
    `conditions:{framing,pressure}`, `transcript`, `contextKey`, `verdicts[]`). Verdict =
    `{judge(UI key), scope, score(number −1…+1), summary(=direction), rationale?}`. **No**
    title/taxonomy. Canonical sort fixed here.
  - `build_catalog(...)` — generic: `schema_version`, `dataset`{title,description,language,
    `license:"CC-BY-4.0"`}, `scale`{min,center,max}, `ramp`(scoreColor stops, **no labels**),
    `subjects`, `judges`(JUDGE_UI key/full_grid; Opus badged), `conditionAxes`
    (framing+pressure values), a `groupBy` axis + `items`(id, label, **manifest-declared**
    shard path), `fingerprint`.
- [ ] `source_fingerprint(global_resolved_stream)` shared helper (hash of the sorted
  `(subj,scenario,pressure,framing,judge,scope,score,direction,rationale)` tuples) —
  importable by `export_raw` **and** `export_results` (Phase 2).
- [ ] Field **allowlist** applied (positive list only).
- [ ] `workflows/analysis/tests/test_export_raw.py`.

#### Implementation Details
- Reuse (don't fork) `normalize_subject/_judge`, `resolve_judgments`, `_scenario_universe`,
  `JUDGE_UI`, `CANONICAL_SUBJECTS`. Score emitted as a number (no rescale). **No disk writes**
  here (Phase 2), mirroring #49's transform/writer split.

#### Acceptance Criteria
- [ ] Field-parity: a shipped verdict's preserved fields == the #49-resolved judgment.
- [ ] Aggregate reconciliation: a `results/` slice recomputed from **all** raw-tier verdicts
      == the score-tier slice.
- [ ] Orphan verdict, out-of-universe sitting, duplicate sitting, conflicting prefix each
      abort loudly.
- [ ] Transcript sourced only from the full-grid run; normalized join drops nothing.
- [ ] Fingerprint deterministic + changes on any judgment change.

#### Test Plan
- **Unit**: sitting normalization/dedup/conflict; contexts pool; allowlist; fingerprint.
- **Integration**: `build_raw_corpus` over a multi-root fixture → parity + reconciliation.
- **Manual**: run against real `taoism` roots.

#### Rollback Strategy
New module + tests only; revert the commit.

#### Risks
- **Risk**: silent cell drop on join. **Mitigation**: normalized key + orphan abort + tests.

---

### Phase 2: Fingerprint cross-tier plumbing + streaming writer + `export-raw` CLI + size measurement
**Dependencies**: Phase 1

#### Objectives
- Make the fingerprint a checkable cross-tier invariant, serialize deterministically at
  scale, wire the CLI, and measure real sizes early.

#### Deliverables
- [ ] **Fingerprint threading (#49, additive but real):** `build_corpus_export` retains the
  global resolved stream; `export_results.build_manifest` stamps
  `source_fingerprint(global_stream)` — the **same** function/input shape as `export_raw`.
  Update `test_export_results.py`. (Signature changes through `build_corpus_export`/
  `export_dataset` as needed.)
- [ ] `export_raw.write_dataset(...)` — **per-tradition streaming**: build → serialize →
  `gzip(level 9, mtime=0)` → **hold only compressed bytes** → validate all sizes → write;
  prunes stale shards; **no wall-clock**; `schema_version` in catalog + every shard;
  **manifest-declared** shard paths; safe **multi-segment** path guard
  (`_require_safe_relpath`: per-component `_SAFE_SEGMENT` + extension + no `..`); ceilings
  (per-shard ≤ 512 KB, per-run ≤ 200 MB).
- [ ] `--limit N` mode (small dev fixture for the SPA).
- [ ] `analysis export-raw` Typer command in `analysis/cli.py` (run roots; `--run-id`,
  `--out results-raw`, `--limit`).
- [ ] **Size measurement** logged (gz total, uncompressed total, ratio) so the deploy
  representation decision is grounded (informs Phase 8; gz-baked already chosen).

#### Acceptance Criteria
- [ ] Byte-identical re-export over identical inputs.
- [ ] Raw manifest `fingerprint` == `results/` manifest `fingerprint` (same fixture).
- [ ] Over-ceiling shard/total aborts before any write.
- [ ] Peak memory bounded (streaming; not the whole corpus live).
- [ ] `cli_smoke` covers `export-raw --limit`.

#### Test Plan
- **Unit**: determinism; size-ceiling abort; multi-seg path guard; fingerprint equality vs
  `export`.
- **Integration**: end-to-end `export-raw` on a fixture.
- **Manual**: full `export-raw` on real roots; record sizes.

#### Rollback Strategy
Revert; the additive `results/` fingerprint is backward-compatible (zod tolerant, Phase 5).

#### Risks
- **Risk**: the two exporters hash differently. **Mitigation**: one shared fn, one global
  input shape, equality test.

---

### Phase 3: Presets (export-computed) — Models split, Judges differed, Steadfastness cliff
**Dependencies**: Phase 2

#### Objectives
- Compute the three curated preset lists at export into the catalog, deterministically.

#### Deliverables
- [ ] Preset computation (Spec *Presets*): **Models split** (turn1 Gemini widest cross-subject
  spread), **Judges differed** (full-scope two-judge |Δ| ≥ 1.0), **Steadfastness cliff**
  (largest negative full−turn1, Gemini). Each: deterministic, cap 12, one-per-scenario dedup,
  `(scenario,pressure,framing)` tie-break, **stable keys**, sparse-Opus-safe (skip, never
  zero-fill). Emitted as deep-link param maps into the catalog.
- [ ] Tests for each algorithm.

#### Acceptance Criteria
- [ ] Deterministic, capped, deduped-per-scenario, stable-keyed; sparse-Opus cells skipped.
- [ ] Each entry is a valid deep-link param map for the Phase-7 navigator.

#### Test Plan
- **Unit**: thresholds, caps, dedup, tie-breaks, sparse-Opus behavior, determinism.

#### Rollback Strategy
Revert; the catalog simply carries no `presets` (viewer tolerates absence).

#### Risks
- **Risk**: one dramatic scenario floods a preset. **Mitigation**: one-per-scenario dedup.

---

### Phase 4: Committed launch dataset + `results-raw/README.md`
**Dependencies**: Phase 3

#### Objectives
- Produce and commit the real launch `results-raw/<run-id>/` gz tier and document the contract.

#### Deliverables
- [ ] Run `export-raw` on the real roots; **commit** the `results-raw/<run-id>/` gz tier
  (its own commit; ~110–150 MB, Waleed-accepted).
- [ ] `results-raw/README.md`: contract, layout, allowlist, size ceilings, fingerprint,
  dual-source, deploy-flow refresh trade, `CC-BY-4.0`, produce/refresh command.

#### Acceptance Criteria
- [ ] The committed dataset validates against the Phase-5 zod contract.
- [ ] Raw/score fingerprints match for the committed run.
- [ ] README documents every contract element above.

#### Test Plan
- **Manual**: inspect a committed shard + the manifest; confirm fingerprint parity with the
  committed `results/<run-id>/`.

#### Rollback Strategy
Revert the data commit (large but clean).

#### Risks
- **Risk**: committed weight. **Mitigation**: Waleed-accepted; determinism → changed-only
  rewrites; documented.

---

### Phase 5: SPA raw data layer — generic zod contract, dual-source resolver, gunzip sniff, version+fingerprint checks, safe paths, dev fixture
**Dependencies**: Phase 4 (dataset shape + fixture)

#### Objectives
- A catalog-generic, fail-soft data layer resolving baked-first / GitHub-fallback with no
  MultiBench vocab or ramp baked in.

#### Deliverables
- [ ] `apps/multibrowser/src/lib/rawContract.ts` — **generic** zod schemas: scale, ramp,
  subjects, judges, `conditionAxes`, `groupBy`, items(+manifest-declared shard paths),
  `contexts`, cells(`conditions:Record<string,string>`), verdicts, presets, `schema_version`,
  `fingerprint`. **No** `tradition`/`scenario`/framing/pressure literals or −1…+1 constant.
- [ ] `apps/multibrowser/src/lib/rawSource.ts` — `DataSource` seam: same-origin **baked** +
  **GitHub** (`github.ts`) impls + resolver (**baked-first**; fall back on baked-absent or
  **fingerprint mismatch**, surfacing a `Notice`). Carries the **magic-byte sniff verbatim**
  (`0x1f 0x8b` else `TextDecoder`); **feature-detects** `DecompressionStream` (message).
- [ ] `apps/multibrowser/src/lib/rawModel.ts` — tolerant parsers (mirror `resultsModel.ts`):
  unsupported `schema_version` → `Notice`; **multi-segment safe-path** guard (`isSafeRelPath`);
  malformed → `Notice`.
- [ ] Extend `resultsModel.ts` with a **tolerant `fingerprint` field** (present/absent both OK).
- [ ] Raw query hooks; add `"results-raw"` to `github.ts` `WALK_DIRS`.
- [ ] Dev fixture under **`apps/multibrowser/src/test/`** (from Phase 2 `--limit`), served
  via the test harness; the baked-coherent path is tested with an **injectable expected
  fingerprint**.

#### Acceptance Criteria
- [ ] Sniff parses both already-decompressed and raw-gz.
- [ ] Version mismatch, malformed shard, 404, rate-limit each → `Notice` (no crash).
- [ ] Resolver: baked coherent → same-origin (no GitHub call); baked absent/stale → GitHub +
      `Notice`.
- [ ] A synthetic non-MultiBench catalog parses (contract genericity).

#### Test Plan
- **Unit**: zod (valid/invalid/version); sniff; resolver (three paths); `isSafeRelPath`.
- **Integration**: hooks vs `fakeRepo`/fixture (no network).

#### Rollback Strategy
New lib modules + a one-line `WALK_DIRS` change + an additive `resultsModel` field; revert.

#### Risks
- **Risk**: importing `scoreColor`'s constant defeats genericity. **Mitigation**: ramp read
  from catalog; generic interpolator in Phase 6 + static check.

---

### Phase 6: Raw view route — transcripts + verdicts (catalog-generic ramp) + live `ResultsRegion` entry + drill-down
**Dependencies**: Phase 5

#### Objectives
- Render a scenario's cells (transcripts, context prefix, per-(judge,scope) verdicts) from
  catalog-generic data; make the seam live.

#### Deliverables
- [ ] New route `/results/$runId/$groupId/$itemId` + component (wired in `router.tsx`).
- [ ] Components: transcript renderer (reuse `Markdown`), context-prefix panel, verdict card
  (score colored by the **catalog-declared ramp**, `summary`, `rationale`, Opus **badge**),
  cell grid iterating `conditionAxes` (no hardcoded axis names).
- [ ] A **generic ramp interpolator** seeded by the catalog scale+stops (not importing the
  `scoreColor` constant); `null` → neutral.
- [ ] Upgrade `components/ResultsRegion.tsx` to a **live in-page entry** (per-scenario summary
  linking into the route) via a `(group,item)→(tradition,scenario)` **adapter**; **edit the
  placeholder string to drop "bands."**
- [ ] Drill-down from `/results`.

#### Acceptance Criteria
- [ ] Renders MultiBench cells (both judges, Opus badged).
- [ ] Renders a synthetic non-MultiBench 0–4 catalog with **no component change**; static
      check: no `tradition`/`scenario` literal or −1…+1 constant in raw components.
- [ ] No band names; placeholder no longer says "bands".
- [ ] `ResultsRegion` links into the route; lazy-loads only that scenario's shard.

#### Test Plan
- **Unit**: verdict-card colors from a catalog ramp; badge; neutral-null; adapter.
- **Integration** (vitest + fixture): render for a MB scenario and a synthetic 0–4 catalog.

#### Rollback Strategy
Revert; `ResultsRegion` returns to inert (its `loadResults` seam remains).

#### Risks
- **Risk**: A/B/deep-links creep in. **Mitigation**: single-view render only here.

---

### Phase 7: A/B compare + deep-link URL state (path params + validated search, incl. run-id) + preset navigation
**Dependencies**: Phase 6

#### Objectives
- jaleesbrowser parity: side-by-side A/B, full shareable URL state, preset navigation.

#### Deliverables
- [ ] A/B subject compare on a cell (two subjects: transcript + verdicts side-by-side).
- [ ] View state: `run/group/item` as **route path params**; `a`, `b`, `framing`, `pressure`,
  `scope` as **validated search** via the route's `validateSearch` zod schema in `router.tsx`
  (using `searchParams.ts` only for flat (de)serialization). Opening a URL restores the view;
  a missing `results-raw/<run-id>/` degrades to a `Notice`.
- [ ] Preset bar reading catalog presets → deep links.

#### Acceptance Criteria
- [ ] A/B renders both; switching updates the URL.
- [ ] Deep-link round-trip incl. run-id restores the exact view; missing run → `Notice`.
- [ ] Each preset opens the intended cell/compare; presets ≤ 12, deduped-per-scenario.

#### Test Plan
- **Unit**: search encode/decode round-trip; preset→params.
- **Integration**: A/B render; preset navigation; missing-run fail-soft.

#### Rollback Strategy
Revert; the single-view route (Phase 6) remains usable.

#### Risks
- **Risk**: run-id dropped from state. **Mitigation**: run-id is a required path param;
  round-trip test.

---

### Phase 8: Railway gz-baked deploy wiring (`--no-gitignore`) + deploy-test safety + documentation + arch-docs
**Dependencies**: Phase 7

#### Objectives
- Bake the gz tier into the Railway static deploy correctly; keep the test build clean;
  document and update governance docs.

#### Deliverables
- [ ] **Predeploy script** (e.g. `apps/multibrowser/scripts/bake-and-deploy.sh`): run
  `analysis export-raw --run-id … --out apps/multibrowser/public/data-raw` (**gz** shards) →
  `railway up --no-gitignore`. **Not** part of `pnpm build` (so `deploy.test.ts`'s real build
  never touches it).
- [ ] `.railwayignore` re-excluding `node_modules`/`dist`; `.gitignore` for
  `apps/multibrowser/public/data-raw/` (baked, not committed).
- [ ] `deploy.test.ts` safety: the fixture is **not** in `public/data-raw/`; add a guard/note
  that `public/data-raw/` is deploy-only so a stray local copy doesn't bloat the test build.
- [ ] `apps/multibrowser/README.md`: raw tier, dual-source (gz-baked), deploy-flow refresh
  trade (baked = re-export + `railway up --no-gitignore`; GitHub updates live).
- [ ] Arch-docs via the **`update-arch-docs` skill**: a raw-tier + dual-source fact in
  `arch-critical.md`; the genericity / gunzip-sniff / fingerprint / Railway-`.gitignore`
  lessons in `lessons-critical.md` (displace weaker entries if capped).

#### Acceptance Criteria
- [ ] `pnpm build` succeeds **with** a baked `public/data-raw/` (bundle serves same-origin
      gz) **and without** it (GitHub fallback); verified locally.
- [ ] `deploy.test.ts` unaffected by the bake (fixture elsewhere).
- [ ] READMEs + arch-docs accurate.

#### Test Plan
- **Manual**: `export-raw --out public/data-raw` → `pnpm build` → `pnpm preview`; confirm
  same-origin gz serving; remove the dir → GitHub fallback + `Notice`.
- **Unit**: `deploy.test.ts` passes unchanged.

#### Rollback Strategy
Revert; the SPA already works via the committed GitHub tier (fallback) without the bake.

#### Risks
- **Risk**: `railway up` drops the bake (`.gitignore`). **Mitigation**: `--no-gitignore` +
  `.railwayignore`; documented + a deploy checklist.

---

## Cross-Phase Notes
- **Per-phase consult** is `["codex","claude"]` (Gemini can't see the worktree); full 3-way
  only where the diff is fed inline (the PR integration CMAP). (lessons-critical.)
- **Test dispatcher** (`.codev/checks/test.sh`) registers `workflows/analysis` +
  `apps/multibrowser`; both run for this builder.
- **Single PR** (issue PR strategy): phases are commits on one branch; PR opens at/after the
  final implement phase unless the architect requests earlier.
- **External-account actions** (Railway, etc.) go through the **architect first** (2026-08-06
  ruling). The gz-baked representation is architect-approved.
- **plan-approval gate** goes to Waleed.
