# Specification: MultiBrowser Results Explorer — Judge & Pressure Selectors + Leaderboard

<!--
SPEC vs PLAN BOUNDARY:
This spec defines WHAT and WHY. The plan defines HOW and WHEN.
-->

## Metadata
- **ID**: spec-2026-08-05-multibrowser-results-explorer
- **Status**: approved
- **Created**: 2026-08-05
- **Approved**: 2026-08-06 (architect, with the simplifying decisions in "Approved Decisions" below)

## Approved Decisions (architect, 2026-08-06 — supersede any conflicting text below)

These are baked, post-approval decisions from Waleed via the architect. Where they conflict with earlier
draft text, **these win**; the affected sections have been reconciled to match.

1. **The leaderboard ranks on Gemini ONLY.** Gemini is the complete judge (full grid, all framings); **Opus
   is never a ranking judge.** There is no Opus-ranked leaderboard in any framing. The **judge selector**
   therefore does not switch *which judge ranks*; it switches **inspection / drill-down** views (per-tradition
   means, coverage badges, judge-agreement context) to Opus **where Opus data exists**, clearly badged as the
   **validation layer**. This **moots** the earlier Critical question about Opus stated/guided ranking.
2. **`min_coverage` is no longer a ranking gate** (the leaderboard is Gemini-only and full-grid, so nothing
   is gated out). Coverage is still **displayed/badged** (`n/N`) for honest Opus inspection views; an internal
   "worth displaying" threshold is allowed at the builder's discretion in the plan.
3. **pressure="all" = cell-pooled mean** (paper convention) — confirmed.
4. **Run discovery** defaults to the **most recent run by manifest date**; a run selector is optional (SHOULD).
5. **Rationale/verdict text**: aggregates-only for v1 stands (no per-judgment rationale published).
6. **Bootstrap CIs**: optional SHOULD, and only for the **pooled Gemini** standings.
7. **`ResultsRegion` seam**: leave **inert** (do not wire the per-scenario results region in this work).
8. **Data / re-export**: the Opus framings-sample tail-fill is essentially complete (~8 straggler sittings
   being swept); plan for **one re-export at seal** once the architect confirms it.

## Clarifying Questions Asked

A spec file did not exist at spawn, so the answers below are drawn from issue #49, the architect's
data-access notes, the real launch data under `tmp/judging-runs/`, and the established repo conventions
(Specs 7, 8, 26; `codev/resources/arch-critical.md`). No live questions were put to the user; the issue
plus reference data already fix the key decisions. The questions the spec had to resolve, and how:

- **Q: Should the SPA compute standings from raw per-cell scores, or read pre-aggregated numbers?**
  A: Read pre-aggregated per-tradition means computed by the *canonical* Python aggregator, and let the
  SPA do only the final equal-weight mean across traditions. This was validated numerically (see
  Desired State) and guarantees the leaderboard reconciles with the paper.
- **Q: What exactly is the "mean of per-tradition means, post-pressure" standings convention?**
  A: For a given (subject, framing, scope): take each tradition's unweighted mean over its in-scope cells,
  then average those seven tradition-means with equal weight. `scope=full` is post-pressure; `scope=turn1`
  is first-response. Verified to equal the paper's `subj_overall` point estimates exactly.
- **Q: How is the dual-judge / Opus alias / sample-coverage problem handled?**
  A: The export alias-normalizes the two Opus **judge** ids to one, and records per-cell coverage
  (`n_judged / n_expected`) so views can degrade honestly where Opus is sample-only. The SPA never sees
  two Opus judges and never presents a sample mean as if it were full-grid.
- **Q: Are only *judge* ids aliased across the source runs?**
  A: No — **subject** ids are also split. `20260803-framings-opus-sample` uses provider-prefixed, lowercased
  subject ids (`anthropic/claude-sonnet-5`, `qwen/qwen3-235b-a22b-2507`, `thinkingmachines/inkling`, …) while
  `20260803-merged` / `-unstated-opus` use the canonical ids (`claude-sonnet-5`,
  `Qwen/Qwen3-235B-A22B-Instruct-2507`, `thinkingmachines/Inkling`, …). A naive "strip prefix + lowercase"
  rule **fails on Qwen** (`qwen3-235b-a22b-2507` vs `Qwen3-235B-A22B-Instruct-2507` — the `-Instruct` segment
  is dropped upstream). So the export needs an **explicit subject alias map** (not an algorithm) plus a test
  asserting exactly five normalized subjects. (Verified against the run data.)
