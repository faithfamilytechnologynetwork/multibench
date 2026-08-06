# Plan: multibrowser raw-results browser — per-scenario transcripts + judge verdicts

## Metadata
- **ID**: plan-2026-08-06-multibrowser-raw-results-brows
- **Status**: draft
- **Specification**: [codev/specs/51-multibrowser-raw-results-brows.md](../specs/51-multibrowser-raw-results-brows.md)
- **Created**: 2026-08-06

## Executive Summary

Implements Spec 51's **Approach 1**: a new committed, per-scenario `results-raw/<run-id>/`
gzip tier (transcripts + judge verdicts) produced by a **sibling `analysis export-raw`**
command that reuses the #49 judgment loaders, plus a **catalog-generic** raw-results view in
the multibrowser SPA that lights up the inert `ResultsRegion` seam and adds a run+scenario
-scoped view with A/B compare, presets, and deep links. Data is served from **two public
sources of identical content** (Spec Decision 14): a Railway-baked full-uncompressed bundle
(same-origin, primary) with the SHA-pinned committed gz tier as authoritative + fallback,
resolved by a shared **source fingerprint**.

The plan is ordered producer → consumer so each phase is independently testable: the export
core (pure transform) → the writer/CLI/committed dataset → the SPA data layer → the view →
A/B + deep-links + presets → deploy bake + docs.

### Two spec-flagged plan decisions — resolved here
- **`context_prefix` pool mechanics (measured):** a **per-shard `contexts` object keyed by
  framing** (`{stated: "…", guided: "…"}`; `unstated` absent); each cell references its
  framing. Measured cost: guided prefix ~6.5 KB raw → ~2–3 KB gz *inside* an already
  -compressed shard, once per framing per shard — negligible against the 161–300 KB shard
  and the 512 KB ceiling. **Per-shard chosen** (self-contained shard; one fetch renders).
- **`export-raw` wiring:** a **sibling Typer command** in `analysis/cli.py` calling a new
  `analysis/export_raw.py`. It reuses `export_results.read_run_root` / `resolve_judgments` /
  the alias maps for **verdicts**, adds a **new normalized sitting reader** for transcripts,
  and shares a **fingerprint helper** with `export_results` (which is additively extended to
  stamp the same fingerprint in the `results/` manifest). Emits the committed **gz** tier by
  default and a **full uncompressed** bundle under `--uncompressed` (identical content +
  fingerprint) for the Railway bake.
- **`results/` `generated_at` (spec Important open Q):** **kept** — #49's default-run
  selection depends on it, and the raw tier's determinism does not require dropping it (the
  raw tier is timestamp-free and always addressed by run-id from score-tier context). We
  only **add** the `fingerprint` field additively (zod tolerant of both).

## Success Metrics
- [ ] All Spec 51 success criteria met (incl. Baked Decisions 1–14).
- [ ] Raw and score tiers carry an **equal source fingerprint** per run-id; field-parity +
      aggregate-reconciliation tests pass.
- [ ] Export is **byte-identical** on re-run (no wall-clock); size ceilings enforced
      pre-write.
- [ ] Catalog-genericity: the raw view renders from a **synthetic non-MultiBench 0–4
      catalog** with no component change; static no-MB-literals check passes.
- [ ] Dual-source resolution: baked-first, GitHub-fallback + `Notice`, fingerprint coherence.
- [ ] Both suites pass via `.codev/checks/test.sh` (`workflows/analysis` pytest +
      `apps/multibrowser` vitest); no coverage regression.

## Phases (Machine Readable)

