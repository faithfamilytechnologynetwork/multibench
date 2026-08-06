# Plan: MultiBrowser Results Explorer — Judge & Pressure Selectors + Leaderboard

## Metadata
- **ID**: plan-2026-08-06-multibrowser-results-explorer
- **Status**: draft
- **Specification**: [codev/specs/49-multibrowser-results-explorer-.md](../specs/49-multibrowser-results-explorer-.md)
- **Created**: 2026-08-06

## Executive Summary

Implements the spec's **Approach 1** (pre-aggregated per-tradition shards; the SPA does only the
equal-weight mean-of-per-tradition-means), with the architect's Approved Decisions baked in — most
importantly **the leaderboard ranks on Gemini only**, and the **judge selector switches the Opus
*validation/inspection* layer**, not the ranking.

Two halves, sequenced so the data contract is proven before the UI consumes it:
1. **A Python export tool** in `workflows/analysis` that reads the three source runs, applies explicit
   **subject** and **judge** alias maps (deduping Opus by identity), computes per-tradition breakdown means
   via the *canonical* `aggregate.py` semantics, and writes a compact, versioned, per-tradition-sharded
   `results/<run-id>/` dataset + manifest (≤ 8 MB total, ≤ 1 MB/shard, no transcripts). Its crown-jewel test
   is **parity**: mean-of-per-tradition-means == the paper's `subj_overall` to full precision.
2. **An additive `/results` explorer** in `apps/multibrowser` that reads that dataset at runtime through the
   existing SHA-pinned GitHub data layer, renders the Gemini-ranked leaderboard with framing/scope/pressure
   selectors and per-tradition drill-down, and switches to the Opus validation layer (coverage-badged) via
   the judge selector — extending the truncation fallback to discover `results/` and validating the remote
   dataset before display.

Phases are ordered by dependency (export contract → SPA data layer → leaderboard → Opus layer → docs) so
each is independently testable and commits atomically. The launch dataset committed in Phase 2 is **interim**
and re-exported (same command) once the architect confirms the Opus tail-fill is sealed (Approved Decision 8).

## Success Metrics
- [ ] All specification Success Criteria met (esp. **leaderboard reconciles with the paper to displayed
      precision**, judge/pressure selectors, Gemini-only ranking, honest Opus coverage badging).
- [ ] Parity test green: export's per-tradition means match `report.json`/`stats_bundle.json` within tolerance,
      and mean-of-per-tradition-means == `subj_overall` for all framings.
- [ ] Committed dataset ≤ 8 MB total, ≤ 1 MB per tradition shard (CI-asserted).
- [ ] Exactly five normalized subjects and two judges; Opus alias dedup verified (disjoint-sum + collision).
- [ ] A second `results/<run-id>/` appears in the browser with no code change, incl. under a truncated tree.
- [ ] Touched-app suites pass (`uv --project workflows/analysis run pytest`, `pnpm -C apps/multibrowser test`);
      no coverage reduction.
- [ ] Documentation complete (`results/README.md` data contract + multibrowser README).

## Phases (Machine Readable)

<!-- REQUIRED: porch uses this JSON to track phase progress. Update this when adding/removing phases. -->

```json
{
  "phases": [
    {"id": "phase_1", "title": "Export core: normalization, aggregation & parity"},
    {"id": "phase_2", "title": "Export writer, manifest, CLI & committed launch dataset"},
    {"id": "phase_3", "title": "SPA results data layer: discovery, loader, validation & truncation fallback"},
    {"id": "phase_4", "title": "Leaderboard route + framing/scope/pressure selectors (Gemini-ranked)"},
    {"id": "phase_5", "title": "Per-tradition drill-down + judge selector + Opus validation layer"},
    {"id": "phase_6", "title": "Documentation: results data-contract README + multibrowser README"}
  ]
}
```

## Phase Breakdown

### Phase 1: Export core — normalization, aggregation & parity
**Dependencies**: None