- **Q: With tiny Opus samples, is "exclude zero-coverage traditions" enough?**
  A: No — measured stated/full Opus coverage ranges from ~2 cells (secular-sage) to ~230 cells (sunni-islam)
  per tradition; equal 1/7 weighting would let a 2-cell estimate count as much as a 230-cell one. Honest
  degradation must cover **tiny-non-zero** coverage via a concrete minimum-coverage rule, not just zero.
- **Q: What granularity keeps the export in single-digit MB with no transcripts?**
  A: Pre-aggregated breakdowns + coverage + score distributions, sharded per tradition. No transcript
  turns and no per-judgment rationale in v1 (see Open Questions for the rationale trade-off).

## Problem Statement

The 20260803 results programme produced a large dual-judged evaluation run (93,420 Gemini judgments across
the full 5-subject × 3-framing × 6-pressure grid for seven traditions, plus two Opus judge layers). Today
those results are reachable only as a 583 MB local, gitignored run directory and a static HTML/PDF paper —
there is no interactive way to browse them alongside the corpus. The `multibrowser` SPA already browses the
tradition corpus live from GitHub but deliberately ships an **inert** results seam (`loadResults` returns
`null`); the judging output was never bound to it.

We need to bring the JaleesBench browser's "explorer" experience — a **leaderboard** with a **judge
selector** and a **pressure selector** — into `multibrowser`, driven by a compact, committed, browsable
results dataset that the SPA reads at runtime exactly the way it reads traditions. The numbers shown must
reconcile with the paper's standings table, the two Opus judge aliases must be collapsed to one, and views
must be honest wherever Opus coverage is only a sample.

## Current State

- **Run data**: `tmp/judging-runs/<run-id>/<tradition>/{sittings,judgments}.jsonl` + per-tradition
  `report.json`/`report.md` + a run-level `analysis-out/` (figures, `analysis_stats.json`, and the report-v2
  `stats_bundle.json`). This is local-only and gitignored (583 MB); the browser cannot read it.
- **The SPA** (`apps/multibrowser/`, Vite 6 / React 19 / TS / Tailwind 4 / HeroUI v3 / TanStack
  Router+Query) browses the corpus by reading GitHub at runtime: it resolves the latest `main` SHA, lists
  files via one git-trees call, and fetches content from `raw.githubusercontent.com` pinned to that SHA
  (raw is off the 60/hr unauthenticated API budget). New/edited traditions appear without a redeploy.
- **Results are stubbed out**: `src/lib/results.ts` (`loadResults → null`), an intentionally empty
  `ScenarioResults` type, and a reserved `ResultsRegion` placeholder — an explicit additive seam awaiting
  the judging output's shape. There is no `/results` route, no leaderboard, and no selectors.
- **The canonical aggregation** already exists in Python: `workflows/analysis/analysis/aggregate.py`
  faithfully reproduces `judging.report`'s numeric semantics (cell = subject × scenario × pressure × framing
  × scope; cell score = mean of present judges; breakdown = unweighted mean of in-scope cells; headline =
  unstated + full; steadfastness = full − turn1). The report-v2 `stats_bundle.json.subj_overall` holds the
  paper's standings point estimates + bootstrap CIs.
- **The Opus judge alias split is real**: in `20260803-framings-opus-sample`, Opus judgments appear under
  both `claude-opus-4-8` (batch) and `anthropic/claude-opus-4.8` (OpenRouter tail); the split is
  per-tradition and the sample dir is still being tail-filled (counts moving until the architect seals it).
- **A subject-id split is *also* real** (not just judges): the sample run's subject ids are provider-prefixed
  and lowercased and, for Qwen, drop the `-Instruct` segment — so a merge on the raw subject key yields ten
  subjects instead of five. Verified: merged/unstated-opus use `{Qwen/Qwen3-235B-A22B-Instruct-2507,
  claude-sonnet-5, gemini-3.6-flash, gpt-5.6-terra, thinkingmachines/Inkling}`; the sample run uses
  `{qwen/qwen3-235b-a22b-2507, anthropic/claude-sonnet-5, google/gemini-3.6-flash, openai/gpt-5.6-terra,
  thinkingmachines/inkling}`.
- **`gemini-3.6-flash` is both a judge and a subject**: it is the sole judge of the merged run *and* one of
  the five evaluated subjects. In the merged run the Gemini judge *does* score the `gemini-3.6-flash` subject
  (no self-skip for the launch data), so both roles coexist and must be disambiguated in the data and UI.

## Desired State

A **Results Explorer** in `multibrowser`, added as new routes/facets without disturbing corpus browsing:

