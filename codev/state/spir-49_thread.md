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
Commit: [Spec 49][Phase: export-core] (888d506). porch done → tests pass → per-phase consult.

**Phase 1 consult iter1**: Claude APPROVE, Codex REQUEST_CHANGES (overlapping valid points). Addressed:
- v2 orphan now REJECTED (loader "never adds a vote"); same-file dup base identity REJECTED (loader parity).
- Tightened real-data tests: observed subjects==5 canonical & judges=={gemini,opus} (not len); added
  per-tradition Gemini by_framing==report.json parity; added LIVE sunni-islam alias-collision dedup test
  (deduped < raw, all identities unique).
- Added committed fixtures tests/fixtures/export/ (gemini-run + opus-run, README) + end-to-end test.
- Cleanups: removed dead _IDKEY, shared _NORM_FIELDS, multi-report universe consistency check.
Full suite 97 pass, 0 skip. Ruff clean. Rebuttal written. Re-committing → porch done.

Phase 1 consult iter2: Codex REQUEST_CHANGES (v2 dup precedence should be file-order not ts; add disjoint-
alias test), Claude APPROVE. Fixed: v2 same-identity dedup = file-order last-wins (loader parity), later-ts
only for base cross-alias collision; added disjoint-alias (count==sum) + v2 file-order regression tests.
Phase 1 consult iter3: **BOTH APPROVE** (unanimous). 99 pass, 0 skip. Commits 888d506, +2 fix commits.
Advancing to Phase 2 (export writer/manifest/CLI + committed launch dataset — must PING ARCHITECT before
committing the dataset to eyeball size+manifest).

### Phase 2 (export writer/manifest/CLI) — code done, dataset pending architect eyeball.
- export_results.py: serialize_tradition (shard), build_manifest, write_dataset (size ceilings ≤8MB/≤1MB),
  export_dataset; added n_judgments to TraditionExport. cli.py: `analysis export` Typer command.
- 7 Phase 2 tests (manifest fields+judge consistency, shard round-trip, deterministic write, size-ceiling,
  end-to-end). 23 export tests total, ruff clean.
- Generated launch dataset results/20260803/ via CLI: 174KB total, largest shard 26KB (sunni-islam), 8 files.
  Manifest: 5 subjects, 2 judges (opus absorbs both aliases sample=true; gemini full_grid), counts
  gemini=93420 (matches issue!) opus=40114, 7 traditions w/ n_scenarios.
- Leaderboard recomputed FROM WRITTEN SHARDS == paper (all 15). 
- Code committed; DATASET commit HELD pending architect eyeball (they asked). Pinged architect, waiting.

**Phase 2 DATASET APPROVED** by architect (independently re-verified: 105 by-framing + 35 steadfastness ==
report.json; counts reconcile 93420=46710×2, 40114=31114+9000). Committed results/20260803/ (3c3224c).
Phase 2 consult iter1: Codex REQUEST_CHANGES / Claude APPROVE → added manifest coverage summary (Gemini 100%,
Opus unstated 99.9% / stated-guided 14.5% — replaces misleading per-judge sample flag), validate-before-write
+ stale-prune in write_dataset, committed-artifact tests, fail-fast/malformed-JSON/cli fixes.
Phase 2 consult iter2: Codex COMMENT (non-blocking) / Claude APPROVE → polished CLI output (counts) + CLI
command tests. 110 tests pass. Phase 2 DONE. **PR gate held for WALEED (not architect).**

### Phase 3 (SPA results data layer) — STARTING.
Plan: new resultsModel.ts (zod, parseResultsManifest — avoid parse.ts parseManifest collision), discovery +
useResults hooks in queries.ts, extend github.ts walkTraditions→results/ (truncation fallback), runtime
validation → Notice not crash. Tests via fakeFetch/renderApp. VITE_MULTIBENCH_REF for pre-merge view.