#### Objectives
- Establish the pure, tested transform from the three source run directories to normalized per-tradition
  breakdown means — the correctness heart of the whole feature, provable without any file I/O or UI.

#### Deliverables
- [ ] New module `workflows/analysis/analysis/export_results.py` with pure functions:
      subject/judge alias maps, `normalize_subject`, `normalize_judge`, Opus identity-dedup (later-`ts`
      overlay), and a builder that produces, per (tradition, subject, framing, scope, pressure-incl-"all",
      judge), the breakdown **mean** + **coverage** (`n_judged`, `n_expected`) using the canonical
      `analysis.aggregate` semantics (import and reuse `aggregate.py`; do not re-derive the convention).
- [ ] Tests `workflows/analysis/tests/test_export_results.py`.
- [ ] No disk output in this phase (functions return in-memory structures).

#### Implementation Details
- **Alias maps (explicit, not algorithmic)**:
  - Subjects → 5 canonical: `Qwen/Qwen3-235B-A22B-Instruct-2507`, `claude-sonnet-5`, `gemini-3.6-flash`,
    `gpt-5.6-terra`, `thinkingmachines/Inkling`. Map every source variant (provider-prefixed / lowercased /
    Qwen-without-`-Instruct`) to these; **fail loudly** on an unmapped subject id (fail-fast, no silent
    passthrough).
  - Judges → 2 canonical: `gemini-3.6-flash`; `claude-opus-4-8` (absorbing `anthropic/claude-opus-4.8`).
- **Opus dedup**: normalized identity `(subject, tradition, scenario_id, pressure, framing, judge, scope)`;
  the two aliases are expected disjoint (sum), but on collision keep the later `ts` (overlay), count once.
- **Aggregation**: reuse `analysis.aggregate` cell/breakdown functions so a "cell" = mean of present judges
  and a breakdown = unweighted mean of in-scope cells (uncovered excluded, never 0). Produce per-tradition
  means for every slice the UI needs; the leaderboard's cross-tradition mean is *not* computed here (the SPA
  does it) — but a parity helper computes it for the test.
- **Coverage / `n_expected`**: per the spec data contract — specific pressure → `n_scenarios(tradition)`;
  pooled "all" → `n_scenarios × 6`. `n_scenarios` derived from the run (distinct `scenario_id` per tradition).
- Read the top-level numeric `score`, never the `raw` string.

#### Acceptance Criteria
- [ ] Merging the three runs yields **exactly five** subjects; `qwen/qwen3-235b-a22b-2507` →
      `Qwen/Qwen3-235B-A22B-Instruct-2507` (explicit test on the `-Instruct` case); an unmapped id raises.
- [ ] Opus alias dedup: disjoint aliases → count == sum; same identity under both → counted once (later `ts`).
- [ ] **Parity**: for judge=Gemini, `mean over traditions of per-tradition by_framing[full]` equals
      `stats_bundle.subj_overall[subject|framing][0]` within 1e-9 for all subjects × framings; per-tradition
      means match `report.json.scorecard` within tolerance.
- [ ] All tests pass.

#### Test Plan
- **Unit Tests**: alias maps (incl. Qwen + unmapped-raises), dedup (disjoint + collision), coverage/`n_expected`,
  per-slice means on a small hand-built fixture.
- **Integration Tests**: parity against the real launch runs under `tmp/judging-runs/` (mean-of-means ==
  `subj_overall`; per-tradition == `report.json`).
- **Manual Testing**: run the parity helper in a REPL against `20260803-merged` and eyeball a couple of cells.

#### Rollback Strategy
Delete the new module + test; nothing else references it yet.

#### Risks
- **Risk**: An unmapped subject/judge variant appears in the (still-filling) sample run.
  - **Mitigation**: fail-fast with the offending id; the map is the single place to extend; re-export at seal.
- **Risk**: Re-deriving aggregation drifts from canonical semantics.
  - **Mitigation**: import `analysis.aggregate` directly; the parity test is the guard.

---