- A **leaderboard** showing overall standings by subject for the selected framing and scope, computed as
  the **mean of per-tradition means, post-pressure** (the paper's `tab_standings` convention), with a
  **per-tradition drill-down**, a **framing toggle** (unstated / stated / guided), and a **scope toggle**
  (first-response = `turn1` / post-pressure = `full`).
- **The leaderboard ranks on Gemini only** (Approved Decision 1). Gemini is the complete judge, so standings
  exist for every framing/scope/pressure without coverage gaps. A **judge selector** does **not** re-rank the
  board; instead it switches the **inspection / drill-down** context to **Opus where Opus data exists** —
  per-tradition means, coverage badges, and judge-agreement context — clearly badged as the **validation
  layer**. "Judge" and "subject" are kept distinct everywhere: `gemini-3.6-flash` is both the ranking judge
  and one of the five ranked **subjects**, and the UI must never conflate the two.
- **Honest degradation for Opus inspection views**: each Opus tradition-mean carries its coverage (`n_judged
  / n_expected`) and is badged `sample (n/N)`; zero-coverage traditions show nothing rather than a 0. Because
  the leaderboard is Gemini-only, coverage is **not** a ranking gate (Approved Decision 2) — it governs only
  what the Opus validation views display; the builder may keep an internal "worth displaying" threshold.
- A **pressure selector** that filters every results view by one of the six pressures or "all".
- The whole explorer is fed by a **committed, additive results dataset** the SPA reads at runtime:
  `results/<run-id>/` with a **manifest** (subjects, judges, framings, pressures, scopes, counts, dates,
  per-cell coverage) plus **per-tradition shards** (scores + metadata only — no transcripts). Total per run
  lands in **single-digit MB**, sharded so any single raw fetch is small. A newly exported+committed run
  appears in the browser with **no code change** (same git-trees + raw mechanism as traditions).

**Reconciliation is guaranteed by construction.** The export publishes each tradition's breakdown means
computed by the canonical Python aggregator; the SPA's only client-side statistic for the leaderboard is
the equal-weight mean across the seven tradition-means. This was verified against the launch data (judge = Gemini; the ranked subject is `gemini-3.6-flash`; scope =
full; pressure = all):

| framing | mean-of-per-tradition-means (subject `gemini-3.6-flash`) | paper `subj_overall[gemini-3.6-flash]` | match |
|---|---|---|---|
| unstated | 0.138790 | 0.138790 | exact |
| stated | 0.555226 | 0.555226 | exact |
| guided | 0.939201 | 0.939201 | exact |

## Stakeholders
- **Primary Users**: MultiBench researchers/readers exploring the 20260803 results interactively and
  cross-checking them against the paper.
- **Secondary Users**: Future run authors who export a new run and expect it to surface without redeploy.
- **Technical Team**: This builder (spir-49); maintainers of `apps/multibrowser` and `workflows/analysis`.
- **Business Owners**: The architect (project 49 owner) and the MultiBench project lead.

## Success Criteria
- [ ] **Leaderboard reconciles with the paper**: overall standings (mean of per-tradition means) for every
      subject × framing at `scope=full`, judge=Gemini, pressure=all, match the paper's standings table to
      the displayed precision.
- [ ] **Leaderboard ranks on Gemini only** in every framing/scope/pressure; no Opus-ranked board exists.
- [ ] **Judge selector** switches the **inspection/drill-down** views to a single normalized Opus judge
      (validation layer, badged) where Opus data exists; it does not re-rank the leaderboard; the SPA never
      exposes two Opus judges.
- [ ] **Pressure selector** filters every results view by each of the six pressures and by "all".
- [ ] **Framing toggle** (unstated/stated/guided) and **scope toggle** (first-response/post-pressure) drive
      the leaderboard and drill-down.
- [ ] **Per-tradition drill-down** shows each tradition's contributing mean for the current selection.
- [ ] **Honest degradation (Opus inspection views)**: where Opus coverage is sample-only (stated/guided),
      the view is badged as a sample and shows coverage (`n_judged / n_expected`); zero-coverage traditions
      show nothing, never a 0. (Coverage is display-only, not a ranking gate — the board is Gemini-only.)
- [ ] **Subject normalization**: the export maps all source subject-id variants to exactly **five** canonical
      subjects via an explicit alias map (covering the Qwen `-Instruct` case); a test asserts exactly five.
- [ ] **Judge alias normalization**: the export collapses `claude-opus-4-8` and `anthropic/claude-opus-4.8`
      into one Opus judge, deduping any identity present under both aliases (no double-counting); a test
      covers both the disjoint-sum case and the collision-dedup case.
- [ ] **Additive, no-redeploy publish**: a new `results/<run-id>/` exported and committed appears in the
      browser without a code change; corpus browsing is unchanged. This holds **even when the recursive git
      tree is truncated** — the truncation fallback must discover `results/` as well as `traditions/`.
- [ ] **Size budget (exact, CI-checked)**: each run's committed dataset is **≤ 8 MB total** and each
      per-tradition shard is **≤ 1 MB**; a test/CI assertion enforces these byte ceilings.
- [ ] **Runtime dataset validation**: the SPA validates the manifest and shards (schema version, well-formed
      JSON, finite in-range scores, known selector values); malformed/missing data renders an inline notice,
      never a crash.
- [ ] Judge & pressure selectors work on the live Railway deploy (manual `railway up`).
- [ ] All tests pass (the touched-app suites: `pnpm -C apps/multibrowser test` and, if the export is Python,
      `uv … pytest` for the export module); no reduction in coverage.
- [ ] Documentation updated (a `results/README.md` data contract + the multibrowser README).

## Constraints

### Technical Constraints
<!-- These are fixed architectural constraints taken verbatim from issue #49 ("Constraints (arch-critical)"
     and "What"/"Data access"/"Acceptance"). Treat each as baked; do not relitigate in Solution Approaches. -->
