# spir-49 — multibrowser: results explorer (judge & pressure selectors + leaderboard)

Builder for Spec 49. STRICT mode (porch-orchestrated). Started 2026-08-05.

## Phase: Specify (in progress)

Spec file did not exist at spawn — writing it fresh from issue #49 + reference data.

### Context gathered (pre-draft)

**Run data** (`tmp/judging-runs/` — READ-ONLY symlink to architect's data; never commit from it):
- Canonical launch set: `20260803-merged` (Gemini 3.6 Flash, full grid) + `20260803-unstated-opus`
  (Opus, unstated only, full grid) + `20260803-framings-opus-sample` (Opus, stated/guided SAMPLE).
- `framings-opus-sample` is a LIVE tail-fill (still appending) — counts are moving until architect
  seals it. It also carries the Opus alias split: `claude-opus-4-8` (batch) + `anthropic/claude-opus-4.8`
  (OpenRouter tail). Export MUST alias-normalize to one Opus judge.

**Data schema** (per tradition dir): `sittings.jsonl` (subject, tradition, scenario_id, pressure,
framing, turns[], usage) + `judgments.jsonl` (sitting_key, subject, tradition, scenario_id, pressure,
framing, judge, scope, score, direction, rationale, raw, usage). Also `report.json`/`report.md` per
tradition + `analysis-out/` (analysis_stats.json, figures, report-v2 html/pdf + stats_bundle.json).
- Grid: 5 subjects × 3 framings × 6 pressures × N scenarios (buddhism 52 … sunni-islam 140).
- `scope` ∈ {`turn1` (first-response), `full` (post-pressure)} — 2 judgments per sitting.
- Raw run = 583MB. Export target: single-digit MB, sharded per tradition, SCORES + METADATA ONLY
  (no transcript turns, likely drop rationale/raw to hit budget — open question in spec).

**Aggregation convention** (`workflows/analysis/analysis/aggregate.py` — CANONICAL, reuse it):
- cell = (subject, scenario_id, pressure, framing, scope); cell score = mean of present judges' scores.
- breakdown mean = unweighted mean of in-scope cell scores.
- headline = unstated framing, `full` scope; steadfastness = full − turn1.
- Leaderboard/standings = **mean of per-tradition means** (equal weight per tradition), per
  subject × framing × scope; matches paper Table `tab_standings`. Source: `stats_bundle.json.subj_overall`
  = subject|framing → [mean, ci_lo, ci_hi] (bootstrap CIs, seed 12345, n_boot 5000).

**SPA** (`apps/multibrowser/`, Vite6/React19/TS/Tailwind4/HeroUI v3/TanStack Router+Query):
- Already has a RESERVED inert results seam: `src/components/ResultsRegion.tsx` + `loadResults`
  in `src/lib/results.ts` (§4.1 seam for judging workflow #8). Additive slot exists.
- Data layer: `src/lib/github.ts` (SHA resolve + git-trees 1 call + raw fetch, SHA-pinned),
  `src/lib/queries.ts` (SHA-keyed), `useLatestSha` polls `VITE_SHA_POLL_MS` (5min) + focus/reconnect;
  403 → banner + cached. Unauthenticated 60/hr.
- Palette: `workflows/analysis/analysis/colors.py` — 7-stop diverging (deep red→grey-beige→deep green),
  `score_color` TwoSlopeNorm(−1,0,1) linear. Reuse for score cells.

### Explore agents (done)

**SPA map:** `/results` is a clean additive route — add one `createRoute` (+ `validateSearch`) in
`src/router.tsx` + nav link in `RootLayout`; mirror `src/lib/filtering.ts` + `searchParams.ts` for the
deep-linkable selection model; reuse `FilterBar` `Toggle`/native-`<select>` idiom for the four selectors;
fetch via existing SHA-pinned hooks (`queries.ts`, add a `loadResults`-style loader + `useResults` hook);
HeroUI v3 provider-less, semantic color tokens (no chart lib yet — leaderboard is first dataviz); test via
`fakeFetch` + `renderApp` (Vitest). Reserved seam: `results.ts`/`ScenarioResults`/`ResultsRegion`.

**JaleesBench parity:** the interactive-explorer specifics (judge/pressure selectors, `tab_standings`) are
NOT in this repo — they live in external `github.com/iaser-ai/jaleesbench`. BUT the repo gives the data
contract (Spec 8/26 §4.1), metric defs (headline=unstated/full; steadfastness=full−turn1; scope turn1/full;
numeric −1..+1, NO band names), and the reserved seam. I reconstructed + VERIFIED the standings convention
empirically (see below) — no external read needed.

### KEY VERIFIED FACT (backs the core acceptance criterion)
Leaderboard = equal-weight mean across the 7 traditions of each tradition's `by_framing[framing]` (full
scope) == paper `stats_bundle.subj_overall[subject|framing][0]`, matched to FULL precision for
unstated/stated/guided. So: export publishes per-tradition breakdown means (canonical aggregate.py); SPA's
only client math is a mean-of-per-tradition-means → guaranteed reconciliation + tiny size.

### Design chosen for spec (pre-aggregated, not per-cell)
Export = pre-aggregated per-tradition shards: subject × framing × scope × pressure(+all) × judge → {mean,
coverage(n_judged/n_expected)}, alias-normalized Opus, computed by canonical aggregate.py. + manifest
(subjects/judges/framings/pressures/scopes/counts/dates + per-cell coverage for honest Opus-sample degrade).
No transcripts, no rationale (size budget) — flagged as open Q. Per-scenario drill-down = SHOULD/limited
(size risk). Discovery: `results/*/manifest.json` via git-trees, latest by date, new run → no redeploy.

### Phase: Specify — draft committed (00a871a), 2-way consult done, revised for iter1 feedback.

Both reviewers (codex + claude) → REQUEST_CHANGES, HIGH confidence. All findings verified against real data
before incorporating. Load-bearing catches:
- **Subject-id split** (not just judge aliases): framings-opus-sample uses provider-prefixed lowercase ids;
  Qwen even drops `-Instruct` → naive merge = 10 subjects. Needs EXPLICIT subject alias map + test. (verified)
- **Tiny-non-zero Opus coverage**: secular-sage stated/full ≈ 2 cells vs sunni-islam ≈ 230 — equal 1/7 weight
  is dishonest. Added `min_coverage` rule (default 0.5) → exclude low-coverage tradition-means from
  mean-of-means, show k/7. (verified)
- **Truncation fallback** (`github.ts` walkTraditions) walks ONLY traditions/ → results/ would silently vanish
  on truncated tree. Must extend fallback + test. (verified)
- Plus: n_expected pinned to full grid; judge-vs-subject disambiguation for gemini-3.6-flash; Opus alias
  collision dedup (later-ts-wins overlay); asymmetric turn1/full → matched-cell steadfastness; exact size
  ceilings (≤8MB/run, ≤1MB/shard) for CI; runtime zod validation + schema_version; interim export permitted.

Design still Approach 1 (pre-aggregated per-tradition shards, canonical aggregate.py, SPA does mean-of-means).
Consultation Log filled. Re-committing, then porch next.

### GATE: spec-approval reached (2026-08-05) — STOPPED, waiting for human.

Wrote rebuttal (porch-tracked/gitignored, like consult outputs), ran `porch done` → `porch gate 49`.
Notified architect via `afx send`. Will NOT self-approve. Two Critical open questions surfaced to architect:
`min_coverage` threshold (default 0.5) and how Opus stated/guided ranks in the leaderboard.
Next action (after `porch approve 49 spec-approval` by human): `porch run`/`porch next` → Plan phase.

Commits so far: 00a871a (initial draft), 940d12c (with multi-agent review).

### Spec APPROVED (2026-08-06) + Plan phase.

Architect approved with simplifying decisions (folded into spec §"Approved Decisions", commit 525d843):
- **Leaderboard ranks GEMINI ONLY** (full grid). Opus never ranks; judge selector = inspection/validation
  layer only (drill-down/coverage badges where Opus data exists). Moots the Opus-ranking Critical Q.
- min_coverage no longer a ranking gate — display/badge only.
- pressure=all = cell-pooled mean (confirmed); run discovery = latest-by-manifest-date (selector optional);
  rationale = aggregates-only v1; CIs = optional SHOULD (pooled Gemini only); ResultsRegion seam = inert;
  one re-export at Opus tail-fill seal.

Gate flipped by architect (2ec8f5f). Now PLAN phase.

Dispatcher note: `.codev/checks/test.sh` ALREADY registers workflows/analysis (uv pytest) + apps/multibrowser
(pnpm test) — no dispatcher change needed. Export tool → `workflows/analysis` (Typer `export` cmd), reuses
aggregate.py.

**Plan drafted + revised through 2-way consult** (codex+claude, both REQUEST_CHANGES HIGH, all verified).
6 phases: (1) export core, (2) writer+manifest+CLI+dataset, (3) SPA data layer, (4) leaderboard+selectors
(Gemini-ranked), (5) drill-down+judge/Opus, (6) docs. Linear deps.

Iter-1 plan fixes (load-bearing, verified against code/data):
- **Ingestion**: `loaders.load_run_dir` HARD-FAILS on the 2 Opus runs (no report.json); `load_corpus` rejects
  dup traditions. → purpose-built row reader (reuse is_valid_score/_REQUIRED_JUDGMENT_KEYS); PROMOTE private
  `_mean_over` → public breakdown helper in aggregate.py.
- **judgments_v2.jsonl overlays** exist (buddhism 6, secular-sage 2, sunni 2) → handle overlay; normalize
  judge FIRST then overlay+dedup (overlay key includes judge, excludes tradition).
- **Coverage denominator**: pin n_scenarios to Gemini full grid (report.json.by_scenario), NOT Opus rows
  (else 2-cell panel = ~100% → defeats honest degradation). Validate Opus scenarios ⊆ full grid.
- **Tests**: committed miniature fixtures (deterministic) + skipif real-data parity (tmp/ is gitignored/CI-
  unavailable).
- **Steadfastness OUT OF SCOPE v1** (not a Success Criterion; avoids asymmetric turn1/full panel pitfall).
- Minor: canonical-model-id shards + UI-key map; parseResultsManifest (parseManifest name collision);
  add check-types+build to SPA phases; "CI-asserted" → dispatcher/local (no GitHub pytest job);
  VITE_MULTIBENCH_REF for pre-merge live view.

**DATA SEALED (2026-08-06)**: Opus tail-fill complete (9000 judgments, 0 missing). Collision LIVE: ~1810
sunni-islam cells under both aliases → later-ts dedup runs on real data. Single clean export (no interim).

Commits: spec 00a871a/940d12c/525d843; plan draft (initial) + revised (with multi-agent review).

### GATE: plan-approval reached (2026-08-06) — STOPPED, waiting for human.

Wrote plan rebuttal (porch-tracked), `porch done` → `porch gate 49`. Notifying architect. Will NOT
self-approve. Next (after `porch approve 49 plan-approval`): plan→implement transition, then Phase 1
(export core). NOTE: porch only re-extracts plan phases at plan→implement — 6 phases are locked in now.

### Parity target confirmed (architect, 2026-08-06)
Architect applied v2-then-dedupe to the paper's stats bundle (same semantics as plan) → export parity
reconciles against CURRENT `stats_bundle.json`. Dual-judge/framings_sample: r=0.777, n=9000 (that's the Opus
correlation metric, not Gemini standings). RE-VERIFIED just now: all 15 Gemini subject×framing
mean-of-per-tradition-means == current `subj_overall[·][0]` to <1e-9 — merged run has NO v2 overlay so the
Gemini leaderboard target (the acceptance-critical one) is unmoved. **Phase 1 parity anchor: judge=Gemini
mean-of-means must equal stats_bundle.subj_overall exactly (1e-9).** Opus parity is the dual-judge stats, not
a ranking.

### Plan CONDITIONAL APPROVAL (Waleed, 2026-08-06): steadfastness INTO v1 scope.
Reversed my iter1 scope-out. Amended plan (pre-approval, no rollback): steadfastness = matched-cell
(full−turn1, cells present in BOTH scopes) added as a third leaderboard METRIC (first-response/post-pressure/
steadfastness), pressure-filterable, per-tradition drill-down, Gemini-ranked, Opus badged-validation.
- Export (Phase 1/2): new steadfastness slice {subject×framing×pressure-incl-all×judge → {steadfastness,
  matched_n}}. Gemini panels balanced → matched-cell == report.json scorecard.steadfastness (+by_pressure) =
  parity anchor. Opus matched-cell handles asymmetry.
- UI (Phase 4/5): metric toggle (turn1/full/steadfastness); reads shard steadfastness slice directly (no
  client subtraction → preserves matched-cell def). NOTE: spec Test 5 already specified matched-cell, so plan
  now MATCHES spec (my iter1 scope-out had diverged).
Architect said NO re-consult needed (not structural). Committing amended plan → message architect → they
approve gate.

### Plan APPROVED (2026-08-06, gate 3c9d995). IMPLEMENT phase.

**Phase 1 (export core) — DONE, committing.**
- `aggregate.py`: promoted private `_mean_over` → public `breakdown_mean` (+ back-comat alias). 81 existing
  analysis tests still green (non-breaking).
- New `analysis/export_results.py`: explicit subject+judge alias maps (fail-fast on unmapped), purpose-built
  row reader (NOT load_run_dir — Opus runs have no report.json), v2-then-dedupe with later-ts (resolves the
  live ~1801 sunni-islam alias collisions), coverage pinned to Gemini full-grid universe (report.json
  by_scenario), matched-cell steadfastness, per-(judge,subject,framing,scope,pressure-incl-all) slice means.
- New `tests/test_export_results.py`: 7 deterministic unit tests (synthetic run roots in tmp_path — no
  tmp/judging-runs dep) + 3 skipif real-data parity tests. 11 pass. Ruff clean. Full suite 92 pass.
- VERIFIED real-data: all 15 Gemini mean-of-means == subj_overall (<1e-9); steadfastness == report.json
  (headline + by_pressure) all traditions; secular-sage Opus stated coverage honestly 18/294 (~6%, sealed
  data); Gemini full-grid 312/312.
Commit: [Spec 49][Phase: export-core]. Then porch done (dispatcher runs workflows/analysis pytest + per-phase
consult codex+claude).