### Phase 2: Export writer, manifest, CLI & committed launch dataset
**Dependencies**: Phase 1

#### Objectives
- Serialize the Phase-1 structures into the committed, versioned, per-tradition-sharded `results/<run-id>/`
  dataset + manifest, expose it as a Typer CLI command, and commit the (interim) launch dataset.

#### Deliverables
- [ ] Writer in `export_results.py` producing `results/<run-id>/manifest.json` + one shard per tradition
      (`results/<run-id>/<tradition>.json`), with `schema_version`.
- [ ] New Typer subcommand `export` in `workflows/analysis/analysis/cli.py` (args: source run dirs, `--run-id`,
      `--out results/`), consistent with the existing `report` command.
- [ ] Tests for serialization, size ceilings, manifest/shard schema, and a round-trip (write → re-read →
      equals the in-memory structure).
- [ ] **Committed output**: `results/<run-id>/**` for the launch set (Gemini + both Opus layers merged),
      generated by running the CLI against `tmp/judging-runs/` (commit only the OUTPUT, never from the symlink).

#### Implementation Details
- **Manifest** fields: `schema_version`, `run_id`, `generated_at` (passed in / stamped post-run — do not call
  `Date.now()` in library code), `subjects` (5 canonical), `judges` (`gemini`, `opus` with source-alias
  provenance), `framings`, `pressures`, `scopes`, per-tradition `n_scenarios`, and roll-up `counts`
  (judgments per judge, coverage summary). Records that the Opus stated/guided layer is a sample.
- **Shard** (per tradition): the slice table {subject × framing × scope × pressure-incl-"all" × judge →
  {mean, n_judged, n_expected}} — Gemini full, Opus where present. Compact keys; floats only; **no transcript
  turns, no rationale** (Approved Decision 5). Optional (SHOULD): pooled-Gemini bootstrap CIs if they fit.
- **Run-id**: single combined id for the launch (e.g. `20260803`) so one `results/<run-id>/` holds both
  judges; document the choice in the shard/manifest.
- **Size**: assert ≤ 8 MB total and ≤ 1 MB/shard in a test; if exceeded, trim optional fields (CIs first).
- **Interim + re-export**: the committed dataset is interim; a `porch`-independent re-run of the same CLI at
  seal regenerates it (Approved Decision 8) — no schema change, just fresher numbers.

#### Acceptance Criteria
- [ ] CLI `uv --project workflows/analysis run python -m analysis export <runs…> --run-id … --out results/`
      writes a valid dataset; re-reading it round-trips.
- [ ] Committed `results/<run-id>/` is ≤ 8 MB total, every shard ≤ 1 MB; manifest carries all required fields.
- [ ] Regenerating is deterministic (same inputs → byte-stable output, modulo the passed timestamp).
- [ ] All tests pass.

#### Test Plan
- **Unit Tests**: manifest/shard schema, size ceilings, round-trip, deterministic serialization (sorted keys).
- **Integration Tests**: full export of the launch runs; assert size + that Gemini standings recomputed from
  the shards still equal `subj_overall`.
- **Manual Testing**: inspect `results/<run-id>/manifest.json` and one shard by eye.

#### Rollback Strategy
`git rm -r results/<run-id>` and revert the writer/CLI changes; Phase 1 core remains intact.

#### Risks
- **Risk**: Dataset exceeds the size budget.
  - **Mitigation**: aggregates-only, drop optional CIs, per-tradition sharding; the size test fails loudly first.
- **Risk**: Committing from the read-only `tmp/judging-runs/` symlink.
  - **Mitigation**: write only under `results/`; stage explicit paths; the worktree write-guard also blocks
    out-of-worktree writes.

---

### Phase 3: SPA results data layer — discovery, loader, validation & truncation fallback
**Dependencies**: Phase 2 (dataset schema finalized)

#### Objectives
- Teach the SPA to discover, fetch, and validate `results/<run-id>/` at runtime through the existing
  SHA-pinned GitHub layer — with the truncation fallback extended so results never silently vanish.