- **Client-side only, GitHub-at-runtime**: the SPA reads GitHub at runtime (SHA-pinned git-trees + `raw`
  fetches, unauthenticated 60/hr budget). Results data must be **committed files, additive, no backend, no
  baked data** — a new run appears without redeploy. Results add effectively zero API calls (same one
  git-tree per snapshot; shard content via `raw` is off-budget).
- **Stack**: Vite / React 19 / TS / Tailwind 4 / HeroUI v3 (**provider-less** — no `HeroUIProvider`) /
  TanStack Router + Query. Reuse the existing data layer and filter/deep-link machinery.
- **Corpus browsing must remain intact**; results features are **additive routes/facets**.
- **Scores + metadata only — no full transcripts.** Raw run data is 583 MB; the export must land in
  single-digit MB, **sharded per tradition** so raw fetches stay small. Include a **manifest** (subjects,
  judges, framings, pressures, scopes, counts, dates).
- **Dual-judge with Opus judge-alias normalization**: the run is Gemini 3.6 Flash (full grid) + Claude Opus
  4.8 (unstated full + stated/guided sample). Opus judgments exist under two aliases (`claude-opus-4-8` vs
  `anthropic/claude-opus-4.8`); **the export must alias-normalize** so the SPA sees one Opus judge. The
  normalized judgment identity is `(subject, tradition, scenario_id, pressure, framing, judge, scope)`; the
  two aliases are expected to be **disjoint** (batch vs tail-fill), so the normalized count equals the sum —
  but if the *same* identity appears under both, the later `ts` **wins (overlay)** and it is counted once (no
  double-vote). Views must **degrade honestly** where Opus coverage is sample-only.
- **Subject-id normalization**: the export must map every source subject-id variant to one of exactly five
  canonical subjects via an **explicit alias map** (not an algorithmic prefix-strip, which breaks on Qwen's
  dropped `-Instruct`). Canonical set: `Qwen/Qwen3-235B-A22B-Instruct-2507`, `claude-sonnet-5`,
  `gemini-3.6-flash`, `gpt-5.6-terra`, `thinkingmachines/Inkling`.
- **Coverage & `n_expected` (data contract)**: every published tradition-mean carries `n_judged` and
  `n_expected`. For a slice `(tradition, subject, framing, scope, pressure)` where pressure is a specific
  pressure, `n_expected = n_scenarios(tradition)`; for the pooled `pressure="all"` slice,
  `n_expected = n_scenarios(tradition) × 6`. `n_scenarios(tradition)` is fixed per tradition (recorded in the
  manifest) and is judge-independent, so coverage is a true fraction of the full grid, not of observed rows.
- **Truncation fallback must cover `results/`**: the SPA's git-tree read is one recursive call in the normal
  case, but GitHub may report the recursive tree `truncated`; the existing per-directory fallback walks only
  `traditions/`. Adding `results/` shards increases tree size (raising truncation odds), so the fallback
  **must be extended to also walk `results/`**, or results would silently vanish on a truncated tree. The
  "exactly one git-tree call" property holds only for the normal, non-truncated snapshot.
- **Exact size ceilings (CI-enforced)**: committed dataset **≤ 8 MB total per run**; **≤ 1 MB per tradition
  shard**. These replace the informal "single-digit MB" so a CI assertion is unambiguous.
- **Versioned, validated dataset**: the manifest carries a `schema_version`; the SPA validates the manifest
  and shards (well-formed JSON, finite scores in −1…+1, known subjects/judges/framings/pressures/scopes) and
  renders an inline notice on any violation rather than crashing.