<!-- REQUIRED: porch uses this JSON to track phase progress. Update this when adding/removing phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Raw export core: normalized sitting reader, verdict join, shard/catalog build, fingerprint (pure transform)"},
    {"id": "phase_2", "title": "Export writer + export-raw CLI + presets + fingerprint into results/ manifest + committed launch dataset + README"},
    {"id": "phase_3", "title": "SPA raw data layer: generic zod contract, dual-source resolution, gunzip sniff, version+fingerprint checks, dev fixture"},
    {"id": "phase_4", "title": "Raw view route: transcripts + verdicts (catalog-generic ramp) + live ResultsRegion entry + drill-down"},
    {"id": "phase_5", "title": "A/B side-by-side compare + deep-link URL state (incl. run-id) + preset navigation"},
    {"id": "phase_6", "title": "Railway baked-bundle deploy wiring + documentation + arch-doc updates"}
  ]
}
```

## Phase Breakdown

### Phase 1: Raw export core — normalized sitting reader, verdict join, shard/catalog build, fingerprint (pure transform)
**Dependencies**: None

#### Objectives
- Produce the in-memory raw-tier documents (per-scenario shards + catalog) from the run
  roots, reusing the #49 judgment resolution and adding transcript reading, with agreement
  guaranteed by construction and a shared fingerprint.

#### Deliverables
- [ ] New `workflows/analysis/analysis/export_raw.py`:
  - `read_full_grid_sittings(root)` — a **new** sitting reader over the **report.json-bearing
    (full-grid) run only**; parses `sittings.jsonl`, keys each sitting by **normalized**
    subject (`export_results.normalize_subject`) + `(scenario_id, pressure, framing)`;
    validates vocab (FRAMINGS/PRESSURES); extracts the allowlisted turns `{role, content}`
    and the `context_prefix`. Ignores every non-full-grid root's sittings.
  - `build_raw_corpus(roots)` — resolve verdicts via `export_results.build_corpus_export`'s
    path (`read_run_root` + `resolve_judgments`, per tradition) and join to the full-grid
    transcripts; **abort loudly** on a resolved verdict with no matching normalized
    transcript (orphan guard); **abort loudly** on a full-grid sitting subject that
    normalizes outside `CANONICAL_SUBJECTS`.
  - `build_scenario_shard(...)` — a self-contained shard doc: `schema_version`, `item`
    (id/title/taxonomy tags from the tradition corpus), a `contexts` pool keyed by framing,
    and `cells[]` (each: normalized `subject`, `framing`, `pressure`, `transcript`, framing
    key into `contexts`, `verdicts[]`). Verdict = `{judge (UI key), scope, score (number),
    summary(=direction), rationale?}`. Canonical sort order fixed here.
  - `build_catalog(...)` — generic catalog: `schema_version`, `dataset` (title, description,
    `language`, `license: "CC-BY-4.0"`), **scale** (`{min:-1, center:0, max:1}`) + **ramp**
    (the #49 `scoreColor` stops, **no rung labels**), `subjects` (catalog-declared),
    `judges` (reuse `JUDGE_UI` key/full_grid; Opus badged), a generic **grouping axis**
    (group=tradition) + **items** with **manifest-declared shard paths**, `fingerprint`.
- [ ] Shared **fingerprint** helper (over the resolved-judgments stream: sorted
  `(subj, scenario, pressure, framing, judge, scope, score, direction, rationale)`),
  importable by both `export_raw` and `export_results`.
- [ ] The export field **allowlist** applied here (positive list; nothing else emitted).
- [ ] Tests in `workflows/analysis/tests/test_export_raw.py`.

#### Implementation Details
- Reuse, do not fork: `normalize_subject`/`normalize_judge`, `resolve_judgments`,
  `_scenario_universe`, `JUDGE_UI`, `CANONICAL_SUBJECTS` from `export_results.py`.
- Score is validated by the #49 `is_valid_score` contract and emitted as a **number** on
  −1…+1 (no rescale).
- Pure transform only — **no disk writes** in this phase (writer is Phase 2), mirroring
  #49's Phase-1/Phase-2 split.

#### Acceptance Criteria
- [ ] Field-parity: a sampled shipped verdict's preserved fields equal the #49-resolved
      judgment for that identity.
- [ ] Aggregate reconciliation: a `results/` slice mean recomputed from **all** raw-tier
      verdicts equals the score-tier slice.
- [ ] Orphan-verdict and out-of-universe sitting both abort loudly.
- [ ] Transcript sourced only from the full-grid run (a differing non-full-grid sitting does
      not change output); normalized join across divergent spellings drops nothing.
- [ ] Fingerprint is deterministic and changes when any resolved judgment changes.

#### Test Plan
- **Unit**: sitting reader normalization; contexts-pool build; allowlist (no disallowed key);
  fingerprint determinism/sensitivity.
- **Integration**: `build_raw_corpus` over a small multi-root fixture (full-grid + an Opus
  layer) → field-parity + aggregate-reconciliation vs `export_results`.
- **Manual**: run against one real tradition (taoism) in `tmp/judging-runs/…`.

#### Rollback Strategy
New module + new tests only; revert the commit — no existing behavior touched.

#### Risks
- **Risk**: transcript↔verdict join drops cells silently. **Mitigation**: normalized-subject
  key + orphan abort + explicit tests (spec tests 5, 6).

---

### Phase 2: Export writer + `export-raw` CLI + presets + fingerprint into `results/` manifest + committed launch dataset + README
**Dependencies**: Phase 1

#### Objectives
- Serialize the raw tier deterministically to disk (gz + uncompressed), wire the CLI,
  compute presets, make the fingerprint checkable across both tiers, and land the committed
  launch dataset + contract README.

#### Deliverables
- [ ] `export_raw.write_dataset(...)`: writes `results-raw/<run-id>/manifest.json` +
  `<tradition>/<scenario>.json.gz`; deterministic (`sort_keys`, compact separators,
  `gzip(level 9, mtime=0)`); **no wall-clock**; `schema_version` in catalog **and** every
  shard; **manifest-declared** shard paths; `_require_safe_segment` on run-id/tradition/
  scenario; **validate all sizes before any write** (per-shard ≤ 512 KB, per-run ≤ 200 MB);
  prune stale shards.
- [ ] `--uncompressed` mode: emit the identical corpus as plain `.json` (full bundle for the
  bake) — same content + **same fingerprint**.
- [ ] `--limit N` mode: small dev fixture (baked into the SPA repo for network-free tests).
- [ ] Presets computed at export into the catalog (Spec *Presets*): **Models split**
  (turn1 Gemini widest cross-subject spread), **Judges differed** (full-scope two-judge
  |Δ| ≥ 1.0), **Steadfastness cliff** (largest negative full−turn1, Gemini); deterministic,
  cap 12, one-per-scenario dedup, `(scenario,pressure,framing)` tie-break, stable keys,
  sparse-Opus-safe (skip, never zero-fill).
- [ ] `analysis export-raw` Typer command in `analysis/cli.py` (args: run roots; options:
  `--run-id`, `--out results-raw`, `--uncompressed`, `--limit`).
- [ ] **Additive #49 change**: `export_results.build_manifest` stamps the shared
  `fingerprint`; update `test_export_results.py` accordingly.
- [ ] Produce + **commit** the launch `results-raw/<run-id>/` gz dataset (the real run).
- [ ] `results-raw/README.md`: contract, layout, allowlist, size ceilings, fingerprint,
  dual-source, deploy-flow refresh trade, `CC-BY-4.0`, produce/refresh command.

#### Implementation Details
- Mirror `export_results.write_dataset`'s validate-before-write + prune discipline.
- The committed launch dataset is large (~110–150 MB gz) — Waleed-accepted (Spec Decision
  14); commit it as its own commit within the phase.

#### Acceptance Criteria
- [ ] Re-running `export-raw` over identical inputs yields **byte-identical** shards + catalog.
- [ ] Dual-representation identity: gz and `--uncompressed` carry identical content +
      fingerprint.
- [ ] Raw manifest `fingerprint` == `results/` manifest `fingerprint` for the run-id.
- [ ] Over-ceiling shard/total aborts before any write (no partial tier).
- [ ] `cli_smoke` covers `export-raw --limit`.

#### Test Plan
- **Unit**: determinism (byte-identity), size-ceiling abort, safe-segment guard, preset
  determinism/cap/dedup, dual-representation identity.
- **Integration**: end-to-end `export-raw` on a fixture → manifest+shards validate; fingerprint
  equality vs an `export` run on the same fixture.
- **Manual**: full `export-raw` on the real roots; inspect one shard + sizes.

#### Rollback Strategy
Revert the phase commit(s); the additive `results/` fingerprint is backward-compatible
(zod tolerant, Phase 3), so no coordinated rollback needed.

#### Risks
- **Risk**: committing ~110–150 MB bloats the PR/history. **Mitigation**: Waleed-accepted;
  determinism → only changed shards rewrite on refresh; documented in README.

---

### Phase 3: SPA raw data layer — generic zod contract, dual-source resolution, gunzip sniff, version+fingerprint checks, dev fixture
**Dependencies**: Phase 2 (fixture + dataset shape)

#### Objectives
- A catalog-generic, fail-soft data layer that resolves baked-first / GitHub-fallback and
  never bakes MultiBench vocab or the ramp.

#### Deliverables
- [ ] `apps/multibrowser/src/lib/rawContract.ts` — **generic** zod schemas (catalog + shard):
  scale/ramp, subjects, judges, grouping axis, items (+manifest-declared shard paths),
  `contexts` pool, cells, verdicts, presets, `schema_version`, `fingerprint`. **No**
  `tradition`/`scenario`/framing/pressure literals or −1…+1 constant.
- [ ] `apps/multibrowser/src/lib/rawSource.ts` — `DataSource` seam with two implementations
  (same-origin baked; GitHub via `github.ts`) + a resolver: **baked-first**, fall back to
  GitHub when baked absent or **fingerprint-mismatched**, surfacing a `Notice`. Carries the
  **magic-byte gunzip sniff verbatim** (`0x1f 0x8b`; else `TextDecoder`) and
  **feature-detects** `DecompressionStream` (message, no polyfill).
- [ ] `apps/multibrowser/src/lib/rawModel.ts` — tolerant parsers (mirror `resultsModel.ts`):
  unsupported `schema_version` → `Notice`; `isSafePathSegment` on manifest paths;
  malformed → `Notice`, never throw.
- [ ] Raw query hooks (TanStack) in `lib/queries.ts` (or a sibling); add `"results-raw"` to
  `github.ts` `WALK_DIRS`.
- [ ] Baked dev fixture under `apps/multibrowser/` (from Phase 2 `--limit`) wired into tests.

#### Implementation Details
- Reuse `github.ts` (raw + SHA-pin + truncation fallback) unchanged except `WALK_DIRS`.
- The gunzip sniff makes baked `.json` and GitHub `.json.gz` share one parse path.

#### Acceptance Criteria
- [ ] Gunzip sniff parses both already-decompressed and raw-gz bytes.
- [ ] Version mismatch, malformed shard, 404, and rate-limit each yield a `Notice` (no crash).
- [ ] Source resolution: baked coherent → same-origin, no GitHub call; baked absent/stale →
      GitHub + `Notice`.
- [ ] A **synthetic non-MultiBench catalog** parses (genericity at the contract layer).

#### Test Plan
- **Unit**: zod parsers (valid/invalid/version); sniff; source resolver (three paths);
  `isSafePathSegment`.
- **Integration**: hooks against `fakeRepo`/fixture (no network).

#### Rollback Strategy
New lib modules + a one-line `WALK_DIRS` change; revert the commit.

#### Risks
- **Risk**: importing `scoreColor`'s constant defeats genericity. **Mitigation**: the ramp is
  read from the catalog; Phase 4 supplies a generic interpolator; static check in Phase 4.

---

### Phase 4: Raw view route — transcripts + verdicts (catalog-generic ramp) + live `ResultsRegion` entry + drill-down
**Dependencies**: Phase 3

#### Objectives
- Render a scenario's cells (transcripts, context prefix, per-(judge,scope) verdicts) from
  the catalog-generic data, and turn the inert seam into a live entry.

#### Deliverables
- [ ] New run+scenario-scoped route (e.g. `/results/$runId/$groupId/$itemId`) + component in
  `apps/multibrowser/src/routes/` (wired in `router.tsx`).
- [ ] Components: transcript renderer (reuse `Markdown`), context-prefix panel, verdict card
  (score colored by the **catalog-declared ramp**, `summary`, `rationale`, Opus **badge**),
  cell grid.
- [ ] A **generic ramp interpolator** seeded by the catalog's scale+stops (not importing the
  `scoreColor` constant); `null` → neutral.
- [ ] Upgrade `components/ResultsRegion.tsx` to a **live in-page entry** (compact per-scenario
  summary linking into the route); **edit the placeholder string to drop "bands."**
- [ ] Drill-down from `/results` into the route.

#### Acceptance Criteria
- [ ] Renders MultiBench cells (transcripts + both judges' verdicts, Opus badged).
- [ ] **Renders a synthetic non-MultiBench 0–4 catalog with no component change**; static
      check: no `tradition`/`scenario` literal or −1…+1 ramp constant in raw components.
- [ ] No band names anywhere; the edited placeholder no longer says "bands".
- [ ] `ResultsRegion` links into the route; lazy-loads only the one scenario's shard.

#### Test Plan
- **Unit**: verdict card colors from a catalog ramp; badge; neutral-null.
- **Integration** (vitest + fixture): render the route for a MB scenario and for a synthetic
  0–4 catalog; assert genericity + no-band-names.

#### Rollback Strategy
Revert the phase; `ResultsRegion` returns to inert (its `loadResults` seam stays).

#### Risks
- **Risk**: A/B and deep-links creep into this phase. **Mitigation**: scoped to single-view
  render here; A/B + URL state is Phase 5.

---

### Phase 5: A/B side-by-side compare + deep-link URL state (incl. run-id) + preset navigation
**Dependencies**: Phase 4

#### Objectives
- The jaleesbrowser parity features: side-by-side A/B on a cell, full shareable URL state,
  and preset-driven navigation.

#### Deliverables
- [ ] A/B subject compare on a cell (two subjects side-by-side: transcript + verdicts).
- [ ] Full view state in the URL via `searchParams.ts` (validated search): **run-id**,
  group, item, A subject, B subject, framing, pressure, scope; opening a URL restores the
  view; a missing `results-raw/<run-id>/` degrades to a `Notice`.
- [ ] Preset bar reading the catalog presets → deep links (Models split / Judges differed /
  Steadfastness cliff).

#### Acceptance Criteria
- [ ] A/B renders both subjects; switching updates the URL.
- [ ] Deep-link round-trip incl. run-id restores the exact view; missing run → `Notice`.
- [ ] Each preset entry opens the intended cell/compare; presets ≤12, deduped-per-scenario.

#### Test Plan
- **Unit**: URL encode/decode incl. run-id (round-trip); preset→params.
- **Integration**: A/B render; preset navigation; missing-run fail-soft.

#### Rollback Strategy
Revert the phase; the single-view route (Phase 4) remains usable.

#### Risks
- **Risk**: run-id absent from state (spec defect). **Mitigation**: run-id is a required
  search param; test asserts round-trip.

---

### Phase 6: Railway baked-bundle deploy wiring + documentation + arch-doc updates
**Dependencies**: Phase 5

#### Objectives
- Bake the full uncompressed bundle into the Railway static deploy; document the tier and
  the deploy flow; update governance docs.

#### Deliverables
- [ ] Deploy wiring: a documented pre-deploy step that runs `analysis export-raw
  --uncompressed --out apps/multibrowser/public/data-raw` before `railway up`, so `pnpm
  build` includes it same-origin; **gitignore** `apps/multibrowser/public/data-raw/`
  (baked, not committed); the SPA falls back to GitHub when the baked dir is absent (so CI
  builds without the ~150 MB data still work).
- [ ] `apps/multibrowser/README.md`: the raw tier, dual-source, deploy-flow refresh trade
  (baked = re-export + `railway up`; GitHub updates live).
- [ ] Arch-doc updates via the **`update-arch-docs` skill** (hot/cold tiers): a raw-tier +
  dual-source fact in `arch-critical.md`; the genericity/gunzip-sniff/fingerprint lessons in
  `lessons-critical.md` (displace weaker entries if capped).

#### Acceptance Criteria
- [ ] `pnpm build` succeeds **with** the baked dir (bundle includes `/data-raw`) **and
      without** it (falls back to GitHub); documented flow verified locally.
- [ ] READMEs + arch-docs updated and accurate.

#### Test Plan
- **Manual**: local `export-raw --uncompressed` → `pnpm build` → `pnpm preview`; confirm the
  raw view serves same-origin; remove the dir and confirm GitHub fallback + `Notice`.
- **Unit**: existing `deploy.test.ts` still passes.

#### Rollback Strategy
Revert the phase; the SPA already works via the committed GitHub tier (fallback) without the
bake, so deploy is unaffected.

#### Risks
- **Risk**: a build without local data ships an empty baked dir. **Mitigation**: absent dir →
  GitHub fallback (not an empty-but-present dir); document + guard the copy step.

---

## Cross-Phase Notes
- **Per-phase consult** in this repo is `["codex","claude"]` (Gemini can't see the worktree);
  full 3-way only where the diff is fed inline (the PR integration CMAP). (lessons-critical.)
- **Test dispatcher** (`.codev/checks/test.sh`) already registers `workflows/analysis` and
  `apps/multibrowser`; both suites run for this builder.
- **Single PR** per the issue's PR strategy: phases are git commits on one branch; the PR
  opens at/after the final implement phase unless the architect requests earlier.
- **plan-approval gate** goes to Waleed (architect note).