**Phase 3 CODE done, 13 results-data tests pass, typecheck clean, build OK.**
- github.ts: walkTraditions→walkTopDirs (truncation fallback now covers traditions/ AND results/).
- resultsModel.ts (new): zod schemas + parseResultsManifest/parseResultsShard (fail-soft → Notice; score
  ranges; unsupported schema_version rejected). Fixed a bug: coverage schema had one rec() too many.
- queries.ts: resultsRunIds, loadResultsRuns (latest-by-date default), loadResultsManifest, loadResultsShard
  + useResultsRuns/useResultsShard hooks.
- fakeRepo.ts: non-recursive git-trees support (truncation walk) + resultsFiles() helper.

⚠️ BLOCKER (pre-existing, NOT mine): src/deploy.test.ts "REAL smoke" fails in sandbox. Confirmed git status:
deploy.test.ts/package.json/vite.config.ts UNTOUCHED by me. Cause: sandbox node v26 (app engine wants 20.x);
PORT=4199 not propagating to `serve -s dist -l ${PORT:-4173}` → server binds 4173, test polls 4199 → timeout.
Full suite: 109 pass / 1 fail (only this smoke). Since Phase 3 touches apps/multibrowser, porch dispatcher
runs `pnpm test` → this fails → blocks porch-done. It's the architect's deploy guard → NOTIFYING before any
skip. Proposed: conditional skip on node major != 20 (preserves CI coverage). Awaiting architect guidance.