- **Leaderboard convention is fixed**: overall standings by framing = **mean of per-tradition means,
  post-pressure**, the same convention as the paper's Table `tab_standings`. Numbers must reconcile with the
  paper's tables. To guarantee this, the export must use the **canonical aggregation semantics** already
  encoded in `workflows/analysis` (cell = mean of present judges; breakdown = unweighted mean of in-scope
  cells; uncovered cells excluded, never 0).
- **Charts, if any, follow the repo's dataviz palette** — the seven-stop diverging score colormap
  (`workflows/analysis/analysis/colors.py`, deep red → grey-beige → deep green, `TwoSlopeNorm(−1,0,1)`
  linear). **No band-name labels** (Burns/Sparks/… are forbidden in any output); the scale is numeric −1…+1.
- **Canonical launch data**: `20260803-merged` (Gemini) + `20260803-unstated-opus` + the (moving)
  `20260803-framings-opus-sample`. The run data is a **read-only symlink** in the worktree
  (`tmp/judging-runs/`); build/test the export against it but **commit only the export OUTPUT**.

### Business Constraints
- **Timeline**: N/A — no time estimates (AI-age; measure by completed phases).
- **Budget**: N/A — no monetary budget constraint on this work.
- **Compliance**: N/A — public, read-only benchmark data; no PII, no auth.

## Assumptions
- The judging output schema is stable for the launch run: `judgments.jsonl` rows carry a numeric top-level
  `score` (∈ {−1, −0.5, 0, 0.5, 1}) and the identity keys `(subject, tradition, scenario_id, pressure,
  framing, judge, scope)`; the export reads the top-level `score`, never the `raw` string.
- The three source run directories together supply Gemini (all framings, full grid) and Opus (unstated full
  + stated/guided sample) for the same seven traditions and five *logical* subjects — but the subject **and**
  judge ids are spelled differently across runs (see Current State). After the export applies its explicit
  subject and judge alias maps, exactly five subjects and two judges (Gemini, Opus) remain; the export
  **merges** the runs into per-tradition, per-judge shards on the normalized keys.
- The canonical aggregation in `workflows/analysis/analysis/aggregate.py` is the source of truth for cell
  and breakdown semantics; the export reuses it (or re-derives identical numbers verified against
  `report.json` / `stats_bundle.json`).
- `framings-opus-sample` counts are still moving; the export is **re-runnable**, so an **interim** committed
  dataset is acceptable and is regenerated (same command) once the architect confirms the sample is sealed.
  The manifest records the run's coverage and an export timestamp, so an interim export is self-describing
  rather than misleading. (This resolves the first-round "sample sealing" concern — it does not block.)
- The SPA continues to have exactly one git-tree call per snapshot; results shards are additional `raw`
  fetches (off-budget) fetched lazily per tradition/run.

## Solution Approaches

### Approach 1: Pre-aggregated per-tradition shards; SPA does only mean-of-means (RECOMMENDED)
**Description**: A Python export tool (reusing `workflows/analysis` aggregation) reads the merged run +
the two Opus layers, alias-normalizes Opus, and writes `results/<run-id>/manifest.json` plus one shard per
tradition. Each shard carries, per (subject × framing × scope × pressure-including-"all" × judge), the
tradition's breakdown **mean** and **coverage** (`n_judged`, `n_expected`), plus per-subject score
distributions. The SPA reads the shards and computes the leaderboard as the **equal-weight mean across the
seven tradition-means**; the drill-down just lists those tradition-means. Selectors/toggles pick which
precomputed slice to display.

**Pros**:
- Reconciliation is guaranteed — tradition-means come from the canonical aggregator, and mean-of-means was
  verified to equal the paper exactly.
- Tiny: ~a few thousand floats + counts per run → comfortably single-digit MB (likely << 1 MB core).
- Client math is trivial and pressure/framing/scope/judge are a fixed finite slice space, so no TS
  re-implementation of the aggregation convention is needed.
- Honest degradation falls out of the coverage counts already in each slice.

**Cons**:
- The slice space is fixed at export time; a genuinely new cross-cut (e.g. arbitrary per-scenario filtering)
  would need an export change. Mitigated: the issue's required cuts (judge/pressure/framing/scope, per
  tradition) are all covered, and per-scenario is a bounded SHOULD.

**Estimated Complexity**: Medium
**Risk Level**: Low

### Approach 2: Publish compact per-cell scores; SPA aggregates client-side
**Description**: Export a compact per-cell shard (subject, scenario, pressure, framing, scope, judge →
score) per tradition; re-implement the aggregation convention in TypeScript so the SPA computes every
breakdown live.

**Pros**:
- Maximum flexibility for future cross-cuts (per-scenario, custom groupings) with no re-export.