#### Deliverables
- [ ] New result-model types + a zod schema in `apps/multibrowser/src/lib/model.ts` (or a new
      `resultsModel.ts`): manifest + shard shapes, mirroring the Phase-2 contract.
- [ ] Discovery + loader hooks in `src/lib/queries.ts`: `resultsRunIds(entries)` (regex over
      `results/([^/]+)/manifest.json`), `useResultsRuns(sha)` (list + latest-by-`generated_at`),
      `useResultsShard(sha, runId, tradition)` — SHA-keyed, `staleTime: Infinity`, off-budget `raw` fetches.
- [ ] Extend `src/lib/github.ts` `walkTraditions` → a generalized top-dir walk covering **both**
      `traditions/` and `results/` on a truncated tree.
- [ ] Runtime validation: parse manifest/shards through zod; malformed JSON, out-of-range/non-finite scores,
      unknown enum values, or unsupported `schema_version` surface as `Notice`s (display-first), never crashes.
- [ ] Tests in `src/lib/queries.test.ts` / `github.test.ts` (+ a small results fixture in `src/test/`).

#### Implementation Details
- Follow the existing pipeline exactly: `github.ts` (fetch) → parse/validate → `queries.ts` (SHA-keyed hooks).
- Keep the "one git-tree call per snapshot" property in the normal case; the extended fallback only triggers
  on `truncated`.
- Do **not** touch the inert per-scenario seam (`results.ts`/`ResultsRegion`) — Approved Decision 7 leaves it
  inert; the explorer uses these *new* run-level hooks instead.
- Reuse the `RateLimitError`/banner path unchanged (results add no on-budget calls).

#### Acceptance Criteria
- [ ] `resultsRunIds` lists runs from a fake tree; `useResultsRuns` defaults to the most recent by manifest date.
- [ ] Under a `truncated` fake tree, `results/` is still discovered and a shard loads (regression guard).
- [ ] A malformed shard / bad score / unknown enum / unsupported `schema_version` / missing field renders a
      `Notice`, not a crash; a 403 serves cached data + banner.
- [ ] All tests pass.

#### Test Plan
- **Unit Tests**: `resultsRunIds`, latest-by-date selection, zod validation (each failure mode), the
  generalized truncation walk.
- **Integration Tests**: `fakeFetch` serving a two-run `results/` tree (normal + truncated) via `renderApp`-level
  hook tests.
- **Manual Testing**: point a dev build at the committed launch dataset; confirm the run loads.

#### Rollback Strategy
Revert the new hooks/types and the `github.ts` fallback change; the corpus routes are untouched.

#### Risks
- **Risk**: Generalizing the fallback regresses tradition discovery.
  - **Mitigation**: keep the existing `traditions/` behavior identical; add tests for both dirs incl. truncated.

---

### Phase 4: Leaderboard route + framing/scope/pressure selectors (Gemini-ranked)
**Dependencies**: Phase 3

#### Objectives
- Ship the acceptance-critical view: a Gemini-ranked leaderboard (mean-of-per-tradition-means) at a new
  `/results` route, with deep-linkable framing, scope, and pressure selectors.

#### Deliverables
- [ ] `resultsRoute` (`/results`, `validateSearch`) added in `src/router.tsx` + a nav link in
      `src/routes/RootLayout.tsx`.
- [ ] `src/routes/ResultsPage.tsx` — loads the latest run + shards, computes the **equal-weight mean across
      the seven tradition-means** for the current selection, renders the standings table (subjects ranked,
      scores colored via the score palette).
- [ ] `src/lib/resultsSelection.ts` — the selection/deep-link model (judge, framing, scope, pressure), mirroring
      `filtering.ts`/`searchParams.ts` (typed search params, fail-soft).
- [ ] `src/lib/scoreColor.ts` — TS port of the diverging score palette stops from
      `workflows/analysis/analysis/colors.py` (single source of truth documented), `TwoSlopeNorm(−1,0,1)` linear.