**RESOLVED by architect**: my node/PORT diagnosis was WRONG. Real cause: a leaked `serve` grandchild from the
defunct air-46 worktree squatting on port 4199 since Monday (test killed the pnpm wrapper, not the serve
grandchild; dead worktree's dist deleted → 404s; new serves fell back to ephemeral ports). Architect killed it.
Deploy smoke now passes (554ms), full multibrowser suite 110/110 green, port 4199 clean after run.
Applied architect-requested HARDENING to deploy.test.ts (authorized): (1) spawn detached:true + finally kills
the process GROUP (process.kill(-pid,SIGTERM) try/catch → server.kill()); (2) assertPortFree(4199) pre-flight
with fail-fast diagnostic naming the leaked-serve cause. To note in review doc. → porch done Phase 3.

**Phase 3 consult**: Claude APPROVE all 3 iters; Codex REQUEST_CHANGES each iter (incremental hardening, all
addressed): iter1 shard↔manifest cross-validation + instant date sort; iter2 shard.judges[] validation;
iter3 manifest-own-vocab validation + absent-counts degradation notices. Porch hit its **iter-3 SAFETY
CEILING and force-advanced to Phase 4** (eb272eb) — iter3 fixes committed (e2e71eb) but not formally
re-reviewed. All Codex points addressed in good faith; 119 multibrowser tests pass, typecheck+build clean.
NOTE FOR REVIEW/PR: Phase 3 force-advanced (Codex's final verdict was still REQUEST_CHANGES though its points
were fixed); the final PR CMAP will re-review the full diff. deploy.test.ts hardening to note in review too.

### Phase 4 (leaderboard route + framing/metric/pressure selectors, Gemini-ranked) — DONE.
- scoreColor.ts: TS port of colors.py 7-stop diverging palette (TwoSlopeNorm −1,0,1 linear) + text color.
- resultsSelection.ts: Metric type, ResultsSelection, resultsSearchSchema (fail-soft), parse (defaults +
  manifest-vocab clamping) / serialize (omit defaults → clean URL).
- leaderboard.ts: computeStandings = equal-weight mean of per-tradition means (Gemini full-grid judge),
  turn1/full read means slice, steadfastness reads steadfastness slice (no client subtraction); null
  coverage excluded not zeroed; contributions kept for Phase 5 drill-down.
- queries.ts: loadResultsRun/useResultsRun (manifest + all shards).
- ResultsPage.tsx + /results route + RootLayout nav link. Segmented single-select controls (framing/metric/
  pressure), standings table with score-colored cells + k/N traditions.
- Tests: scoreColor(4) + resultsSelection(7) + leaderboard(6) + results route(5) = 22. Full suite 141 pass,
  typecheck + build clean. Deep-link verified (metric=turn1 in URL); Gemini-ranked; empty-state.
Phase 4 consult: iter1 both REQUEST_CHANGES (page swallowed notices → blank on malformed; missing real-number
reconciliation; steadfastness coverage always 100%; selector coverage). Fixed: surface all data notices +
validate ?run= + real committed-dataset reconciliation test (gemini==paper all framings/7 trads) + steadfast
coverage = full-grid denom + framing/pressure/steadfastness UI tests. iter2 **BOTH APPROVE** (unanimous).
147 tests pass. Commits under [Phase: leaderboard].

### Phase 5 (drill-down + judge selector + Opus validation layer) — STARTING.
Judge selector switches drill-down/inspection to Opus (badged sample n/N) where data exists; NEVER re-ranks
(leaderboard stays Gemini). Per-tradition drill-down (means + steadfastness), pressure-filterable. contributions
already computed in computeStandings (Phase 4). Coverage badges from n_judged/n_expected per slice.

**Phase 5 DONE.** leaderboard.ts: subjectTraditionValues (per-tradition values for a specific judge, omits
missing → honest zero-coverage hidden). ResultsPage: judge selector (Segmented, "gemini (ranking)"/"opus
(validation)"), Opus caption when non-full-grid judge selected, expandable standings rows → per-tradition
drill-down (score-colored + n/N coverage + "sample" badge when nJudged<nExpected & judge is sample). KEY:
judge selector re-points ONLY the drill-down; leaderboard ranking stays Gemini (structurally — computeStandings
always uses rankingJudgeModel). Tests: subjectTraditionValues unit + drill-down + judge-switch-doesn't-rerank
+ Opus partial-coverage (taoism omitted, buddhism badged sample). 150 tests pass, typecheck + build clean.
Phase 6 next: docs (results/README data contract + multibrowser README). Then Review + PR (gate for WALEED).

Phase 6 consult: iter1 Claude REQUEST_CHANGES (doc↔impl contradictions: run selection, stale "no results UI"
bullet, byte-stable overclaim, score ranges, judges order), Codex APPROVE → all fixed. iter2 **BOTH APPROVE**.

### REVIEW phase — DONE. PR #50 OPEN.
- Review doc written (codev/reviews/49-...md): spec compliance, deviations, metrics (64 commits, 260 tests),
  consultation summary, lessons.
- Arch/lessons routed via update-arch-docs skill: HOT arch-critical (+results-tier fact, 7→8), HOT
  lessons-critical (+reconciliation pattern, 9→10), COLD lessons-learned (+porch force-advance, +shared-port
  zombie-serve reap-group).
- e2e green: py 110, js 150, typecheck+build clean. Branch pushed. **PR #50** created (Closes #49).
- (.claude/hooks/ untracked = harness local config, pre-existing, NOT committed — not my deliverable.)
- **PR gate is held for WALEED** (architect said so). Notifying. Do NOT merge myself.

**Phase 5 consult: BOTH APPROVE first iteration** (judge selector structurally can't re-rank; steadfastness
denominators correct; zero-coverage omission verified vs real shards). Only cosmetic suggestions.

### Phase 6 (docs) — DONE.
- results/README.md: full data contract (layout, export command, manifest+shard schema, cell arrays,
  semantics [cell/pooled-all/steadfastness/coverage], normalization [subject/judge alias+dedup+v2], explorer
  behavior, size ceilings).
- apps/multibrowser/README.md: added Results explorer section (leaderboard mean-of-means Gemini-ranked,
  deep-linkable framing/metric/pressure selectors, judge selector = Opus validation drill-down never re-ranks,
  display-first notices).
Docs only. → porch done → consult. Then Review phase (arch-docs via update-arch-docs skill) + PR (WALEED gate).