**Cons**:
- Must faithfully re-implement `aggregate.py`'s convention in TS and keep it in sync — direct reconciliation
  risk against the paper (the exact failure the "reconcile to displayed precision" acceptance guards).
- Larger: ~65k+ Gemini cells + Opus across seven traditions; feasible in single-digit MB only with a packed
  columnar layout, pushing complexity onto both writer and reader.

**Estimated Complexity**: High
**Risk Level**: Medium

### Approach 3: Hybrid — Approach 1 core + a bounded per-scenario layer
**Description**: Ship Approach 1 for the leaderboard/drill-down, and additionally emit per-scenario means at
the headline (and optionally per-framing) condition (mirroring `report.json.by_scenario`) for a scenario-level
drill-down, kept small by limiting the per-scenario cross-cut.

**Pros**: Adds scenario-level exploration without the full per-cell cost or the TS-aggregation reconciliation
risk.
**Cons**: More surface than the issue strictly requires; per-scenario across all framing×scope×pressure would
blow the size budget, so the cross-cut must be deliberately limited.
**Estimated Complexity**: Medium-High
**Risk Level**: Low-Medium

**Recommendation**: **Approach 1** for v1 (meets every acceptance criterion with guaranteed reconciliation
and the smallest reconciliation risk), with the **per-scenario layer of Approach 3 as an optional SHOULD**
if it fits the size budget. Approach 2 is not recommended because it puts the paper-reconciliation guarantee
at risk.

Several issues raised in first-round consultation are now **resolved** in the sections above and are noted
here for traceability: subject-id alias map (Constraints); Opus judge-alias dedup/overlay semantics
(Constraints); `n_expected` definition (Constraints); truncation-fallback extension to `results/`
(Constraints); exact size ceilings and runtime validation (Constraints/Success Criteria); pooled
`pressure="all"` = cell-pooled mean emitted directly by the export (below); judge-vs-subject disambiguation
(Desired State). The remaining genuine questions:

**All previously-open questions were resolved by the architect's Approved Decisions (see top of spec):**
- ~~`min_coverage` threshold as a ranking gate~~ → **resolved**: leaderboard is Gemini-only, so coverage is
  not a ranking gate; it is display-only for Opus inspection views (Decision 2).
- ~~Opus stated/guided ranking presentation~~ → **mooted**: Opus never ranks (Decision 1).
- ~~Rationale/verdict text~~ → **resolved**: aggregates-only for v1 (Decision 5).
- ~~Run discovery UX~~ → **resolved**: default most-recent-by-manifest-date; selector optional SHOULD (Decision 4).
- ~~Pooled `pressure="all"`~~ → **resolved**: cell-pooled mean, paper convention (Decision 3).
- ~~Bootstrap CIs~~ → **resolved**: optional SHOULD, pooled Gemini standings only (Decision 6).
- ~~Wire the `ResultsRegion` seam~~ → **resolved**: leave inert (Decision 7).

No open questions remain that block planning.

## Performance Requirements
- **API budget**: no material increase to the unauthenticated 60/hr GitHub budget — results reuse the one
  per-snapshot git-tree call; all shard/manifest content is fetched via `raw` (off-budget).
- **Payload size**: each run's committed dataset **single-digit MB total**, sharded per tradition so any one
  shard fetch is small (target: largest tradition shard well under ~1 MB).
- **Response time**: leaderboard renders from a small number of `raw` fetches (manifest + the needed shards)
  within interactive latency; switching selectors/toggles is client-side and instant (no refetch beyond the
  already-cached shards).
- **Resource usage**: negligible client memory (aggregates only, no transcripts).

## Security Considerations
- **Authentication**: none — public, read-only SPA reading public GitHub content; a client app holds no
  token (unauthenticated requests only).
- **Authorization**: N/A — all data is public benchmark output.
- **Data privacy**: results are model scores and metadata; **no transcripts** are published, so no risk of
  leaking scenario transcript content through the results layer.
- **Audit**: the committed dataset is versioned in git (the run-id + manifest date provide provenance).

## Test Scenarios

### Functional Tests
1. **Leaderboard reconciliation (happy path)**: given the launch shards, the leaderboard for each subject ×
   framing at scope=full / judge=Gemini / pressure=all equals the paper's standings to displayed precision.
2. **Judge switch**: selecting Opus recomputes every view from the normalized Opus judge; the alias split
   never surfaces as two judges. Alias-normalization tests: (a) disjoint aliases → normalized count == sum;
   (b) same identity under both aliases → counted once, later `ts` wins.
3. **Subject normalization**: merging the three source runs yields exactly five canonical subjects; the Qwen
   variant `qwen/qwen3-235b-a22b-2507` maps to `Qwen/Qwen3-235B-A22B-Instruct-2507` (a test guards the
   `-Instruct` case); no run produces a sixth subject.