- [ ] Leaderboard + selector components (e.g. `LeaderboardTable`, selector controls reusing the `FilterBar`
      `Toggle`/native-`<select>` idiom).
- [ ] Tests: reconciliation, selector behavior + deep-link, Gemini-only ranking.

#### Implementation Details
- **Ranking is Gemini-only** (Approved Decision 1): the standings statistic always uses judge=Gemini
  regardless of the judge selector (which affects only the Phase-5 drill-down/inspection layer). Because
  Gemini is full-grid, all seven traditions contribute for every selection — no coverage gating.
- **pressure="all"** reads the pooled cell-mean slice directly from the shard (never pools cells client-side).
- Selectors: framing (unstated/stated/guided) and scope (turn1=first-response / full=post-pressure) as toggles;
  pressure as the six + "all". All deep-linkable via `validateSearch`, exactly like the corpus filters.
- **No band-name labels** anywhere; numeric −1…+1 with the diverging palette.

#### Acceptance Criteria
- [ ] For the committed launch dataset, standings at framing∈{unstated,stated,guided}, scope=full,
      pressure=all match the paper's `subj_overall` to displayed precision (a test asserts this against a
      fixture derived from the real numbers).
- [ ] Changing any selector updates the table and the URL search string (deep-link round-trips).
- [ ] The leaderboard is unaffected by the judge selector's presence (ranking stays Gemini).
- [ ] All tests pass.

#### Test Plan
- **Unit Tests**: `resultsSelection` parse/serialize; `scoreColor` boundaries (−1, 0, +1).
- **Integration Tests**: `fakeFetch` + `renderApp("/results")` — reconciliation table, selector clicks assert
  DOM + `router.state.location.searchStr`.
- **Manual Testing**: dev build against the committed dataset; compare a column to the paper's table.

#### Rollback Strategy
Remove the route + nav link + new files; the SPA reverts to corpus-only.

#### Risks
- **Risk**: Client mean-of-means drifts from the paper.
  - **Mitigation**: tradition-means come pre-computed from canonical Python; the only client math is a mean;
    reconciliation test guards it.
- **Risk**: Route/search wiring regresses corpus routes.
  - **Mitigation**: additive `createRoute`; existing route tests stay green.

---

### Phase 5: Per-tradition drill-down + judge selector + Opus validation layer
**Dependencies**: Phase 4

#### Objectives
- Add the per-tradition drill-down and the **judge selector** as an inspection/validation switch: show Opus
  per-tradition means (coverage-badged) where Opus data exists, without ever re-ranking the board.