4. **Pressure filter**: selecting each of the six pressures (and "all") changes the standings/drill-down to
   the corresponding precomputed slice; "all" matches the cell-pooled convention.
5. **Framing & scope toggles**: unstated/stated/guided and turn1/full each select the correct slice.
   Steadfastness (full − turn1) is computed **only over cells present in both scopes** (the unstated-opus
   panel has slightly more turn1 than full cells), so the test uses a matched-cell definition, not raw
   scope totals.
6. **Honest degradation (Opus inspection view)**: switching the judge selector to Opus for framing=stated
   shows per-tradition means badged `sample (n/N)` (e.g. secular-sage's ~2-cell mean is badged, not silently
   averaged in); a zero-coverage tradition shows nothing, never a 0. The **leaderboard itself stays Gemini-
   ranked** and unchanged by the judge selector.
7. **Additive no-redeploy publish**: with a second `results/<run-id>/` present in the fake repo tree, the
   explorer lists/loads it without any code change; the corpus routes are unaffected.
8. **Truncated-tree discovery**: when the fake repo reports the recursive tree `truncated`, the extended
   fallback still discovers `results/` and the explorer loads (regression guard for the current
   `traditions/`-only fallback).
9. **Runtime validation / missing data**: a malformed shard, an out-of-range/non-finite score, an unknown
   selector value, an unsupported `schema_version`, or an absent shard/manifest field each renders an inline
   notice (display-first), not a crash; a 403 serves cached data + the rate-limit banner.

### Non-Functional Tests
1. **Size check**: the exported launch dataset is **≤ 8 MB total** and **each tradition shard ≤ 1 MB** (a
   CI assertion on the committed output, using the exact byte ceilings).
2. **Export parity**: the export's tradition-means match `report.json` / `stats_bundle.json` within numeric
   tolerance (self-check against the canonical aggregator).
3. **API-budget**: loading the explorer adds no new on-budget API calls beyond the existing git-tree poll
   (verified via the fake-fetch harness call log).

## Dependencies
- **External Services**: GitHub (`api.github.com` git-trees + `raw.githubusercontent.com`), read-only,
  unauthenticated — already the SPA's only dependency. Railway static hosting for deploy (manual `railway up`).
- **Internal Systems**: `workflows/analysis/analysis/aggregate.py` (+ `colors.py` palette) as the canonical
  aggregation/palette source; `workflows/judging` output schema (Spec 8) as the input contract; the
  `multibrowser` data layer (`src/lib/github.ts`, `queries.ts`, `filtering.ts`, `searchParams.ts`) and the
  reserved results seam (`results.ts`, `ScenarioResults`, `ResultsRegion`).
- **Libraries/Frameworks**: existing SPA deps (TanStack Router/Query, HeroUI v3, Tailwind 4, Vitest); Python
  `uv` toolchain for the export (consistent with `workflows/analysis` and the validator).

## References
- Issue #49 (this project) — feature definition, constraints, acceptance, PR strategy.
- `codev/specs/7-jaleesbrowser-browse-explore-m.md` + review — the corpus browser and the reserved,
  deferred results seam (§4.1).
- `codev/specs/26-workflows-analysis-port-jalees.md` — the analysis port: cell/breakdown/scope/steadfastness
  definitions, the `report.json` contract, numeric-only "no band names" rule, asymmetric-panel handling.
- `codev/resources/arch-critical.md` / `lessons-critical.md` — SPA shape, client-side GitHub data-layer
  rules, HeroUI v3 provider-less, multi-app porch checks.
- `workflows/analysis/analysis/aggregate.py`, `colors.py`; run-level `analysis-out/figures-report-v2/stats_bundle.json`
  (`subj_overall` = paper standings point estimates + CIs).
- External JaleesBench (`github.com/iaser-ai/jaleesbench`) — the explorer-feature reference the issue cites
  (not readable from this worktree; the standings convention was reconstructed and verified from launch data).