#### Deliverables
- [ ] Per-tradition drill-down UI (each tradition's contributing mean for the current selection), reachable
      from the leaderboard.
- [ ] Judge selector control: Gemini (default) | Opus. Selecting Opus swaps the **drill-down/inspection**
      numbers to the normalized Opus judge where present, each badged `sample (n/N)`; zero-coverage traditions
      show nothing (never 0). The top-level standings remain Gemini-ranked and labeled as such.
- [ ] Optional (SHOULD): judge-agreement context and/or pooled-Gemini CIs if carried by the dataset.
- [ ] Tests: judge selector switches inspection (not ranking), coverage badges render, zero-coverage hidden.

#### Implementation Details
- The judge selector is part of the same deep-linkable `resultsSelection` model (`judge=gemini|opus`).
- "Validation layer" framing in the UI copy: Opus is the second judge that spot-checks Gemini; make the sample
  nature unmistakable (badge + n/N + a short caption).
- Coverage comes straight from the shard's `n_judged/n_expected`; an internal "worth displaying" threshold is
  allowed (builder's discretion, Approved Decision 2) but is **not** a ranking gate.
- Keep the palette/label rules from Phase 4.

#### Acceptance Criteria
- [ ] Toggling the judge selector to Opus changes only the drill-down/inspection numbers; the leaderboard
      ranking is unchanged.
- [ ] Opus stated/guided views are badged `sample (n/N)`; a zero-coverage tradition renders nothing, not 0.
- [ ] `judge` participates in the deep-link URL.
- [ ] All tests pass.

#### Test Plan
- **Unit Tests**: coverage-badge formatting; selection model with `judge`.
- **Integration Tests**: `fakeFetch` dataset with uneven Opus coverage (mirror secular-sage ~2-cell case) →
  assert badge + hidden zero-coverage + unchanged ranking on judge toggle.
- **Manual Testing**: dev build; switch to Opus on stated framing; confirm badges + that standings don't move.

#### Rollback Strategy
Hide the judge selector + drill-down (feature-flag or remove the components); Phase 4 leaderboard still stands.

#### Risks
- **Risk**: Users read Opus sample numbers as authoritative rankings.
  - **Mitigation**: no Opus ranking exists; prominent sample badges + caption; zero-coverage hidden.

---

### Phase 6: Documentation — results data-contract README + multibrowser README
**Dependencies**: Phase 5

#### Objectives
- Document the results data contract and how to export a new run, so the additive no-redeploy workflow is
  reproducible by a future run author.

#### Deliverables
- [ ] `results/README.md` — the data-contract: directory layout, manifest + shard schema (`schema_version`),
      normalization rules (subject/judge alias maps, Opus dedup), coverage/`n_expected` definition, size
      ceilings, and the exact `analysis export …` command (incl. the re-export-at-seal note).
- [ ] Update `apps/multibrowser/README.md` — the `/results` explorer, the runtime results-read, and the
      Gemini-ranked-with-Opus-validation model.
- [ ] (Review phase, not here) arch-doc routing via the `update-arch-docs` skill — noted for the Review phase.

#### Implementation Details
- Keep the README the single source of truth for the data contract; the SPA zod schema and the Python writer
  both point to it.

#### Acceptance Criteria
- [ ] A reader can export + commit a new run from the README alone and see it appear in the browser.
- [ ] READMEs match the shipped schema and routes.

#### Test Plan
- **Unit Tests**: N/A (docs).
- **Integration Tests**: N/A.
- **Manual Testing**: follow the README end-to-end for a second (dummy) run-id and confirm it appears.

#### Rollback Strategy
Revert the doc files.

#### Risks
- **Risk**: Docs drift from the schema.
  - **Mitigation**: written last, against the shipped code; the data contract lives in one README.

## Dependency Map
```
Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4 ──→ Phase 5 ──→ Phase 6
(export core) (writer+  (SPA data   (leaderboard  (drill-down  (docs)
              dataset)  layer)      + selectors)  + judge/Opus)
```

## Resource Requirements
### Development Resources
- **Engineers**: this builder (spir-49) — Python (`uv`, Typer) for Phases 1–2; TS/React/TanStack/HeroUI for
  Phases 3–5.
- **Environment**: worktree with the read-only `tmp/judging-runs/` symlink; pnpm + uv toolchains present.

### Infrastructure
- No database, no services, no config changes. New committed data under `results/`. Railway static deploy is
  unchanged (verified via manual `railway up` in the Verify phase).

## Integration Points
### External Systems
- **GitHub** (git-trees + `raw`, unauthenticated): the runtime data source.
  - **Integration Type**: HTTP (existing `github.ts`).
  - **Phase**: Phase 3.
  - **Fallback**: 403 → cached data + banner; truncated tree → extended per-dir walk (Phase 3).
- **Railway** (static hosting): deploy target, manual `railway up`; verified in the Verify phase.

### Internal Systems
- **`workflows/analysis/analysis/aggregate.py`** (+ `colors.py`): canonical aggregation + palette source.
  - **Integration Type**: Python import.
  - **Phase**: Phases 1–2 (aggregate), Phase 4 (palette port).
- **`apps/multibrowser` data layer** (`github.ts`, `queries.ts`, `filtering.ts`, `searchParams.ts`): reused/extended.
  - **Phase**: Phases 3–5.

## Risk Analysis
### Technical Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Leaderboard drifts from the paper | L | H | Canonical per-tradition means; SPA does only mean-of-means; parity + reconciliation tests | builder |
| Subject/judge alias miss (10 subjects / bad Qwen merge) | M | H | Explicit maps, fail-fast on unmapped, tests incl. `-Instruct` + dedup | builder |
| Dataset exceeds size budget | L | M | Aggregates-only, per-tradition shards, drop optional CIs; CI size assertion | builder |
| Results vanish on truncated tree | M | H | Extend fallback to `results/`; regression test | builder |
| Malformed remote dataset crashes SPA | M | M | zod validation + `schema_version`; inline notices | builder |
| Opus sample read as ranking | M | M | No Opus ranking; sample badges + n/N; zero-coverage hidden | builder |

### Schedule Risks
| Risk | Probability | Impact | Mitigation | Owner |
|------|------------|--------|------------|-------|
| Opus tail-fill not sealed at first export | H | L | Interim export is valid + self-describing; re-export at seal (same command) | architect/builder |

## Validation Checkpoints
1. **After Phase 1**: parity green against the real runs (mean-of-means == `subj_overall`).
2. **After Phase 2**: committed dataset within size ceilings; Gemini standings recomputed from shards == paper.
3. **After Phase 3**: results discovered + validated, incl. under a truncated tree.
4. **After Phase 4**: leaderboard reconciles to displayed precision; selectors deep-link.
5. **After Phase 5**: judge selector switches inspection only; Opus coverage badged honestly.
6. **Before Production (Verify phase)**: `railway up` deploy; judge & pressure selectors work live; a fresh
   run-id appears without a code change.

## Monitoring and Observability
### Metrics to Track
- N/A — static client-side SPA, no backend telemetry. (Freshness is the SHA poll; rate-limit state shows the banner.)

### Logging Requirements
- N/A at runtime (browser). The export CLI echoes a summary (counts, size, coverage) to stderr/stdout.

### Alerting
- N/A.

## Documentation Updates Required
- [ ] `results/README.md` (data contract) — Phase 6
- [ ] `apps/multibrowser/README.md` (explorer + runtime read) — Phase 6
- [ ] Architecture docs via `update-arch-docs` skill — Review phase (a new committed `results/` data tier + the
      Gemini-ranked/Opus-validation convention are durable, cross-cutting facts)
- [ ] Runbooks / config guides — N/A

## Post-Implementation Tasks
- [ ] Performance validation — confirm the explorer adds no on-budget GitHub calls (fake-fetch call-log test).
- [ ] Security audit — N/A beyond "public read-only data, no secrets"; confirm no token introduced.
- [ ] Load testing — N/A (static site).
- [ ] User acceptance testing — architect review of the live leaderboard vs the paper.
- [ ] Monitoring validation — N/A.

## Expert Review
**Date**: (pending — porch runs the 2-way plan consultation: Codex + Claude)
**Model**: Codex, Claude
**Key Feedback**:
- (to be filled after consultation)

**Plan Adjustments**:
- (to be filled after consultation)

## Approval
- [ ] Technical Lead Review
- [ ] Engineering Manager Approval
- [ ] Resource Allocation Confirmed
- [ ] Expert AI Consultation Complete

## Change Log
| Date | Change | Reason | Author |
|------|--------|--------|--------|
| 2026-08-06 | Initial plan | Spec approved with simplifying decisions (Gemini-only ranking) | builder |

## Notes
- **Spec/plan boundary**: exact JSON key names, component names, and file splits may adjust during
  implementation as long as the data contract (Phase 2/6 README), the Gemini-only ranking, the Opus
  validation-layer model, and the acceptance criteria hold.
- **Re-export at seal** (Approved Decision 8): a single re-run of the Phase-2 CLI regenerates
  `results/<run-id>/` with the sealed Opus sample — no schema change, no code change, a fresh commit.
- **Per-phase consult** here is `[codex, claude]` (Gemini can't see the worktree); the full 3-way runs only
  where the diff is fed inline (the PR integration CMAP).