## Risks and Mitigation
| Risk | Probability | Impact | Mitigation Strategy |
|------|------------|--------|-------------------|
| Leaderboard drifts from the paper's numbers | Medium | High | Publish canonical tradition-means from `workflows/analysis`; SPA does only mean-of-means (verified exact); add an export-parity test against `report.json`/`stats_bundle.json`. |
| Export exceeds single-digit MB | Low | Medium | Aggregates-only, no transcripts/rationale in v1; per-tradition shards; a size assertion in CI; per-scenario layer gated on fitting the budget. |
| Opus judge-alias double-counting | Medium | High | Normalize both aliases to one judge; dedup by normalized identity with later-`ts`-wins overlay; test the disjoint-sum and collision-dedup cases; the SPA never sees two Opus judges. |
| Subject-id split → 10 subjects / wrong Qwen merge | High | High | Explicit subject alias map (not prefix-strip); test asserting exactly five canonical subjects incl. the Qwen `-Instruct` case. |
| Tiny-non-zero Opus sample presented as authoritative | High | High | `min_coverage` rule (default 0.5) excludes low-coverage tradition-means from the mean-of-means; drill-down badges `sample (n/N)`; leaderboard shows `k/7` contributing traditions. |
| Results silently vanish on a truncated git tree | Medium | High | Extend the per-directory fallback to walk `results/` as well as `traditions/`; regression test with a `truncated` fake tree. |
| Malformed remote dataset crashes the SPA | Medium | Medium | Versioned manifest + zod validation of shards; out-of-range/non-finite/unknown values and missing shards render inline notices, not crashes. |
| `framings-opus-sample` still moving at export | High | Medium | Re-runnable export; regenerate the committed dataset once the architect seals the sample; manifest records coverage-as-of-export. |
| Breaking corpus browsing | Low | High | Additive routes/facets only; reuse existing data layer; keep existing tests green; new tests via `fakeFetch`/`renderApp`. |

## Expert Consultation
**Date**: 2026-08-05
**Models Consulted**: Codex (GPT) and Claude (2-way per this repo's `porch.consultation.models=[codex,claude]`
— Gemini's per-phase consult cannot see the worktree here).

Both returned **REQUEST_CHANGES** (HIGH confidence). Every issue below was independently verified against the
real run data before incorporation.

**Sections Updated (iteration 1 feedback):**
- **Subject-id alias split** (Claude, verified): source runs spell subjects differently (`anthropic/claude-sonnet-5`
  vs `claude-sonnet-5`; Qwen drops `-Instruct`) → naive merge yields 10 subjects. Added explicit subject
  alias-map requirement + test (Constraints, Success Criteria, Test Scenario 3); fixed the false "five
  subjects" claim in Assumptions; documented in Current State.
- **Tiny-non-zero Opus coverage** (Claude, verified: secular-sage stated/full ≈ 2 cells vs sunni-islam ≈ 230):
  added the `min_coverage` rule (default 0.5) excluding low-coverage tradition-means from the mean-of-means,
  with `k/7` annotation (Desired State, Success Criteria, Test Scenario 6); promoted the ranking question to
  Critical.
- **Truncation fallback** (both, verified `github.ts` walks only `traditions/`): added the requirement to
  extend the fallback to `results/` + regression test (Constraints, Success Criteria, Test Scenario 8); qualified
  the "one git-tree call" property.
- **`n_expected` undefined** (both): pinned the coverage denominator to the full grid (Constraints data contract).
- **Judge/subject ambiguity for `gemini-3.6-flash`** (Claude): disambiguated judge vs subject throughout
  (Current State, Desired State, reconciliation table).
- **Opus alias collision vs "sum of aliases"** (Codex): defined normalized identity + later-`ts`-wins overlay
  dedup (Constraints, Test Scenario 2).
- **Asymmetric turn1/full panels** (both): steadfastness test now uses a matched-cell definition (Test Scenario 5).
- **Exact size limits** (Codex): replaced "single-digit MB" with CI-enforceable ≤ 8 MB total / ≤ 1 MB per shard.
- **Runtime dataset validation** (Codex): added schema-version + zod validation requirement (Constraints,
  Success Criteria, Test Scenario 9).
- **Sample sealing** (both): explicitly permitted an interim re-runnable export rather than blocking (Assumptions,
  Open Questions).

Note: All consultation feedback has been incorporated directly into the relevant sections above.

## Approval
- [x] Technical Lead Review — architect, 2026-08-06 (with Approved Decisions)
- [x] Product Owner Review — Waleed, 2026-08-06 (the two simplifying decisions)
- [x] Stakeholder Sign-off — 2026-08-06
- [x] Expert AI Consultation Complete — Codex + Claude, iteration 1

## Notes
- **Scope boundary**: the leaderboard/drill-down is a new top-level `/results` route family (with
  deep-linkable judge/pressure/framing/scope selectors, mirroring the corpus filter machinery). Wiring the
  per-scenario `ResultsRegion` seam on the scenario page is optional (Open Question) and not required for
  acceptance.
- **Why not per-cell in the SPA**: the paper-reconciliation acceptance is safest when the ranking statistic
  is computed by the canonical Python and the SPA does only an equal-weight mean — hence pre-aggregated
  shards rather than a TS re-implementation of the aggregation convention.
